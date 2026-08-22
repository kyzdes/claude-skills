# kyzdes/claude-skills · operator notes

Документация моего личного маркетплейса Claude Code skills. Не для друзей-пользователей (для них есть `README.md` в самом маркетплейс-репо), а для меня и для будущих Claude-сессий, которые будут что-то на этом маркетплейсе делать.

> **Назначение:** объяснить как всё устроено, чтобы через 6 месяцев / в новой сессии / при context-reset не пришлось reverse-engineer'ить с нуля.

## Содержание

1. [Что это и зачем](#1-что-это-и-зачем)
2. [Топология: 6 репо](#2-топология-6-репо)
3. [Анатомия плагина](#3-анатомия-плагина)
4. [Анатомия маркетплейса](#4-анатомия-маркетплейса)
5. [Auto-update механизм](#5-auto-update-механизм)
6. [User-side flow: установка, обновление, удаление](#6-user-side-flow-установка-обновление-удаление)
7. [Dev-side flow: добавить скилл, запушить апдейт, deprecate](#7-dev-side-flow)
8. [Статистика и телеметрия](#8-статистика-и-телеметрия)
9. [Quirks per plugin](#9-quirks-per-plugin)
10. [Troubleshooting](#10-troubleshooting)
11. [Как сюда дошло (краткая история)](#11-как-сюда-дошло-краткая-история)

---

## 1. Что это и зачем

**Маркетплейс = тонкий orchestrator, плагины = независимые репо.**

Цели, которые он должен закрывать:

- **«Поделиться скиллом одной командой»** — друг получает все нужные мне скиллы через `/plugin marketplace add` + `/plugin install <name>@claude-skills`.
- **«Обновлять автоматически без действий друга»** — каждый push в любой из плагин-репо доезжает до друга при следующем старте `claude`, без `/plugin marketplace update` руками.
- **«Per-skill granularity»** — друг ставит только то что хочет, не пакетом.
- **«Plugins живут в отдельных репо»** — каждый плагин версионируется независимо, маркетплейс — просто manifest со ссылками. Менять один плагин не значит трогать остальные.
- **«Codex CLI — потом»** — формат `marketplace.json` пока Claude Code-only. Codex использует `~/.claude/skills/<name>/SKILL.md` напрямую; для него позже добавлю `scripts/install-codex.sh` который symlink'ает skill subdirs.

**Чего маркетплейс не закрывает:**

- Per-user аналитика (Anthropic не отдаёт стат по третьесторонним маркетплейсам — только GitHub clones как proxy).
- Платные плагины / лицензирование (никакой инфраструктуры биллинга).
- Cross-platform (только macOS-критичные плагины типа `keys-keeper` работают только на macOS — это ограничение самих плагинов, не маркетплейса).

---

## 2. Топология: 6 репо

```
                    ┌──────────────────────────────────┐
                    │  github.com/kyzdes/claude-skills │ ← orchestrator
                    │                                  │
                    │  .claude-plugin/marketplace.json │
                    │     ↓ ссылается на 5 плагинов:   │
                    └──────────────────────────────────┘
                                    │
                ┌───────────────────┼───────────────────┐
                ↓                   ↓                   ↓
   ┌──────────────────────┐ ┌─────────────────┐ ┌──────────────────────┐
   │ kyzdes/              │ │ kyzdes/         │ │ kyzdes/              │
   │ keys-keeper-skill    │ │ ux-planner-skill│ │ context-map-skill    │
   │                      │ │                 │ │                      │
   │ .claude-plugin/      │ │ .claude-plugin/ │ │ .claude-plugin/      │
   │ skills/keys-keeper/  │ │ skills/ux-..../ │ │ skills/context-map/  │
   │ hooks/hooks.json     │ │ hooks/hooks.json│ │ hooks/hooks.json     │
   │ scripts/auto-update.sh│ │ scripts/...    │ │ scripts/...          │
   └──────────────────────┘ └─────────────────┘ └──────────────────────┘

                ┌───────────────────┴───────────────────┐
                ↓                                       ↓
   ┌──────────────────────┐         ┌────────────────────────────────┐
   │ kyzdes/              │         │ kyzdes/claude-stitch-design    │
   │ trip-planner-skill   │         │ (= "stitch-skill" локально)    │
   │ ...                  │         │ skills/{stitch-design,         │
   └──────────────────────┘         │         stitch-theme,          │
                                    │         stitch-edit,           │
                                    │         stitch-upload}/        │
                                    │ ← 4 sub-skills в одном плагине │
                                    └────────────────────────────────┘
```

**6 репо итого = 1 маркетплейс + 5 плагинов.**

| Репо | Роль | Локально лежит в |
|---|---|---|
| [`kyzdes/claude-skills`](https://github.com/kyzdes/claude-skills) | маркетплейс-orchestrator | `~/Desktop/Projects/claude-skills/` |
| [`kyzdes/keys-keeper-skill`](https://github.com/kyzdes/keys-keeper-skill) | **монолит**: плагин + Python CLI + tests в одном репо | `~/Desktop/Projects/keys-keeper-skill/keys-keeper-skill/` ⚠️ глубокая структура |
| [`kyzdes/ux-planner-skill`](https://github.com/kyzdes/ux-planner-skill) | плагин (renamed из ux-researcher-skill) | `~/Desktop/Projects/ux-planner-skill/` |
| [`kyzdes/context-map-skill`](https://github.com/kyzdes/context-map-skill) | плагин | `~/Desktop/Projects/context-map-skill/` |
| [`kyzdes/trip-planner-skill`](https://github.com/kyzdes/trip-planner-skill) | плагин | `~/Desktop/Projects/trip-planner-skill/` |
| [`kyzdes/claude-stitch-design`](https://github.com/kyzdes/claude-stitch-design) | плагин (4 sub-skills) | `~/Desktop/Projects/stitch-skill/` |

⚠️ **`keys-keeper-skill` — монолит (обновлено 2026-05-11):**
- ~~Раньше: канонический скилл жил в `kyzdes/keys-keeper`, плагин-копия в `kyzdes/keys-keeper-skill`, ручной sync.~~
- **Сейчас:** `kyzdes/keys-keeper` **архивирован**. `kyzdes/keys-keeper-skill` содержит и плагин (`.claude-plugin/`, `skills/`, `hooks/`, `scripts/`), и Python CLI source (`src/keys_keeper/`, `tests/`, `pyproject.toml`). Один источник правды — никаких sync операций.
- SKILL.md теперь генерируется из `src/keys_keeper/agent_rules/canonical.py` через `keys init claude --force`. CI step `keys init claude --check` ловит drift.
- Локальный fossil `~/Desktop/Projects/keys-keeper-skill-repo/` (pre-monolith) перенесён в `~/Desktop/Projects/_design-archive/keys-keeper-skill-repo-pre-monolith-2026-05-11/`. Не использовать.

---

## 3. Анатомия плагина

Каждый плагин — Git-репо со следующей структурой:

```
<plugin-repo>/
├── .claude-plugin/
│   └── plugin.json           ← манифест (минимум: {"name": "..."})
├── skills/
│   └── <skill-name>/
│       ├── SKILL.md          ← основной файл скилла
│       └── references/       ← опциональные подфайлы которые SKILL.md использует
├── hooks/
│   └── hooks.json            ← SessionStart hook (см. §5)
├── scripts/
│   └── auto-update.sh        ← скрипт hook'а (debounced auto-update)
└── README.md                 ← описание (опционально)
```

### `.claude-plugin/plugin.json`

```json
{
  "name": "keys-keeper",
  "description": "macOS-first secrets manager skill...",
  "author": { "name": "kyzdes" }
}
```

**Поля:**
- `name` — **обязательное**. Идентификатор плагина. По нему друг ставит: `/plugin install <name>@<marketplace>`.
- `description`, `author`, `version` — опциональные, только для отображения в UI.

Минимально валидный `plugin.json` это `{"name": "x"}` — Claude Code сам автодискавер'ит `skills/`, `hooks/`, `commands/`, `agents/`, `mcp/` папки.

### `skills/<skill-name>/SKILL.md`

Стандартный Claude Code skill — markdown с YAML frontmatter:

```yaml
---
name: keys-keeper
description: <одно предложение для триггера + use-cases>
---
```

**Имя в frontmatter `SKILL.md` не обязано совпадать с именем плагина** — но обычно совпадает. У `claude-stitch-design` плагин один (`name: "stitch-design"`), а внутри `skills/{stitch-design,stitch-theme,stitch-edit,stitch-upload}/` — четыре скилла, каждый со своим `name:` в frontmatter (`stitch-design`, `stitch-theme`, и т.д.).

Файлы из `references/` или другие, которые SKILL.md адресует через relative path (`references/foo.md`), должны лежать рядом со SKILL.md (в `skills/<name>/references/`), не в root репо.

### `hooks/hooks.json`

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash ${CLAUDE_PLUGIN_ROOT}/scripts/auto-update.sh",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

**Что важно:**
- Файл в `hooks/hooks.json`, **не в `.claude-plugin/hooks.json`** (это distinct path).
- Event `SessionStart` (CamelCase, не `session_start`).
- `${CLAUDE_PLUGIN_ROOT}` — env var, который Claude Code раскрывает в путь установленного плагина (например, `~/.claude/plugins/cache/claude-skills/keys-keeper/<sha>/`).
- `timeout: 30` — лимит в секундах. Если hook висит дольше, Claude Code его убьёт.

### `scripts/auto-update.sh`

Идентичный во всех 5 плагинах. Логика см. §5.

---

## 4. Анатомия маркетплейса

Структура `kyzdes/claude-skills`:

```
claude-skills/
├── .claude-plugin/
│   └── marketplace.json
├── README.md                 ← публичный, для друзей
└── .gitignore
```

Никаких `skills/`, `hooks/`, или `scripts/` в маркетплейс-репо нет — это just-a-manifest.

### `.claude-plugin/marketplace.json`

```json
{
  "name": "claude-skills",
  "owner": {
    "name": "kyzdes",
    "email": "kyzdes5@gmail.com"
  },
  "metadata": {
    "description": "kyzdes' personal Claude Code skill marketplace.",
    "version": "1.0.0"
  },
  "plugins": [
    {
      "name": "keys-keeper",
      "description": "macOS Keychain-backed secrets manager...",
      "source": {
        "source": "github",
        "repo": "kyzdes/keys-keeper-skill"
      }
    },
    ...
  ]
}
```

**Ключевые поля:**

- `name` — имя маркетплейса. **Это то, что пишут друзья после `@`** (`/plugin install x@claude-skills`). Не путать с именем репо `claude-skills` — здесь они совпадают потому что я так решил, но могло бы быть `kyzdes-skills` или `vibes-stack`.
- `owner.name` — обязателен.
- `plugins[].source` — поддерживает несколько форм (см. документацию Claude Code):
  - `{"source": "github", "repo": "owner/repo"}` ← мы используем это
  - `{"source": "url", "url": "https://..."}` — любой git URL
  - `{"source": "git-subdir", "url": "...", "path": "..."}` — для monorepo
  - `"./local-path"` — string, для плагинов внутри маркетплейс-репо
  - `{"source": "npm", "package": "..."}` — npm packages

Использование `github` source важно, потому что это позволяет каждому плагину жить в своём репо и версионироваться отдельно. Если бы все плагины лежали в самом маркетплейс-репо как subdirs, любой коммит в любой плагин трогал бы общий репо.

---

## 5. Auto-update механизм

Это **самая нетривиальная часть**. Давай разберём по шагам.

### Проблема

Native `marketplace.json` НЕ автообновляется. Доки Claude Code прямо говорят: «Users refresh their local copy with `/plugin marketplace update`». То есть друг должен **руками** запустить эту команду, иначе он навсегда останется на той версии плагина, которая была когда он установил.

Это противоречит моему требованию «без действий друга». Решение — добавить `SessionStart` hook в **каждый** плагин, который вызывает обновление автоматически на каждом старте `claude`.

### Решение в одной картинке

```
friend types `claude` → session starts → SessionStart hook fires
                                                ↓
                         (от каждого установленного плагина claude-skills'а)
                                                ↓
                         все вызывают bash auto-update.sh
                                                ↓
                       первый: смотрит ~/.cache/kyzdes-claude-skills/last-update
                                  — если < 4ч назад, exit 0
                                  — иначе: touch stamp, дальше
                                                ↓
                       остальные: видят stamp = новый, exit 0 (silent)
                                                ↓
                       первый: claude plugin marketplace update claude-skills
                                                ↓
                       первый: для каждого installed plugin от этого маркетплейса:
                              claude plugin update <name>@claude-skills
                                                ↓
                       Claude Code скачивает новые SHA в кэш (новые SHA-папки)
                                                ↓
                       installed_plugins.json:
                              version → новый SHA
                              installPath → путь к новой SHA-папке
                                                ↓
                       сообщение: "Restart to apply changes"
                                                ↓
                       при следующем старте claude — новый код активен
```

### Файлы и их роли

**`scripts/auto-update.sh`** (полный текст — см. любой плагин-репо):

```bash
#!/usr/bin/env bash
set -e
MARKETPLACE="claude-skills"
STAMP_DIR="${HOME}/.cache/kyzdes-claude-skills"
STAMP="${STAMP_DIR}/last-update"
LOG="${STAMP_DIR}/update.log"
DEBOUNCE_SEC="${KKZ_AUTO_UPDATE_INTERVAL_SEC:-14400}"  # 4h default

# Debounce: shared timestamp file
if [ -f "$STAMP" ]; then
  age=$(...);  if [ "$age" -lt "$DEBOUNCE_SEC" ]; then exit 0; fi
fi

mkdir -p "$STAMP_DIR" && date > "$STAMP"

CLAUDE_BIN="$(command -v claude || true)"
[ -n "$CLAUDE_BIN" ] && [ -x "$CLAUDE_BIN" ] || exit 0

# 1. Refresh manifest (cheap, just git-fetches the marketplace repo)
"$CLAUDE_BIN" plugin marketplace update "$MARKETPLACE" 2>&1 | sed 's/^/  /' || true

# 2. For each installed plugin from this marketplace, check + update
python3 -c "
import json
with open('${HOME}/.claude/plugins/installed_plugins.json') as f:
    data = json.load(f)
suffix = '@${MARKETPLACE}'
for key in data.get('plugins', {}):
    if key.endswith(suffix):
        print(key[:-len(suffix)])
" 2>/dev/null | while read -r plugin; do
  "$CLAUDE_BIN" plugin update "$plugin@${MARKETPLACE}" 2>&1 | sed 's/^/    /' || true
done
```

Логика:
- **Дебаунс через shared stamp file** — если 5 плагинов из маркетплейса установлены, и каждый при `SessionStart` запускает свой hook, то они все стартуют почти одновременно. Первый создаёт stamp, остальные видят свежий stamp и тихо выходят. **Экономия:** N×1 → 1×N (где N — обращений к GitHub).
- **Default debounce 4 часа** — на usual usage (несколько `claude` сессий в день) обновления подтянутся 1-2 раза в сутки. Friend может переопределить через env var `KKZ_AUTO_UPDATE_INTERVAL_SEC=...`.
- **`claude plugin marketplace update`** обновляет marketplace.json (кэш в `~/.claude/plugins/marketplaces/<name>/`).
- **`claude plugin update <plugin>@<marketplace>`** — это и есть **настоящий update**. Claude Code чекает source repo, и если есть новый коммит, скачивает новый SHA в `~/.claude/plugins/cache/<marketplace>/<plugin>/<new-sha>/`.

### Cache layout

После N установок и M обновлений у друга на диске будет:

```
~/.claude/plugins/
├── marketplaces/
│   └── claude-skills/                ← clone маркетплейс-репо
│       ├── .git/
│       ├── .claude-plugin/marketplace.json
│       └── README.md
├── cache/
│   └── claude-skills/                ← плагин-кэш по этому маркетплейсу
│       ├── keys-keeper/
│       │   ├── 62693fe23663/         ← старый SHA (не удаляется автоматически)
│       │   ├── 11842e0153dd/
│       │   └── 810a41728a95/         ← actively-loaded SHA
│       ├── ux-planner/
│       │   └── 20b2c1a0fd16/
│       └── ...
├── installed_plugins.json            ← truth source: какой SHA сейчас активен
└── known_marketplaces.json
```

**Старые SHA-папки накапливаются** — Claude Code не удаляет их при `plugin update`. Friend может вызвать `claude plugin prune` чтобы убрать старые. Не критично — это просто диск.

### Что считается «активной версией»

Claude Code читает **`installed_plugins.json`**:

```json
{
  "version": 2,
  "plugins": {
    "keys-keeper@claude-skills": [
      {
        "scope": "user",
        "installPath": "/Users/.../cache/claude-skills/keys-keeper/810a41728a95",
        "installedAt": "2026-05-07T03:08:43.816Z",
        "lastUpdated": "2026-05-07T09:14:41.584Z",
        "gitCommitSha": "11842e0153dd..."  // ⚠️ это поле НЕ обновляется при update
      }
    ]
  }
}
```

**Авторитетные поля** для определения текущей версии: `installPath` (директория с актуальным кодом) + `version` из `claude plugin list --json`. Поле `gitCommitSha` в `installed_plugins.json` — **legacy, не апдейтится**, не доверять.

### "Restart required to apply"

Claude Code пишет это после `plugin update`. Это означает: новый код **скачан**, но **не загружен** в текущую сессию. Текущая сессия продолжает работать со старым SHA. На **следующем** старте `claude` — новый.

Это нормальное поведение и оно неизбежно — нельзя горячо подменять загруженные skills/agents/hooks без неконсистентного состояния.

---

## 6. User-side flow: установка, обновление, удаление

Что делает друг.

### Установка

```bash
# 1. Добавить маркетплейс (один раз)
/plugin marketplace add https://github.com/kyzdes/claude-skills

# 2. Установить нужные плагины
/plugin install keys-keeper@claude-skills
/plugin install ux-planner@claude-skills
/plugin install context-map@claude-skills
/plugin install trip-planner@claude-skills
/plugin install stitch-design@claude-skills

# 3. Рестартнуть claude — плагины активируются
```

После этого:
- При следующем старте каждого SessionStart hook'а сработает дебаунсный auto-update (один из них пройдёт работу, остальные silent skip).
- Пейлоад скиллов доступен — Claude Code находит их при инициализации.

### Обновления

**Автоматически** — friend ничего не делает. Каждый старт `claude`:
1. Hook вызывает `claude plugin marketplace update claude-skills` (refresh manifest).
2. Hook вызывает `claude plugin update <name>@claude-skills` для каждого установленного плагина.
3. Если есть новые коммиты — скачиваются.
4. Применятся при **следующем** старте.

**Вручную** (если нужно прямо сейчас, не дожидаясь сессии):
```bash
/plugin marketplace update claude-skills
/plugin update keys-keeper@claude-skills
```

**Принудительно сбросить дебаунс** (debug):
```bash
rm ~/.cache/kyzdes-claude-skills/last-update
```

**Сменить периодичность авто-апдейтов:**
```bash
export KKZ_AUTO_UPDATE_INTERVAL_SEC=86400  # раз в сутки
export KKZ_AUTO_UPDATE_INTERVAL_SEC=0       # каждый старт сессии
```

### Удаление

**Один плагин:**
```bash
/plugin uninstall keys-keeper@claude-skills
```

**Весь маркетплейс:**
```bash
/plugin uninstall keys-keeper@claude-skills
/plugin uninstall ux-planner@claude-skills
# ... все
/plugin marketplace remove claude-skills
```

**Подчистить старые SHA-кэши:**
```bash
/plugin prune
```

Auto-update hook автоматически перестаёт работать если ни один плагин из маркетплейса не установлен (некому стартануть hook).

---

## 7. Dev-side flow

### Запушить апдейт скилла

Самый частый случай. Я редактирую скилл локально, надо донести до друзей.

```bash
cd ~/Desktop/Projects/<plugin-repo>/
# редактирую SKILL.md или references/...
git add . && git commit -m "..." && git push origin main
```

**Всё.** В течение 4 часов (default debounce) каждый друг при старте `claude` получит новый SHA. Применится на следующем рестарте.

⚠️ **keys-keeper особый случай (обновлено 2026-05-11/2026-05-14):**

После monolith merge всё в одном `kyzdes/keys-keeper-skill` репо. **Двух мест правды больше нет.** Плюс плагин **tagged** (semver), поэтому нужен tag-aware flow:

```bash
cd ~/Desktop/Projects/keys-keeper-skill/keys-keeper-skill

# Если правишь SKILL.md prose — правь canonical.py, потом регенерируй:
# vim src/keys_keeper/agent_rules/canonical.py
# keys init claude --force   # regen skills/keys-keeper/SKILL.md
git add . && git commit -m "feat|fix: ..."

# Bump версии в 3 местах (CLI binary = semver promise):
# .claude-plugin/plugin.json, pyproject.toml, src/keys_keeper/__init__.py
git add . && git commit -m "chore: bump 0.3.X → 0.3.Y"

# Tag + push (ОБЯЗАТЕЛЬНО, иначе auto-update не пробьёт)
git tag -a v0.3.Y -m "v0.3.Y — <description>"
git push origin main
git push origin v0.3.Y
```

Подробнее про tag-aware см. `CLAUDE.md` Operation 2.

### Добавить новый скилл (6-й плагин)

1. **Создать новый плагин-репо**:
   ```bash
   gh repo create kyzdes/<new-skill>-skill --public --description "..."
   mkdir ~/Desktop/Projects/<new-skill>-skill && cd $_
   git init -b main
   ```

2. **Структура**:
   ```
   .claude-plugin/plugin.json   {"name": "<new-skill>", ...}
   skills/<new-skill>/SKILL.md  + references/ если надо
   hooks/hooks.json             ← скопировать из любого существующего
   scripts/auto-update.sh       ← скопировать тоже
   README.md                    ← короткий
   ```

3. **Скопировать hook + скрипт** из любого существующего плагина — они идентичны:
   ```bash
   cp -R ~/Desktop/Projects/keys-keeper-skill/keys-keeper-skill/{hooks,scripts} .
   ```

4. **Запушить**:
   ```bash
   git add . && git commit -m "chore: initial..." && git push -u origin main
   ```

5. **Добавить в `marketplace.json`** в `kyzdes/claude-skills`:
   ```json
   {
     "name": "<new-skill>",
     "description": "...",
     "source": { "source": "github", "repo": "kyzdes/<new-skill>-skill" }
   }
   ```

6. **Закоммитить + запушить marketplace**:
   ```bash
   cd ~/Desktop/Projects/claude-skills/
   git add .claude-plugin/marketplace.json README.md   # README тоже обнови
   git commit -m "feat: add <new-skill> plugin"
   git push
   ```

7. **Друзья**: при следующем `/plugin marketplace update claude-skills` (или auto-update через 4ч) увидят новый плагин в списке. Они должны явно `/plugin install <new-skill>@claude-skills` — auto-install новых плагинов нет.

### Deprecate скилл

1. **Убрать из `marketplace.json`** entry плагина → push маркетплейса.
2. У уже-установленных друзей плагин остаётся (Claude Code не удаляет installed plugin'ы при удалении из маркетплейса).
3. Опционально архивировать сам репо: `gh repo archive kyzdes/<skill>-skill`.

### Обновить hook/auto-update логику во всех плагинах

Если меняется `auto-update.sh` (например хочется новой логики дебаунса) — надо запушить во **все 5** плагин-репо одновременно, иначе у друзей будет mix старой и новой версий хуков. Скрипт-helper для этого был у меня в `/tmp/kkz-marketplace-hook-tpl/` во время первоначальной настройки; можно восстановить:

```bash
# Создать template
mkdir -p /tmp/kkz-tpl/{hooks,scripts}
# ... написать новый auto-update.sh + hooks.json ...

# Раскатить во все 5
for repo_dir in keys-keeper-skill/keys-keeper-skill ux-planner-skill context-map-skill trip-planner-skill stitch-skill; do
  cd ~/Desktop/Projects/$repo_dir
  cp /tmp/kkz-tpl/scripts/auto-update.sh scripts/
  cp /tmp/kkz-tpl/hooks/hooks.json hooks/
  git add . && git commit -m "chore: update auto-update hook"
  git push origin main
  cd -
done
```

---

## 8. Статистика и телеметрия

### Что доступно

**GitHub Traffic API** (per-repo, 14-day window, агрегаты):
```bash
gh api "repos/kyzdes/keys-keeper-skill/traffic/clones"
gh api "repos/kyzdes/keys-keeper-skill/traffic/views"
```

В браузере: `https://github.com/kyzdes/<repo>/graphs/traffic`.

Каждое `claude plugin install` делает `git clone` — отлавливается как clone event. `claude plugin update` использует существующий clone + git fetch — НЕ создаёт новый clone event (так что для подсчёта именно установок clones — хороший proxy).

### Что НЕ доступно

- **Anthropic install counts** (`~/.claude/plugins/install-counts-cache.json`) — только для `claude-plugins-official`. Третьесторонние маркетплейсы Anthropic не агрегирует. Подтверждено: 392 entries в кэше — все `@claude-plugins-official`.
- **Per-user / per-friend visibility** — GitHub clone stats анонимные. Узнать «вася установил X» без явного opt-in от васи нельзя.
- **Beyond 14 days** — GitHub Traffic API хранит только 2 недели. Для длинной истории нужен self-hosted accumulator (cron + sqlite).

### Если потом понадобится накопительная статистика

~50 строк bash + sqlite, запускается раз в сутки через launchd:

```bash
#!/usr/bin/env bash
DB=~/.local/share/kyzdes-marketplace-stats.sqlite
sqlite3 "$DB" "CREATE TABLE IF NOT EXISTS traffic (repo TEXT, ts TEXT, clones INT, uniques INT, PRIMARY KEY(repo, ts))"
for r in keys-keeper-skill ux-planner-skill context-map-skill trip-planner-skill claude-stitch-design claude-skills; do
  gh api "repos/kyzdes/$r/traffic/clones" --jq '.clones[] | [."timestamp", .count, .uniques] | @csv' | \
    awk -F',' -v repo="$r" '{print "INSERT OR REPLACE INTO traffic VALUES(\""repo"\","$1","$2","$3");"}' | \
    sqlite3 "$DB"
done
```

Не сделал — нет насущной нужды. Если друзья начнут реально пользоваться, добавлю.

---

## 9. Quirks per plugin

### `keys-keeper`

- **Требует `pipx install git+https://github.com/kyzdes/keys-keeper.git`** на стороне друга (это сам CLI `keys`). Скилл — это markdown-инструкции для агента; CLI `keys` — отдельный binary.
- **Two-place truth**: канонический скилл в `kyzdes/keys-keeper/skills/keys-keeper/` (главный продуктовый репо), плагин-репо `kyzdes/keys-keeper-skill` — отдельный sync. См. §7.
- **macOS-only** (Keychain). На Linux/Win не запустится.

### `ux-planner`

- **Был раньше `kyzdes/ux-researcher-skill`**, переименован в `kyzdes/ux-planner-skill` (GitHub держит redirect, но local clone уже set-url).
- В frontmatter `SKILL.md` — `name: ux-planner` (всегда было).
- Старая версия `~/Desktop/Projects/ux-planner-skill/` (без git remote, до 2026-04-29) лежит в `~/Desktop/Projects/_design-archive/ux-planner-skill-old-fossil-2026-04-29/` как backup. Можно удалить.

### `context-map`

- Содержит `scripts/*.py` (`migrate_legacy.py`, `inspect_project.py`, `discover_projects.py`, etc.) — **в `skills/context-map/scripts/`**, не в root репо. SKILL.md ссылается через `scripts/...` — relative к SKILL.md, всё работает.
- Repo root содержит ещё `landing/`, `conext-map-skill-plan/` — это project-internal docs, не часть плагина.

### `trip-planner`

- **Чистый** — только SKILL.md, никаких references / scripts. Ставится без зависимостей.
- Был приватным до миграции — публичен сейчас (явное согласие на это было).

### `stitch-design`

- **4 sub-skills в одном плагине**: `stitch-design`, `stitch-theme`, `stitch-edit`, `stitch-upload`. Установка через `/plugin install stitch-design@claude-skills` тащит все 4.
- **Был в отдельном маркетплейсе** `stitch-design-marketplace` (тот же репо, но как самостоятельный marketplace). Сейчас удалён — стич только из `claude-skills`.
- **Требует Google Stitch API key + Node.js** на стороне друга. Setup-скилл `stitch-setup` объясняет как.

---

## 10. Troubleshooting

### Друг говорит «`/plugin install ...` ругается на 404»

Скорее всего исходный репо плагина приватный или удалён. Проверить:
```bash
gh repo view kyzdes/<plugin>-skill --json visibility,url
```

Если visibility: PRIVATE, надо сделать public (`gh repo edit ... --visibility public`).

### Auto-update не работает у друга

Проверить:

1. **`claude` CLI на PATH?** Hook ищет через `command -v claude`. Если друг ставил Claude Code нестандартно, может не быть в PATH.
2. **stamp-файл существует и свежий?** `~/.cache/kyzdes-claude-skills/last-update` — если времянке < 4ч, hook silent skip. Это работает как задумано.
3. **Логи?** `~/.cache/kyzdes-claude-skills/update.log` — там видно что hook делал на последний раз.
4. **Hook вообще запустился?** Запустить вручную:
   ```bash
   bash ~/.claude/plugins/cache/claude-skills/keys-keeper/<sha>/scripts/auto-update.sh
   echo "exit=$?"
   ```

### `installed_plugins.json` показывает старый sha, а `claude plugin list --json` — новый

Это норма. Поле `gitCommitSha` в `installed_plugins.json` **legacy и не обновляется**. Авторитетный — `version` из `claude plugin list --json` или `installPath` (там SHA-папки). Не баг, не переживать.

### «Restart required to apply changes» — а если рестартнуть?

Тогда новый SHA становится активным. До рестарта старый код продолжает работать в текущей сессии — это by design.

### Hooks из 5 плагинов одновременно стартуют — не задавит ли?

Нет. Дебаунс через `~/.cache/kyzdes-claude-skills/last-update`: первый создаёт файл, остальные видят свежий, exit. Время выполнения 4-х silent-skip'ов — миллисекунды. Только один за 4 часа делает реальный network roundtrip.

### Я сделал push, друг рестартнул, всё равно старая версия

Возможные причины (по убыванию вероятности):
1. Дебаунс ещё не остыл — у друга stamp-файл < 4ч свежий. Решение: `rm ~/.cache/kyzdes-claude-skills/last-update`, рестартнуть `claude`.
2. `claude` не на PATH или права на bash-выполнение скрипта не выставлены (`chmod +x`).
3. У друга нет интернета (silent fail в скрипте — там везде `|| true`).
4. Тебе показалось что push'нул — проверь `gh repo view ... --json defaultBranchRef --jq .defaultBranchRef.target.history.nodes`.

---

## 11. Как сюда дошло (краткая история)

Чтобы будущий контекст-резет не пытался reverse-engineer-ить решения:

- **2026-05-07 (вечер)** — brainstorm: per-skill marketplace + auto-update без действий друга. Решено: native Claude Code marketplace через `marketplace.json` + GitHub source per plugin + SessionStart hook для авто-апдейтов.
- **2026-05-07 (ночь)**:
  - Слияние ux-researcher-skill → ux-planner-skill (renamed, dropped ux-researcher).
  - Создан `kyzdes/keys-keeper-skill` extract из основного `kyzdes/keys-keeper`.
  - Нормализованы 3 root-level скилла (`SKILL.md` → `skills/<name>/`).
  - Stitch уже был plugin-shaped, не трогал.
  - Создан `kyzdes/claude-skills` маркетплейс.
  - Auto-update hook v1: делал `git pull` на cache dirs. **Это было неправильно** — Claude Code хранит plugin checkouts в SHA-папках, `git pull` на них ничего не апдейтит.
  - Smoke test показал баг → переписал hook на `claude plugin update` CLI.
  - Все 5 репо запушены, все public, маркетплейс public.
- **2026-05-08** — миграция самого автора на marketplace-installed версии (eat your own dog food). Удалены legacy `~/.claude/skills/{keys-keeper,context-map,trip-planner}/` (директории) и сломанный симлинк `ux-planner`. Удалён старый `stitch-design-marketplace` маркетплейс.
- **2026-05-09** — эта документация.

**Ключевое архитектурное решение, которое стоит помнить:**

> **Каждый плагин — независимый репо, маркетплейс — тонкий manifest.** Альтернатива (один маркетплейс-репо, плагины как subdirs) была бы проще на этапе создания, но любое изменение в любом плагине бьёт по common репо — это плохо для версионирования и для friend'овского `git pull` который тащит всё. Per-repo разделение даёт независимое версионирование + clean traffic stats per skill + возможность сделать любой плагин private не трогая остальных.
