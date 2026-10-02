# Changelog

## [1.24.0] — 2026-10-02

- Update the immutable Keys Keeper source pin to 0.11.1: legacy macOS Keychain
  reads preserve the original UTF-8 bytes using the explicitly framed
  `security -g` representation.
  Multiline credentials, trailing newlines, Unicode and literal hex strings
  are read without guessing whether an unmarked value is hex-encoded. Stored
  items and Keychain ACLs are unchanged.
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
