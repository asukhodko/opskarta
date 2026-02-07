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
