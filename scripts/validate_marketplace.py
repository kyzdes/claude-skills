#!/usr/bin/env python3
"""Validate the catalog, published sources, and isolated plugin-only installs.

No command in this validator starts a Claude session or executes plugin code.
The explicit private-repository waiver produces partial coverage, never a pass.
"""
import argparse
import base64
import concurrent.futures
import functools
import json
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import shutil
import signal
import subprocess
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parent.parent
REPO_URL = re.compile(r"https://github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)\.git\Z")
NAME = re.compile(r"[a-z0-9][a-z0-9-]*\Z")
SHA = re.compile(r"[0-9a-f]{40}\Z")
PLUGIN_ROOT = re.compile(r"\$\{PLUGIN_ROOT:-\$\{CLAUDE_PLUGIN_ROOT\}\}|\$\{(?:CLAUDE_PLUGIN_ROOT|PLUGIN_ROOT)\}|\$(?:CLAUDE_PLUGIN_ROOT|PLUGIN_ROOT)(?=/|$)")
SHARED_UPDATERS = ("scripts/auto-update.sh", "scripts/auto_update.py")
VALIDATED = {"passed", "local-passed"}


def validate_catalog(data, policy):
    if not isinstance(data, dict) or data.get("name") != "claude-skills":
        raise ValueError("marketplace name is invalid")
    if not isinstance(data.get("owner"), dict) or not data["owner"].get("name"):
        raise ValueError("marketplace owner is invalid")
    if not re.fullmatch(r"\d+\.\d+\.\d+", data.get("metadata", {}).get("version", "")):
        raise ValueError("catalog version must be x.y.z")
    entries = data.get("plugins")
    if not isinstance(entries, list) or not entries:
        raise ValueError("plugins must be a non-empty list")
    names, repos = set(), set()
    for item in entries:
        if not isinstance(item, dict):
            raise ValueError("plugin entries must be objects")
        name = item.get("name", "")
        if not isinstance(name, str) or not NAME.fullmatch(name) or name in names:
            raise ValueError("invalid or duplicate plugin name")
        names.add(name)
        if not isinstance(item.get("description"), str) or not item["description"].strip():
            raise ValueError("missing description: " + name)
        source = item.get("source", {})
        if not isinstance(source, dict) or not isinstance(source.get("url"), str):
            raise ValueError("source must be a full HTTPS GitHub .git URL: " + name)
        match = REPO_URL.fullmatch(source["url"])
        if source.get("source") != "url" or not match:
            raise ValueError("source must be a full HTTPS GitHub .git URL: " + name)
        if set(source) - {"source", "url", "ref", "sha"}:
            raise ValueError("unsupported source options: " + name)
        if "sha" in source and (not isinstance(source["sha"], str) or not SHA.fullmatch(source["sha"])):
            raise ValueError("source sha must be a full lowercase commit SHA: " + name)
        if "ref" in source and (not isinstance(source["ref"], str) or not source["ref"].strip()):
            raise ValueError("source ref must be a nonempty string: " + name)
        repo = match.group(1)
        if repo in repos:
            raise ValueError("duplicate source repository: " + name)
        repos.add(repo)
    if not isinstance(policy, dict):
        raise ValueError("catalog policy must be an object")
    for key, allowed in (("private_repositories", repos), ("shared_updater_plugins", names)):
        values = policy.get(key, [])
        if not isinstance(values, list) or any(not isinstance(v, str) for v in values):
            raise ValueError(key + " must be a list of strings")
        if len(values) != len(set(values)) or not set(values) <= allowed:
            raise ValueError(key + " contains duplicates or entries outside the catalog")
    renames = data.get("renames", {})
    if not isinstance(renames, dict):
        raise ValueError("renames must be an object")
    for previous, target in renames.items():
        if not NAME.fullmatch(previous) or previous in names:
            raise ValueError("invalid or still-listed rename source")
        if target is not None and (not isinstance(target, str) or not NAME.fullmatch(target)):
            raise ValueError("invalid rename target: " + previous)
        seen, current = set(), previous
        while current in renames:
            if current in seen:
                raise ValueError("rename cycle: " + previous)
            seen.add(current)
            current = renames[current]
        if current is not None and current not in names:
            raise ValueError("rename target missing: " + previous)
    return entries


