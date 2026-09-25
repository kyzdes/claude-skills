import base64
import contextlib
import copy
import importlib.util
import io
import json
import os
import shlex
import shutil
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock
import urllib.error

spec = importlib.util.spec_from_file_location("validator", Path(__file__).resolve().parents[1] / "scripts/validate_marketplace.py")
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)
SHA = "a" * 40
TREE_SHA = "b" * 40


class Fixture(unittest.TestCase):
    def setUp(self):
        auth = mock.patch.object(validator, "github_token", return_value=None)
        auth.start()
        self.addCleanup(auth.stop)
        self.entry = {"name": "sample", "description": "A sample", "source": {"source": "url", "url": "https://github.com/kyzdes/sample.git"}}
        self.catalog = {"name": "claude-skills", "owner": {"name": "kyzdes"}, "metadata": {"version": "1.0.0"}, "plugins": [self.entry]}
        self.policy = {"private_repositories": [], "shared_updater_plugins": []}
        self.files = {".claude-plugin/plugin.json": json.dumps({"name": "sample"}), "skills/sample/SKILL.md": "# Sample\n"}

    def tree(self):
        return {"tree": [{"path": path, "type": "blob", "mode": "100644", "size": len(content)} for path, content in self.files.items()]}

    def validate_files(self, manifest=None):
        validator.validate_source_files(self.entry, manifest or {"name": "sample"}, self.tree(), self.files.__getitem__, self.policy)

    def hooks(self, command):
        return json.dumps({"hooks": {"SessionStart": [{"hooks": [{"type": "command", "command": command}]}]}})

    def remote(self, path, timeout=30):
        if path == "repos/kyzdes/sample":
            return {"default_branch": "main", "private": False, "archived": False, "disabled": False}
        if "/commits/" in path:
            return {"sha": SHA, "commit": {"tree": {"sha": TREE_SHA}}}
        if "/git/trees/" in path:
            return self.tree()
        if "/contents/" in path:
            name = path.split("/contents/", 1)[1].split("?ref=", 1)[0]
            return {"type": "file", "encoding": "base64", "content": base64.b64encode(self.files[name].encode()).decode()}
        raise AssertionError(path)


class CatalogTests(Fixture):
    def test_valid_catalog(self):
        self.assertEqual(len(validator.validate_catalog(self.catalog, self.policy)), 1)

    def test_duplicate_plugin_rejected(self):
        self.catalog["plugins"].append(self.entry)
        with self.assertRaises(ValueError):
            validator.validate_catalog(self.catalog, self.policy)

    def test_lookalike_host_rejected(self):
        self.entry["source"]["url"] = "https://github.com.evil.test/kyzdes/sample.git"
        with self.assertRaises(ValueError):
            validator.validate_catalog(self.catalog, self.policy)

    def test_executable_source_options_rejected(self):
        self.entry["source"]["headersHelper"] = "touch /tmp/never"
        with self.assertRaises(ValueError):
            validator.validate_catalog(self.catalog, self.policy)

    def test_private_allowlist_cannot_hide_unknown_repo(self):
        self.policy["private_repositories"] = ["kyzdes/unknown"]
        with self.assertRaises(ValueError):
            validator.validate_catalog(self.catalog, self.policy)

    def test_shared_updater_consumers_must_exist(self):
        self.policy["shared_updater_plugins"] = ["unknown"]
        with self.assertRaises(ValueError):
            validator.validate_catalog(self.catalog, self.policy)

    def test_rename_cycle_rejected(self):
        self.catalog["renames"] = {"a": "b", "b": "a"}
        with self.assertRaises(ValueError):
            validator.validate_catalog(self.catalog, self.policy)

    def test_rename_migration(self):
        self.catalog["renames"] = {"old": "sample", "retired": None}
        validator.validate_catalog(self.catalog, self.policy)


