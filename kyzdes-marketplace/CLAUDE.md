# CLAUDE.md · operator instructions for kyzdes/claude-skills marketplace

Это agent-facing инструкция. Когда пользователь говорит «добавь X в мой маркетплейс» / «обнови такой-то скилл» / «выложи новый skill» — открыть этот файл и работать строго по нему.

## ⚡ Обязательное чтение перед действием

| Что делаешь | Что читать **обязательно** |
|---|---|
| Любая операция | этот файл целиком |
| Добавление нового скилла | + `README.md` §3, §4, §7 |
| Sync keys-keeper между двумя репо | + `README.md` §9 (quirk: two-place truth) |
| Меняешь auto-update logic | + `README.md` §5 (механизм), §7 «Обновить hook во всех» |
| У друга что-то не работает | + `README.md` §10 (troubleshooting) |
| Нужна общая картинка | + `topology.md` |

Не дублирую сюда то что в `README.md` — переходи туда по ссылкам. Этот файл — оператор-чеклисты.

---

## Реестр репо (то что нельзя путать)

⚠️ **Обновлено 2026-05-11:** `kyzdes/keys-keeper` репо **архивирован**. Был monolith merge в `kyzdes/keys-keeper-skill` — теперь это один репо, содержит и плагин (`.claude-plugin/`, `skills/`, `hooks/`, `scripts/auto-update.sh`), и Python CLI source (`src/keys_keeper/`, `tests/`, `pyproject.toml`). Sync-pain между двумя репо больше не существует.

| Логическое имя | GitHub | Локальный путь | Роль |
|---|---|---|---|
| маркетплейс | `kyzdes/claude-skills` | `~/Desktop/Projects/claude-skills/` | manifest, only |
| keys-keeper (монолит) | `kyzdes/keys-keeper-skill` | `~/Desktop/Projects/keys-keeper-skill/keys-keeper-skill/` ⚠️ глубокая структура | плагин + CLI + tests в одном репо |
| ~~keys-keeper canonical~~ | ~~`kyzdes/keys-keeper`~~ | — | **АРХИВИРОВАН 2026-05-11**, всё переехало в `kyzdes/keys-keeper-skill` |
| ux-planner | `kyzdes/ux-planner-skill` | `~/Desktop/Projects/ux-planner-skill/` | плагин |
| context-map | `kyzdes/context-map-skill` | `~/Desktop/Projects/context-map-skill/` | плагин |
| trip-planner | `kyzdes/trip-planner-skill` | `~/Desktop/Projects/trip-planner-skill/` | плагин |
| stitch | `kyzdes/claude-stitch-design` | `~/Desktop/Projects/stitch-skill/` ⚠️ локальное имя ≠ repo name | плагин (4 sub-skills) |

**Правило:** прежде чем `git push`, **всегда** проверяй `git remote -v` — пути локальные и GitHub-имена местами расходятся.

---

## Operation 1 · Добавить новый скилл

Самая частая операция. Гарантия успеха = строго по чеклисту.

### Pre-flight (проверь до начала)

- [ ] Скилл уже доведён до ship-quality локально (есть рабочий `SKILL.md` с frontmatter, refs/scripts если нужны).
- [ ] Имя скилла короткое (kebab-case) и уникальное среди существующих 5.
- [ ] Уточнил у пользователя: будет ли репо public (для маркетплейса нужен public; cм. §10 README про trip-planner-skill инцидент).
- [ ] У пользователя установлен `gh` и авторизован (`gh auth status`).

### Шаги

#### 1. Создать GitHub-репо
```bash
gh repo create kyzdes/<NEW-SKILL>-skill --public --description "..."
```

Naming: `<skill-name>-skill` (с суффиксом `-skill`). Все существующие так названы — не ломай pattern.

#### 2. Bootstrap локально

```bash
mkdir -p ~/Desktop/Projects/<NEW-SKILL>-skill && cd $_
git init -b main
mkdir -p .claude-plugin skills/<NEW-SKILL> hooks scripts
```

#### 3. Заполнить manifest

`.claude-plugin/plugin.json`:
```json
{
  "name": "<NEW-SKILL>",
  "description": "<одно предложение>",
  "author": { "name": "kyzdes" }
}
```

**`name` должен быть тот же что после `@` при install** — то есть `<NEW-SKILL>`, не `<NEW-SKILL>-skill`. Имя БЕЗ `-skill` суффикса.

#### 4. Положить SKILL.md + references

```bash
# Если скилл был в root какого-то локального dir (типичный legacy случай):
cp /path/to/source/SKILL.md skills/<NEW-SKILL>/SKILL.md
cp -R /path/to/source/references skills/<NEW-SKILL>/  # если есть
```

