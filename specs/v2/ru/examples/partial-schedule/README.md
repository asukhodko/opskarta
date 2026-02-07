# Пример: Partial-schedule (частичное расписание)

Этот пример демонстрирует ключевую возможность opskarta v2: **часть узлов запланирована на текущий спринт, а остальные остаются в бэклоге без календарных дат**.

## Что демонстрирует

### Ключевая идея: Opt-in Scheduling

В v2 только узлы, явно указанные в `schedule.nodes`, участвуют в календарном планировании. Остальные узлы:

- ✅ Существуют в структуре плана
- ✅ Имеют оценки effort
- ✅ Имеют зависимости (after)
- ✅ Отображаются в tree/list/deps
- ❌ Не имеют календарных дат
- ❌ Не появляются на Gantt (если не отфильтрованы)

### Когда использовать частичное расписание

| Сценарий | Описание |
|----------|----------|
| **Спринт-планирование** | Текущий спринт запланирован, бэклог — нет |
| **Итеративная разработка** | Ближайшие итерации детализированы, дальние — нет |
| **Горизонт планирования** | Детальные даты только на 2-4 недели вперёд |
| **Гибкое планирование** | Часть работ фиксирована, часть — плавающая |

## Файлы

| Файл | Описание |
|------|----------|
| `sprint.plan.yaml` | План спринта с частичным расписанием |

## Структура примера

```
project (Мобильное приложение) [89 sp]
│
├── auth (Авторизация) [21 sp] — ВЕСЬ ЭПИК В СПРИНТЕ
│   ├── auth-ui [3 sp]        ✓ scheduled
│   ├── auth-api [5 sp]       ✓ scheduled
│   ├── auth-oauth [8 sp]     ✓ scheduled
│   └── auth-2fa [5 sp]       ✓ scheduled
│
├── profile (Профиль) [13 sp] — ЧАСТИЧНО В СПРИНТЕ
│   ├── profile-view [3 sp]   ✓ scheduled
│   ├── profile-edit [5 sp]   ✓ scheduled
│   ├── profile-privacy [3 sp] ✗ backlog
│   └── profile-export [2 sp]  ✗ backlog
│
├── notifications (Уведомления) [21 sp] — ВЕСЬ ЭПИК В БЭКЛОГЕ
│   ├── notif-push [8 sp]     ✗ backlog
│   ├── notif-email [5 sp]    ✗ backlog
│   ├── notif-settings [3 sp] ✗ backlog
│   └── notif-history [5 sp]  ✗ backlog
│
├── social (Социальные функции) [34 sp] — ВЕСЬ ЭПИК В БЭКЛОГЕ
│   ├── social-friends [8 sp]  ✗ backlog
│   ├── social-feed [13 sp]    ✗ backlog
│   ├── social-sharing [8 sp]  ✗ backlog
│   └── social-comments [5 sp] ✗ backlog
│
└── mvp-release (Веха)        ✓ scheduled
```

## Ключевая функция: фильтр `has_schedule`

Представления (views) могут фильтровать узлы по наличию расписания:

```yaml
views:
  # Только запланированные задачи (текущий спринт)
  sprint:
    title: "Текущий спринт"
    where:
      has_schedule: true  # ТОЛЬКО узлы из schedule.nodes

  # Только незапланированные задачи (бэклог)
  backlog:
    title: "Бэклог"
    where:
      has_schedule: false  # ТОЛЬКО узлы НЕ в schedule.nodes
```

Это позволяет:
- Показывать Gantt только для запланированных задач
- Отдельно просматривать бэклог
- Отслеживать прогресс спринта vs общий прогресс

## Особенности примера

### Три категории узлов

1. **Полностью в спринте** — эпик `auth` (все 4 задачи запланированы)
2. **Частично в спринте** — эпик `profile` (2 из 4 задач запланированы)
3. **Полностью в бэклоге** — эпики `notifications` и `social`

### Зависимости между scheduled и unscheduled

