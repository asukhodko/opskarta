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
