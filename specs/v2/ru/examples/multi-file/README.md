# Пример: Multi-file (многофайловый план)

Этот пример демонстрирует концепцию **Plan Set** — разбиение плана на несколько файлов (фрагментов), которые сливаются в единый план.

## Что демонстрирует

### Концепция Plan Set

- **Разделение ответственности**: структура, расписание и представления в отдельных файлах
- **Детерминированное слияние**: порядок файлов не влияет на результат
- **Отслеживание источников**: ошибки указывают файл-источник

### Ключевые особенности v2

- **Overlay Schedule**: расписание как отдельный слой поверх структуры
- **Зависимости в nodes**: поле `after` определяется в узлах, не в schedule
- **Чистые views**: представления не содержат `excludes` (перенесён в calendars)
- **Effort без дат**: трудозатраты оцениваются независимо от календаря

## Файлы

| Файл | Содержимое | Описание |
|------|------------|----------|
| `main.plan.yaml` | `meta`, `statuses`, `x` | Метаданные проекта и статусы |
| `nodes.plan.yaml` | `nodes` | Структура работ с иерархией и зависимостями |
| `schedule.plan.yaml` | `schedule` | Календари и расписание узлов |
| `views.plan.yaml` | `views` | Представления для визуализации |

## Структура плана

```
project (Веб-платформа v1.0)
│
├── backend (Бэкенд)
│   ├── api (REST API)
│   │   ├── api-auth
│   │   ├── api-tasks
│   │   └── api-projects
│   └── database (База данных)
│       ├── db-schema
│       ├── db-migrations
│       └── db-indexes
│
├── frontend (Фронтенд)
│   ├── ui-components (UI компоненты)
│   │   ├── ui-design-system
│   │   ├── ui-forms
│   │   └── ui-tables
│   └── pages (Страницы)
│       ├── page-dashboard
│       ├── page-tasks
│       └── page-settings
│
├── testing (Тестирование)
│   ├── e2e-tests
│   └── performance-tests
│
└── release-v1 (Релиз v1.0) [milestone]
```

## Представления

| Представление | Назначение |
|---------------|------------|
| `overview` | Обзор для руководства (фазы и эпики) |
| `gantt-full` | Полная диаграмма Ганта с лейнами |
| `backlog` | Незапланированные задачи |
| `in-progress` | Задачи в работе |
| `backend-tasks` | Задачи бэкенд-команды |
| `tree` | Полная структура проекта |
| `deps` | Граф зависимостей |

## Использование

### Валидация

```bash
cd specs/v2

# Валидация всех файлов плана
python tools/cli.py validate \
  ru/examples/multi-file/main.plan.yaml \
  ru/examples/multi-file/nodes.plan.yaml \
  ru/examples/multi-file/schedule.plan.yaml \
  ru/examples/multi-file/views.plan.yaml
```

### Рендеринг

```bash
cd specs/v2

# Диаграмма Ганта
python tools/cli.py render gantt \
  ru/examples/multi-file/main.plan.yaml \
  ru/examples/multi-file/nodes.plan.yaml \
  ru/examples/multi-file/schedule.plan.yaml \
  ru/examples/multi-file/views.plan.yaml \
  --view gantt-full

# Дерево проекта
python tools/cli.py render tree \
  ru/examples/multi-file/main.plan.yaml \
  ru/examples/multi-file/nodes.plan.yaml \
  ru/examples/multi-file/schedule.plan.yaml \
  ru/examples/multi-file/views.plan.yaml \
  --view tree

# Граф зависимостей
python tools/cli.py render deps \
  ru/examples/multi-file/main.plan.yaml \
  ru/examples/multi-file/nodes.plan.yaml \
  ru/examples/multi-file/schedule.plan.yaml \
  ru/examples/multi-file/views.plan.yaml \
  --view deps
```

## Особенности примера

### Разделение структуры и расписания

В v1 даты указывались прямо в узлах:

```yaml
# v1 — даты в узлах
nodes:
  task1:
    title: "Задача"
    start: "2024-03-01"
    duration: 5d
```

В v2 структура и расписание разделены:

```yaml
# v2 — nodes.plan.yaml (структура)
nodes:
  task1:
    title: "Задача"
    effort: 5  # трудозатраты без дат

# v2 — schedule.plan.yaml (расписание)
schedule:
  nodes:
    task1:
      start: "2024-03-01"
      duration: "5d"
```

### Зависимости в nodes

Зависимости (`after`) определяются в узлах, а не в schedule:

```yaml
# nodes.plan.yaml
nodes:
  task2:
    title: "Задача 2"
    after: [task1]  # зависимость здесь

# schedule.plan.yaml
schedule:
  nodes:
    task2:
      duration: "3d"
      # start вычисляется из after в nodes
```

### Частичное расписание

Не все узлы обязаны иметь расписание. В этом примере:

- Узлы в `schedule.nodes` — запланированы (появятся на Gantt)
- Узлы без записи в `schedule.nodes` — только в структуре (tree, list, deps)

Фильтр `has_schedule` в views позволяет разделить их:

```yaml
views:
  gantt:
    where:
      has_schedule: true  # только запланированные
  
  backlog:
    where:
      has_schedule: false  # только незапланированные
```

### Множественные календари

Пример показывает использование разных календарей:

```yaml
schedule:
  calendars:
    work:
      excludes: [weekends, "2024-03-08"]
    
    urgent:
      excludes: ["2024-03-08"]  # без выходных
  
  default_calendar: work
  
  nodes:
    performance-tests:
      duration: "2d"
      calendar: urgent  # срочная задача
```

## Когда использовать многофайловую структуру

Разбиение на файлы полезно когда:

- **Большой план**: сотни узлов сложно редактировать в одном файле
- **Командная работа**: разные люди отвечают за структуру и расписание
- **Переиспользование**: общие статусы или календари для нескольких планов
- **Версионирование**: отдельные коммиты для структуры и расписания

Для небольших планов можно использовать один файл — см. примеры [no-schedule](../no-schedule/) и [partial-schedule](../partial-schedule/).

## См. также

- [Спецификация Plan Set](../../spec/10-plan-set.md)
- [Спецификация Schedule](../../spec/30-schedule.md)
- [Руководство по миграции с v1](../../MIGRATION.md)