```yaml
nodes:
  profile-edit:
    after: [profile-view]  # scheduled → scheduled ✓
  
  profile-privacy:
    after: [profile-edit]  # unscheduled → scheduled
    # profile-privacy в бэклоге, но зависит от scheduled задачи
```

При добавлении `profile-privacy` в schedule, её start автоматически вычислится из `profile-edit.finish`.

### Веха MVP

```yaml
nodes:
  mvp-release:
    after: [auth, profile]
    milestone: true

schedule:
  nodes:
    mvp-release: {}  # start вычисляется из зависимостей
```

Веха `mvp-release` запланирована и её дата вычисляется из завершения эпиков `auth` и `profile`.

## Использование

### Валидация

```bash
cd specs/v2

# Валидация плана с частичным расписанием
python tools/cli.py validate ru/examples/partial-schedule/sprint.plan.yaml
```

### Рендеринг спринта

```bash
cd specs/v2

# Gantt-диаграмма спринта (только scheduled узлы)
python tools/cli.py render gantt ru/examples/partial-schedule/sprint.plan.yaml --view gantt

# Список задач спринта
python tools/cli.py render list ru/examples/partial-schedule/sprint.plan.yaml --view sprint

# Дерево спринта
python tools/cli.py render tree ru/examples/partial-schedule/sprint.plan.yaml --view sprint
```

### Рендеринг бэклога

```bash
cd specs/v2

# Список задач в бэклоге
python tools/cli.py render list ru/examples/partial-schedule/sprint.plan.yaml --view backlog

# Дерево бэклога
python tools/cli.py render tree ru/examples/partial-schedule/sprint.plan.yaml --view backlog
```

### Полный план

```bash
cd specs/v2

# Полное дерево проекта (все узлы)
python tools/cli.py render tree ru/examples/partial-schedule/sprint.plan.yaml --view tree

# Граф зависимостей
python tools/cli.py render deps ru/examples/partial-schedule/sprint.plan.yaml --view deps
```

## Типичный workflow спринт-планирования

### 1. Начало спринта

```yaml
# Добавляем задачи в schedule.nodes
schedule:
  nodes:
    task-1:
      start: "2024-03-01"
      duration: "3d"
    task-2:
      duration: "5d"
```

### 2. Во время спринта

- Используем view `sprint` для отслеживания прогресса
- Используем view `backlog` для груминга следующего спринта
- Gantt показывает только текущий спринт

### 3. Конец спринта

- Незавершённые задачи остаются в schedule (переносятся)
- Или удаляются из schedule (возвращаются в бэклог)

### 4. Планирование следующего спринта

```yaml
# Добавляем новые задачи из бэклога
schedule:
  nodes:
    # Существующие...
    
    # Новые из бэклога:
    profile-privacy:
      duration: "3d"
    notif-push:
      duration: "6d"
```

## Сравнение представлений

| View | has_schedule | Что показывает |
|------|--------------|----------------|
| `sprint` | `true` | Только задачи текущего спринта |
| `backlog` | `false` | Только задачи в бэклоге |
| `tree` | не указан | Все задачи проекта |
| `gantt` | `true` | Gantt только для спринта |

## Effort-метрики

Даже для незапланированных задач вычисляются effort-метрики:

```yaml
# Эпик notifications (весь в бэклоге):
# effort = 21 (явно задан)
# effort_rollup = 8 + 5 + 3 + 5 = 21
# effort_gap = 0 (декомпозиция полная)
```

Это позволяет:
- Оценивать объём бэклога
- Планировать capacity следующих спринтов
- Отслеживать прогресс по effort

## См. также

- [Спецификация Schedule](../../spec/30-schedule.md)
- [Спецификация Views](../../spec/40-views.md)
- [Пример no-schedule](../no-schedule/) — план без расписания
- [Пример multi-file](../multi-file/) — многофайловый план
- [Руководство по миграции с v1](../../MIGRATION.md)
