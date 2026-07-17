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
/plugin install agentix@claude-skills
/plugin install sentryx@claude-skills
/plugin install model-to-bot@claude-skills
/plugin install dokpilot@claude-skills
/plugin install hostbrr-vps@claude-skills
/plugin install openfang@claude-skills
/plugin install clarity@claude-skills
```

## What's in here

| Plugin | What it does | Triggers on |
|---|---|---|
| **keys-keeper** | macOS Keychain-backed secrets manager. Agents put API keys, SSH keys, server creds into your files **without ever seeing the value** — Sealed wrapper + env-gated reveal make leakage architecturally impossible. | "save my OpenRouter key", "put $X into .env", "ssh into prod" |
| **ux-planner** | Turns vague product descriptions into structured English UX specs ready for handoff to a visual-design agent. Hybrid interview + advisor mode for archetype matching. | "хочу приложение для X", "design a SaaS", "сделай продукт" |
| **context-map** | Generates / audits / updates `context-map.md` files — project memory that survives AI context resets. Tracks decisions, known issues, gotchas. | "make a context map", "audit project docs", "agent onboarding doc" |
| **trip-planner** | Extracts flight + hotel data from Aviasales (`avs.io`, `aviasales.ru`) and Ostrovok (`corp.ostrovok.ru`) links, compiles into self-contained HTML itinerary. | Pasting `avs.io/*` / `corp.ostrovok.ru/*` links, "поездка", "отель", "перелёт" |
| **stitch-design** | Google Stitch AI UI generation — bundles 4 sub-skills (design / theme / edit / upload). Generates HTML mockups with Tailwind CSS + PNG screenshots from text prompts. | "design a UI", "make a mockup", "stitch this screen" |
| **agentix** | Teaches agents to work the [Agentix](https://github.com/kyzdes/agentix) issue tracker over MCP — orient via `get_started` + the wiki index, load one issue with `get_context`, file well-specced issues (task-spec + checklist). Full tool reference + index convention. | Connected to an `agentix` MCP server, "заведи задачу", "create an issue", "plan an epic", Agentix |
| **sentryx** | Instrument an app with SentryX over a remote MCP — error tracking + distributed tracing + product analytics/funnels, correlated by `trace_id`. Connect-once flow, stack-aware instrument flow, and a fix-bugs flow (`search_issues` → `prepare_fix_bundle`). | Connected to a `sentryx` MCP server, "instrument my app", "error tracking", "define a funnel", "set up SentryX" |
| **dokpilot** | Agent-native VPS deploy/ops over Dokploy — one command from a GitHub repo to a running app with SSL + auto-deploy, plus managing servers, databases, domains, and logs. | "deploy this", "put it online", "set up a VPS", "my site is down", "redeploy", Dokploy |
| **hostbrr-vps** | Manage HostBRR VPS via the VirtFusion REST API — list servers, rebuild/reinstall the OS, power actions, SSH keys, ISO, VNC, rescue mode, resource packs, async task polling. | HostBRR servers, `vps.hostbrr.com`, "rebuild a VPS", a HostBRR API token |
| **model-to-bot** | Turns a model / HF Space / API into a production Telegram bot — 7-phase playbook (Discover→…→Deploy) + 32-entry gotchas catalog + real starter templates. *(Private repo — installs for the owner.)* | "build a telegram bot for X", "wrap this Space in a bot", "model-backed bot" |
| **openfang** | Operator playbook for OpenFang v0.6.9 (the Rust "agent operating system"). Router SKILL.md + 11 references + 3 slash commands + a read-only diagnose script + the OpenFang MCP server. Every claim marked VERIFIED / UPSTREAM / SUSPECT; 385 verified against a live install. Upstream is abandoned at v0.6.9 — workarounds are permanent. | "перезапусти openfang", "агент не отвечает", "добавь модель", "openfang молчит", "telegram bot silent" |
| **clarity** | Правка русских текстов до чёткой и ёмкой речи: диагноз → 14 законов → линт со словарями → тон-чек. Синтез 6 верифицированных ресерчей школ ясности (Williams, Оруэлл/Zinsser, Пинкер, Чуковский/Галь, инфостиль, психолингвистика); лечит и канцелярит, и AI-звучание; мифы — в чёрном списке. | "упакуй/причеши текст", "убери канцелярит", "звучит как ИИ", "сделай чётко и ёмко", "сократи без потери смысла" |

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
- [`kyzdes/agentix-skill`](https://github.com/kyzdes/agentix-skill)
- [`kyzdes/sentryx-skill`](https://github.com/kyzdes/sentryx-skill)
- [`kyzdes/model-to-bot`](https://github.com/kyzdes/model-to-bot) *(private)*
- [`kyzdes/dokpilot`](https://github.com/kyzdes/dokpilot)
- [`kyzdes/hostbrr-vps-skill`](https://github.com/kyzdes/hostbrr-vps-skill)
- [`kyzdes/openfang-skill`](https://github.com/kyzdes/openfang-skill)

## Codex CLI?

Codex CLI compatibility with Claude Code's `marketplace.json` format is not documented. Codex reads `~/.claude/skills/<name>/SKILL.md` directly, so for Codex users a separate install path (e.g. `git clone` + symlink) will be added later. Today this marketplace is Claude Code-only.

## License

MIT for the marketplace manifest. Each plugin has its own LICENSE; check the linked repos.
