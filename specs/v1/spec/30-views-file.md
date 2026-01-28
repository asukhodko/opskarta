# Файл представлений (`*.views.yaml`)

Файл представлений описывает, *как* смотреть на план.

## Корневые поля

- `version` *(int)*
- `project` *(string)* — должен совпадать с `meta.id` плана
- `gantt_views` *(object)* — набор Gantt‑представлений (опционально)

## Gantt view

- `title` *(string)* — заголовок
- `excludes` *(list[string])* — исключения календаря (пока поддерживается только `weekends`)
- `lanes` *(object)* — полосы/лейны
  - `<lane_id>.title` *(string)*
  - `<lane_id>.nodes` *(list[string])* — список node_id, которые показываем в этом лейне

## Пример

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
