# Пример: No-schedule (план без расписания)

Этот пример демонстрирует, что план opskarta v2 может быть **валидным и полезным без блока `schedule`** — только структура, иерархия, зависимости и оценки трудозатрат (effort).

## Что демонстрирует

### Ключевая идея v2: Overlay Schedule

В v2 календарное планирование — это **опциональный слой**, который накладывается на структуру работ. План без `schedule`:

- ✅ Полностью валиден
- ✅ Можно рендерить как tree, list, deps
- ✅ Вычисляются effort-метрики (rollup, gap)
- ❌ Нельзя рендерить Gantt (нет дат)

### Когда использовать план без расписания

| Сценарий | Описание |
|----------|----------|
| **Бэклог продукта** | Список фич с приоритетами и оценками, без привязки к датам |
| **Roadmap** | Стратегическое видение развития продукта |
| **Ранее планирование** | Декомпозиция и оценка до определения сроков |
| **Оценка объёма** | Понимание масштаба работ перед планированием |
| **Груминг** | Уточнение требований и оценок |

## Файлы

| Файл | Описание |
|------|----------|
| `backlog.plan.yaml` | Полный план бэклога мобильного приложения |

## Структура примера

```
backlog (Бэклог мобильного приложения) [100 sp]
│
├── onboarding (Онбординг пользователей) [21 sp]
│   ├── welcome-screens [5 sp]
│   ├── registration [8 sp]
│   ├── profile-setup [5 sp]
│   └── tutorial [3 sp]
│
├── core-features (Основной функционал) [34 sp]
│   ├── dashboard [8 sp]
│   ├── search [5 sp]
│   ├── notifications [8 sp]
│   ├── settings [5 sp]
│   └── offline-mode [8 sp]
│
├── social (Социальные функции) [21 sp]
│   ├── user-profiles [5 sp]
│   ├── friends [8 sp]
│   ├── sharing [5 sp]
│   └── comments [3 sp]
│
├── monetization (Монетизация) [13 sp]
│   ├── premium-subscription [8 sp]
│   └── in-app-purchases [5 sp]
│
└── tech-debt (Технический долг) [11 sp]
    ├── refactor-auth [3 sp]
    ├── improve-performance [5 sp]
    └── update-dependencies [3 sp]
```

## Особенности примера

### Effort без дат

Каждый узел имеет оценку трудозатрат в story points (`effort`), но **без календарных дат**:

```yaml
nodes:
  registration:
    title: "Регистрация"
    kind: user_story
    parent: onboarding
    after: [welcome-screens]  # зависимость есть
    status: ready
    effort: 8                 # оценка есть
    # start, finish, duration — НЕТ (это в schedule)
```

### Вычисление effort-метрик

Даже без расписания система вычисляет:

- **effort_rollup** — сумма effort детей
- **effort_effective** — итоговый effort узла
- **effort_gap** — разница между явным effort и rollup (показывает неполноту декомпозиции)

```yaml
# Пример вычислений для эпика onboarding:
# effort = 21 (явно задан)
# effort_rollup = 5 + 8 + 5 + 3 = 21 (сумма детей)
# effort_gap = max(0, 21 - 21) = 0 (декомпозиция полная)
```

### Зависимости без дат

Зависимости (`after`) определяют **логический порядок**, даже без календарного планирования:

```yaml
nodes:
  registration:
    after: [welcome-screens]  # сначала приветствие, потом регистрация
  
  profile-setup:
    after: [registration]     # сначала регистрация, потом профиль
```

Это полезно для:
- Понимания критического пути
- Визуализации графа зависимостей
- Будущего планирования (когда добавите schedule)

### Представления (views)

План включает несколько представлений для разных целей:

| View | Назначение |
|------|------------|
| `tree` | Полная структура бэклога |
| `by-status` | Группировка по статусам |
| `ready-for-dev` | Только готовые к разработке |
| `ideas` | Идеи для груминга |
| `epics` | Эпики для roadmap |
| `user-stories` | Все user stories |
| `deps` | Граф зависимостей |

## Использование

### Валидация

```bash
cd specs/v2

# Валидация плана без schedule — должна пройти успешно
python tools/cli.py validate ru/examples/no-schedule/backlog.plan.yaml
```

### Рендеринг

```bash
cd specs/v2

# Дерево бэклога
python tools/cli.py render tree ru/examples/no-schedule/backlog.plan.yaml

# Дерево с фильтром (только эпики)
python tools/cli.py render tree ru/examples/no-schedule/backlog.plan.yaml --view epics

# Список готовых к разработке
python tools/cli.py render list ru/examples/no-schedule/backlog.plan.yaml --view ready-for-dev

# Граф зависимостей
python tools/cli.py render deps ru/examples/no-schedule/backlog.plan.yaml --view deps
```

### Gantt — недоступен

```bash
# Это вызовет ошибку — нет schedule для построения Gantt
python tools/cli.py render gantt ru/examples/no-schedule/backlog.plan.yaml --view tree
# Error: Cannot render Gantt without schedule
```

## Добавление расписания позже

Когда придёт время планировать сроки, просто добавьте блок `schedule`:

```yaml
# Можно добавить в тот же файл или в отдельный schedule.plan.yaml

schedule:
  calendars:
    work:
      excludes: [weekends]
  
  default_calendar: work
  
  nodes:
    # Планируем только то, что готово к разработке
    welcome-screens:
      start: "2024-04-01"
      duration: "5d"
    
    registration:
      duration: "8d"
      # start вычислится из after: [welcome-screens]
```

При этом:
- Структура узлов остаётся неизменной
- Зависимости уже определены в `nodes.after`
- Effort-оценки сохраняются
- Незапланированные узлы остаются в бэклоге

## Сравнение с v1

В v1 даты были обязательной частью узлов:

```yaml
# v1 — даты в узлах (обязательно для Gantt)
nodes:
  task1:
    title: "Задача"
    start: "2024-03-01"
    duration: 5d
```

В v2 структура и расписание разделены:

```yaml
# v2 — nodes (структура, всегда валидна)
nodes:
  task1:
    title: "Задача"
    effort: 5

# v2 — schedule (опционально, добавляется когда нужно)
schedule:
  nodes:
    task1:
      start: "2024-03-01"
      duration: "5d"
```

## См. также

- [Спецификация Nodes](../../spec/20-nodes.md)
- [Спецификация Schedule](../../spec/30-schedule.md)
- [Пример multi-file](../multi-file/) — план с расписанием
- [Пример partial-schedule](../partial-schedule/) — частичное расписание
- [Руководство по миграции с v1](../../MIGRATION.md)