**Critical**: `SKILL.md` ссылается на `references/foo.md` через relative path. Они должны лежать **рядом со SKILL.md** в `skills/<NEW-SKILL>/references/`, не в корне репо. Проверь grep'ом:
```bash
grep -E "references/|scripts/|assets/" skills/<NEW-SKILL>/SKILL.md
```
— все упомянутые пути должны существовать в `skills/<NEW-SKILL>/`.

#### 5. Скопировать hook + auto-update.sh из существующего плагина

**Hook идентичен во всех 5 плагинах** — копируй как есть, **не переписывай руками**:

```bash
cp -R ~/Desktop/Projects/keys-keeper-skill/keys-keeper-skill/hooks .
cp -R ~/Desktop/Projects/keys-keeper-skill/keys-keeper-skill/scripts .
chmod +x scripts/auto-update.sh
```

(Любой из 5 плагинов подойдёт как источник — все идентичны. `keys-keeper-skill/keys-keeper-skill` — самый "канонический".)

#### 6. README.md (минимальный)

```markdown
# <NEW-SKILL>-skill

Claude Code skill: <одно предложение>.

## Install

\`\`\`
/plugin marketplace add https://github.com/kyzdes/claude-skills
/plugin install <NEW-SKILL>@claude-skills
\`\`\`

## License

MIT
```

И `LICENSE` (MIT) если есть привычка добавлять.

#### 7. Initial commit + push

```bash
git add .
git status -s  # перепроверь что нет лишнего
git commit -m "chore: initial plugin scaffold"
git remote add origin https://github.com/kyzdes/<NEW-SKILL>-skill.git
git push -u origin main
```

#### 8. Зарегистрировать в маркетплейсе

```bash
cd ~/Desktop/Projects/claude-skills
```

Открыть `.claude-plugin/marketplace.json`, в массиве `plugins` добавить:

```json
{
  "name": "<NEW-SKILL>",
  "description": "<одно предложение>",
  "source": {
    "source": "url",
    "url": "https://github.com/kyzdes/<NEW-SKILL>-skill.git"
  }
}
```

⚠️ **`source: "url"` с явным HTTPS, НЕ `source: "github"` shorthand.** История: 2026-05-11 friend на Windows словил `Permission denied (publickey)` потому что `github` shorthand триггерит SSH clone, а на Винде с git-for-windows SSH частично-настроен (клиент есть, ключей для github нет) и fallback на HTTPS не срабатывает. С `url` form Claude Code сразу идёт через HTTPS, для public репо аутентификация не нужна. См. также §«Константы» ниже.

⚠️ **Не забыть запятую** перед новым entry если он не последний. JSON.

