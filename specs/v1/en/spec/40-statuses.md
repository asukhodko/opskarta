# Statuses (`statuses`)

`statuses` — a dictionary of arbitrary statuses that your toolset understands.

## Structure

The `statuses` section in the plan file is **optional**. However, if at least one node has a `status` field, the `statuses` section becomes required.

### Referential Integrity Rule

If a node has a `status` field, the value MUST be a key from the `statuses` dictionary:

```yaml
statuses:
  done: { label: "Done" }
  in_progress: { label: "In Progress" }

nodes:
  task1:
    title: "Task"
    status: done          # ✓ correct
  task2:
    title: "Another Task"
    status: pending       # ✗ error: pending is not in statuses
```

## Recommended Status Keys

The following keys are not required, but help with tool compatibility:

- `not_started`
- `in_progress`
- `done`
- `blocked`

## Status Fields

Each status is an object with the following fields:

| Field | Type | Requirement | Description |
|-------|------|-------------|-------------|
| `label` | string | Recommended | Human-readable status name |
| `color` | string | Optional | Color in hex format for visualizations |

### Field `label`

- If `label` is not specified, renderers MAY use the status key as label.

### Field `color`

- Format: hex color, regex `^#[0-9a-fA-F]{6}$`.
- Examples: `#22c55e`, `#9ca3af`, `#fecaca`.
- If `color` is not specified, renderers MAY use default colors (see Renderer profile).

```yaml
# Correct colors
color: "#22c55e"
color: "#9CA3AF"

# Incorrect colors
color: "green"      # Named colors not supported
color: "#fff"       # Must be 6-character hex
color: "22c55e"     # Must start with #
```

## Example

### Minimal

```yaml
statuses:
  done: { label: "Done" }
  in_progress: { label: "In Progress" }
```

### Full

```yaml
statuses:
  not_started:
    label: "Not Started"
    color: "#9ca3af"
  in_progress:
    label: "In Progress"
    color: "#0ea5e9"
  done:
    label: "Done"
    color: "#22c55e"
  blocked:
    label: "Blocked"
    color: "#fecaca"
```
