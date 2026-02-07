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