Также обновить таблицу в `README.md` маркетплейса (секция «What's in here»).

```bash
git add .claude-plugin/marketplace.json README.md
git commit -m "feat: add <NEW-SKILL> plugin"
git push
```

### Post-flight (проверь после push)

- [ ] `gh repo view kyzdes/<NEW-SKILL>-skill --json visibility` → `PUBLIC`
- [ ] `gh repo view kyzdes/claude-skills` head — последний коммит про новый плагин
- [ ] JSON валидный: `python3 -c "import json; json.load(open('.claude-plugin/marketplace.json'))"`
- [ ] Smoke install: `claude plugin install <NEW-SKILL>@claude-skills` — должно сработать без ошибок (можно потом uninstall)

### Что **не** надо делать

- ❌ Класть `SKILL.md` в root репо. Только в `skills/<NEW-SKILL>/`. Claude Code автодискавер ищет именно там.
- ❌ Использовать `name` плагина с суффиксом `-skill` (то есть `<X>-skill` в `plugin.json`). После `@` пишут именно содержимое поля `name` — пусть будет коротко.
- ❌ Менять `MARKETPLACE="claude-skills"` в hook'е (см. §«Константы» ниже).
- ❌ Делать `gh repo edit ... --visibility public` без явного согласия пользователя — это access-control change.

---

## Operation 2 · Запушить апдейт существующего скилла

Самая частая операция в life-cycle.

### ⚠️ Tag-aware release (важный gotcha, 2026-05-14)

Если у плагин-репо **есть semver-тэги** (например `v0.2.0`), Claude Code's `claude plugin update` резолвит установленную версию **по highest semver tag**, не по `main`. То есть `git push origin main` **сам по себе не пробьёт** новый код к друзьям — они навсегда останутся залочены на последнем тэге.

**Правило:** для tag'нутого плагина любой пользовательский релиз = bump версии + commit + tag + push:

```bash
cd ~/Desktop/Projects/<plugin-repo>/
# 1. Закоммитить изменения
git add . && git commit -m "feat|fix|docs: ..."

# 2. Bump версии в plugin.json (+ pyproject.toml + src/<pkg>/__init__.py если есть)
# minor для новой фичи, patch для багфикса, major для breaking
# (для keys-keeper-skill — все три места: .claude-plugin/plugin.json,
#  pyproject.toml, src/keys_keeper/__init__.py)
# ... edit version 0.3.0 → 0.3.1 ...
git add . && git commit -m "chore: bump 0.3.0 → 0.3.1"

# 3. Tag + push (тэг ОБЯЗАТЕЛЬНО, иначе auto-update не сработает)
git tag -a v0.3.1 -m "v0.3.1 — <short description>"
git push origin main
git push origin v0.3.1
```

Проверка что reach'ит друзей:
```bash
# Сбросить debounce + запустить hook напрямую
rm -f ~/.cache/kyzdes-claude-skills/last-update
LATEST=$(ls -t ~/.claude/plugins/cache/claude-skills/<plugin>/ | head -1)
bash ~/.claude/plugins/cache/claude-skills/<plugin>/$LATEST/scripts/auto-update.sh
grep -E "<plugin>.*updated from" ~/.cache/kyzdes-claude-skills/update.log | tail -2
# expect: "updated from <old-version> to <new-version>"
```

### Untagged-плагин (без semver-тэгов)

Если у репо **нет** ни одного `v*.*.*` тэга, Claude Code fallback'нется на main HEAD SHA. Тогда обычный flow работает:

```bash
cd ~/Desktop/Projects/<plugin-repo>/
git add . && git commit -m "..." && git push origin main
# дальше всё подтянется через 4ч debounce на стороне друга
```

**Tagging policy (зафиксировано 2026-05-15):**

| Плагин | Mode | Reason |
|---|---|---|
| `keys-keeper-skill` | **tagged** (v0.1, v0.2, v0.3.0) | Содержит Python CLI binary — нужны semver-обещания, breaking-change communication. Релиз = bump + tag (см. tag-aware flow выше) |
| `ux-planner-skill` | main-tracked | Markdown-only. Friend получает свежий SHA при каждом push без церемоний |
| `context-map-skill` | main-tracked | Markdown + python helpers. То же |
| `trip-planner-skill` | main-tracked | Markdown-only. То же |
| `claude-stitch-design` | main-tracked | Markdown + node scratch. То же |

**Правило:** новый плагин в маркетплейсе → **start main-tracked**. Перевести в tag-aware ТОЛЬКО если плагин начинает экспозить binary/CLI/API с semver-обещаниями. Переход НЕОБРАТИМ — после первого `v*.*.*` тэга Claude Code залочится на тэгах навсегда (main-HEAD больше не подтянется до следующего тэга).

Не путать с `package.json` `"version"` или `pyproject.toml` `version =` — это внутренние поля, Claude Code их игнорирует. Только git tag вида `v*.*.*` имеет значение.

### keys-keeper (особый случай больше **НЕ** актуален с 2026-05-11)

**Раньше** скилл был в двух репо (`kyzdes/keys-keeper` + `kyzdes/keys-keeper-skill`) и требовал ручной sync. Сейчас monolith merge (commit `1f75db1`) — обе вещи живут в `kyzdes/keys-keeper-skill`:
- Python CLI source: `src/keys_keeper/`
- Skill content: `skills/keys-keeper/`

Один репо = один источник правды. Стандартный tag-aware flow (см. выше).

Дополнительная деталь: SKILL.md теперь генерируется из canonical.py через `keys init claude --force`. Если правишь канонический prose — правь `src/keys_keeper/agent_rules/canonical.py`, потом `keys init claude --force` чтобы перегенерировать `skills/keys-keeper/SKILL.md`, потом commit/tag/push. CI step `keys init claude --check` ловит drift.

---

## Operation 3 · Изменить auto-update hook (раскатить во все 5)

Если меняется `auto-update.sh` или `hooks.json` — **обязательно** во **все** 5 одновременно. Иначе у друзей будет mix старой и новой версий.

```bash
# 1. Подготовь template
TPL=/tmp/kkz-tpl
mkdir -p "$TPL/hooks" "$TPL/scripts"
# ... напиши новый hooks.json и auto-update.sh в /tmp/kkz-tpl/...
chmod +x "$TPL/scripts/auto-update.sh"

# 2. Раскатать
for repo_dir in keys-keeper-skill/keys-keeper-skill ux-planner-skill context-map-skill trip-planner-skill stitch-skill; do
  cd ~/Desktop/Projects/$repo_dir
  cp "$TPL/scripts/auto-update.sh" scripts/
  cp "$TPL/hooks/hooks.json" hooks/
  if git diff --quiet; then continue; fi
  git add hooks scripts/auto-update.sh
  git commit -m "chore: update auto-update hook"
  git push origin main
done
```

Для понимания почему текущая логика именно такая (debounce, два CLI-вызова, `${CLAUDE_PLUGIN_ROOT}` env var) — `README.md` §5.

---

## Operation 4 · Deprecate скилл

```bash
# 1. Убрать из marketplace.json
cd ~/Desktop/Projects/claude-skills
# ... удалить entry плагина из массива .plugins ...
git add .claude-plugin/marketplace.json README.md
git commit -m "chore: remove <X> from marketplace"
git push

# 2. Опционально архивировать сам репо
gh repo archive kyzdes/<X>-skill
```

⚠️ У уже-установивших друзей плагин **остаётся локально** — Claude Code не делает auto-uninstall при removal из маркетплейса. Это by design (избегаем неожиданного исчезновения функциональности у пользователя).

---

## Константы которые НИКОГДА не менять без обсуждения

Эти значения завязаны друг на друге через файловые пути / запросы / конфиги. Изменение одного без согласования с остальными ломает auto-update.

| Константа | Где задана | Почему важно |
|---|---|---|
| `"name": "claude-skills"` | `marketplace.json` | После `@` друзья пишут это значение. Меняется → старые установки orphan'ятся. |
| `MARKETPLACE="claude-skills"` | `auto-update.sh` (все 5 плагинов) | Hook фильтрует installed_plugins по этому суффиксу. Меняется → hook не апдейтит ничего. |
| `~/.cache/kyzdes-claude-skills/last-update` | `auto-update.sh` (все 5) | Shared debounce stamp. Меняется в одном — теряется дедупликация. |
| `https://github.com/kyzdes/<X>-skill.git` | `marketplace.json` `source.url` | Friend Claude Code clone'ит по этой строке через HTTPS. Renaming → надо синхронно править `marketplace.json`. **Использовать `source: "url"`, не `source: "github"` — иначе friend на Windows получит `Permission denied (publickey)`.** |
| `${CLAUDE_PLUGIN_ROOT}` | `hooks/hooks.json` | Это env var Claude Code'а, не наша. **Не менять.** |
| `event: SessionStart` | `hooks/hooks.json` | Один из определённых event'ов Claude Code. CamelCase. **Не менять.** |

---

## Verification checklist (для любой операции)

Перед тем как сказать «готово»:

- [ ] `gh repo view <touched-repo>` показывает свежий коммит
- [ ] `python3 -c "import json; json.load(open('<touched-json>'))"` не падает (валидный JSON)
- [ ] Если меняется hooks/scripts: все 5 плагинов получили update (см. Operation 3)
- [ ] Если добавляется новый плагин: `claude plugin install <new>@claude-skills` отрабатывает локально
- [ ] Если запушено в репо отличный от текущего dir: проверил `git remote -v` (не запушил случайно в другой репо)

---

## Quick references (FAQ)

**«Где живёт SessionStart hook у плагина?»**
→ `hooks/hooks.json` (НЕ `.claude-plugin/hooks/`). См. `README.md` §3.

**«Минимальный `plugin.json`?»**
→ `{"name": "x"}`. Только `name` обязательное.

**«Как клиенты получат новую версию?»**
→ Авто, через 4ч после push'а (на следующем `claude` старте после истечения debounce). Ручной форс: `/plugin marketplace update claude-skills`. См. `README.md` §5, §6.

**«Можно ли смотреть статистику установок?»**
→ GitHub Traffic API за 14 дней — да. Anthropic-side counts — нет, только для официального маркетплейса. См. `README.md` §8.

**«Какие квирки у конкретных плагинов?»**
→ `README.md` §9. Особенно про keys-keeper (two-place truth) и stitch (4 sub-skills, нужен Stitch API key).

**«Что-то у друга не работает»**
→ `README.md` §10 troubleshooting.

**«У друга `Permission denied (publickey)` при `/plugin install ...`»**
→ Friend на Windows / Linux с git-for-windows / partial SSH. Решение: проверь что в `marketplace.json` source `url` с https URL, **не** `github` shorthand. Если стоит `github` — поменяй на `url` (см. Operation 1 шаг 8), запушь, скажи другу: `/plugin marketplace update claude-skills` + retry install. Уже починено 2026-05-11.

**«Нужна вся картинка одним экраном»**
→ `topology.md`.

---

## Memory hooks (для агента)

Если в будущей сессии встречаешь:

- «обнови мой скилл X в маркетплейсе» → Operation 2
- «выложи новый скилл / добавь к моим скиллам» → Operation 1
- «исправь hook» / «у друга не апдейтится» → Operation 3 + `README.md` §10
- «убери из маркетплейса» → Operation 4
- «как у меня устроен маркетплейс?» → пользователь хочет напоминание, читай `README.md` §1-2

При неясности **переспроси один раз** прежде чем создавать репо / делать destructive op. Создание GH-репо обратимо (`gh repo delete`), но visibility-changes и rebases — нет.