class SourceFileTests(Fixture):
    def test_valid_packaged_files(self):
        self.validate_files()

    def test_manifest_mismatch(self):
        with self.assertRaisesRegex(ValueError, "manifest name"):
            self.validate_files({"name": "other"})

    def test_missing_skill(self):
        del self.files["skills/sample/SKILL.md"]
        with self.assertRaisesRegex(ValueError, "no packaged SKILL"):
            self.validate_files()

    def test_empty_skill(self):
        self.files["skills/sample/SKILL.md"] = ""
        with self.assertRaisesRegex(ValueError, "empty SKILL"):
            self.validate_files()

    def test_truncated_tree_fails_closed(self):
        tree = self.tree()
        tree["truncated"] = True
        with self.assertRaisesRegex(ValueError, "truncated"):
            validator.validate_source_files(self.entry, {"name": "sample"}, tree, self.files.__getitem__, self.policy)

    def test_missing_manifest_declared_hooks_file(self):
        with self.assertRaisesRegex(ValueError, "missing regular plugin file"):
            self.validate_files({"name": "sample", "hooks": "./custom/hooks.json"})

    def test_malformed_hook_json_rejected(self):
        self.files["hooks/hooks.json"] = "{"
        with self.assertRaises(json.JSONDecodeError):
            self.validate_files()

    def test_invalid_hook_structure_rejected(self):
        self.files["hooks/hooks.json"] = json.dumps({"hooks": {"SessionStart": {"hooks": []}}})
        with self.assertRaisesRegex(ValueError, "hook event"):
            self.validate_files()

    def test_missing_hook_target_quoted_and_unquoted(self):
        for command in ('bash "${CLAUDE_PLUGIN_ROOT}/scripts/missing.sh"',
                        "bash '${CLAUDE_PLUGIN_ROOT}'/scripts/missing.sh",
                        'bash $CLAUDE_PLUGIN_ROOT/scripts/missing.sh'):
            with self.subTest(command=command):
                self.files["hooks/hooks.json"] = self.hooks(command)
                with self.assertRaisesRegex(ValueError, "missing regular plugin file"):
                    self.validate_files()

    def test_existing_hook_with_space_in_name(self):
        self.files["scripts/my hook.sh"] = "exit 0\n"
        self.files["hooks/hooks.json"] = self.hooks('bash "${CLAUDE_PLUGIN_ROOT}/scripts/my hook.sh" >/dev/null')
        self.validate_files()

    def test_codex_root_with_claude_fallback(self):
        self.files["scripts/hook.sh"] = "exit 0\n"
        self.files["hooks/hooks.json"] = self.hooks('bash ${PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}/scripts/hook.sh')
        self.validate_files()

    def test_inline_hook_and_path_traversal(self):
        inline = json.loads(self.hooks('bash "${CLAUDE_PLUGIN_ROOT}/../escape.sh"'))
        with self.assertRaisesRegex(ValueError, "stay inside"):
            self.validate_files({"name": "sample", "hooks": inline})

    def test_hook_symlink_is_rejected(self):
        self.files["hooks/hooks.json"] = self.hooks('bash "${CLAUDE_PLUGIN_ROOT}/scripts/hook.sh"')
        self.files["scripts/hook.sh"] = "../outside"
        tree = self.tree()
        next(row for row in tree["tree"] if row["path"] == "scripts/hook.sh")["mode"] = "120000"
        with self.assertRaisesRegex(ValueError, "missing regular"):
            validator.validate_source_files(self.entry, {"name": "sample"}, tree, self.files.__getitem__, self.policy)

    def test_legacy_updater_rejected_despite_spacing(self):
        self.files["scripts/auto-update.sh"] = 'for plugin in registry.get( "plugins" , {} ):\n    pass\n'
        with self.assertRaisesRegex(ValueError, "legacy cross-plugin"):
            self.validate_files()

    def test_shared_updater_requires_both_files_and_exact_template(self):
        self.policy["shared_updater_plugins"] = ["sample"]
        for path in validator.SHARED_UPDATERS:
            self.files[path] = (validator.ROOT / "templates/plugin-update" / Path(path).name).read_text()
        self.validate_files()
        self.files["scripts/auto_update.py"] += "\n# Unexpected divergence\n"
        with self.assertRaisesRegex(ValueError, "differs from reviewed template"):
            self.validate_files()
        del self.files["scripts/auto_update.py"]
        with self.assertRaisesRegex(ValueError, "missing regular plugin file"):
            self.validate_files()


