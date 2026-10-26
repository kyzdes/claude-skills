# Changelog

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
