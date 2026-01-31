# Файл представлений (`*.views.yaml`)

Файл представлений описывает, *как* смотреть на план.

## Корневые поля

- `version` *(int)*
- `project` *(string)* — должен совпадать с `meta.id` плана
- `gantt_views` *(object)* — набор Gantt‑представлений (опционально)

## Gantt view

### Core-поля

- `title` *(string)* — заголовок представления
- `excludes` *(list[string])* — исключения календаря
  - `"weekends"` — исключить субботу и воскресенье (core)
  - Конкретные даты в формате `YYYY-MM-DD` — подсказки для рендерера (non-core)
- `lanes` *(object)* — полосы/лейны
  - `<lane_id>.title` *(string)*
  - `<lane_id>.nodes` *(list[string])* — список node_id, которые показываем в этом лейне

### Поля для рендерера Mermaid (non-core)

Следующие поля являются расширениями для Mermaid Gantt рендерера и НЕ влияют на core-алгоритм вычисления дат:

- `date_format` *(string)* — формат входных дат для Mermaid (по умолчанию `YYYY-MM-DD`)
- `axis_format` *(string)* — формат отображения дат на оси X
- `tick_interval` *(string)* — интервал меток на оси X (например, `1week`, `1day`, `1month`)

> **Примечание:** эти поля документированы здесь для совместимости с существующими файлами. Подробное описание маппинга на директивы Mermaid см. в разделе "Renderer profile: Mermaid Gantt".

## Пример

### Минимальный

```yaml
version: 1
project: demo

gantt_views:
  overview:
    title: "Overview"
    excludes: ["weekends"]
    lanes:
      main:
        title: "Main"
        nodes: [root, task1]
```

### Расширенный (с полями для Mermaid)

```yaml
version: 1
project: demo

gantt_views:
  overview:
    title: "Обзор проекта"
    date_format: "YYYY-MM-DD"
    axis_format: "%d %b"
    tick_interval: "1week"
    excludes:
      - weekends
      - "2024-03-08"    # Праздник
    lanes:
      development:
        title: "Разработка"
        nodes: [backend, frontend, integration]
      testing:
        title: "Тестирование"
        nodes: [unit_tests, e2e_tests]
```