class RemoteSourceTests(Fixture):
    def test_archive_and_disabled_sources_fail(self):
        for field in ("archived", "disabled"):
            with self.subTest(field=field), mock.patch.object(validator, "api", return_value={field: True}):
                with self.assertRaisesRegex(ValueError, "archived or disabled"):
                    validator.source_check(self.entry, self.policy)

    def test_visibility_mismatch_fails(self):
        with mock.patch.object(validator, "api", return_value={"private": True}):
            with self.assertRaisesRegex(ValueError, "visibility"):
                validator.source_check(self.entry, self.policy)

    def test_source_ref_is_resolved_and_commit_is_pinned(self):
        self.entry["source"]["ref"] = "release/stable"
        with mock.patch.object(validator, "api", side_effect=self.remote) as api:
            result = validator.source_check(self.entry, self.policy)
        self.assertEqual(result["sha"], SHA)
        self.assertEqual(result["status"], "passed")
        paths = [call.args[0] for call in api.call_args_list]
        self.assertIn("repos/kyzdes/sample/commits/release%2Fstable", paths)
        self.assertIn("repos/kyzdes/sample/git/trees/" + TREE_SHA + "?recursive=1", paths)
        self.assertTrue(all(path.endswith("?ref=" + SHA) for path in paths if "/contents/" in path))

    def test_private_skip_is_explicit_and_never_passed(self):
        self.policy["private_repositories"] = ["kyzdes/sample"]
        failure = urllib.error.HTTPError("url", 404, "error", {}, None)
        with mock.patch.dict(os.environ, {}, clear=True), mock.patch.object(validator, "api", side_effect=failure):
            result = validator.source_check(self.entry, self.policy, allow_skip=True)
            self.assertEqual(result["status"], "private-skipped")
            with self.assertRaises(urllib.error.HTTPError):
                validator.source_check(self.entry, self.policy, allow_skip=False)
        report = {"errors": [], "sources": [result]}
        self.assertEqual(validator.summarize(report, True, False), 0)
        self.assertEqual(report["overall_status"], "partial")
        self.assertEqual(report["summary"]["remote_passed"], 0)

    def test_public_404_and_private_403_never_skipped(self):
        for code, private in ((404, []), (403, ["kyzdes/sample"])):
            self.policy["private_repositories"] = private
            with self.subTest(code=code), mock.patch.dict(os.environ, {}, clear=True), mock.patch.object(validator, "api", side_effect=urllib.error.HTTPError("url", code, "error", {}, None)):
                with self.assertRaises(urllib.error.HTTPError):
                    validator.source_check(self.entry, self.policy, allow_skip=True)

    def test_explicit_private_read_token_failure_is_not_waived(self):
        self.policy["private_repositories"] = ["kyzdes/sample"]
        with mock.patch.dict(os.environ, {"MARKETPLACE_READ_TOKEN": "sensitive-token"}), mock.patch.object(validator, "api", side_effect=urllib.error.HTTPError("url", 404, "error", {}, None)):
            with self.assertRaises(urllib.error.HTTPError):
                validator.source_check(self.entry, self.policy, allow_skip=True)

    def test_source_has_a_total_request_budget(self):
        with mock.patch.object(validator.time, "monotonic", side_effect=[0, 121]):
            with self.assertRaises(TimeoutError):
                validator.source_check(self.entry, self.policy)


