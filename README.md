# kyzdes / claude-skills

A personal marketplace of 14 plugins for Claude Code. Codex can also read this
catalog; compatibility depends on each plugin's packaged skills and integrations.
The canonical catalog is `.claude-plugin/marketplace.json`.

## Install

Claude Code:

```text
/plugin marketplace add kyzdes/claude-skills
/plugin install clarity@claude-skills
```

Replace `clarity` with a plugin name from the table. `model-to-bot`, `aso`, and
`agent-access` require access to their private repositories; adding the public catalog does not
grant that access.

Codex CLI:

```bash
codex plugin marketplace add https://github.com/kyzdes/claude-skills.git
codex plugin list --marketplace claude-skills --available --json
codex plugin add clarity@claude-skills
```

`clarity`, `research-engine`, and `deck-copy` have verified Codex installations.
This does not certify every plugin's MCP server or hook on both hosts.
Open a new Codex task after changing installed plugins so it picks up the new skills.

## Catalog

| Plugin | Purpose | Repository |
|---|---|---|
| **keys-keeper** | Route secret values to explicit local sinks without printing plaintext in normal agent tool output. Background project sync runs at most once per 24 hours; manual Sync runs immediately. This reduces accidental disclosure; it does not isolate secrets from arbitrary code running as the same OS user. | [source](https://github.com/kyzdes/keys-keeper-skill) |
| **ux-planner** | Turn a product description into a structured UX specification. | [source](https://github.com/kyzdes/ux-planner-skill) |
| **trip-planner** | Build a travel itinerary from flight and hotel sources. | [source](https://github.com/kyzdes/trip-planner-skill) |
| **agentix** | Work with a remote Agentix issue tracker using live-contract discovery. | [source](https://github.com/kyzdes/agentix-skill) |
| **model-to-bot** | Build a Telegram bot around a model or API. Private repository; access required. | [source](https://github.com/kyzdes/model-to-bot) |
| **dokpilot** | Deploy and operate applications through Dokploy with explicit mutation controls. | [source](https://github.com/kyzdes/dokpilot) |
| **hostbrr-vps** | Operate HostBRR VPS through the VirtFusion API. | [source](https://github.com/kyzdes/hostbrr-vps-skill) |
| **clarity** | Edit Russian working text for clarity and concision. | [source](https://github.com/kyzdes/clarity-skill) |
| **tailscale-vpn-coexist** | Diagnose Tailscale routing and proxy conflicts with a VPN client. | [source](https://github.com/kyzdes/tailscale-vpn-coexist-skill) |
| **opencode-provider-auditor** | Inspect and configure OpenAI-compatible providers in OpenCode. | [source](https://github.com/kyzdes/opencode-provider-auditor) |
| **aso** | Research and improve App Store listings. Private repository; access required. | [source](https://github.com/kyzdes/aso-skill) |
| **research-engine** | Build a source-backed research knowledge base and methodology. | [source](https://github.com/kyzdes/research-engine-skill) |
| **agent-access** | Shared 1Password API, SSH and env operations, plus credential saving, organization and comments. Requires a separately configured machine-access runtime; writes require Connect WRITE. Private repository; owner access required. | [source](https://github.com/kyzdes/agent-access) |
| **deck-copy** | Write and revise presentation text for its audience and delivery format. | [source](https://github.com/kyzdes/deck-copy-skill) |

Agent Access is available as `agent-access@claude-skills`. Its Marketplace package
uses an existing runtime under `AGENT_ACCESS_HOME` or `~/.local/share/agent-access`;
installation does not provision credentials or change client approval settings.
Existing `agent-access@agent-access-local` installations can keep using that
identifier. Enable one installation at a time to avoid duplicate MCP servers.

## Updates and controls

Claude's native marketplace auto-update is an independent setting, controlled in
`/plugin` → Marketplaces → `claude-skills`. Enabling it allows the host to update
installed plugins, including Keys Keeper and Agentix. Hook environment flags do
not disable the host's updater. Manual update is always explicit:

```bash
claude plugin marketplace update claude-skills
claude plugin update clarity@claude-skills
```

The repaired fallback hooks update **only their own plugin**. They skip work when
native auto-update is enabled, run in the background, serialize Claude writes,
and apply a four-hour cooldown only after success. Failed commands are bounded
and get a short retry delay. Codex hook execution never updates a separate Claude
installation. The fallback requires Python 3.9 or newer.

- `KKZ_NO_AUTOUPDATE=1` disables these fallback hooks.
- `KKZ_AUTO_UPDATE_INTERVAL_SEC` controls their success cooldown (default 14400).
- Keys Keeper's fallback requires `KEYS_KEEPER_ENABLE_MUTABLE_AUTOUPDATE=1`;
  `KEYS_KEEPER_NO_AUTOUPDATE=1` takes precedence. Its wrapper permits one
  automatic attempt per rolling 24 hours, including failed attempts. Native
  host updates and explicit manual updates keep their separate policies.
- Agentix keeps its own updater, disabled unless `AGENTIX_PLUGIN_AUTO_UPDATE=1`;
  that updater targets only Agentix and uses `AGENTIX_PLUGIN_AUTO_UPDATE_INTERVAL_SEC`.
- Plugins without an updater use the host's policy or manual updates.

To forbid all automatic plugin changes, turn off native marketplace auto-update,
set `KKZ_NO_AUTOUPDATE=1`, and leave Agentix opt-in disabled. These controls do not
change Keys Keeper's separate vault-sync policy.

A plugin's `plugin.json` version controls whether a new cached copy is installed.
Increase that version when publishing changes; if it is omitted, the plugin can
track commits. Git tags alone are not the update policy. See the official
[versioning rules](https://code.claude.com/docs/en/plugins/host-marketplace#release-a-new-version).

The Keys Keeper entry in this catalog pins version `0.11.1` to a reviewed source
commit using `source.sha`. Later repository commits enter the catalog through a
reviewed pin update. To update this installed plugin explicitly:

```bash
claude plugin marketplace update claude-skills
claude plugin update keys-keeper@claude-skills --scope user
```

Keys Keeper `0.11.1` preserves multiline credentials, trailing newlines,
Unicode and literal hex strings when reading legacy macOS Keychain items.
For items with a partition policy, the legacy fallback requires explicit
`apple-tool:` authorization before starting the fixed `security` helper.
It also clarifies that a failed credential operation stops after one failed
authorization attempt: metadata-only and
local format/configuration diagnostics may continue, and another access
attempt requires a confirmed repair or explicit user direction. Stored items
and Keychain ACLs are unchanged.

The separate Codex marketplace named `keys-keeper` uses the source repository's
own packaged Codex plugin. Existing users of that identifier update it with:

```bash
codex plugin marketplace upgrade keys-keeper
codex plugin add keys-keeper@keys-keeper
```

Keep each plugin's existing enabled or disabled state when updating. Plugin
updates refresh agent instructions; update the installed `keys` CLI separately
to apply runtime changes. Version `0.11.0` bounds automatic lock waits, worker
descendants, HTTP request input, native bridge deliveries and activity-log
scans. File and replica backends authenticate fresh ciphertext while retaining
one current derived key inside the process; unchanged file mutations perform
no encryption or payload writes. Damaged account registries and deleted
WebVault accounts fail closed. Hidden native panels stop automatic summary
refreshes. Project sync triggers continue to share one automatic attempt per
rolling 24 hours; manual Sync and refresh run immediately. Encryption formats
and PBKDF2 iteration counts are unchanged. Vault synchronization remains
separate from the host's plugin-update policy.

## Validation

```bash
python3 -m unittest discover -s tests -v
python3 templates/plugin-update/test_auto_update.py
python3 scripts/validate_marketplace.py
claude plugin validate .
python3 scripts/validate_marketplace.py --sources --install-smoke --output validation-report.json
```

The source check verifies visibility, archival status, names, packaged skills,
hook targets, and absence of the retired cross-plugin updater. Installation smoke
uses a temporary `CLAUDE_CONFIG_DIR`; it never starts a model, hooks, or MCP server.
It validates packaging, not the business behavior of each skill.

CI runs on pull requests, main pushes, and daily. Public sources must pass.
`catalog-policy.json` names the only private-source exceptions. Without a token
that can read them, CI reports those entries as **private-skipped**, never passed.
A maintainer's authenticated `gh` can validate all 14 locally. For private checks
on trusted main/scheduled runs, configure the optional `MARKETPLACE_READ_TOKEN`
repository secret with read-only access to the listed repositories. It is not
provided to pull-request code.

Operator workflow: [kyzdes-marketplace/CLAUDE.md](kyzdes-marketplace/CLAUDE.md).
Each plugin retains its own licensing terms; check its source repository.
