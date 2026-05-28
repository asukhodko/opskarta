# Executive overlay (`x.exec`)

`x.exec` — встроенный профиль расширения для управленческого и операционного слоя. Он не заменяет `nodes`, `schedule` и `execution`; он собирает поверх них короткую карту для синков, руководительских срезов и документов со статусом программы.

## Структура

```yaml
x:
  exec:
    program: { ... }
    defaults: { ... }
    blocks: { ... }
    edges: [ ... ]
    views: { ... }
```

### `program`

Опциональный блок общей цели:

| Поле | Описание |
|------|----------|
| `committed_date` | Обещанная дата в формате `YYYY-MM-DD`. |
| `nearest_goal` | Ближайшая цель человеческим текстом. |
| `success_by_next_sync` | Что должно быть правдой к следующему синку. |

### `blocks`

`blocks` — словарь `block_id -> block`.

Блок должен задавать ровно одно поле области:

| Поле | Описание |
|------|----------|
| `scope_nodes` | Список обычных `node_id`, из которых считается прогресс блока. |
| `source_blocks` | Список других `block_id`, если блок агрегирует несколько executive-блоков. |

Частые поля блока:

| Поле | Описание |
|------|----------|
| `title` | Короткое название для карточки. |
| `target_gate` | `node_id` ближайшей календарной вехи; узел должен быть в `schedule.nodes`. |
| `kind` | Семантика блока, например `main`, `feeder`, `risk_sidecar`, `aggregate`. |
| `progress_override` | Ручной прогресс `0..1`, если автоматический расчёт не подходит. |
| `mgmt.health` | `green`, `yellow`, `red` или `neutral`. |
| `mgmt.sync_note` | Что сейчас происходит. |
| `mgmt.next_sync_goal` | Что должно сдвинуться к следующему синку. |
| `mgmt.blocker_note` | Внешняя зависимость или blocker. |
| `mgmt.owner` | Человек или команда, если это полезно в отчёте. |

### `edges`

Рёбра связывают executive-блоки:

```yaml
edges:
  - from: prep
    to: cutover
    type: required
  - from: post
    to: cutover
    type: context
    label: "после окна"
```

Допустимые типы:

| Тип | Смысл |
|-----|-------|
| `required` | Обязательный путь. |
| `risk_reduction` | Снижение риска, обычно пунктиром. |
| `context` | Контекстная связь, не основной путь. |

`views.*.edges` может переопределять общий список `edges` для конкретной карты.

### `views`

Executive-view задаёт список блоков и параметры Mermaid-карты:

```yaml
views:
  exec-top:
    direction: LR
    color_mode: mgmt_hybrid
    highlight_current: true
    show_progress: false
    show_gate_date: true
    wrap_title_lines: 2
    blocks: [prep, cutover, post]
```

Поддерживаемые поля:

| Поле | Описание |
|------|----------|
| `direction` | Направление Mermaid flowchart: `LR`, `TB`, `BT`, `RL`. |
| `color_mode` | `status` или `mgmt_hybrid`. |
| `highlight_current` | Подсветить текущий основной блок. |
| `show_progress` | Показывать процент прогресса в карточке. |
| `show_gate_date` | Показывать дату `target_gate`. |
| `show_owner` | Показывать `mgmt.owner`. |
| `wrap_title_lines` | Разбить длинное название на строки. |
| `respect_mgmt_health_for_done` | Для завершённых блоков брать цвет из `mgmt.health`. |
| `reduce_transitive_required_edges` | Скрывать транзитивные `required`-рёбра. |
| `caption` | Текстовая подпись, которую может подхватить Markdown updater. |
| `blocks` | Список `block_id` для вывода. |
| `edges` | Локальный список рёбер для view. |

## Рендеры

```bash
python -m specs.v3.tools.cli render executive plan.yaml exec.yaml --view exec-top
python -m specs.v3.tools.cli render executive-report plan.yaml exec.yaml --section status --lang ru
python -m specs.v3.tools.cli render executive-report plan.yaml exec.yaml --section tracks --view exec-active-tracks --lang ru
python -m specs.v3.tools.cli render executive-report plan.yaml exec.yaml --section signals --view exec-active-tracks --lang ru
```

По умолчанию `executive-report status` использует view `exec-top`, а `tracks`
и `signals` используют `exec-active-tracks`. Передайте `--view`, если секция
документа должна строиться по другому executive-view.
