# Plan Set (многофайловая структура)

Plan Set — это совокупность YAML-файлов (фрагментов), которые сливаются в единый план.

## Концепция

Большие планы можно разбивать на несколько файлов для:

- Организации по логическим частям (структура, расписание, представления)
- Упрощения совместной работы (разные люди редактируют разные файлы)
- Переиспользования компонентов (общие статусы, календари)

## Структура фрагмента

Каждый фрагмент — это YAML-файл с допустимыми top-level блоками:

```yaml
# Допустимые блоки
version: 2
meta: { ... }
statuses: { ... }
nodes: { ... }
schedule: { ... }
views: { ... }
x: { ... }
```

### Правила

- Любой top-level блок, кроме перечисленных, является **ошибкой**.
- Блок `version` ДОЛЖЕН быть одинаковым во всех фрагментах (если указан).
- Пустые фрагменты допустимы.

## Слияние фрагментов

Фрагменты сливаются в **Merged Plan** по следующим правилам:

### 1. Блок `version`

- Должен быть одинаковым во всех фрагментах.
- Если версии различаются — **ошибка**.

### 2. Блок `meta`

- Поля объединяются.
- При конфликте значений одного поля — **ошибка**.

```yaml
# fragment1.yaml
meta:
  id: project-x
  title: "Проект X"

# fragment2.yaml
meta:
  id: project-x      # OK: то же значение
  author: "Иван"     # OK: новое поле

# Результат
meta:
  id: project-x
  title: "Проект X"
  author: "Иван"
```

### 3. Блок `statuses`

- Словари объединяются.
- Дубликат ключа (status_id) — **ошибка** с указанием файлов.

```yaml
# fragment1.yaml
statuses:
  done: { label: "Готово" }

# fragment2.yaml
statuses:
  in_progress: { label: "В работе" }
  done: { label: "Завершено" }  # ОШИБКА: done уже определён

# Ошибка: status 'done' defined in fragment1.yaml and fragment2.yaml
```

### 4. Блок `nodes`

- Словари объединяются.
- Дубликат ключа (node_id) — **ошибка** с указанием файлов.

```yaml
# fragment1.yaml
nodes:
  task1:
    title: "Задача 1"

# fragment2.yaml
nodes:
  task2:
    title: "Задача 2"
  task1:                    # ОШИБКА: task1 уже определён
    title: "Другая задача"

# Ошибка: node 'task1' defined in fragment1.yaml and fragment2.yaml
```

### 5. Блок `schedule`

Schedule сливается по частям:

#### `schedule.calendars`

- Словари объединяются.
- Дубликат ключа (calendar_id) — **ошибка**.

#### `schedule.nodes`

- Словари объединяются.
- Дубликат ключа (node_id) — **ошибка**.

#### `schedule.default_calendar`

- Допускается только в **одном** фрагменте.
- Если указан в нескольких фрагментах — **ошибка**.

```yaml
# fragment1.yaml
schedule:
  default_calendar: work    # OK

# fragment2.yaml
schedule:
  default_calendar: holiday # ОШИБКА: default_calendar уже определён
```

### 6. Блок `views`

- Словари объединяются.
- Дубликат ключа (view_id) — **ошибка**.

### 7. Блок `x` (расширения)

- Словари объединяются.
- Дубликат ключа — **ошибка**.

## Отслеживание источников

Merged Plan сохраняет информацию о файле-источнике для каждого элемента:

```python
# Пример структуры
sources = {
    "node:task1": "nodes.plan.yaml",
    "node:task2": "nodes.plan.yaml",
    "status:done": "main.plan.yaml",
    "calendar:work": "schedule.plan.yaml",
}
```

Это позволяет выдавать информативные сообщения об ошибках с указанием файла.

## Пример многофайлового плана

### main.plan.yaml

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

### nodes.plan.yaml

```yaml
version: 2

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
```

### schedule.plan.yaml

```yaml
version: 2

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
```

### views.plan.yaml

```yaml
version: 2

views:
  gantt:
    title: "Диаграмма Ганта"
    where:
      has_schedule: true
  
  backlog:
    title: "Бэклог"
    where:
      has_schedule: false
    order_by: effort
```

## Загрузка Plan Set

Инструменты загружают Plan Set через функцию:

```python
def load_plan_set(files: list[str]) -> MergedPlan:
    """
    Загружает и сливает фрагменты плана.
    
    Args:
        files: Список путей к YAML-файлам
        
    Returns:
        MergedPlan: Объединённый план
        
    Raises:
        LoadError: При ошибке чтения файла
        MergeConflictError: При конфликте слияния
    """
```

### CLI

```bash
# Загрузка нескольких файлов
opskarta validate main.plan.yaml nodes.plan.yaml schedule.plan.yaml

# Рендеринг
opskarta render gantt main.plan.yaml nodes.plan.yaml schedule.plan.yaml --view gantt
```

## Детерминированность слияния

Слияние фрагментов **детерминировано**:

- Порядок файлов не влияет на результат (кроме порядка ошибок).
- Конфликты всегда обнаруживаются, независимо от порядка.
- Один и тот же набор файлов всегда даёт один и тот же Merged Plan.

Это гарантирует воспроизводимость результатов в CI/CD и при совместной работе.
