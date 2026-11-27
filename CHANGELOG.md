# Changelog

## [1.40.1] — 2026-11-27

- Move `loop-clip` from `810d28f` (0.1.0) to `0dbf894` (0.2.0): looping is now one of two endings
  (loop or play once and hold the call to action), with a size table for feed, stories, README and 16:9.
- Preserve the existing 23 entries and installed plugin states.

## [1.40.0] — 2026-11-27

- Add `loop-clip` (private source `kyzdes/loop-clip-skill`, pinned `810d28f`, 0.1.0): a short looping
  promo clip (GIF + MP4) for a social feed from one HTML page — storyboards to choose from, a page that
  is a pure function of time, a Swift frame shooter, a check script with contact sheets and an
  independent critic agent. macOS only.
- Preserve the existing 22 entries and installed plugin states.

## [1.39.1] — 2026-11-27

- Move `site-craft` from `d8a823d` (0.1.0) to `1608b64` (0.1.1); its source `kyzdes/site-craft-skill`
  is now public. The skill no longer depends on owner-only tools (Mobbin pool, clarity, impeccable are
  used when present) and its README shows how to install it in Codex.
- Preserve the existing 22 entries and installed plugin states.

## [1.39.0] — 2026-11-26

- Add `site-craft` (private source `kyzdes/site-craft-skill`, pinned `d8a823d`, 0.1.0): the approach
  behind budka.app for stylish sites and landing pages — product metaphor as the page's scene, colours
  and fonts with written roles, Mobbin references block by block, a moodboard with three live
  directions before layout, blocks as working demos, short honest copy and a hand-over checklist.
- Preserve the existing 21 entries and installed plugin states.

## [1.38.1] — 2026-11-23

- Move `resilient-fetch` from `1b23edb` (1.0.0) to `ac283f8` (1.0.1): the TLS session
  options are now built from the ones the installed curl_cffi actually has, so a release without
  `CurlOpt.NETRC` cannot break the import. Hosts that pin curl_cffi 0.16.3 keep working.
- Preserve the existing 21 entries and installed plugin states.

## [1.38.0] — 2026-11-23

- Add `resilient-fetch` (private source `kyzdes/resilient-fetch-skill`, pinned `1b23edb`): a portable
  anti-ban HTTP transport — browser TLS/JA3 impersonation through curl_cffi with paired
  (impersonate, User-Agent) profiles, exit-IP rotation through a proxy pool with cooldowns,
  SOCKS5 to HTTP fallback on the same gateway, cookie isolation per request, and a pool doctor
  that classifies every proxy failure by type.
- Preserve the existing 20 entries and installed plugin states.

## [1.37.4] — 2026-11-23

- Move router-inventory from `7a206a5` (0.1.3) to `4287c84` (0.1.4): `send` and `report` no longer
  sweep the home folder for unparsed files (about 30 s saved on each); Codex on Python older than
  3.11 says it needs 3.11+ instead of "could not parse"; tests cover `send` and `report --model`.
- Preserve the existing 20 entries and installed plugin states.

## [1.37.3] — 2026-11-22

- Move router-inventory from `f1e4baf` (0.1.2) to `7a206a5` (0.1.3): OpenCode's router key is also
  found in `opencode.db` (read-only), where newer OpenCode Desktop keeps it instead of `auth.json`.
- Preserve the existing 20 entries and installed plugin states.

## [1.37.2] — 2026-11-22

- Move router-inventory from `e3341a7` (0.1.1) to `f1e4baf` (0.1.2): the snapshot also lists the
  AI programs installed on the machine (Cursor, VS Code, Zed, Claude, Codex and others), routed or
  not, so SuperGateway can show the routed ones apart.
- Preserve the existing 20 entries and installed plugin states.

## [1.37.1] — 2026-11-22

- Move router-inventory from `922b9a6` (0.1.0) to `e3341a7` (0.1.1): a parser error no longer
  copies a config line (possibly a secret) into the snapshot; keys are caught after `\n`, `_` or a
  digit; `send` refuses a file that contains any key found on the machine; the leak check no longer
  relies on `assert`. README gains the marketplace install lines.
- Preserve the existing 20 entries and installed plugin states.

## [1.37.0] — 2026-11-22

- Add router-inventory at `922b9a6` (0.1.0): snapshots which programs on a machine
  (OpenCode, Hermes, Codex, Claude Code; other files that mention the router go to the
  agent for review) use the owner's LLM router, with which LiteLLM key alias and models,
  and flags configured models the router no longer serves. Sent by hand to the router's
  tailnet-only inventory (`kyzdes/llm-router`, `inventory/`); `report --model` shows where
  a model is configured across machines. Keys never leave the machine. Private repository;
  Claude Code and Codex manifests.
- Preserve the existing 19 entries and installed plugin states.

## [1.36.1] — 2026-11-21

