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
