# Extensibility

opskarta specifically allows format extension without breaking basic compatibility.

## Extension Areas

Additional fields (extensions) are allowed in the following places:

### Plan File (`*.plan.yaml`)

| Level | Example Location | Description |
|-------|------------------|-------------|
| File root | `version`, `meta`, `nodes`, **`x:`** | Project metadata |
| `meta` object | `meta.id`, `meta.title`, **`meta.x:`** | Extended metadata |
| `statuses.*` object | `statuses.done.label`, **`statuses.done.x:`** | Additional status attributes |
| Node object `nodes.*` | `nodes.task1.title`, **`nodes.task1.x:`** | Custom node attributes |

### Views File (`*.views.yaml`)

| Level | Example Location | Description |
|-------|------------------|-------------|
| File root | `version`, `project`, **`x:`** | Views metadata |
| `gantt_views.*` object | `gantt_views.main.title`, **`gantt_views.main.x:`** | View settings |
| `lanes.*` object | `lanes.dev.title`, **`lanes.dev.x:`** | Lane settings |

## Rules for Tools

Base tools (validators, renderers) MUST:

1. **Ignore unknown fields** — do not error when encountering unknown field.
2. **Preserve unknown fields** — during "parse → emit" operations (read and write) unknown fields MUST be preserved.

## Recommended Namespace `x:`

For custom and renderer-specific fields it is RECOMMENDED to use namespace `x:`:

```yaml
# At plan root
version: 1
meta:
  id: "my-project"
  title: "My Project"
x:
  team_assignments:
    - team: "Backend"
      lead: "Alice"
  risk_register:
    - risk_id: "R1"
      description: "External API dependency"

nodes:
  task1:
    title: "Task 1"
    x:
      team: "SRE"
      risk: "high"
      custom_field: "any value"
```

```yaml
# In views
version: 1
project: "my-project"
x:
  theme: "dark"
  export_format: "png"

gantt_views:
  main:
    title: "Main Plan"
    x:
      zoom_level: "week"
    lanes:
      dev:
        title: "Development"
        nodes: [task1, task2]
        x:
          color: "#3498db"
```

### Why Use `x:`

1. **Avoid conflicts** — new spec versions won't conflict with your extensions.
2. **Explicit marking** — clear that this is an extension, not part of core spec.
3. **Grouping** — all custom fields are collected in one place.

### When `x:` is Not Required

Using `x:` is RECOMMENDED but not required. The following formats are also allowed:

```yaml
# Allowed (but not recommended)
nodes:
  task1:
    title: "Task"
    team: "SRE"          # extension without namespace
    risk: "high"         # extension without namespace

# Recommended
nodes:
  task1:
    title: "Task"
    x:
      team: "SRE"
      risk: "high"
```

## Renderer Extensions

Renderers MAY support specific extensions. Such extensions MUST:

1. Be documented in renderer profile (see "Renderer profile: Mermaid Gantt").
2. Use namespace `x:` or explicit renderer namespace (e.g., `x.mermaid:`).
3. Not affect core format semantics.

**Example scheduling extension:**

```yaml
nodes:
  child_task:
    title: "Child Task"
    parent: parent_task
    x:
      scheduling:
        anchor_to_parent_start: true  # Optional date inheritance from parent
```

## JSON Schema and Extensibility

JSON Schema for opskarta uses `additionalProperties: true` at all levels where extensions are allowed. This means:

- Schema will NOT error for unknown fields.
- Extensions are validated only by types (if specified in extension schema).

If you need validation of custom extensions, create your own JSON Schema extending the base one.
