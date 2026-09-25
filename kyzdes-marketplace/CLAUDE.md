# Marketplace operator instructions

This repository owns the catalog and validation. Each plugin owns its code and
version in the linked repository. Read this file before catalog or release work.
The user's explicit instructions take precedence over this runbook.

## Inspect before changing

1. Read `.claude-plugin/marketplace.json`, `catalog-policy.json`, and the relevant
   source repository. Check `git status`, branch, and `git remote -v`.
2. Preserve unrelated work. Use an isolated branch/clone when a checkout contains
   WIP or another task's commits. Stage only the intended paths.
3. Recheck GitHub HEAD, visibility, archival status, and applicable repository
   instructions. Source repos may have different release requirements.

The marketplace checkout on the maintainer's current Mac is
`~/Desktop/Projects/skills/claude-skills`; do not assume that path on another host.
Repository URLs in the manifest are authoritative.

## Add or change a plugin

- Preserve marketplace name `claude-skills` and existing plugin identifiers.
- Use full HTTPS GitHub URLs: `{"source":"url","url":"https://github.com/owner/repo.git"}`.
- Match the catalog name to `.claude-plugin/plugin.json` in the source repository.
  The install identifier is **plugin-name@marketplace-name**.
- Package skill entry points under `skills/<name>/SKILL.md` with their relative
  resources. A root-only SKILL.md needs packaging before it joins the catalog.
- Add `.codex-plugin/plugin.json` when publishing a Codex package, and test that
  host separately. Catalog discovery alone does not prove MCP/hook compatibility.
- Keep deliberate private sources clearly labeled and listed in
  `catalog-policy.json`. Never make a repository public merely to pass CI.
- Update the README catalog, bump `metadata.version`, and run validation below.

## Update behavior

Never restore a loop that updates every installed plugin from a SessionStart
hook. The maintained fallback template is in `templates/plugin-update/`.
A copy may update only the plugin whose own manifest it reads. Deploy template
changes together with behavior tests to every source that uses it.

Native Claude auto-update is a separate user policy. Fallback hooks yield to it;
per-hook environment flags do not override it. Document both layers. Keys Keeper
retains explicit opt-in and opt-out for its hook. Agentix retains its independent
scoped updater. Vault synchronization is not plugin updating.

Keep updates bounded, serialize concurrent writes, record a success cooldown
only after success, and avoid logging credentials or raw CLI output. Test
opt-outs, parallel sessions, failed updates, and slow subprocesses.

## Release and migration

1. Bump a plugin's manifest version whenever its published payload changes. If
   both host manifests exist, keep them aligned. If the plugin intentionally has
   no version, clients track its commit. Tags alone do not control this choice.
2. For Keys Keeper, also keep `pyproject.toml`, package `__version__`, and the nested
   Codex manifest aligned; follow that repository's artifact checks.
3. For fang-upgrade, edit the canonical root payload, then run
   `python3 scripts/build_plugin.py` and `--check`. Preserve standalone installs.
4. Publish and validate source changes before merging catalog references to them.
5. Main is protected here: branch → PR → required `validate` → merge. Never bypass
   required checks or force-push the protected branch. Attach the PR to the task.
6. For a renamed entry, append a `renames` map and document the required one-time
   installation. Keep its history. Do not unarchive old source repos or forcibly
   uninstall users' plugins as a side effect of catalog maintenance.

## Verification

Run the README validation commands. `--sources --install-smoke` checks live
sources and installation in an isolated config, without starting a model, hook,
or service. For restricted CI credentials, only the explicit private allowlist
may be skipped; report skips visibly and run those checks with maintainer access.

After publication, recheck remote HEAD and CI, then refresh the local catalog and
only the affected installed plugins. Preserve disabled plugin states. Verify the
resulting versions/files, not only an updater's success message.

When reporting completion, distinguish catalog/schema validity, successful
installation, and real application behavior. Never claim a live operational
scenario passed solely because CI or a manifest validator is green.
