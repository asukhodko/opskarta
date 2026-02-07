# Руководство по миграции с opskarta v1 на v2

Это руководство описывает процесс миграции планов с формата opskarta v1 на v2.

## Оглавление

- [Обзор изменений](#обзор-изменений)
- [Ключевые отличия v2](#ключевые-отличия-v2)
- [Пошаговый процесс миграции](#пошаговый-процесс-миграции)
- [Перенос календарных полей из nodes в schedule.nodes](#перенос-календарных-полей-из-nodes-в-schedulenodes)
- [Перенос excludes из views в schedule.calendars](#перенос-excludes-из-views-в-schedulecalendars)
- [Примеры до/после](#примеры-допосле)
- [Типичные проблемы и решения](#типичные-проблемы-и-решения)
- [Валидация мигрированных планов](#валидация-мигрированных-планов)

---

## Обзор изменений

opskarta v2 реализует концепцию **overlay schedule** — разделение структуры работ и календарного планирования. Это позволяет:

1. Создавать планы без привязки к датам (только структура и зависимости)
2. Добавлять календарное планирование как опциональный слой
3. Разбивать большие планы на несколько файлов (Plan Set)

### Сравнение v1 и v2

| Аспект | v1 | v2 |
|--------|----|----|
| Даты в узлах | `start`, `finish`, `duration` в `nodes` | Только в `schedule.nodes` |
| Календарь | `excludes` в `views` (gantt_views) | `excludes` в `schedule.calendars` |
| План без дат | Невозможен для Gantt | Полностью валиден |
| Зависимости | `after` в `nodes` | `after` в `nodes` (без изменений) |
| Многофайловость | Отдельные файлы plan/views | Единый Plan Set с фрагментами |
| Оценка трудозатрат | Не поддерживается | Поле `effort` (число) |

---

## Ключевые отличия v2

### 1. Поля `start`, `finish`, `duration` перенесены из nodes в schedule.nodes

**v1:** Календарные поля находились непосредственно в узлах.

```yaml
# v1
nodes:
  task1:
    title: "Задача 1"
    start: "2024-03-01"
    duration: "5d"
```

**v2:** Календарные поля находятся в отдельном блоке `schedule.nodes`.

```yaml
# v2
nodes:
  task1:
    title: "Задача 1"

schedule:
  nodes:
    task1:
      start: "2024-03-01"
      duration: "5d"
```

### 2. Поле `excludes` перенесено из views в schedule.calendars

**v1:** Исключения календаря задавались в представлениях.

```yaml
# v1 (views.yaml)
gantt_views:
  main:
    excludes:
      - weekends
      - "2024-03-08"
```

**v2:** Исключения задаются в календарях внутри schedule.

```yaml
# v2
schedule:
  calendars:
    default:
      excludes:
        - weekends
        - "2024-03-08"
  default_calendar: default
```

### 3. Поле `duration` удалено из nodes

В v1 поле `duration` в узлах использовалось для расчёта дат. В v2 для оценки трудозатрат используется отдельное поле `effort` (число), а `duration` доступен только в `schedule.nodes`.

**v1:**
```yaml
nodes:
  task1:
    title: "Задача"
    duration: "5d"  # Использовалось для расчёта дат
```

**v2:**
```yaml
nodes:
  task1:
    title: "Задача"
    effort: 5  # Абстрактная оценка (число)

schedule:
  nodes:
    task1:
      duration: "5d"  # Для расчёта дат
```

### 4. Зависимости остаются в nodes

Поле `after` по-прежнему определяется в `nodes`, **не** в `schedule.nodes`. Это важно: структура зависимостей отделена от календарного планирования.

```yaml
# v2 — правильно
nodes:
  task1:
    title: "Задача 1"
  task2:
    title: "Задача 2"
    after: [task1]  # Зависимости в nodes

schedule:
  nodes:
    task1:
      start: "2024-03-01"
      duration: "3d"
    task2:
      duration: "5d"  # start вычисляется из after в nodes
```

---

## Пошаговый процесс миграции

### Шаг 1: Обновите версию

Измените `version: 1` на `version: 2` в файле плана.

```yaml
# Было
version: 1

# Стало
version: 2
```

### Шаг 2: Создайте блок schedule

Добавьте пустой блок `schedule` с подблоками `calendars` и `nodes`:

```yaml
schedule:
  calendars: {}
  nodes: {}
```

### Шаг 3: Перенесите excludes из views в schedule.calendars

1. Найдите все `excludes` в ваших представлениях (gantt_views)
2. Создайте календарь в `schedule.calendars`
3. Укажите `default_calendar`

**До (v1):**
```yaml
# views.yaml
gantt_views:
  main:
    excludes:
      - weekends
      - "2024-03-08"
```

**После (v2):**
```yaml
schedule:
  calendars:
    default:
      excludes:
        - weekends
        - "2024-03-08"
  default_calendar: default
```

### Шаг 4: Перенесите start/finish/duration из nodes в schedule.nodes

Для каждого узла с календарными полями:

1. Скопируйте `start`, `finish`, `duration` в `schedule.nodes.<node_id>`
2. Удалите эти поля из `nodes.<node_id>`

**До (v1):**
```yaml
nodes:
  task1:
    title: "Задача 1"
    start: "2024-03-01"
    duration: "5d"
  task2:
    title: "Задача 2"
    after: [task1]
    duration: "3d"
```

**После (v2):**
```yaml
nodes:
  task1:
    title: "Задача 1"
  task2:
    title: "Задача 2"
    after: [task1]  # Зависимости остаются в nodes

schedule:
  nodes:
    task1:
      start: "2024-03-01"
      duration: "5d"
    task2:
      duration: "3d"
```

### Шаг 5: Удалите excludes из views

Удалите поле `excludes` из всех представлений. В v2 это поле запрещено в views.

**До (v1):**
```yaml
views:
  gantt:
    title: "Диаграмма Ганта"
    excludes: [weekends]  # Удалить!
```

**После (v2):**
```yaml
views:
  gantt:
    title: "Диаграмма Ганта"
    # excludes удалён — календарь в schedule.calendars
```

### Шаг 6: (Опционально) Добавьте effort

Если вы хотите использовать оценку трудозатрат, добавьте поле `effort` (число) в узлы:

```yaml
meta:
  effort_unit: "sp"  # Единица измерения для UI

nodes:
  task1:
    title: "Задача 1"
    effort: 5  # Story points, дни, или другие единицы
```

### Шаг 7: Объедините файлы (опционально)

В v2 можно объединить `*.plan.yaml` и `*.views.yaml` в один файл или разбить на несколько фрагментов по логике.

---

## Перенос календарных полей из nodes в schedule.nodes

### Правила переноса

| Поле v1 (в nodes) | Поле v2 (в schedule.nodes) |
|-------------------|---------------------------|
| `start` | `start` |
| `finish` | `finish` |
| `duration` | `duration` |

### Пример переноса

**v1:**
```yaml
nodes:
  design:
    title: "Дизайн"
    start: "2024-03-01"
    duration: "5d"
  
  implementation:
    title: "Реализация"
    after: [design]
    duration: "10d"
  
  release:
    title: "Релиз"
    milestone: true
    after: [implementation]
```

**v2:**
```yaml
nodes:
  design:
    title: "Дизайн"
  
  implementation:
    title: "Реализация"
    after: [design]  # Зависимости остаются здесь
  
  release:
    title: "Релиз"
    milestone: true  # Флаг вехи остаётся здесь
    after: [implementation]

schedule:
  calendars:
    default:
      excludes: [weekends]
  default_calendar: default
  
  nodes:
    design:
      start: "2024-03-01"
      duration: "5d"
    implementation:
      duration: "10d"
      # start вычисляется из after: [design]
    release:
      # start вычисляется из after: [implementation]
      # milestone: true берётся из nodes
```

### Важные замечания

1. **Поле `after` остаётся в nodes** — не переносите его в schedule.nodes
2. **Поле `milestone` остаётся в nodes** — это характеристика узла, не расписания
3. **Узлы без дат** — если узел не имел `start`/`duration` в v1, его не нужно добавлять в schedule.nodes

---

## Перенос excludes из views в schedule.calendars

### Правила переноса

1. Создайте календарь в `schedule.calendars`
2. Перенесите значения `excludes` из views
3. Укажите `default_calendar`
4. Удалите `excludes` из views

### Пример переноса

**v1 (два файла):**

```yaml
# project.plan.yaml
version: 1
meta:
  id: project
  title: "Проект"

nodes:
  task1:
    title: "Задача 1"
    start: "2024-03-01"
    duration: "5d"
```

```yaml
# project.views.yaml
version: 1
project: project

gantt_views:
  main:
    title: "Основной вид"
    excludes:
      - weekends
      - "2024-03-08"
      - "2024-05-01"
    lanes:
      dev:
        title: "Разработка"
        nodes: [task1]
```

**v2 (один файл):**

```yaml
version: 2
meta:
  id: project
  title: "Проект"

nodes:
  task1:
    title: "Задача 1"

schedule:
  calendars:
    default:
      excludes:
        - weekends
        - "2024-03-08"
        - "2024-05-01"
  
  default_calendar: default
  
  nodes:
    task1:
      start: "2024-03-01"
      duration: "5d"

views:
  main:
    title: "Основной вид"
    # excludes удалён!
    lanes:
      dev:
        title: "Разработка"
        nodes: [task1]
```

### Несколько календарей

Если в v1 разные представления имели разные `excludes`, создайте несколько календарей:

**v1:**
```yaml
gantt_views:
  team_a:
    excludes: [weekends]
  team_b:
    excludes:
      - weekends
      - "2024-03-08"
```

**v2:**
```yaml
schedule:
  calendars:
    standard:
      excludes: [weekends]
    with_holidays:
      excludes:
        - weekends
        - "2024-03-08"
  
  default_calendar: standard
  
  nodes:
    task_a:
      start: "2024-03-01"
      duration: "5d"
      calendar: standard
    task_b:
      start: "2024-03-01"
      duration: "5d"
      calendar: with_holidays
```

---

## Примеры до/после

### Пример 1: Простой план

**v1:**
```yaml
version: 1
meta:
  id: simple
  title: "Простой проект"

statuses:
  not_started: { label: "Не начато" }
  done: { label: "Готово" }

nodes:
  task1:
    title: "Анализ"
    status: not_started
    start: "2024-03-01"
    duration: "3d"
  
  task2:
    title: "Разработка"
    after: [task1]
    duration: "5d"
  
  task3:
    title: "Тестирование"
    after: [task2]
    duration: "2d"
```

```yaml
# simple.views.yaml
version: 1
project: simple

gantt_views:
  main:
    title: "План проекта"
    excludes: [weekends]
    lanes:
      all:
        title: "Все задачи"
        nodes: [task1, task2, task3]
```

**v2:**
```yaml
version: 2
meta:
  id: simple
  title: "Простой проект"

statuses:
  not_started: { label: "Не начато" }
  done: { label: "Готово" }

nodes:
  task1:
    title: "Анализ"
    status: not_started
  
  task2:
    title: "Разработка"
    after: [task1]
  
  task3:
    title: "Тестирование"
    after: [task2]

schedule:
  calendars:
    default:
      excludes: [weekends]
  
  default_calendar: default
  
  nodes:
    task1:
      start: "2024-03-01"
      duration: "3d"
    task2:
      duration: "5d"
    task3:
      duration: "2d"

views:
  main:
    title: "План проекта"
    lanes:
      all:
        title: "Все задачи"
        nodes: [task1, task2, task3]
```

### Пример 2: План с вехами и обратным планированием

**v1:**
```yaml
version: 1
meta:
  id: release
  title: "Релиз продукта"

nodes:
  prep:
    title: "Подготовка"
    finish: "2024-03-15"
    duration: "5d"
  
  review:
    title: "Ревью"
    after: [prep]
    duration: "2d"
  
  release:
    title: "Релиз"
    milestone: true
    after: [review]
```

```yaml
# release.views.yaml
version: 1
project: release

gantt_views:
  timeline:
    excludes:
      - weekends
      - "2024-03-08"
```

**v2:**
```yaml
version: 2
meta:
  id: release
  title: "Релиз продукта"

nodes:
  prep:
    title: "Подготовка"
  
  review:
    title: "Ревью"
    after: [prep]
  
  release:
    title: "Релиз"
    milestone: true
    after: [review]

schedule:
  calendars:
    default:
      excludes:
        - weekends
        - "2024-03-08"
  
  default_calendar: default
  
  nodes:
    prep:
      finish: "2024-03-15"
      duration: "5d"
    review:
      duration: "2d"
    release:
      # start вычисляется из after

views:
  timeline:
    title: "Таймлайн релиза"
```

### Пример 3: План с частичным расписанием

**v1:** В v1 все узлы с датами отображались на Gantt.

**v2:** Можно иметь узлы без расписания — они не появятся на Gantt, но будут в tree/list.

```yaml
version: 2
meta:
  id: backlog
  title: "Бэклог с частичным планированием"
  effort_unit: "sp"

nodes:
  # Запланированные задачи
  sprint_task1:
    title: "Задача спринта 1"
    effort: 3
  
  sprint_task2:
    title: "Задача спринта 2"
    after: [sprint_task1]
    effort: 5
  
  # Незапланированные задачи (бэклог)
  backlog_task1:
    title: "Идея на будущее"
    effort: 8
  
  backlog_task2:
    title: "Техдолг"
    effort: 13

schedule:
  calendars:
    default:
      excludes: [weekends]
  default_calendar: default
  
  nodes:
    # Только задачи текущего спринта
    sprint_task1:
      start: "2024-03-01"
      duration: "3d"
    sprint_task2:
      duration: "5d"
    # backlog_task1 и backlog_task2 — не в schedule

views:
  gantt:
    title: "Спринт"
    where:
      has_schedule: true  # Только запланированные
  
  backlog:
    title: "Бэклог"
    where:
      has_schedule: false  # Только незапланированные
    order_by: effort
```

---

## Типичные проблемы и решения

### Проблема 1: Ошибка "start is not allowed in nodes"

**Причина:** Поле `start` осталось в узле после миграции.

**Решение:** Перенесите `start` в `schedule.nodes`:

```yaml
# Неправильно
nodes:
  task1:
    title: "Задача"
    start: "2024-03-01"  # Ошибка!

# Правильно
nodes:
  task1:
    title: "Задача"

schedule:
  nodes:
    task1:
      start: "2024-03-01"
```

### Проблема 2: Ошибка "excludes is not allowed in views"

**Причина:** Поле `excludes` осталось в представлении.

**Решение:** Перенесите `excludes` в `schedule.calendars`:

```yaml
# Неправильно
views:
  gantt:
    excludes: [weekends]  # Ошибка!

# Правильно
schedule:
  calendars:
    default:
      excludes: [weekends]
  default_calendar: default

views:
  gantt:
    title: "Gantt"
```

### Проблема 3: Ошибка "node 'X' in schedule.nodes does not exist in nodes"

**Причина:** В `schedule.nodes` указан узел, которого нет в `nodes`.

**Решение:** Убедитесь, что все узлы в `schedule.nodes` определены в `nodes`:

```yaml
# Неправильно
nodes:
  task1:
    title: "Задача 1"

schedule:
  nodes:
    task1:
      start: "2024-03-01"
    task2:  # Ошибка: task2 не определён в nodes!
      start: "2024-03-05"

# Правильно
nodes:
  task1:
    title: "Задача 1"
  task2:
    title: "Задача 2"

schedule:
  nodes:
    task1:
      start: "2024-03-01"
    task2:
      start: "2024-03-05"
```

### Проблема 4: Ошибка "calendar 'X' does not exist"

**Причина:** В `schedule.nodes` или `default_calendar` указан несуществующий календарь.

**Решение:** Создайте календарь в `schedule.calendars`:

```yaml
# Неправильно
schedule:
  default_calendar: work  # Ошибка: календарь 'work' не определён!
  nodes:
    task1:
      start: "2024-03-01"

# Правильно
schedule:
  calendars:
    work:
      excludes: [weekends]
  default_calendar: work
  nodes:
    task1:
      start: "2024-03-01"
```

### Проблема 5: Узел не появляется на Gantt

**Причина:** Узел не добавлен в `schedule.nodes`.

**Решение:** Добавьте узел в `schedule.nodes` с датами:

```yaml
nodes:
  task1:
    title: "Задача 1"

schedule:
  nodes:
    task1:  # Добавьте узел сюда
      start: "2024-03-01"
      duration: "5d"
```

### Проблема 6: Даты вычисляются неправильно

**Причина:** Зависимости `after` указаны в `schedule.nodes` вместо `nodes`.

**Решение:** Зависимости должны быть в `nodes`:

```yaml
# Неправильно
nodes:
  task1:
    title: "Задача 1"
  task2:
    title: "Задача 2"

schedule:
  nodes:
    task1:
      start: "2024-03-01"
      duration: "3d"
    task2:
      after: [task1]  # Ошибка: after запрещён в schedule.nodes!
      duration: "5d"

# Правильно
nodes:
  task1:
    title: "Задача 1"
  task2:
    title: "Задача 2"
    after: [task1]  # Зависимости в nodes

schedule:
  nodes:
    task1:
      start: "2024-03-01"
      duration: "3d"
    task2:
      duration: "5d"  # start вычисляется из after в nodes
```

---

## Валидация мигрированных планов

После миграции проверьте план с помощью CLI:

### Проверка валидности

```bash
# Валидация одного файла
opskarta validate plan.yaml

# Валидация нескольких файлов (Plan Set)
opskarta validate main.yaml nodes.yaml schedule.yaml
```

### Проверка рендеринга

```bash
# Рендеринг дерева (работает без schedule)
opskarta render tree plan.yaml

# Рендеринг списка
opskarta render list plan.yaml

# Рендеринг Gantt (требует schedule)
opskarta render gantt plan.yaml --view gantt

# Рендеринг графа зависимостей
opskarta render deps plan.yaml
```

### Чек-лист миграции

- [ ] Версия изменена на `2`
- [ ] Поля `start`, `finish`, `duration` перенесены из `nodes` в `schedule.nodes`
- [ ] Поле `excludes` перенесено из `views` в `schedule.calendars`
- [ ] Создан `default_calendar` (если используется schedule)
- [ ] Зависимости `after` остались в `nodes`
- [ ] Флаг `milestone` остался в `nodes`
- [ ] Удалены все `excludes` из `views`
- [ ] План проходит валидацию (`opskarta validate`)
- [ ] Gantt рендерится корректно (`opskarta render gantt`)
- [ ] Даты вычисляются правильно

### Пример вывода валидатора

**Успешная валидация:**
```
✓ Plan is valid
  Nodes: 5
  Scheduled nodes: 3
  Calendars: 1
```

**Ошибки валидации:**
```
✗ Validation failed

[error] [validation] plan.yaml
  Node 'task1' contains forbidden field 'start'
  Expected: start should be in schedule.nodes.task1

[error] [validation] plan.yaml
  View 'gantt' contains forbidden field 'excludes'
  Expected: excludes should be in schedule.calendars
```

---

## Заключение

Миграция с v1 на v2 требует:

1. **Перенос календарных полей** (`start`, `finish`, `duration`) из `nodes` в `schedule.nodes`
2. **Перенос исключений** (`excludes`) из `views` в `schedule.calendars`
3. **Сохранение зависимостей** (`after`) и флагов (`milestone`) в `nodes`

Ключевое преимущество v2 — возможность работать с планами без календарного планирования. Структура работ и зависимости существуют независимо от дат, что упрощает раннее планирование и работу с бэклогом.

При возникновении вопросов обратитесь к [полной спецификации v2](SPEC.md).