- Move op-agent from `5f558b1` (0.2.0) to `d444832` (0.2.1): in 0.2.0 every call from
  Git Bash or cmd.exe waited until the caller closed stdin (a `powershell -File` script
  that references `$input` drains a redirected stdin before exiting), so agent shells that
  keep stdin open hung. The shim and `op-agent.cmd` now start `powershell -InputFormat None`
  and `op` inherits stdin. The Windows self-check has 25 checks, two of them for this.
- Preserve the existing 19 entries and installed plugin states.

## [1.36.0] — 2026-11-21

- Move op-agent from `141bdd3` (0.1.0) to `5f558b1` (0.2.0): Windows hardening. In
  PowerShell the wrapper no longer leaves the service-account token in the caller's
  session when `op` fails under `2>$null`, restores the caller's `OP_*` variables and
  console encoding, and passes pipeline input to `op`. Git Bash gets an `op-agent` shim
  that calls PowerShell directly instead of cmd.exe, which split arguments such as
  `a&b` and ran the rest as a command. The installer no longer hangs without a
  keyboard, writes the config as UTF-8, puts `~\.claude\bin` on PATH and gains
  `-FromEnv` (migration from op-agent-vault-windows) and `-Rotate`. New offline
  self-check `test-windows.ps1`. Claude Code and Codex manifests are aligned.
- Preserve the existing 19 entries and installed plugin states.

## [1.35.0] — 2026-11-15

- Move research-engine from `1656d86` (0.5.1) to `3bd4b05` (0.6.0): a second skill,
  research-pipeline, researches a set of objects (accounts, posts, courses, repos,
  people, datasets) — interview, plan, registry in Agentix Notes, random stratified
  sample with user calibration, batches, and a report whose numbers come from SQL.
  It creates its Research project and tables itself and ships `canon.py` for
  canonical keys (Python 3.9+, stdlib). Claude Code and Codex manifests are aligned.
- Preserve the existing 19 entries and installed plugin states.

## [1.34.0] — 2026-11-14

- Move mobbin-pool from `87d4c14` (0.1.1) to `ec6ebb8` (0.2.0): the plugin now also
  serves Kimi Code (manifest `.kimi-plugin/plugin.json`, installed with `/plugins install`
  from a local clone, since Kimi downloads GitHub sources without credentials) and OpenCode
  (`install-opencode.sh` copies the skill into its skills folder). The skill gained the MCP
  config for both agents and per-agent pool keys. This marketplace still serves only
  Claude Code and Codex.
- Preserve the existing 19 entries and installed plugin states.

## [1.33.0] — 2026-11-14

- Add op-agent (0.1.0, `141bdd3`) from its private source repository: one
  plugin for macOS, Linux and Windows that lets agents use 1Password through a
  service account with no Touch ID, Windows Hello or password prompts. The
  `op-agent` wrapper keeps the token in the OS secret store (Keychain, Secret
  Service or a 0600 file, DPAPI); `server-agent` loads an SSH key into a
  throwaway in-memory ssh-agent. It ships Claude Code and Codex manifests.
- Preserve the existing 18 entries and installed plugin states.

## [1.32.1] — 2026-11-14

- Move mobbin-pool from `3536bad` (0.1.0) to `87d4c14` (0.1.1): the skill now knows Mobbin's
  daily Deep Search cap (500 per account, a tool error rather than a 429) and the AI credits beta.
  The change was found by the router's nightly docs watch.
- Preserve the existing 18 entries and installed plugin states.

## [1.32.0] — 2026-11-14

- Add mobbin-pool (0.1.0, `3536bad`) from its private source repository: one
  shared skill for Claude Code and Codex that explains Mobbin through the owner's
  pool gateway — connecting with a pool key, good queries and Deep Search credits,
  collections, pinning one Mobbin account for a piece of work, and the gateway's
  answers. It ships no MCP server, hook or credential.
- Fix the plugin count in the README (it still said 16).
- Preserve the existing 17 entries and installed plugin states.

## [1.31.0] — 2026-11-12

- Add agentix-notes (0.1.0, `bd07da9`) from its private source repository: one
  shared skill for Claude Code and Codex that explains the Agentix Notes MCP
  server — projects, sourced notes, freshness and history, databases, files,
  limits and the 35-tool map. It ships no MCP server, hook or credential.
- Preserve the existing 16 entries and installed plugin states.

## [1.30.0] — 2026-11-12

- Move Agentix from `2441cb4` (0.5.0) to `214a9f2` (0.6.0): the skill now
  describes activity/inbox cursors, the `project` selector for documents that
  share a slug, optional `expectedRevision` on project, epic and milestone
  updates, cursor-paged comments, trimmed issue write results and the 200-item
  caps. Its updater gained an OS lock and a deadline. These service changes are
  not deployed to production yet; the skill detects them from the live schema.
- Preserve the existing 16 entries and installed plugin states.

## [1.29.0] — 2026-10-27

