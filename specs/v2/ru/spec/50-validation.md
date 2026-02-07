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
