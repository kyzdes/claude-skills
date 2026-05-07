# kyzdes / claude-skills

A personal marketplace of [Claude Code](https://docs.claude.com/en/docs/claude-code) skills.

Friends install once, get auto-update on every Claude Code session start. No manual `/plugin marketplace update` ever needed.

## Install

In Claude Code:

```
/plugin marketplace add kyzdes/claude-skills
```

Then install the skills you actually want:

```
/plugin install keys-keeper@claude-skills
/plugin install ux-planner@claude-skills
/plugin install context-map@claude-skills
/plugin install trip-planner@claude-skills
/plugin install stitch-design@claude-skills
```

## What's in here

| Plugin | What it does | Triggers on |
|---|---|---|
| **keys-keeper** | macOS Keychain-backed secrets manager. Agents put API keys, SSH keys, server creds into your files **without ever seeing the value** — Sealed wrapper + env-gated reveal make leakage architecturally impossible. | "save my OpenRouter key", "put $X into .env", "ssh into prod" |
| **ux-planner** | Turns vague product descriptions into structured English UX specs ready for handoff to a visual-design agent. Hybrid interview + advisor mode for archetype matching. | "хочу приложение для X", "design a SaaS", "сделай продукт" |
| **context-map** | Generates / audits / updates `context-map.md` files — project memory that survives AI context resets. Tracks decisions, known issues, gotchas. | "make a context map", "audit project docs", "agent onboarding doc" |
| **trip-planner** | Extracts flight + hotel data from Aviasales (`avs.io`, `aviasales.ru`) and Ostrovok (`corp.ostrovok.ru`) links, compiles into self-contained HTML itinerary. | Pasting `avs.io/*` / `corp.ostrovok.ru/*` links, "поездка", "отель", "перелёт" |
| **stitch-design** | Google Stitch AI UI generation — bundles 4 sub-skills (design / theme / edit / upload). Generates HTML mockups with Tailwind CSS + PNG screenshots from text prompts. | "design a UI", "make a mockup", "stitch this screen" |

## Why auto-update is automatic

Each plugin in this marketplace ships a `SessionStart` hook that pulls its own source and the marketplace itself on every Claude Code session start. The hook is debounced (4h cooldown via shared stamp file), so even if you have all 5 plugins installed they don't 5× the network work.

You can tune the cooldown via `KKZ_AUTO_UPDATE_INTERVAL_SEC` env var. Set it to `0` to update on every session, or to `86400` for once a day.

## Per-plugin source repos

Each plugin lives in its own GitHub repo and versions independently. This marketplace is a thin manifest pointing at them:

- [`kyzdes/keys-keeper-skill`](https://github.com/kyzdes/keys-keeper-skill)
- [`kyzdes/ux-planner-skill`](https://github.com/kyzdes/ux-planner-skill)
- [`kyzdes/context-map-skill`](https://github.com/kyzdes/context-map-skill)
- [`kyzdes/trip-planner-skill`](https://github.com/kyzdes/trip-planner-skill)
- [`kyzdes/claude-stitch-design`](https://github.com/kyzdes/claude-stitch-design)

## Codex CLI?

Codex CLI compatibility with Claude Code's `marketplace.json` format is not documented. Codex reads `~/.claude/skills/<name>/SKILL.md` directly, so for Codex users a separate install path (e.g. `git clone` + symlink) will be added later. Today this marketplace is Claude Code-only.

## License

MIT for the marketplace manifest. Each plugin has its own LICENSE; check the linked repos.