- Add op-agent-vault-windows (0.1.0, `eddc99e`) from its public source
  repository: a Windows-only setup that lets every agent read and write one
  dedicated 1Password vault through a service account, with no password,
  Windows Hello or approval prompts. It ships Claude Code and Codex manifests.
- Preserve the existing 15 entries and installed plugin states.

## [1.28.0] — 2026-10-27

- Move Deck Studio from `5ea0d94` (0.2.2) to `6ab728b` (0.3.0): it adds the
  «Сетка» style, a light corporate deck without the particle field (visible
  grid, mono labels, corner-marked cells, mosaic and vector animations,
  16 layouts), started with `new_deck.py --style grid`. The style ships no
  brand fonts or logos.
- Preserve the existing 15 entries and installed plugin states.

## [1.27.0] — 2026-10-20

- Pin the 13 remaining entries to their current source commits with
  `source.sha`. Every entry is now pinned, so a push to a plugin repository no
  longer reaches users without a catalog PR. The pins are the default-branch
  commits at this date; they were not individually audited.
- Drop the duplicate `version` field from the Keys Keeper entry; its
  `plugin.json` owns the version. Between 1.24.0 and 1.25.0 its pin moved from
  0.11.1 through 0.12.1 to 0.13.0 (`fbd37cd`) without a catalog version bump or
  changelog entry; this entry records it.
- The validator rejects `sha` or `ref` placed beside `source`, and a test keeps
  the README table in step with the catalog.
- Move the operator runbook to `CLAUDE.md` in the repository root so agents
  load it, and remove the redirect README. Trim stale Keys Keeper notes and fix
  the Codex plugin list in the README.
- Ignore `__pycache__/` and `*-report.json`. Update the pinned GitHub Actions to
  releases that run on Node 24.
- Move Deck Studio from `3a64b3f` (0.2) to `5ea0d94` (0.2.2): it brings the
  0.2.1 audit fixes and the `particles: false` option that turns the particle
  field off for strict brand themes. Source CI passed on that commit.
- Preserve the existing 15 entries and installed plugin states.

## [1.26.0] — 2026-10-16

- Add Deck Studio from its public source repository: a single-file HTML
  presentation engine with a morphing particle field, 20 tested layouts, CSS
  theme tokens with three palettes, presenter window, and scripts to start,
  check and build a deck, plus references for the whole path from brief and
  Mobbin moodboard to delivery.
- The plugin ships the reviewed shared updater byte-for-byte; add it to
  `shared_updater_plugins` in catalog policy.
- Preserve the existing 14 entries, source pins and installed plugin states.

## [1.25.0] — 2026-10-04

- Add Agent Access from its private source repository, with packaged Claude and
  Codex skills and MCP configuration for an existing local machine-access runtime.
- Include API, SSH and env operations plus credential saving, organization and
  annotations. Runtime provisioning and Connect WRITE activation are separate.
- Explicitly allow the private source in catalog policy; CI reports it as skipped
  when its credentials cannot read that repository.
- Preserve the existing 13 entries, source pins and installed plugin states.

## [1.24.0] — 2026-10-02

- Update the immutable Keys Keeper source pin to 0.11.1: legacy macOS Keychain
  reads preserve the original UTF-8 bytes using the explicitly framed
  `security -g` representation.
  Multiline credentials, trailing newlines, Unicode and literal hex strings
  are read without guessing whether an unmarked value is hex-encoded. Stored
  items and Keychain ACLs are unchanged.
- Require explicit `apple-tool:` authorization in a legacy item's partition
  policy before starting the fixed `security` helper. Unsupported items fail
  closed without spawning that helper or waiting for its timeout.
- Clarify the credential stop rule: stop the failed credential operation after
  one failed authorization attempt, while permitting metadata-only and local
  format/configuration diagnostics. Retry access only after a confirmed repair
  or explicit user direction.
- Keep the other 12 entries, shared updater templates, catalog policy and
  native host update policy unchanged. Runtime fixes require a separate
  installed CLI update.

## [1.23.0] — 2026-10-02

- Update the immutable Keys Keeper source pin from 0.10.1 to 0.11.0. The plugin
  descriptor and runtime version are owned by its source repository.
- Include the deterministic journal reauthentication test correction. Its
  complete matrix passes 1,451 collected cases; released runtime bytes and
  the immutable 0.11.0 tag/wheel are unchanged.
- Keys Keeper bounds automatic lock waits and worker descendants, HTTP handler
  admission and request input, native bridge deliveries, and audit-log scans.
  Its file and replica backends authenticate fresh ciphertext with a single
  process-local current key; no-op file mutations avoid encryption and writes.
- Keys Keeper validates profile identity and fails closed for deleted WebVault
  accounts and damaged account registries. Encryption formats and PBKDF2
  iteration counts are unchanged. Automatic sync retains its daily limits;
  manual Sync remains immediate.
- Keep the other 12 catalog entries, shared updater templates and native host
  update policy unchanged. Runtime improvements require updating the installed
  `keys` CLI separately from the agent plugin.
