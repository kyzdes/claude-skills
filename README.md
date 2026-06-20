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
/plugin install agent-docs-architect@claude-skills
/plugin install agentix@claude-skills
/plugin install model-to-bot@claude-skills
```

## What's in here

| Plugin | What it does | Triggers on |
|---|---|---|
| **keys-keeper** | macOS Keychain-backed secrets manager. Agents put API keys, SSH keys, server creds into your files **without ever seeing the value** — Sealed wrapper + env-gated reveal make leakage architecturally impossible. | "save my OpenRouter key", "put $X into .env", "ssh into prod" |
| **ux-planner** | Turns vague product descriptions into structured English UX specs ready for handoff to a visual-design agent. Hybrid interview + advisor mode for archetype matching. | "хочу приложение для X", "design a SaaS", "сделай продукт" |
| **context-map** | Generates / audits / updates `context-map.md` files — project memory that survives AI context resets. Tracks decisions, known issues, gotchas. | "make a context map", "audit project docs", "agent onboarding doc" |
| **trip-planner** | Extracts flight + hotel data from Aviasales (`avs.io`, `aviasales.ru`) and Ostrovok (`corp.ostrovok.ru`) links, compiles into self-contained HTML itinerary. | Pasting `avs.io/*` / `corp.ostrovok.ru/*` links, "поездка", "отель", "перелёт" |
| **stitch-design** | Google Stitch AI UI generation — bundles 4 sub-skills (design / theme / edit / upload). Generates HTML mockups with Tailwind CSS + PNG screenshots from text prompts. | "design a UI", "make a mockup", "stitch this screen" |
| **agent-docs-architect** | Decomposes a complex codebase into layered, agent-readable docs (top-level MAP + per-domain deep docs + distributed CLAUDE.md) with a CI gate that keeps them fresh. | "make agent docs", "document this codebase for agents", "layered docs" |
| **agentix** | Teaches agents to work the [Agentix](https://github.com/kyzdes/agentix) issue tracker over MCP — orient via `get_started` + the wiki index, load one issue with `get_context`, file well-specced issues (task-spec + checklist). Full tool reference + index convention. | Connected to an `agentix` MCP server, "заведи задачу", "create an issue", "plan an epic", Agentix |
| **model-to-bot** | Turns a model / HF Space / API into a production Telegram bot — 7-phase playbook (Discover→…→Deploy) + 32-entry gotchas catalog + real starter templates. *(Private repo — installs for the owner.)* | "build a telegram bot for X", "wrap this Space in a bot", "model-backed bot" |

## Why auto-update is automatic

Each plugin in this marketplace ships a `SessionStart` hook that pulls its own source and the marketplace itself on every Claude Code session start. The hook is debounced (4h cooldown via shared stamp file), so even if you have every plugin installed they don't N× the network work.

You can tune the cooldown via `KKZ_AUTO_UPDATE_INTERVAL_SEC` env var. Set it to `0` to update on every session, or to `86400` for once a day.

## Per-plugin source repos

Each plugin lives in its own GitHub repo and versions independently. This marketplace is a thin manifest pointing at them:

- [`kyzdes/keys-keeper-skill`](https://github.com/kyzdes/keys-keeper-skill)
- [`kyzdes/ux-planner-skill`](https://github.com/kyzdes/ux-planner-skill)
- [`kyzdes/context-map-skill`](https://github.com/kyzdes/context-map-skill)
- [`kyzdes/trip-planner-skill`](https://github.com/kyzdes/trip-planner-skill)
- [`kyzdes/claude-stitch-design`](https://github.com/kyzdes/claude-stitch-design)
- [`kyzdes/agent-docs-architect`](https://github.com/kyzdes/agent-docs-architect)
- [`kyzdes/agentix-skill`](https://github.com/kyzdes/agentix-skill)
- [`kyzdes/model-to-bot`](https://github.com/kyzdes/model-to-bot) *(private)*

## Codex CLI?

Codex CLI compatibility with Claude Code's `marketplace.json` format is not documented. Codex reads `~/.claude/skills/<name>/SKILL.md` directly, so for Codex users a separate install path (e.g. `git clone` + symlink) will be added later. Today this marketplace is Claude Code-only.

## License

MIT for the marketplace manifest. Each plugin has its own LICENSE; check the linked repos.
