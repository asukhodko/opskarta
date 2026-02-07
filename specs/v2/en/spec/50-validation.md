# Validation

This section describes validation rules for v2 plan files.

## Validation Levels

1. **Syntax** — YAML/JSON correctness
2. **Schema** — JSON Schema compliance (types, formats)
3. **Semantics** — referential integrity, business rules

## Severity Levels

| Level | Description | Behavior |
|-------|-------------|----------|
| **error** | Critical error | Validation fails |
| **warn** | Potential problem | Validation succeeds with warning |
| **info** | Informational message | Validation succeeds |

## Fragment Validation

### Allowed Top-Level Blocks

A fragment can only contain:

- `version`
- `meta`
- `statuses`
- `nodes`
- `schedule`
- `views`
- `x`

```yaml
# ERROR: invalid block
version: 2
nodes: { ... }
custom_block: { ... }  # ERROR: unknown top-level block 'custom_block'
```

### Version

- `version` MUST be integer `2`.
- Different versions in fragments — **error**.

## Nodes Validation

### Required Fields

- `title` *(string)* — REQUIRED for each node.

```yaml
# ERROR: missing title
nodes:
  task1:
    kind: task  # ERROR: missing required field 'title'
```

### Forbidden Fields

In v2, the following fields are **forbidden** in nodes:

| Field | Error |
|-------|-------|
| `start` | "field 'start' is not allowed in nodes (use schedule.nodes)" |
| `finish` | "field 'finish' is not allowed in nodes (use schedule.nodes)" |
| `duration` | "field 'duration' is not allowed in nodes (use schedule.nodes)" |
| `excludes` | "field 'excludes' is not allowed in nodes (use schedule.calendars)" |

```yaml
# ERROR: forbidden fields
nodes:
  task1:
    title: "Task"
    start: "2024-03-01"  # ERROR: field 'start' is not allowed in nodes
```

### Effort Format

- `effort` MUST be a **non-negative number** (≥ 0).

```yaml
# Correct
nodes:
  task1:
    title: "Task"
    effort: 5
  task2:
    title: "Task"
    effort: 0      # OK: zero is allowed
  task3:
    title: "Task"
    effort: 3.5    # OK: decimals are allowed

# ERROR
nodes:
  task:
    title: "Task"
    effort: -1     # ERROR: effort must be >= 0
    effort: "5sp"  # ERROR: effort must be a number
```

## Referential Integrity

### Parent References (`parent`)

- The `parent` value MUST be an existing `node_id`.
- Circular references through `parent` are **forbidden**.

```yaml
# ERROR: non-existent parent
nodes:
  child:
    title: "Child"
    parent: nonexistent  # ERROR: parent 'nonexistent' does not exist

# ERROR: circular reference
nodes:
  a:
    title: "A"
    parent: b
  b:
    title: "B"
    parent: a  # ERROR: circular parent reference
```

### Dependencies (`after`)

- Each element in `after` MUST be an existing `node_id`.
- Circular dependencies through `after` are **forbidden**.

```yaml
# ERROR: non-existent dependency
nodes:
  task:
    title: "Task"
    after: [missing]  # ERROR: after reference 'missing' does not exist

# ERROR: circular dependency
nodes:
  a:
    title: "A"
    after: [b]
  b:
    title: "B"
    after: [a]  # ERROR: circular dependency
```

### Statuses (`status`)

- The `status` value MUST be a key from `statuses`.

```yaml
statuses:
  done: { label: "Done" }

nodes:
  task:
    title: "Task"
    status: completed  # ERROR: status 'completed' does not exist
```

## Schedule Validation

### Node References

- `node_id` in `schedule.nodes` MUST exist in `nodes`.

```yaml
nodes:
  task1:
    title: "Task 1"

schedule:
  nodes:
    task1:
      start: "2024-03-01"
    task2:                    # ERROR: node 'task2' does not exist
      start: "2024-03-05"
```

### Calendar References

- `calendar` in `schedule.nodes` MUST exist in `schedule.calendars`.
- `default_calendar` MUST exist in `schedule.calendars`.

```yaml
schedule:
  calendars:
    work:
      excludes: [weekends]
  
  default_calendar: holiday  # ERROR: calendar 'holiday' does not exist
  
  nodes:
    task1:
      start: "2024-03-01"
      calendar: custom       # ERROR: calendar 'custom' does not exist
```

### Date Format

- `start` and `finish` MUST match format `YYYY-MM-DD`.

```yaml
schedule:
  nodes:
    task:
      start: "2024-3-1"      # ERROR: invalid date format
      start: "01-03-2024"    # ERROR: invalid date format
      start: "2024-03-01"    # OK
```

