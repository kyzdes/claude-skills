# Catalog and update flow

```text
claude-skills/.claude-plugin/marketplace.json
  └── HTTPS source repository per plugin
        ├── .claude-plugin/plugin.json
        ├── .codex-plugin/plugin.json (where supported)
        └── skills/<name>/SKILL.md + resources
```

Claude and Codex keep separate installed caches and registries. Registering a
catalog does not install every plugin or grant access to private repositories.

Claude native marketplace auto-update owns updates when enabled. Maintained
fallback hooks yield to that setting; otherwise each hook updates only its own
plugin, with serialized writes and bounded retries. Agentix keeps a separate,
explicitly enabled, host-aware updater. No hook should update another plugin.

`keys-keeper-skill` contains both the Python CLI and plugin; the old `keys-keeper`
repository is archived. `fang-upgrade-skill` replaces the archived `openfang-skill`
entry and generates its marketplace payload while preserving standalone clones.

CI checks catalog structure, live public sources, and isolated installs daily as
well as on PRs/main. Private-source coverage is shown explicitly in the report.
The workflow and `catalog-policy.json` are the source of truth for check scope.
