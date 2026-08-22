# Topology · cheat sheet

Один экран — вся картина «кто где живёт и как связан».

## Repo graph

```
                              ┌─────────────────────────────────────┐
                              │  github.com/kyzdes/claude-skills    │
                              │  ─────────────────────────────────  │
                              │  .claude-plugin/marketplace.json    │
                              │  README.md (для друзей)             │
                              │  (никаких skills/, hooks/, scripts/)│
                              │                                     │
                              │  marketplace name: "claude-skills"  │
                              └──┬──────────┬─────────┬─────────┬───┘
                                 │ source:  │ source: │ source: │
                                 │ github   │ github  │ github  │ ...
                                 ↓          ↓         ↓         ↓
              ┌────────────┬────┴───┐  ┌───┴───┐  ┌─┴────┐ ┌────────┐
              │            │        │  │       │  │      │ │        │
              ↓            ↓        ↓  ↓       ↓  ↓      ↓ ↓        ↓
         keys-keeper-     ux-     context-  trip-   claude-stitch-design
         skill            planner- map-     planner- ("stitch-skill"
                          skill    skill    skill   локально)
                                                       │
                                  каждый из них:       │
                                  ────────────────     │
                                  .claude-plugin/      │
                                    plugin.json        │ stitch — особый:
                                  skills/<name>/       │ 4 sub-skills:
                                    SKILL.md           │ skills/stitch-design/
                                    references/...     │ skills/stitch-theme/
                                  hooks/hooks.json     │ skills/stitch-edit/
                                  scripts/             │ skills/stitch-upload/
                                    auto-update.sh     │
                                  README.md            ←
```

## Plugin shape (точная)

```
<plugin-repo>/
├── .claude-plugin/
│   └── plugin.json                {"name": "..."}                    ← required
├── skills/
│   └── <skill-name>/
│       ├── SKILL.md               YAML frontmatter + markdown        ← required
│       └── references/            опциональные подфайлы              ← optional
│           └── *.md
├── hooks/
│   └── hooks.json                 SessionStart → bash auto-update.sh ← optional, у нас есть
├── scripts/
│   └── auto-update.sh             debounced update logic             ← у нас есть
├── README.md                      описание                           ← optional
├── LICENSE                        MIT обычно                         ← optional
└── .gitignore
```

## Marketplace shape (точная)

```
claude-skills/
├── .claude-plugin/
│   └── marketplace.json           {"name", "owner", "plugins"[]}     ← required
├── README.md                      friend-facing install instructions
└── .gitignore
```

## Friend's local cache layout

```
~/.claude/plugins/
├── installed_plugins.json         truth source — что установлено
├── known_marketplaces.json        кеш списка marketplaces
├── install-counts-cache.json      кэш Anthropic-side counts (только для claude-plugins-official)
├── marketplaces/
│   └── claude-skills/             clone маркетплейс-репо
│       ├── .git/
│       └── .claude-plugin/marketplace.json
└── cache/
    └── claude-skills/             plugin-checkouts по этому маркетплейсу
        ├── keys-keeper/
        │   ├── 62693fe23663/      old SHA (накапливается, прунится claude plugin prune)
        │   └── 810a41728a95/      ← active SHA (см. installPath в installed_plugins.json)
        ├── ux-planner/
        │   └── 20b2c1a0fd16/
        ├── context-map/
        │   └── ff306658b76f/
        ├── trip-planner/
        │   └── 2b36294622ec/
        └── stitch-design/
            └── 0.2.0/             tagged versions если есть, иначе SHA prefix
                └── skills/stitch-{design,theme,edit,upload}/
```

## Mapping: dev-side ↔ user-side

| dev-side path | user-side path |
|---|---|
| `~/Desktop/Projects/<plugin>-skill/skills/<n>/SKILL.md` | `~/.claude/plugins/cache/claude-skills/<plugin>/<sha>/skills/<n>/SKILL.md` |
| `~/Desktop/Projects/<plugin>-skill/hooks/hooks.json` | `~/.claude/plugins/cache/claude-skills/<plugin>/<sha>/hooks/hooks.json` |
| `~/Desktop/Projects/claude-skills/.claude-plugin/marketplace.json` | `~/.claude/plugins/marketplaces/claude-skills/.claude-plugin/marketplace.json` |

## Ритм обновления

```
me:                           friend's claude:               friend's view:
─────────────                  ────────────────                ─────────────
edit + push to GH      ───→
                                next `claude` start
                               + 4h since last hook   ───→    SessionStart hook fires
                                                              hook calls
                                                                claude plugin marketplace update
                                                                claude plugin update <each>
                                                              → new SHA dirs created in cache
                                                              → installed_plugins.json updated
                               friend continues this           old code still loaded
                               session with OLD code           in current session
                                          ↓
                               friend exits + restarts claude
                                                              ─→ new code loaded
```

**Latency:** dev push → friend has new code = max(4h debounce, time-to-restart). В среднем «следующее утро».
