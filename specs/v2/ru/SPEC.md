<!-- Этот файл сгенерирован автоматически. Не редактируйте вручную! -->
<!-- Для изменений редактируйте файлы в spec/ и запустите: python tools/build_spec.py --lang ru -->

## Оглавление

- [Спецификация opskarta v2](#спецификация-opskarta-v2)
- [Plan Set (многофайловая структура)](#plan-set-многофайловая-структура)
- [Узлы (`nodes`)](#узлы-nodes)
- [Schedule (слой календарного планирования)](#schedule-слой-календарного-планирования)
- [Views (представления)](#views-представления)
- [Валидация](#валидация)

# Спецификация opskarta v2

Эта спецификация описывает формат opskarta v2 с концепцией **overlay schedule** — разделение структуры работ (nodes) и календарного планирования (schedule).

- Формат сериализации: **YAML** (рекомендовано) или JSON.
- Версионирование: поле `version: 2` в корне документа.
- Идентификаторы узлов: строковые ключи в мапе `nodes:`.

> Статус: **Draft**. Спецификация v2 расширяет и переосмысливает v1.

## Ключевые концепции v2

### Overlay Schedule (наложенное расписание)

Главное отличие v2 от v1 — **разделение структуры работ и календарного планирования**:

| Аспект | v1 | v2 |
|--------|----|----|
| Даты в узлах | `start`, `finish`, `duration` в `nodes` | Только в `schedule.nodes` |
| Календарь | `excludes` в `views` | `excludes` в `schedule.calendars` |
| План без дат | Невозможен | Полностью валиден |
| Зависимости | `after` в `nodes` | `after` в `nodes` (без изменений) |

### Plan Set (многофайловая структура)

v2 поддерживает разбиение плана на несколько файлов (фрагментов):

```
project/
├── main.plan.yaml      # meta, statuses
├── nodes.plan.yaml     # nodes
├── schedule.plan.yaml  # schedule
└── views.plan.yaml     # views
```

Фрагменты сливаются в единый **Merged Plan** детерминированным образом.

### Effort (оценка трудозатрат)

v2 вводит поле `effort` — абстрактная оценка трудозатрат в относительных единицах:

```yaml
nodes:
  epic:
    title: "Авторизация"
    effort: 13  # story points, дни, или другие единицы
```

Единица измерения задаётся в `meta.effort_unit` для отображения в UI.

## Структура документа

| Файл | Описание |
|------|----------|
| `10-plan-set.md` | Plan Set: многофайловая структура, слияние фрагментов |
| `20-nodes.md` | Узлы: структура работ без календарных полей |
| `30-schedule.md` | Schedule: слой календарного планирования |
| `40-views.md` | Views: представления для визуализации |
| `50-validation.md` | Валидация: правила и сообщения об ошибках |

## Допустимые top-level блоки

Каждый YAML-файл (фрагмент) может содержать следующие блоки:

| Блок | Описание | Обязательность |
|------|----------|----------------|
| `version` | Версия схемы (должна быть `2`) | Рекомендуется |
| `meta` | Метаданные плана | Опционально |
| `statuses` | Словарь статусов | Опционально |
| `nodes` | Словарь узлов работ | Опционально |
| `schedule` | Слой календарного планирования | Опционально |
| `views` | Представления для визуализации | Опционально |
| `x` | Расширения (namespace для кастомных полей) | Опционально |

Любые другие top-level блоки являются **ошибкой**.

## Минимальный пример

```yaml
version: 2
meta:
  id: demo
  title: "Demo Project"

nodes:
  root:
    title: "Проект"
    kind: summary
```

Этот план валиден без `schedule` — структура работ существует независимо от календарного планирования.

## Полный пример

```yaml
version: 2
meta:
  id: project-x
  title: "Проект X"
  effort_unit: "sp"

statuses:
  not_started: { label: "Не начато", color: "#9ca3af" }
  in_progress: { label: "В работе", color: "#0ea5e9" }
  done: { label: "Готово", color: "#22c55e" }

nodes:
  root:
    title: "Проект X"
    kind: summary
    status: in_progress
  
  phase1:
    title: "Фаза 1: Анализ"
    kind: phase
    parent: root
    effort: 10
  
  phase2:
    title: "Фаза 2: Разработка"
    kind: phase
    parent: root
    after: [phase1]
    effort: 20

schedule:
  calendars:
    default:
      excludes:
        - weekends
        - "2024-03-08"
  
  default_calendar: default
  
  nodes:
    phase1:
      start: "2024-03-01"
      duration: "10d"
    
    phase2:
      duration: "20d"
      # start вычисляется из after: [phase1] в nodes

views:
  gantt:
    title: "Диаграмма Ганта"
    where:
      has_schedule: true
```

---

# Plan Set (многофайловая структура)

Plan Set — это совокупность YAML-файлов (фрагментов), которые сливаются в единый план.

## Концепция

Большие планы можно разбивать на несколько файлов для:

- Организации по логическим частям (структура, расписание, представления)
- Упрощения совместной работы (разные люди редактируют разные файлы)
- Переиспользования компонентов (общие статусы, календари)

## Структура фрагмента

Каждый фрагмент — это YAML-файл с допустимыми top-level блоками:

```yaml
# Допустимые блоки
version: 2
meta: { ... }
statuses: { ... }
nodes: { ... }
schedule: { ... }
views: { ... }
x: { ... }
```

### Правила

- Любой top-level блок, кроме перечисленных, является **ошибкой**.
- Блок `version` ДОЛЖЕН быть одинаковым во всех фрагментах (если указан).
- Пустые фрагменты допустимы.

## Слияние фрагментов

Фрагменты сливаются в **Merged Plan** по следующим правилам:

### 1. Блок `version`

- Должен быть одинаковым во всех фрагментах.
- Если версии различаются — **ошибка**.

### 2. Блок `meta`

- Поля объединяются.
- При конфликте значений одного поля — **ошибка**.

```yaml
# fragment1.yaml
meta:
  id: project-x
  title: "Проект X"

# fragment2.yaml
meta:
  id: project-x      # OK: то же значение
  author: "Иван"     # OK: новое поле

# Результат
meta:
  id: project-x
  title: "Проект X"
  author: "Иван"
```

### 3. Блок `statuses`

- Словари объединяются.
- Дубликат ключа (status_id) — **ошибка** с указанием файлов.

```yaml
# fragment1.yaml
statuses:
  done: { label: "Готово" }

# fragment2.yaml
statuses:
  in_progress: { label: "В работе" }
  done: { label: "Завершено" }  # ОШИБКА: done уже определён

# Ошибка: status 'done' defined in fragment1.yaml and fragment2.yaml
```

### 4. Блок `nodes`

- Словари объединяются.
- Дубликат ключа (node_id) — **ошибка** с указанием файлов.

```yaml
# fragment1.yaml
nodes:
  task1:
    title: "Задача 1"

# fragment2.yaml
nodes:
  task2:
    title: "Задача 2"
  task1:                    # ОШИБКА: task1 уже определён
    title: "Другая задача"

# Ошибка: node 'task1' defined in fragment1.yaml and fragment2.yaml
```

### 5. Блок `schedule`

Schedule сливается по частям:

#### `schedule.calendars`

- Словари объединяются.
- Дубликат ключа (calendar_id) — **ошибка**.

#### `schedule.nodes`

- Словари объединяются.
- Дубликат ключа (node_id) — **ошибка**.

#### `schedule.default_calendar`

- Допускается только в **одном** фрагменте.
- Если указан в нескольких фрагментах — **ошибка**.

```yaml
# fragment1.yaml
schedule:
  default_calendar: work    # OK

# fragment2.yaml
schedule:
  default_calendar: holiday # ОШИБКА: default_calendar уже определён
```

### 6. Блок `views`

- Словари объединяются.
- Дубликат ключа (view_id) — **ошибка**.

### 7. Блок `x` (расширения)

- Словари объединяются.
- Дубликат ключа — **ошибка**.

## Отслеживание источников

Merged Plan сохраняет информацию о файле-источнике для каждого элемента:

```python
# Пример структуры
sources = {
    "node:task1": "nodes.plan.yaml",
    "node:task2": "nodes.plan.yaml",
    "status:done": "main.plan.yaml",
    "calendar:work": "schedule.plan.yaml",
}
```

Это позволяет выдавать информативные сообщения об ошибках с указанием файла.

## Пример многофайлового плана

### main.plan.yaml

```yaml
version: 2
meta:
  id: project-x
  title: "Проект X"
  effort_unit: "sp"

statuses:
  not_started: { label: "Не начато", color: "#9ca3af" }
  in_progress: { label: "В работе", color: "#0ea5e9" }
  done: { label: "Готово", color: "#22c55e" }
```

### nodes.plan.yaml

```yaml
version: 2

nodes:
  root:
    title: "Проект X"
    kind: summary
    status: in_progress
  
  phase1:
    title: "Фаза 1: Анализ"
    kind: phase
    parent: root
    effort: 10
  
  phase2:
    title: "Фаза 2: Разработка"
    kind: phase
    parent: root
    after: [phase1]
    effort: 20
```

### schedule.plan.yaml

```yaml
version: 2

schedule:
  calendars:
    default:
      excludes:
        - weekends
        - "2024-03-08"
  
  default_calendar: default
  
  nodes:
    phase1:
      start: "2024-03-01"
      duration: "10d"
    
    phase2:
      duration: "20d"
```

### views.plan.yaml

```yaml
version: 2

views:
  gantt:
    title: "Диаграмма Ганта"
    where:
      has_schedule: true
  
  backlog:
    title: "Бэклог"
    where:
      has_schedule: false
    order_by: effort
```

## Загрузка Plan Set

Инструменты загружают Plan Set через функцию:

```python
def load_plan_set(files: list[str]) -> MergedPlan:
    """
    Загружает и сливает фрагменты плана.
    
    Args:
        files: Список путей к YAML-файлам
        
    Returns:
        MergedPlan: Объединённый план
        
    Raises:
        LoadError: При ошибке чтения файла
        MergeConflictError: При конфликте слияния
    """
```

### CLI

```bash
# Загрузка нескольких файлов
opskarta validate main.plan.yaml nodes.plan.yaml schedule.plan.yaml

# Рендеринг
opskarta render gantt main.plan.yaml nodes.plan.yaml schedule.plan.yaml --view gantt
```

## Детерминированность слияния

Слияние фрагментов **детерминировано**:

- Порядок файлов не влияет на результат (кроме порядка ошибок).
- Конфликты всегда обнаруживаются, независимо от порядка.
- Один и тот же набор файлов всегда даёт один и тот же Merged Plan.

Это гарантирует воспроизводимость результатов в CI/CD и при совместной работе.

---

# Узлы (`nodes`)

Узел — это единица работ в структуре плана. В v2 узлы описывают **структуру и зависимости** без календарных полей.

## Идентификаторы узлов (node_id)

Каждый узел идентифицируется ключом в словаре `nodes`. Этот ключ (`node_id`) используется для ссылок в `parent`, `after`, `schedule.nodes`, `views`.

### Требования

- `node_id` ДОЛЖЕН быть уникальным в пределах `nodes`.
- `node_id` ДОЛЖЕН быть строкой.

### Рекомендации

- **Рекомендуемый формат:** `^[a-zA-Z][a-zA-Z0-9._-]*$`
  - Начинается с буквы
  - Содержит только буквы, цифры, точки, подчёркивания, дефисы
- **Для совместимости с Mermaid:** избегайте пробелов, скобок, двоеточий.

```yaml
# Хорошие идентификаторы
nodes:
  kickoff: ...
  phase_1: ...
  backend-api: ...
  JIRA.123: ...

# Проблемные идентификаторы
nodes:
  "task with spaces": ...     # Пробелы
  "task:important": ...       # Двоеточие
  123: ...                    # Начинается с цифры
```

## Поля узла

### Обязательные поля

| Поле | Тип | Описание |
|------|-----|----------|
| `title` | string | Название работы |

### Опциональные поля

| Поле | Тип | Описание |
|------|-----|----------|
| `kind` | string | Тип узла (summary, phase, epic, task и др.) |
| `status` | string | Ключ статуса из `statuses` |
| `parent` | string | ID родительского узла (иерархия) |
| `after` | list[string] | Зависимости "после чего" (граф) |
| `milestone` | boolean | Является ли узел вехой |
| `effort` | number | Оценка трудозатрат (≥ 0) |
| `issue` | string | Ссылка на задачу в трекере |
| `notes` | string | Заметки/контекст |
| `x` | object | Расширения |

### Запрещённые поля (перенесены в schedule)

В v2 следующие поля **запрещены** в `nodes`:

| Поле | Куда перенесено |
|------|-----------------|
| `start` | `schedule.nodes.<id>.start` |
| `finish` | `schedule.nodes.<id>.finish` |
| `duration` | `schedule.nodes.<id>.duration` |
| `excludes` | `schedule.calendars.<id>.excludes` |

```yaml
# ОШИБКА в v2
nodes:
  task1:
    title: "Задача"
    start: "2024-03-01"    # ОШИБКА: start запрещён в nodes
    duration: "5d"          # ОШИБКА: duration запрещён в nodes
```

## Поле `kind`

Тип узла для классификации. Рекомендованные значения:

| Значение | Описание |
|----------|----------|
| `summary` | Верхнеуровневый контейнер |
| `phase` | Этап/фаза проекта |
| `epic` | Крупная сущность |
| `user_story` | История/ценность |
| `task` | Конкретная задача |

```yaml
nodes:
  root:
    title: "Проект"
    kind: summary
  
  phase1:
    title: "Анализ"
    kind: phase
    parent: root
```

## Поле `parent` (иерархия)

Определяет родительский узел для построения дерева декомпозиции.

```yaml
nodes:
  root:
    title: "Проект"
  
  phase1:
    title: "Фаза 1"
    parent: root
  
  task1:
    title: "Задача 1"
    parent: phase1
```

### Правила

- Значение `parent` ДОЛЖНО быть существующим `node_id`.
- Циклические ссылки через `parent` **запрещены**.

## Поле `after` (зависимости)

Список узлов, после завершения которых может начаться данный узел.

```yaml
nodes:
  design:
    title: "Дизайн"
  
  implementation:
    title: "Реализация"
    after: [design]
  
  testing:
    title: "Тестирование"
    after: [implementation]
```

### Семантика

- Узел может стартовать после завершения **всех** узлов из `after`.
- Зависимости определяются в `nodes`, **не** в `schedule.nodes`.
- При вычислении расписания учитываются только **scheduled** зависимости.

### Правила

- Каждый элемент `after` ДОЛЖЕН быть существующим `node_id`.
- Циклические зависимости через `after` **запрещены**.

## Поле `milestone` (вехи)

Веха — это событие-точка на временной шкале, а не задача с длительностью.

```yaml
nodes:
  release_v1:
    title: "Релиз v1.0"
    milestone: true
    after: [testing]
```

### Поведение

- Веха отображается как точка/ромб на диаграмме Gantt.
- При вычислении `start` из `after` для вехи **не добавляется** следующий рабочий день:
  - Обычный узел: `start = next_workday(max_finish)`
  - Веха: `start = max_finish`

## Поле `effort` (оценка трудозатрат)

Абстрактная оценка трудозатрат в относительных единицах.

```yaml
meta:
  effort_unit: "sp"  # story points — только для UI

nodes:
  epic:
    title: "Авторизация"
    effort: 13
  
  story1:
    title: "Вход по email"
    parent: epic
    effort: 5
  
  story2:
    title: "Вход через OAuth"
    parent: epic
    effort: 8
```

### Требования

- `effort` ДОЛЖЕН быть **неотрицательным числом** (≥ 0).
- Единица измерения задаётся в `meta.effort_unit` (только для отображения).

### Вычисляемые метрики

Для узлов с детьми автоматически вычисляются:

| Метрика | Описание |
|---------|----------|
| `effort_rollup` | Сумма `effort_effective` всех прямых детей |
| `effort_effective` | `effort` если задан, иначе `effort_rollup` |
| `effort_gap` | `max(0, effort - effort_rollup)` — неполнота декомпозиции |

```yaml
# Пример вычисления
nodes:
  epic:
    title: "Авторизация"
    effort: 13
    # effort_rollup = 5 + 8 = 13
    # effort_effective = 13 (задан явно)
    # effort_gap = max(0, 13 - 13) = 0
  
  story1:
    title: "Вход по email"
    parent: epic
    effort: 5
    # effort_effective = 5 (листовой узел)
  
  story2:
    title: "Вход через OAuth"
    parent: epic
    effort: 8
    # effort_effective = 8 (листовой узел)
```

### Алгоритм вычисления

```python
def compute_effort(node_id):
    node = nodes[node_id]
    children = [n for n in nodes if nodes[n].parent == node_id]
    
    if not children:
        # Листовой узел
        node.effort_effective = node.effort
        return
    
    # Узел с детьми
    for child in children:
        compute_effort(child)
    
    node.effort_rollup = sum(nodes[c].effort_effective or 0 for c in children)
    
    if node.effort is not None:
        node.effort_effective = node.effort
        node.effort_gap = max(0, node.effort - node.effort_rollup)
    else:
        node.effort_effective = node.effort_rollup
```

## Поле `status`

Ссылка на статус из словаря `statuses`.

```yaml
statuses:
  done: { label: "Готово", color: "#22c55e" }

nodes:
  task:
    title: "Задача"
    status: done
```

### Правила

- Значение `status` ДОЛЖНО быть ключом из `statuses`.
- Несуществующий статус — **ошибка**.

## Поля `issue` и `notes`

```yaml
nodes:
  task:
    title: "Реализовать API"
    issue: "JIRA-123"
    notes: |
      Нужно учесть:
      - Авторизацию
      - Rate limiting
```

## Поле `x` (расширения)

Namespace для кастомных полей, не определённых в спецификации.

```yaml
nodes:
  task:
    title: "Задача"
    x:
      assignee: "ivan"
      priority: high
      custom_field: "value"
```

## Пример: план без schedule

План может быть полностью валидным без календарного планирования:

```yaml
version: 2
meta:
  id: backlog
  title: "Бэклог продукта"
  effort_unit: "sp"

nodes:
  epic1:
    title: "Авторизация"
    kind: epic
    effort: 13
  
  story1:
    title: "Вход по email"
    kind: user_story
    parent: epic1
    effort: 5
  
  story2:
    title: "Вход через OAuth"
    kind: user_story
    parent: epic1
    after: [story1]
    effort: 8
```

Такой план можно рендерить как tree, list, deps, но не как Gantt (нет дат).

---

# Schedule (слой календарного планирования)

Schedule — это **опциональный** слой календарного планирования, накладываемый на структуру узлов.

## Концепция

В v2 календарное планирование отделено от структуры работ:

- **Nodes** описывают *что* нужно сделать и в каком порядке (зависимости)
- **Schedule** описывает *когда* это будет сделано (даты, календари)

План может существовать и быть полезным **без** блока `schedule`.

## Структура блока schedule

```yaml
schedule:
  calendars:
    <calendar_id>:
      excludes: [...]
  
  default_calendar: <calendar_id>
  
  nodes:
    <node_id>:
      start: "YYYY-MM-DD"
      finish: "YYYY-MM-DD"
      duration: "Nd"
      calendar: <calendar_id>
```

## Календари (`schedule.calendars`)

Календарь определяет рабочие дни с исключениями.

```yaml
schedule:
  calendars:
    work:
      excludes:
        - weekends
        - "2024-03-08"
        - "2024-05-01"
    
    no_weekends:
      excludes:
        - weekends
    
    all_days:
      excludes: []
```

### Поле `excludes`

Список исключений из рабочих дней:

| Значение | Описание |
|----------|----------|
| `weekends` | Исключить субботу и воскресенье |
| `YYYY-MM-DD` | Исключить конкретную дату (праздник и т.п.) |

```yaml
excludes:
  - weekends           # Сб, Вс
  - "2024-03-08"       # 8 марта
  - "2024-05-01"       # 1 мая
  - "2024-05-09"       # 9 мая
```

## Календарь по умолчанию (`schedule.default_calendar`)

Календарь, используемый для узлов без явного указания `calendar`.

```yaml
schedule:
  calendars:
    work:
      excludes: [weekends]
  
  default_calendar: work  # Используется по умолчанию
  
  nodes:
    task1:
      start: "2024-03-01"
      duration: "5d"
      # calendar не указан → используется "work"
```

### Правила

- `default_calendar` ДОЛЖЕН ссылаться на существующий календарь.
- Допускается только в **одном** фрагменте при многофайловой структуре.

## Расписание узлов (`schedule.nodes`)

Словарь с параметрами планирования для конкретных узлов.

```yaml
schedule:
  nodes:
    task1:
      start: "2024-03-01"
      duration: "5d"
    
    task2:
      duration: "3d"
      # start вычисляется из after в nodes
    
    milestone1:
      # start вычисляется из after в nodes
```

### Поля schedule.nodes

| Поле | Тип | Описание |
|------|-----|----------|
| `start` | string | Дата начала (YYYY-MM-DD) |
| `finish` | string | Дата окончания (YYYY-MM-DD) |
| `duration` | string | Длительность (Nd, Nw) |
| `calendar` | string | Ссылка на календарь |

### Правила

- `node_id` в `schedule.nodes` ДОЛЖЕН существовать в `nodes`.
- `calendar` ДОЛЖЕН существовать в `schedule.calendars`.
- Поле `after` **запрещено** в `schedule.nodes` — зависимости только в `nodes`.

## Состояния узлов

Узлы имеют три возможных состояния относительно расписания:

| Состояние | Описание |
|-----------|----------|
| **unscheduled** | Узел отсутствует в `schedule.nodes` |
| **scheduled** | Узел присутствует в `schedule.nodes` |
| **computed** | scheduled + даты успешно вычислены |

```yaml
nodes:
  task1:
    title: "Задача 1"
  task2:
    title: "Задача 2"
  task3:
    title: "Задача 3"
    after: [task2]

schedule:
  nodes:
    task1:
      start: "2024-03-01"
      duration: "5d"
    # task2 — unscheduled (нет в schedule.nodes)
    task3:
      duration: "3d"
      # task3 — scheduled, но unschedulable (зависит от unscheduled task2)
```

## Вычисление дат

### Приоритет вычисления start

1. **Явный `start`**: использовать указанную дату
2. **`finish` + `duration`**: вычислить `start` назад от `finish`
3. **Зависимости `after`**: вычислить из завершения зависимостей

### Алгоритм для after

При вычислении `start` из `after`:

1. Взять зависимости из `nodes.<id>.after` (не из schedule!)
2. Отфильтровать только **scheduled** зависимости
3. Вычислить `max(finish)` для всех scheduled зависимостей
4. Для обычного узла: `start = next_workday(max_finish)`
5. Для вехи: `start = max_finish`

```yaml
nodes:
  task1:
    title: "Задача 1"
  task2:
    title: "Задача 2"
    after: [task1]
  task3:
    title: "Задача 3"
    after: [task1, task2]

schedule:
  nodes:
    task1:
      start: "2024-03-01"
      duration: "5d"
      # finish = 2024-03-05
    
    # task2 — unscheduled
    
    task3:
      duration: "3d"
      # after = [task1, task2]
      # scheduled зависимости = [task1]
      # start = next_workday(2024-03-05) = 2024-03-06
```

### Unschedulable узлы

Узел становится **unschedulable**, если:

- Нет явного `start`
- Нет `finish` + `duration`
- Все зависимости `after` либо unscheduled, либо unschedulable

```yaml
nodes:
  task1:
    title: "Задача 1"
  task2:
    title: "Задача 2"
    after: [task1]

schedule:
  nodes:
    # task1 — unscheduled
    task2:
      duration: "3d"
      # task2 — unschedulable: зависит от unscheduled task1
      # Предупреждение: "Node 'task2': all dependencies are unschedulable"
```

## Формат полей

### Поле `start` и `finish`

Формат: `YYYY-MM-DD` (ISO 8601)

```yaml
start: "2024-03-01"
finish: "2024-03-15"
```

### Поле `duration`

Формат: `<число><единица>`

| Единица | Описание |
|---------|----------|
| `d` | Рабочие дни |
| `w` | Недели (1w = 5 рабочих дней) |

```yaml
duration: "5d"   # 5 рабочих дней
duration: "2w"   # 2 недели = 10 рабочих дней
```

### Правила

- Число ДОЛЖНО быть положительным целым (≥ 1).
- Формат: регулярное выражение `^[1-9][0-9]*[dw]$`.

## Вычисление finish

```
finish = add_workdays(start, duration - 1, calendar)
```

День начала (`start`) включается в длительность.

| start | duration | finish | Пояснение |
|-------|----------|--------|-----------|
| 2024-03-01 | 1d | 2024-03-01 | Один день |
| 2024-03-01 | 5d | 2024-03-05 | Пять дней: 01-05 |
| 2024-03-01 (пт) | 5d (weekends) | 2024-03-07 | Пт, Пн, Вт, Ср, Чт |

## Обратное планирование (finish → start)

Если указаны `finish` и `duration`, но нет `start`:

```
start = sub_workdays(finish, duration - 1, calendar)
```

```yaml
schedule:
  nodes:
    release_prep:
      finish: "2024-03-15"  # Дедлайн
      duration: "5d"
      # start = 2024-03-11 (5 рабочих дней назад)
```

## Согласованность start/finish/duration

Если указаны все три поля, они ДОЛЖНЫ быть согласованы:

```yaml
# Корректно
schedule:
  nodes:
    task:
      start: "2024-03-01"
      finish: "2024-03-05"
      duration: "5d"

# ОШИБКА: несогласованность
schedule:
  nodes:
    task:
      start: "2024-03-01"
      finish: "2024-03-10"  # Должно быть 2024-03-05
      duration: "5d"
```

## Нормализация start

Если `start` попадает на исключённый день (выходной, праздник):

- **Для обычных узлов**: нормализуется на следующий рабочий день + предупреждение
- **Для вех**: не нормализуется (вехи могут быть на любой день)

```yaml
# excludes: [weekends]

schedule:
  nodes:
    task:
      start: "2024-03-02"  # Суббота
      duration: "3d"
      # Предупреждение: start нормализован на 2024-03-04 (понедельник)
      # finish = 2024-03-06
```

## Пример: частичный schedule

```yaml
version: 2

nodes:
  milestone1:
    title: "MVP"
    milestone: true
    after: [task2]
  
  task1:
    title: "Backend API"
    effort: 3
  
  task2:
    title: "Frontend"
    after: [task1]
    effort: 5
  
  task3:
    title: "Документация"
    effort: 2

schedule:
  calendars:
    work:
      excludes: [weekends]
  
  default_calendar: work
  
  nodes:
    task1:
      start: "2024-03-01"
      duration: "3d"
    
    task2:
      duration: "5d"
      # start из after: [task1]
    
    milestone1:
      # start из after: [task2]
      # milestone: true берётся из nodes
```

В этом примере:

- `task1`, `task2`, `milestone1` — scheduled (появятся на Gantt)
- `task3` — unscheduled (не появится на Gantt, но есть в tree/list)

---

# Views (представления)

Views — это представления для визуализации плана. В v2 views **не влияют** на расчёт расписания.

## Концепция

| Аспект | v1 | v2 |
|--------|----|----|
| Календарь | `excludes` в views | `excludes` в `schedule.calendars` |
| Влияние на расчёт | Да | Нет |
| Назначение | Визуализация + календарь | Только визуализация |

Views определяют **как** смотреть на план, но не влияют на **когда** выполняются работы.

## Структура блока views

```yaml
views:
  <view_id>:
    title: "Название"
    where: { ... }
    order_by: "field"
    group_by: "field"
    lanes: { ... }
    date_format: "YYYY-MM-DD"
    axis_format: "%d %b"
    tick_interval: "1week"
```

## Поля view

| Поле | Тип | Описание |
|------|-----|----------|
| `title` | string | Заголовок представления |
| `where` | object | Структурный фильтр узлов |
| `order_by` | string | Поле для сортировки |
| `group_by` | string | Поле для группировки |
| `lanes` | object | Лейны для Gantt |
| `date_format` | string | Формат дат (для рендерера) |
| `axis_format` | string | Формат оси X (для Gantt) |
| `tick_interval` | string | Интервал меток (для Gantt) |

### Запрещённые поля

В v2 поле `excludes` **запрещено** в views:

```yaml
# ОШИБКА в v2
views:
  gantt:
    title: "Gantt"
    excludes: [weekends]  # ОШИБКА: excludes запрещён в views
```

Календарь определяется в `schedule.calendars`.

## Фильтрация (`where`)

Структурный фильтр для выборки узлов.

```yaml
views:
  scheduled_tasks:
    title: "Запланированные задачи"
    where:
      kind: [task]
      has_schedule: true
```

### Поля фильтра

| Поле | Тип | Описание |
|------|-----|----------|
| `kind` | list[string] | Узлы с указанными kind |
| `status` | list[string] | Узлы с указанными status |
| `has_schedule` | boolean | Только scheduled/unscheduled узлы |
| `parent` | string | Потомки указанного узла |

### Примеры фильтров

```yaml
views:
  # Только задачи
  tasks:
    where:
      kind: [task]
  
  # Только завершённые
  done:
    where:
      status: [done, completed]
  
  # Только запланированные
  scheduled:
    where:
      has_schedule: true
  
  # Только незапланированные (бэклог)
  backlog:
    where:
      has_schedule: false
  
  # Потомки конкретного узла
  phase1_tasks:
    where:
      parent: phase1
  
  # Комбинация условий (AND)
  scheduled_tasks:
    where:
      kind: [task]
      has_schedule: true
```

### Логика фильтрации

- Все условия в `where` объединяются через **AND**.
- Узел проходит фильтр, если удовлетворяет **всем** условиям.

## Сортировка (`order_by`)

Поле для сортировки узлов в результате.

```yaml
views:
  by_effort:
    title: "По трудозатратам"
    order_by: effort
  
  by_status:
    title: "По статусу"
    order_by: status
```

### Доступные поля для сортировки

- `title` — по названию (алфавитно)
- `kind` — по типу
- `status` — по статусу
- `effort` — по трудозатратам
- `start` — по дате начала (для scheduled)
- `finish` — по дате окончания (для scheduled)

## Группировка (`group_by`)

Поле для группировки узлов.

```yaml
views:
  by_status:
    title: "По статусам"
    group_by: status
  
  by_kind:
    title: "По типам"
    group_by: kind
```

## Лейны (`lanes`)

Явное распределение узлов по полосам для Gantt.

```yaml
views:
  gantt:
    title: "Диаграмма Ганта"
    lanes:
      development:
        title: "Разработка"
        nodes: [backend, frontend, integration]
      testing:
        title: "Тестирование"
        nodes: [unit_tests, e2e_tests]
```

### Структура лейна

| Поле | Тип | Описание |
|------|-----|----------|
| `title` | string | Заголовок лейна |
| `nodes` | list[string] | Список node_id в этом лейне |

## Настройки формата (для рендереров)

Поля для настройки отображения в конкретных рендерерах:

```yaml
views:
  gantt:
    title: "Gantt"
    date_format: "YYYY-MM-DD"
    axis_format: "%d %b"
    tick_interval: "1week"
```

### Поля формата

| Поле | Описание | Пример |
|------|----------|--------|
| `date_format` | Формат входных дат | `YYYY-MM-DD` |
| `axis_format` | Формат дат на оси X | `%d %b`, `%Y-%m-%d` |
| `tick_interval` | Интервал меток | `1day`, `1week`, `1month` |

## Использование views в рендерерах

### Gantt

```bash
opskarta render gantt plan.yaml --view gantt
```

- `view_id` **обязателен** для Gantt.
- Применяется фильтрация из `where`.
- Используется календарь из `schedule`, **не** из view.

### Tree, List, Deps

```bash
opskarta render tree plan.yaml --view backlog
opskarta render list plan.yaml --view tasks
opskarta render deps plan.yaml
```

- `view_id` **опционален**.
- Если указан — применяется фильтрация и сортировка.
- Если не указан — отображаются все узлы.

## Примеры

### Минимальный view

```yaml
views:
  all:
    title: "Все узлы"
```

### View с фильтрацией

```yaml
views:
  active_tasks:
    title: "Активные задачи"
    where:
      kind: [task]
      status: [in_progress]
    order_by: effort
```

### View для Gantt

```yaml
views:
  project_gantt:
    title: "Диаграмма проекта"
    where:
      has_schedule: true
    axis_format: "%d %b"
    tick_interval: "1week"
    lanes:
      main:
        title: "Основные работы"
        nodes: [phase1, phase2, phase3]
      milestones:
        title: "Вехи"
        nodes: [mvp, release]
```

### View для бэклога

```yaml
views:
  backlog:
    title: "Бэклог"
    where:
      has_schedule: false
    order_by: effort
    group_by: kind
```

## Полный пример

```yaml
version: 2

nodes:
  epic1:
    title: "Авторизация"
    kind: epic
    effort: 13
  
  task1:
    title: "Backend API"
    kind: task
    parent: epic1
    status: in_progress
    effort: 5
  
  task2:
    title: "Frontend"
    kind: task
    parent: epic1
    status: not_started
    effort: 8

schedule:
  calendars:
    work:
      excludes: [weekends]
  default_calendar: work
  nodes:
    task1:
      start: "2024-03-01"
      duration: "5d"

views:
  # Все запланированные узлы
  gantt:
    title: "Gantt"
    where:
      has_schedule: true
  
  # Бэклог (незапланированные)
  backlog:
    title: "Бэклог"
    where:
      has_schedule: false
    order_by: effort
  
  # Только задачи
  tasks:
    title: "Задачи"
    where:
      kind: [task]
    order_by: status
  
  # Задачи в работе
  in_progress:
    title: "В работе"
    where:
      status: [in_progress]
```

---

# Валидация

Этот раздел описывает правила валидации файлов плана v2.

## Уровни валидации

1. **Синтаксис** — корректность YAML/JSON
2. **Схема** — соответствие JSON Schema (типы, форматы)
3. **Семантика** — ссылочная целостность, бизнес-правила

## Уровни серьёзности

| Уровень | Описание | Поведение |
|---------|----------|-----------|
| **error** | Критическая ошибка | Валидация завершается неудачей |
| **warn** | Потенциальная проблема | Валидация успешна с предупреждением |
| **info** | Информационное сообщение | Валидация успешна |

## Валидация фрагментов

### Допустимые top-level блоки

Фрагмент может содержать только:

- `version`
- `meta`
- `statuses`
- `nodes`
- `schedule`
- `views`
- `x`

```yaml
# ОШИБКА: недопустимый блок
version: 2
nodes: { ... }
custom_block: { ... }  # ОШИБКА: unknown top-level block 'custom_block'
```

### Версия

- `version` ДОЛЖЕН быть целым числом `2`.
- Разные версии в фрагментах — **ошибка**.

## Валидация nodes

### Обязательные поля

- `title` *(string)* — ОБЯЗАТЕЛЕН для каждого узла.

```yaml
# ОШИБКА: отсутствует title
nodes:
  task1:
    kind: task  # ОШИБКА: missing required field 'title'
```

### Запрещённые поля

В v2 следующие поля **запрещены** в nodes:

| Поле | Ошибка |
|------|--------|
| `start` | "field 'start' is not allowed in nodes (use schedule.nodes)" |
| `finish` | "field 'finish' is not allowed in nodes (use schedule.nodes)" |
| `duration` | "field 'duration' is not allowed in nodes (use schedule.nodes)" |
| `excludes` | "field 'excludes' is not allowed in nodes (use schedule.calendars)" |

```yaml
# ОШИБКА: запрещённые поля
nodes:
  task1:
    title: "Задача"
    start: "2024-03-01"  # ОШИБКА: field 'start' is not allowed in nodes
```

### Формат effort

- `effort` ДОЛЖЕН быть **неотрицательным числом** (≥ 0).

```yaml
# Корректно
nodes:
  task1:
    title: "Задача"
    effort: 5
  task2:
    title: "Задача"
    effort: 0      # OK: ноль допустим
  task3:
    title: "Задача"
    effort: 3.5    # OK: дробные числа допустимы

# ОШИБКА
nodes:
  task:
    title: "Задача"
    effort: -1     # ОШИБКА: effort must be >= 0
    effort: "5sp"  # ОШИБКА: effort must be a number
```

## Ссылочная целостность

### Родительские ссылки (`parent`)

- Значение `parent` ДОЛЖНО быть существующим `node_id`.
- Циклические ссылки через `parent` **запрещены**.

```yaml
# ОШИБКА: несуществующий parent
nodes:
  child:
    title: "Child"
    parent: nonexistent  # ОШИБКА: parent 'nonexistent' does not exist

# ОШИБКА: циклическая ссылка
nodes:
  a:
    title: "A"
    parent: b
  b:
    title: "B"
    parent: a  # ОШИБКА: circular parent reference
```

### Зависимости (`after`)

- Каждый элемент `after` ДОЛЖЕН быть существующим `node_id`.
- Циклические зависимости через `after` **запрещены**.

```yaml
# ОШИБКА: несуществующая зависимость
nodes:
  task:
    title: "Task"
    after: [missing]  # ОШИБКА: after reference 'missing' does not exist

# ОШИБКА: циклическая зависимость
nodes:
  a:
    title: "A"
    after: [b]
  b:
    title: "B"
    after: [a]  # ОШИБКА: circular dependency
```

### Статусы (`status`)

- Значение `status` ДОЛЖНО быть ключом из `statuses`.

```yaml
statuses:
  done: { label: "Готово" }

nodes:
  task:
    title: "Task"
    status: completed  # ОШИБКА: status 'completed' does not exist
```

## Валидация schedule

### Ссылки на узлы

- `node_id` в `schedule.nodes` ДОЛЖЕН существовать в `nodes`.

```yaml
nodes:
  task1:
    title: "Задача 1"

schedule:
  nodes:
    task1:
      start: "2024-03-01"
    task2:                    # ОШИБКА: node 'task2' does not exist
      start: "2024-03-05"
```

### Ссылки на календари

- `calendar` в `schedule.nodes` ДОЛЖЕН существовать в `schedule.calendars`.
- `default_calendar` ДОЛЖЕН существовать в `schedule.calendars`.

```yaml
schedule:
  calendars:
    work:
      excludes: [weekends]
  
  default_calendar: holiday  # ОШИБКА: calendar 'holiday' does not exist
  
  nodes:
    task1:
      start: "2024-03-01"
      calendar: custom       # ОШИБКА: calendar 'custom' does not exist
```

### Формат дат

- `start` и `finish` ДОЛЖНЫ соответствовать формату `YYYY-MM-DD`.

```yaml
schedule:
  nodes:
    task:
      start: "2024-3-1"      # ОШИБКА: invalid date format
      start: "01-03-2024"    # ОШИБКА: invalid date format
      start: "2024-03-01"    # OK
```

### Формат duration

- `duration` ДОЛЖЕН соответствовать формату `^[1-9][0-9]*[dw]$`.

```yaml
schedule:
  nodes:
    task:
      duration: "5d"   # OK
      duration: "2w"   # OK
      duration: "0d"   # ОШИБКА: duration must be >= 1
      duration: "5"    # ОШИБКА: missing unit (d or w)
      duration: "5m"   # ОШИБКА: invalid unit
```

### Согласованность start/finish/duration

Если указаны все три поля, они ДОЛЖНЫ быть согласованы.

```yaml
schedule:
  nodes:
    task:
      start: "2024-03-01"
      finish: "2024-03-10"
      duration: "5d"
      # ОШИБКА: inconsistent start/finish/duration
      # computed finish from start+duration = 2024-03-05, but specified 2024-03-10
```

### Запрещённые поля в schedule.nodes

Поле `after` **запрещено** в `schedule.nodes`:

```yaml
schedule:
  nodes:
    task:
      start: "2024-03-01"
      after: [other]  # ОШИБКА: 'after' is not allowed in schedule.nodes
```

## Валидация views

### Запрет excludes

Поле `excludes` **запрещено** в views:

```yaml
views:
  gantt:
    title: "Gantt"
    excludes: [weekends]  # ОШИБКА: 'excludes' is not allowed in views
```

### Валидация where

Поля в `where` должны быть из допустимого списка:

- `kind`
- `status`
- `has_schedule`
- `parent`

```yaml
views:
  custom:
    where:
      kind: [task]        # OK
      custom_field: value # ОШИБКА: unknown filter field 'custom_field'
```

## Валидация слияния

### Конфликты node_id

```
Error: Merge conflict - node 'task1' defined in multiple files
  File 1: nodes.plan.yaml
  File 2: extra.plan.yaml
```

### Конфликты status_id

```
Error: Merge conflict - status 'done' defined in multiple files
  File 1: main.plan.yaml
  File 2: statuses.plan.yaml
```

### Конфликты meta

```
Error: Merge conflict - meta.title has different values
  File 1: main.plan.yaml, value: "Project A"
  File 2: extra.plan.yaml, value: "Project B"
```

### Конфликты default_calendar

```
Error: Merge conflict - schedule.default_calendar defined in multiple files
  File 1: schedule1.plan.yaml
  File 2: schedule2.plan.yaml
```

## Классификация ошибок

| Ошибка | Уровень | Фаза |
|--------|---------|------|
| Невалидный YAML | error | Загрузка |
| Недопустимый top-level блок | error | Загрузка |
| Конфликт node_id | error | Слияние |
| Конфликт status_id | error | Слияние |
| Конфликт meta-полей | error | Слияние |
| Конфликт default_calendar | error | Слияние |
| Отсутствует title у узла | error | Валидация |
| Узел содержит start/finish/duration | error | Валидация |
| Невалидный формат effort | error | Валидация |
| Несуществующий parent | error | Валидация |
| Несуществующий after | error | Валидация |
| Несуществующий status | error | Валидация |
| Несуществующий node в schedule.nodes | error | Валидация |
| Несуществующий calendar | error | Валидация |
| View содержит excludes | error | Валидация |
| Циклические зависимости | error | Валидация |
| Несогласованные start/finish/duration | error | Планирование |
| Цепочка after без якоря | warn | Планирование |
| start раньше finish зависимости | warn | Планирование |
| start на исключённом дне | warn | Планирование |

## Формат сообщений об ошибках

```
[severity] [phase] [file:line] message
  path: element.path
  value: actual_value
  expected: expected_format
```

### Примеры

```
[error] [validation] nodes.plan.yaml:15 Invalid effort value
  path: nodes.task1.effort
  value: -5
  expected: number >= 0
```

```
[error] [validation] schedule.plan.yaml:8 Invalid reference
  path: schedule.nodes.task2
  value: task2
  expected: existing node_id from nodes
  available: task1, task3
```

```
[error] [merge] Merge conflict
  element: node 'task1'
  file1: nodes.plan.yaml
  file2: extra.plan.yaml
```

```
[warn] [scheduling] schedule.plan.yaml:12 Start date on excluded day
  path: schedule.nodes.task1.start
  value: 2024-03-02 (Saturday)
  normalized: 2024-03-04 (Monday)
```

## Отслеживание источников

Все ошибки валидации содержат путь к файлу-источнику:

```python
# Структура ошибки
class ValidationError:
    severity: str      # "error", "warn", "info"
    phase: str         # "load", "merge", "validation", "scheduling"
    source_file: str   # путь к файлу
    path: str          # путь к элементу (nodes.task1.effort)
    message: str       # описание ошибки
    value: Any         # фактическое значение
    expected: str      # ожидаемый формат
```

Это позволяет быстро находить и исправлять ошибки в многофайловых планах.