### Duration Format

- `duration` MUST match format `^[1-9][0-9]*[dw]$`.

```yaml
schedule:
  nodes:
    task:
      duration: "5d"   # OK
      duration: "2w"   # OK
      duration: "0d"   # ERROR: duration must be >= 1
      duration: "5"    # ERROR: missing unit (d or w)
      duration: "5m"   # ERROR: invalid unit
```

### start/finish/duration Consistency

If all three fields are specified, they MUST be consistent.

```yaml
schedule:
  nodes:
    task:
      start: "2024-03-01"
      finish: "2024-03-10"
      duration: "5d"
      # ERROR: inconsistent start/finish/duration
      # computed finish from start+duration = 2024-03-05, but specified 2024-03-10
```

### Forbidden Fields in schedule.nodes

The `after` field is **forbidden** in `schedule.nodes`:

```yaml
schedule:
  nodes:
    task:
      start: "2024-03-01"
      after: [other]  # ERROR: 'after' is not allowed in schedule.nodes
```

## Views Validation

### excludes Prohibition

The `excludes` field is **forbidden** in views:

```yaml
views:
  gantt:
    title: "Gantt"
    excludes: [weekends]  # ERROR: 'excludes' is not allowed in views
```

### where Validation

Fields in `where` must be from the allowed list:

- `kind`
- `status`
- `has_schedule`
- `parent`

```yaml
views:
  custom:
    where:
      kind: [task]        # OK
      custom_field: value # ERROR: unknown filter field 'custom_field'
```

## Merge Validation

### node_id Conflicts

```
Error: Merge conflict - node 'task1' defined in multiple files
  File 1: nodes.plan.yaml
  File 2: extra.plan.yaml
```

### status_id Conflicts

```
Error: Merge conflict - status 'done' defined in multiple files
  File 1: main.plan.yaml
  File 2: statuses.plan.yaml
```

### meta Conflicts

```
Error: Merge conflict - meta.title has different values
  File 1: main.plan.yaml, value: "Project A"
  File 2: extra.plan.yaml, value: "Project B"
```

### default_calendar Conflicts

```
Error: Merge conflict - schedule.default_calendar defined in multiple files
  File 1: schedule1.plan.yaml
  File 2: schedule2.plan.yaml
```

## Error Classification

| Error | Level | Phase |
|-------|-------|-------|
| Invalid YAML | error | Load |
| Invalid top-level block | error | Load |
| node_id conflict | error | Merge |
| status_id conflict | error | Merge |
| meta field conflict | error | Merge |
| default_calendar conflict | error | Merge |
| Missing title in node | error | Validation |
| Node contains start/finish/duration | error | Validation |
| Invalid effort format | error | Validation |
| Non-existent parent | error | Validation |
| Non-existent after | error | Validation |
| Non-existent status | error | Validation |
| Non-existent node in schedule.nodes | error | Validation |
| Non-existent calendar | error | Validation |
| View contains excludes | error | Validation |
| Circular dependencies | error | Validation |
| Inconsistent start/finish/duration | error | Scheduling |
| after chain without anchor | warn | Scheduling |
| start before dependency finish | warn | Scheduling |
| start on excluded day | warn | Scheduling |

## Error Message Format

```
[severity] [phase] [file:line] message
  path: element.path
  value: actual_value
  expected: expected_format
```

### Examples

```
[error] [validation] nodes.plan.yaml:15 Invalid effort value
  path: nodes.task1.effort
  value: -5
  expected: number >= 0
```

```
[error] [validation] schedule.plan.yaml:8 Invalid reference
  path: schedule.nodes.task2
  value: task2
  expected: existing node_id from nodes
  available: task1, task3
```

```
[error] [merge] Merge conflict
  element: node 'task1'
  file1: nodes.plan.yaml
  file2: extra.plan.yaml
```

```
[warn] [scheduling] schedule.plan.yaml:12 Start date on excluded day
  path: schedule.nodes.task1.start
  value: 2024-03-02 (Saturday)
  normalized: 2024-03-04 (Monday)
```

## Source Tracking

All validation errors contain the source file path:

```python
# Error structure
class ValidationError:
    severity: str      # "error", "warn", "info"
    phase: str         # "load", "merge", "validation", "scheduling"
    source_file: str   # file path
    path: str          # element path (nodes.task1.effort)
    message: str       # error description
    value: Any         # actual value
    expected: str      # expected format
```

This allows quickly finding and fixing errors in multi-file plans.