def run_bounded(args, *, timeout, env=None, cwd=None, capture=True):
    """Kill the entire process group on timeout; never include output in errors."""
    target = subprocess.PIPE if capture else subprocess.DEVNULL
    proc = subprocess.Popen(args, stdin=subprocess.DEVNULL, stdout=target, stderr=target,
                            env=env, cwd=cwd, text=True, start_new_session=os.name != "nt")
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
        else:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        proc.communicate(timeout=10)
        raise TimeoutError("command exceeded its time budget") from None
    return subprocess.CompletedProcess(args, proc.returncode, stdout, stderr)


@functools.lru_cache(maxsize=1)
def github_token():
    token = os.environ.get("MARKETPLACE_READ_TOKEN") or os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token and shutil.which("gh"):
        try:
            proc = run_bounded(["gh", "auth", "token", "--hostname", "github.com"], timeout=10)
            if proc.returncode == 0:
                token = proc.stdout.strip()
        except (OSError, TimeoutError):
            pass
    return token


def api(path, timeout=30):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "kyzdes-marketplace-validator"}
    token = github_token()
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request("https://api.github.com/" + path, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.load(response)


def safe_error(error):
    # Never print response bodies, subprocess output, environment, or credentials.
    if isinstance(error, urllib.error.HTTPError):
        return "GitHub API returned HTTP " + str(error.code)
    if isinstance(error, urllib.error.URLError):
        return "GitHub API network request failed"
    if isinstance(error, TimeoutError):
        return "operation exceeded its time budget"
    if isinstance(error, json.JSONDecodeError):
        return "invalid JSON (line " + str(error.lineno) + ")"
    if isinstance(error, ValueError):
        message = str(error)
        for key, value in os.environ.items():
            if value and len(value) >= 8 and any(part in key.upper() for part in ("TOKEN", "SECRET", "PASSWORD", "API_KEY")):
                message = message.replace(value, "[redacted]")
        return message
    return type(error).__name__ + " while validating source or installation"


def relative_file(value):
    if not isinstance(value, str):
        raise ValueError("plugin file paths must be strings")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or "\\" in value or not path.parts:
        raise ValueError("plugin file path must stay inside its source")
    return str(path)


def validate_source_files(entry, manifest, tree, read, policy):
    name = entry["name"]
    if not isinstance(manifest, dict) or manifest.get("name") != name:
        raise ValueError(name + ": manifest name does not match catalog")
    if tree.get("truncated"):
        raise ValueError(name + ": truncated tree cannot be validated")
    files = {item["path"]: item for item in tree["tree"] if item["type"] == "blob"}
    skills = [p for p in files if p.startswith("skills/") and p.endswith("/SKILL.md")]
    if not skills:
        raise ValueError(name + ": no packaged SKILL.md")

    def require(path):
        path = relative_file(path)
        if path not in files or files[path].get("mode") == "120000":
            raise ValueError(name + ": missing regular plugin file: " + path)
        return path

    require(".claude-plugin/plugin.json")
    for path in skills:
        require(path)
        if files[path].get("size") == 0:
            raise ValueError(name + ": empty SKILL.md: " + path)
    configs = []
    config_paths = set()
    if "hooks/hooks.json" in files:
        config_paths.add("hooks/hooks.json")
    declared = manifest.get("hooks", [])
    if not isinstance(declared, list):
        declared = [declared]
    for item in declared:
        if isinstance(item, str):
            config_paths.add(require(item))
        elif isinstance(item, dict):
            configs.append(item)
        else:
            raise ValueError(name + ": invalid manifest hooks configuration")
    configs += [json.loads(read(require(p))) for p in sorted(config_paths)]
    hook_targets = set()
    for config in configs:
        if not isinstance(config, dict) or not isinstance(config.get("hooks"), dict):
            raise ValueError(name + ": hooks configuration must contain a hooks object")
        for groups in config["hooks"].values():
            if not isinstance(groups, list):
                raise ValueError(name + ": hook event must contain a list")
            for group in groups:
                if not isinstance(group, dict) or not isinstance(group.get("hooks"), list):
                    raise ValueError(name + ": hook matcher must contain a hooks list")
                for hook in group["hooks"]:
                    if not isinstance(hook, dict) or hook.get("type") not in ("command", "prompt", "agent", "http"):
                        raise ValueError(name + ": unsupported hook type")
                    if hook["type"] != "command":
                        continue
                    command = hook.get("command")
                    if not isinstance(command, str) or not command.strip():
                        raise ValueError(name + ": command hook is empty")
                    lexer = shlex.shlex(command, posix=True, punctuation_chars="();<>|&")
                    lexer.whitespace_split = True
                    for token in lexer:
                        for match in PLUGIN_ROOT.finditer(token):
                            suffix = token[match.end():]
                            if not suffix:
                                continue
                            if not suffix.startswith("/") or "$" in suffix or "`" in suffix:
                                raise ValueError(name + ": cannot resolve plugin-root hook target")
                            hook_targets.add(require(suffix[1:]))
    # Agentix has its own scoped implementation. The explicit consumers below
    # must ship both exact reviewed files; omission cannot evade this check.
    if name in policy.get("shared_updater_plugins", []):
        for path in SHARED_UPDATERS:
            require(path)
            expected = (ROOT / "templates/plugin-update" / Path(path).name).read_text(encoding="utf-8")
            if read(path) != expected:
                raise ValueError(name + ": shared updater differs from reviewed template: " + path)
    for path in hook_targets | (set(SHARED_UPDATERS) & files.keys()):
        content = read(path)
        if re.search(r"for\s+\w+\s+in\s+\w+\.get\(\s*['\"]plugins['\"]\s*,\s*\{\s*\}\s*\)", content):
            raise ValueError(name + ": legacy cross-plugin updater is forbidden: " + path)


def local_files(root):
    proc = run_bounded(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=root, timeout=10)
    if proc.returncode:
        raise ValueError("local source must be a Git working tree")
    files = []
    for path in sorted(set(proc.stdout.rstrip("\0").split("\0")) - {""}):
        source = root / relative_file(path)
        if source.is_file() or source.is_symlink():
            files.append({"path": path, "type": "blob", "mode": "120000" if source.is_symlink() else "100644", "size": source.lstat().st_size})
    return {"tree": files}


def source_check(entry, policy, allow_skip=False, local_sources=None, timeout=120):
    name = entry["name"]
    repo = REPO_URL.fullmatch(entry["source"]["url"]).group(1)
    base = {"name": name, "repository": repo}
    deadline = time.monotonic() + timeout
    local = local_sources / repo.split("/", 1)[1] if local_sources else None
    if local and local.is_dir():
        local = local.resolve()
        tree = local_files(local)
        def read(path):
            file = local / relative_file(path)
            if not file.resolve().is_relative_to(local) or file.is_symlink():
                raise ValueError(name + ": source file escapes local plugin")
            return file.read_text(encoding="utf-8")
        head = run_bounded(["git", "rev-parse", "HEAD"], cwd=local, timeout=10)
        if head.returncode or not SHA.fullmatch(head.stdout.strip()):
            raise ValueError(name + ": local source has no valid HEAD")
        commit = head.stdout.strip()
        dirty = run_bounded(["git", "status", "--porcelain"], cwd=local, timeout=10)
        if dirty.returncode:
            raise ValueError(name + ": cannot read local source status")
        base.update(mode="local-working-tree", local_path=str(local), dirty=bool(dirty.stdout), remote_metadata="not-checked")
    else:
        def request(path):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError()
            return api(path, timeout=min(30, remaining))
        try:
            meta = request("repos/" + repo)
        except urllib.error.HTTPError as error:
            if (error.code == 404 and repo in policy["private_repositories"] and allow_skip
                    and not os.environ.get("MARKETPLACE_READ_TOKEN")):
                return dict(base, status="private-skipped", mode="remote",
                            reason="Allowlisted private source returned 404 without MARKETPLACE_READ_TOKEN; existence, state, contents, and install were not verified")
            raise
        if meta.get("archived") or meta.get("disabled"):
            raise ValueError(name + ": source is archived or disabled")
        if bool(meta.get("private")) != (repo in policy["private_repositories"]):
            raise ValueError(name + ": visibility does not match explicit policy")
        ref = entry["source"].get("sha") or entry["source"].get("ref") or meta["default_branch"]
        revision = request("repos/" + repo + "/commits/" + urllib.parse.quote(ref, safe=""))
        commit = revision["sha"]
        if not SHA.fullmatch(commit):
            raise ValueError(name + ": GitHub did not return a full commit SHA")
        tree_sha = revision["commit"]["tree"]["sha"]
        tree = request("repos/" + repo + "/git/trees/" + tree_sha + "?recursive=1")
        def read(path):
            obj = request("repos/" + repo + "/contents/" + urllib.parse.quote(path, safe="/") + "?ref=" + commit)
            if obj.get("type") != "file" or obj.get("encoding") != "base64":
                raise ValueError(name + ": cannot read source file as base64")
            return base64.b64decode(obj["content"], validate=False).decode("utf-8")
        base.update(mode="remote", remote_metadata="passed")
    # A small memo avoids duplicate API reads of hook targets and updater files.
    read = functools.lru_cache(maxsize=64)(read)
    manifest = json.loads(read(".claude-plugin/plugin.json"))
    validate_source_files(entry, manifest, tree, read, policy)
    return dict(base, status="local-passed" if local and local.is_dir() else "passed", sha=commit, version=manifest.get("version"))


def verify_install(config, entry, result):
    registry = json.loads((config / "plugins/installed_plugins.json").read_text(encoding="utf-8"))
    records = registry.get("plugins", {}).get(entry["name"] + "@marketplace-smoke", [])
    if not isinstance(records, list) or len(records) != 1:
        raise ValueError("isolated install registry must contain exactly one plugin record")
    record = records[0]
    location = Path(record.get("installPath", "")).resolve()
    if not location.is_relative_to(config.resolve()):
        raise ValueError("plugin install escaped its isolated configuration")
    manifest = json.loads((location / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
    if manifest.get("name") != entry["name"]:
        raise ValueError("installed manifest name does not match the requested plugin")
    if not any(location.glob("skills/**/SKILL.md")):
        raise ValueError("installed plugin contains no SKILL.md")
    if result["status"] == "passed" and record.get("gitCommitSha") != result["sha"]:
        raise ValueError("installed Git commit does not match validated source")


def install_smoke(entries, results, client, *, command_timeout=90, total_timeout=600):
    """Install only, with hooks disabled, from a temporary unrelated directory."""
    by_name = {row["name"]: row for row in results}
    selected = []
    for entry in entries:
        result = by_name[entry["name"]]
        result["install_smoke"] = "not-run"
        if result["status"] in VALIDATED:
            selected.append(entry)
        else:
            result["install_smoke"] = "skipped" if result["status"] == "private-skipped" else "not-run"
            result["install_reason"] = "source was not validated"
    if not selected:
        return
    deadline = time.monotonic() + total_timeout
    with tempfile.TemporaryDirectory(prefix="marketplace-smoke-") as tmp:
        root = Path(tmp)
        config, marketplace, cwd = root / "config", root / "catalog", root / "cwd"
        config.mkdir()
        cwd.mkdir()
        (marketplace / ".claude-plugin").mkdir(parents=True)
        (config / "settings.json").write_text(json.dumps({"disableAllHooks": True, "enableAllProjectMcpServers": False}), encoding="utf-8")
        pinned = []
        for entry in selected:
            result = by_name[entry["name"]]
            item = {"name": entry["name"], "description": entry["description"]}
            if result["status"] == "local-passed":
                local = Path(result["local_path"])
                dest = marketplace / "plugins" / entry["name"]
                for file in local_files(local)["tree"]:
                    target = dest / file["path"]
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(local / file["path"], target, follow_symlinks=False)
                item["source"] = "./plugins/" + entry["name"]
            else:
                item["source"] = {"source": "url", "url": entry["source"]["url"], "sha": result["sha"]}
            pinned.append(item)
        (marketplace / ".claude-plugin/marketplace.json").write_text(json.dumps({"name": "marketplace-smoke", "owner": {"name": "kyzdes"}, "plugins": pinned}), encoding="utf-8")
        env = dict(os.environ, CLAUDE_CONFIG_DIR=str(config), GIT_TERMINAL_PROMPT="0", CI="1",
                   CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC="1", DISABLE_TELEMETRY="1", DISABLE_ERROR_REPORTING="1",
                   KKZ_NO_AUTOUPDATE="1", KEYS_KEEPER_NO_AUTOUPDATE="1")
        # Git receives the same GitHub credential as source inspection. Keep it
        # in this child environment only, never argv, files, or CLI output.
        token = github_token()
        if token:
            index = int(env.get("GIT_CONFIG_COUNT", "0"))
            for value in ("", "AUTHORIZATION: basic " + base64.b64encode(("x-access-token:" + token).encode()).decode()):
                env["GIT_CONFIG_KEY_" + str(index)] = "http.https://github.com/.extraheader"
                env["GIT_CONFIG_VALUE_" + str(index)] = value
                index += 1
            env["GIT_CONFIG_COUNT"] = str(index)
        # Model credentials are unnecessary for the plugin-management CLI.
        for key in ("ANTHROPIC_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN", "ANTHROPIC_AUTH_TOKEN"):
            env.pop(key, None)
        def invoke(args):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError()
            proc = run_bounded([client, "plugin"] + args, cwd=cwd, env=env,
                               timeout=min(command_timeout, remaining), capture=False)
            if proc.returncode:
                raise ValueError("plugin-management command failed (exit " + str(proc.returncode) + ")")
        try:
            invoke(["marketplace", "add", str(marketplace)])
        except Exception as error:
            for entry in selected:
                by_name[entry["name"]].update(install_smoke="failed", install_reason="isolated marketplace setup: " + safe_error(error))
            return
        for entry in selected:
            result = by_name[entry["name"]]
            try:
                invoke(["install", entry["name"] + "@marketplace-smoke", "--scope", "user"])
                verify_install(config, entry, result)
                result["install_smoke"] = "passed"
            except Exception as error:
                result.update(install_smoke="failed", install_reason=safe_error(error))


def summarize(report, requested_sources, requested_install):
    rows = report["sources"]
    report["summary"] = {key: sum(row["status"] == value for row in rows) for key, value in (
        ("remote_passed", "passed"), ("local_passed", "local-passed"), ("private_skipped", "private-skipped"), ("source_failed", "failed"))}
    report["summary"].update(install_passed=sum(row.get("install_smoke") == "passed" for row in rows),
                             install_failed=sum(row.get("install_smoke") == "failed" for row in rows))
    failed = bool(report["errors"] or report["summary"]["source_failed"] or report["summary"]["install_failed"])
    if failed:
        report["overall_status"] = "failed"
    elif not requested_sources:
        report["overall_status"] = "catalog-only"
    elif report["summary"]["private_skipped"]:
        report["overall_status"] = "partial"
    elif report["summary"]["local_passed"]:
        report["overall_status"] = "local-validated"
    else:
        report["overall_status"] = "passed"
    report["install_requested"] = requested_install
    return int(failed)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", action="store_true", help="check published GitHub sources")
    parser.add_argument("--install-smoke", action="store_true", help="also install validated sources using plugin-only CLI commands")
    parser.add_argument("--allow-private-unavailable", action="store_true", help="allow explicit private policy entries to report skipped on HTTP 404 without MARKETPLACE_READ_TOKEN")
    parser.add_argument("--local-sources", type=Path, help="use Git working trees under DIR/<repository-name> when present; results do not verify remote publication or state")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    requested_sources = args.sources or args.install_smoke or bool(args.local_sources)
    report = {"catalog_version": None, "plugins": 0, "catalog_status": "not-run", "sources": [], "errors": []}
    try:
        data = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
        policy = json.loads((ROOT / "catalog-policy.json").read_text(encoding="utf-8"))
        entries = validate_catalog(data, policy)
        report.update(catalog_version=data["metadata"]["version"], plugins=len(entries), catalog_status="passed")
        if args.local_sources and not args.local_sources.is_dir():
            raise ValueError("--local-sources must name an existing directory")
        if requested_sources:
            # Resolve auth once before starting workers; no credentials are logged.
            github_token()
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
                futures = {pool.submit(source_check, entry, policy, args.allow_private_unavailable, args.local_sources): entry for entry in entries}
                for future in concurrent.futures.as_completed(futures):
                    try:
                        report["sources"].append(future.result())
                    except Exception as error:
                        entry = futures[future]
                        report["sources"].append({"name": entry["name"], "repository": REPO_URL.fullmatch(entry["source"]["url"]).group(1), "status": "failed", "reason": safe_error(error)})
            report["sources"].sort(key=lambda row: row["name"])
            if args.install_smoke:
                client = shutil.which("claude")
                if not client:
                    raise ValueError("claude is required for --install-smoke")
                install_smoke(entries, report["sources"], client)
    except Exception as error:
        report["errors"].append(safe_error(error))
        if report["catalog_status"] == "not-run":
            report["catalog_status"] = "failed"
    result = summarize(report, requested_sources, args.install_smoke)
    text = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return result


if __name__ == "__main__":
    raise SystemExit(main())