class InstallTests(Fixture):
    def result(self, name="sample"):
        return {"name": name, "status": "passed", "sha": SHA}

    def fake_client(self, args, *, env, cwd, timeout, capture):
        self.assertEqual(args[:2], ["fake-claude", "plugin"])
        self.assertFalse(capture)
        self.assertGreater(timeout, 0)
        self.assertLessEqual(timeout, 90)
        self.assertEqual(env["KKZ_NO_AUTOUPDATE"], "1")
        self.assertNotIn("ANTHROPIC_API_KEY", env)
        self.assertEqual(Path(cwd).name, "cwd")
        config = Path(env["CLAUDE_CONFIG_DIR"])
        self.assertTrue(json.loads((config / "settings.json").read_text())["disableAllHooks"])
        if args[2:4] == ["marketplace", "add"]:
            catalog = json.loads((Path(args[4]) / ".claude-plugin/marketplace.json").read_text())
            self.assertEqual(catalog["plugins"][0]["source"]["sha"], SHA)
            self.assertNotIn("ref", catalog["plugins"][0]["source"])
        elif args[2] == "install":
            self.assertEqual(args[4:], ["--scope", "user"])
            name = args[3].split("@", 1)[0]
            location = config / "plugins/cache" / name
            (location / ".claude-plugin").mkdir(parents=True)
            (location / ".claude-plugin/plugin.json").write_text(json.dumps({"name": name}))
            (location / "skills/sample").mkdir(parents=True)
            (location / "skills/sample/SKILL.md").write_text("# Sample")
            registry = config / "plugins/installed_plugins.json"
            data = json.loads(registry.read_text()) if registry.exists() else {"plugins": {}}
            data["plugins"][args[3]] = [{"scope": "user", "installPath": str(location), "gitCommitSha": SHA}]
            registry.write_text(json.dumps(data))
        else:
            self.fail("unexpected command: " + repr(args))
        return subprocess.CompletedProcess(args, 0)

    def test_smoke_uses_only_plugin_commands_in_isolated_config(self):
        result = self.result()
        self.entry["source"]["ref"] = "mutable-ref"
        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "never-pass-to-client"}), mock.patch.object(validator, "run_bounded", side_effect=self.fake_client) as run:
            validator.install_smoke([self.entry], [result], "fake-claude")
        self.assertEqual(run.call_count, 2)
        self.assertEqual(result["install_smoke"], "passed")

    def test_git_auth_stays_in_child_environment(self):
        result = self.result()
        def client(args, **kwargs):
            self.assertNotIn("unit-github-token", " ".join(args))
            env = kwargs["env"]
            self.assertEqual(env["GIT_CONFIG_COUNT"], "3")
            self.assertEqual(env["GIT_CONFIG_KEY_0"], "user.name")
            self.assertEqual(env["GIT_CONFIG_KEY_1"], "http.https://github.com/.extraheader")
            self.assertEqual(env["GIT_CONFIG_VALUE_1"], "")
            expected = base64.b64encode(b"x-access-token:unit-github-token").decode()
            self.assertEqual(env["GIT_CONFIG_VALUE_2"], "AUTHORIZATION: basic " + expected)
            return self.fake_client(args, **kwargs)
        with mock.patch.dict(os.environ, {"GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "user.name", "GIT_CONFIG_VALUE_0": "Test"}), mock.patch.object(validator, "github_token", return_value="unit-github-token"), mock.patch.object(validator, "run_bounded", side_effect=client):
            validator.install_smoke([self.entry], [result], "fake-claude")
        self.assertEqual(result["install_smoke"], "passed")

    @unittest.skipUnless(os.environ.get("MARKETPLACE_CLI_SMOKE_TEST") == "1" and shutil.which("claude"), "opt-in real CLI probe")
    def test_real_cli_does_not_run_hooks_or_mcp(self):
        with tempfile.TemporaryDirectory(prefix="plugin-no-execution-") as tmp:
            root = Path(tmp)
            source = root / "plugin"
            source.mkdir()
            marker = root / "unexpected-execution"
            subprocess.run(["git", "init", "-q"], cwd=source, check=True, capture_output=True)
            code = "from pathlib import Path; Path(" + repr(str(marker)) + ").write_text('executed')"
            self.files[".claude-plugin/plugin.json"] = json.dumps({"name": "sample", "version": "1.0.0"})
            self.files["hooks/hooks.json"] = self.hooks("python3 -c " + shlex.quote(code))
            self.files[".mcp.json"] = json.dumps({"mcpServers": {"probe": {"command": sys.executable, "args": ["-c", code]}}})
            for name, content in self.files.items():
                path = source / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content)
            result = {"name": "sample", "status": "local-passed", "local_path": str(source)}
            validator.install_smoke([self.entry], [result], shutil.which("claude"))
            self.assertEqual(result.get("install_smoke"), "passed", result.get("install_reason"))
            self.assertFalse(marker.exists(), "plugin installation executed a hook or MCP command")

    def test_setup_failure_marks_all_selected_and_preserves_reportable_status(self):
        result = self.result()
        with mock.patch.object(validator, "run_bounded", return_value=subprocess.CompletedProcess([], 9)):
            validator.install_smoke([self.entry], [result], "fake-claude")
        self.assertEqual(result["install_smoke"], "failed")
        self.assertIn("exit 9", result["install_reason"])

    def test_failed_install_does_not_prevent_remaining_plugins(self):
        other = copy.deepcopy(self.entry)
        other["name"] = "other"
        results = [self.result(), self.result("other")]
        def client(args, **kwargs):
            if args[2:4] == ["install", "sample@marketplace-smoke"]:
                return subprocess.CompletedProcess(args, 7)
            return self.fake_client(args, **kwargs)
        with mock.patch.object(validator, "run_bounded", side_effect=client):
            validator.install_smoke([self.entry, other], results, "fake-claude")
        self.assertEqual([r["install_smoke"] for r in results], ["failed", "passed"])

    def test_private_skips_are_not_installed(self):
        result = {"name": "sample", "status": "private-skipped"}
        with mock.patch.object(validator, "run_bounded") as run:
            validator.install_smoke([self.entry], [result], "fake-claude")
        run.assert_not_called()
        self.assertEqual(result["install_smoke"], "skipped")

    def test_total_install_budget_stops_before_cli(self):
        result = self.result()
        with mock.patch.object(validator, "run_bounded") as run:
            validator.install_smoke([self.entry], [result], "fake-claude", total_timeout=0)
        run.assert_not_called()
        self.assertEqual(result["install_smoke"], "failed")
        self.assertIn("time budget", result["install_reason"])


class LocalSourceTests(Fixture):
    def test_local_working_tree_includes_uncommitted_files_and_is_labelled(self):
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            source = parent / "sample"
            source.mkdir()
            for args in (["git", "init", "-q"], ["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "--allow-empty", "-qm", "fixture"]):
                subprocess.run(args, cwd=source, check=True, capture_output=True)
            for name, content in self.files.items():
                file = source / name
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_text(content)
            with mock.patch.object(validator, "api") as api:
                result = validator.source_check(self.entry, self.policy, local_sources=parent)
            api.assert_not_called()
            self.assertEqual(result["status"], "local-passed")
            self.assertTrue(result["dirty"])
            self.assertEqual(result["remote_metadata"], "not-checked")
            report = {"sources": [result], "errors": []}
            validator.summarize(report, True, False)
            self.assertEqual(report["overall_status"], "local-validated")


class ReportTests(Fixture):
    def test_report_is_written_even_if_install_smoke_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".claude-plugin").mkdir()
            (root / ".claude-plugin/marketplace.json").write_text(json.dumps(self.catalog))
            (root / "catalog-policy.json").write_text(json.dumps(self.policy))
            out = root / "reports/report.json"
            with mock.patch.object(validator, "ROOT", root), mock.patch.object(validator, "github_token"), mock.patch.object(validator, "source_check", return_value={"name": "sample", "status": "passed", "sha": SHA}), mock.patch.object(validator.shutil, "which", return_value="fake-claude"), mock.patch.object(validator, "install_smoke", side_effect=ValueError("install failed")), contextlib.redirect_stdout(io.StringIO()):
                code = validator.main(["--install-smoke", "--output", str(out)])
            self.assertEqual(code, 1)
            report = json.loads(out.read_text())
            self.assertEqual(report["overall_status"], "failed")
            self.assertEqual(report["sources"][0]["sha"], SHA)
            self.assertEqual(report["errors"], ["install failed"])

    def test_sensitive_exception_text_redacted(self):
        with mock.patch.dict(os.environ, {"MARKETPLACE_READ_TOKEN": "a-sensitive-value"}):
            self.assertNotIn("a-sensitive-value", validator.safe_error(ValueError("failure a-sensitive-value")))
        error = urllib.error.HTTPError("https://example.invalid/token", 403, "secret response body", {}, None)
        self.assertEqual(validator.safe_error(error), "GitHub API returned HTTP 403")

    @unittest.skipIf(os.name == "nt", "POSIX process-group test")
    def test_timeout_kills_descendant_process(self):
        with tempfile.TemporaryDirectory() as tmp:
            marker = str(Path(tmp) / "child-survived")
            child = "import time; from pathlib import Path; time.sleep(1); Path(" + repr(marker) + ").write_text('alive')"
            parent = "import subprocess, sys, time; subprocess.Popen([sys.executable, '-c', " + repr(child) + "]); time.sleep(30)"
            with self.assertRaises(TimeoutError):
                validator.run_bounded([sys.executable, "-c", parent], timeout=0.2)
            time.sleep(1.1)
            self.assertFalse(Path(marker).exists(), "timed-out CLI left its child process running")


if __name__ == "__main__":
    unittest.main()
