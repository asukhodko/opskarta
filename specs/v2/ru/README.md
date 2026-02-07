# opskarta Specification v2

**Статус**: Alpha
**Релиз**: Draft

## Обзор

Версия 2 спецификации opskarta реализует концепцию "overlay schedule" — разделение структуры работ (nodes) и календарного планирования (schedule). Это позволяет:

1. Создавать планы без привязки к датам (только структура и зависимости)
2. Добавлять календарное планирование как опциональный слой
3. Разбивать большие планы на несколько файлов (Plan Set)
4. Использовать views только для визуализации, без влияния на расчёт

### Ключевые принципы

- **Separation of Concerns**: структура работ отделена от календарного планирования
- **Opt-in Scheduling**: только явно включённые узлы участвуют в расчёте расписания
- **Deterministic Merge**: слияние фрагментов детерминировано, конфликты — ошибка
- **Views are Pure**: представления не влияют на расчёт, только на отображение

## Изменения относительно v1

### Новое в v2

| Возможность | v1 | v2 |
|-------------|----|----|
| Многофайловые планы | ❌ | ✅ Plan Set |
| Планы без дат | ❌ | ✅ Schedule опционален |
| Effort-метрики | ❌ | ✅ effort, rollup, gap |
| Структурная фильтрация | ❌ | ✅ view.where |
| Календари | В views | В schedule.calendars |

### Перенесённые поля

| Поле | v1 | v2 |
|------|----|----|
| `start`, `finish`, `duration` | nodes | schedule.nodes |
| `excludes` | views | schedule.calendars |

### Новые поля

| Поле | Описание |
|------|----------|
| `nodes.*.effort` | Абстрактная оценка трудозатрат (число ≥ 0) |
| `meta.effort_unit` | Единица измерения для UI ("sp", "points", "дни") |
| `schedule.calendars` | Словарь календарей с исключениями |
| `schedule.default_calendar` | Календарь по умолчанию |
| `view.where` | Структурный фильтр (kind, status, has_schedule, parent) |

## Быстрые ссылки

- [Полная спецификация](SPEC.md)
- [Руководство по миграции с v1](MIGRATION.md)
- [Примеры](examples/)
  - [multi-file/](examples/multi-file/) — многофайловый план
  - [no-schedule/](examples/no-schedule/) — план без расписания
  - [partial-schedule/](examples/partial-schedule/) — частичное расписание
- [JSON Schema](../schemas/)
- [Референсные инструменты](../tools/)

## Пример: План без расписания

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

Этот план валиден без блока `schedule`. Можно рендерить tree/list/deps, но не Gantt.

## Пример: Многофайловый план

**main.plan.yaml**
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

**nodes.plan.yaml**
```yaml
version: 2

nodes:
  phase1:
    title: "Фаза 1: Анализ"
    kind: phase
    effort: 10

  phase2:
    title: "Фаза 2: Разработка"
    kind: phase
    after: [phase1]
    effort: 20
```

**schedule.plan.yaml**
```yaml
version: 2

schedule:
  calendars:
    default:
      excludes: [weekends, "2024-03-08"]

  default_calendar: default

  nodes:
    phase1:
      start: "2024-03-01"
      duration: "10d"

    phase2:
      duration: "20d"
      # start вычисляется из after: [phase1]
```
