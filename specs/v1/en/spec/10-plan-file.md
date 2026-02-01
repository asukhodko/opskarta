# Plan File (`*.plan.yaml`)

## Root Fields

- `version` *(int)* — schema version.
- `meta` *(object)* — plan metadata.
  - `id` *(string)* — project/program ID. Used for linking with view files.
  - `title` *(string)* — human-readable name.
- `statuses` *(object)* — status dictionary.
- `nodes` *(object)* — work nodes dictionary: `{ <node_id>: <node> }`.

## Example

```yaml
version: 1
meta:
  id: demo
  title: "Demo"

statuses:
  not_started: { label: "Not Started", color: "#9ca3af" }
  in_progress: { label: "In Progress", color: "#0ea5e9" }

nodes:
  root:
    title: "Root"
    kind: summary
    status: in_progress
```
