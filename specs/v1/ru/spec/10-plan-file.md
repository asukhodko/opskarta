# Файл плана (`*.plan.yaml`)

## Корневые поля

- `version` *(int)* — версия схемы.
- `meta` *(object)* — метаданные плана.
  - `id` *(string)* — ID проекта/программы. Используется для связки с файлами представлений.
  - `title` *(string)* — человекочитаемое имя.
- `statuses` *(object)* — словарь статусов.
- `nodes` *(object)* — словарь узлов работ: `{ <node_id>: <node> }`.

## Пример

```yaml
version: 1
meta:
  id: demo
  title: "Demo"

statuses:
  not_started: { label: "Не начато", color: "#9ca3af" }
  in_progress: { label: "В работе",  color: "#0ea5e9" }

nodes:
  root:
    title: "Root"
    kind: summary
    status: in_progress
```
