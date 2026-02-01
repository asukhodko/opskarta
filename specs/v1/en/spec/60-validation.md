# Validation Rules

This section describes validation rules for plan and view files.

## Plan File Validation (`*.plan.yaml`)

### Required Fields

- `version` *(int)* — MUST be present at document root.
- `nodes` *(object)* — MUST be present (may be empty).
- For each node: `title` *(string)* — required field.

### Field `meta.id`

- `meta.id` is RECOMMENDED for all plan files.
- `meta.id` is REQUIRED if plan file is used together with views file (`*.views.yaml`).

```yaml
# Minimal plan (without views)
version: 1
nodes:
  task1:
    title: "Task"

# Plan for use with views (meta.id is required)
version: 1
meta:
  id: "my-project"
  title: "My Project"
nodes:
  task1:
    title: "Task"
```

### Referential Integrity

#### Parent References (`parent`)

- If a node contains `parent` field, value MUST be a key of existing node in `nodes`.
- Circular references via `parent` are forbidden.

```yaml
# Correct
nodes:
  root:
    title: "Root"
  child:
    title: "Child"
    parent: root  # root exists

# Error: non-existent parent
nodes:
  child:
    title: "Child"
    parent: nonexistent  # error!
```

#### Dependencies (`after`)

- Each element of `after` list MUST be a key of existing node in `nodes`.
- Circular dependencies via `after` are forbidden.

```yaml
# Correct
nodes:
  task1:
    title: "Task 1"
  task2:
    title: "Task 2"
    after: [task1]  # task1 exists

# Error: non-existent dependency
nodes:
  task2:
    title: "Task 2"
    after: [missing_task]  # error!
```

#### Statuses (`status`)

- If a node contains `status` field, value MUST be a key from `statuses` dictionary.

```yaml
statuses:
  done: { label: "Done" }

nodes:
  task:
    title: "Task"
    status: done  # correct, done exists in statuses

# Error: non-existent status
nodes:
  task:
    title: "Task"
    status: completed  # error, if completed is not in statuses!
```

### Scheduling Field Formats

#### Field `start`

- If specified, MUST match format `YYYY-MM-DD`.
- Format: regex `^\d{4}-\d{2}-\d{2}$`.
- RECOMMENDED to validate date correctness (existing calendar day).

```yaml
# Correct
start: "2024-03-15"

# Format errors
start: "2024-3-15"   # month without leading zero
start: "15-03-2024"  # wrong order
start: "2024/03/15"  # wrong separator
```

#### Field `finish`

- If specified, MUST match format `YYYY-MM-DD`.
- Format: regex `^\d{4}-\d{2}-\d{2}$`.
- RECOMMENDED to validate date correctness (existing calendar day).
- If `start`, `finish`, and `duration` are all specified, they MUST be consistent (error on inconsistency).

```yaml
# Correct
finish: "2024-03-15"

# Format errors (similar to start)
finish: "2024-3-15"   # month without leading zero
finish: "15-03-2024"  # wrong order
```

#### Field `duration`

- If specified, MUST match format `<number><unit>`.
- Format: regex `^[1-9][0-9]*[dw]$`.
- Units: `d` (days), `w` (weeks, where 1w = 5 workdays).
- Number MUST be positive integer (≥ 1).

```yaml
# Correct
duration: "5d"   # 5 days
duration: "2w"   # 2 weeks (10 workdays)
duration: "10d"  # 10 days

# Format errors
duration: "0d"   # zero is not allowed
duration: "-1d"  # negatives are not allowed
duration: "5"    # missing unit
duration: "5m"   # unknown unit
duration: "d5"   # wrong order
```

## Views File Validation (`*.views.yaml`)

### Required Fields

- `version` *(int)* — MUST be present.
- `project` *(string)* — MUST be present.

### Link to Plan File

- `project` field MUST match `meta.id` of corresponding plan file.
- If plan file is missing `meta.id`, link validation MUST fail.

```yaml
# plan.yaml
meta:
  id: my-project

# views.yaml
project: my-project  # must match meta.id
```

### Node References in Views

- Each `node_id` in `lanes[].nodes` MUST exist in plan file.

```yaml
# If plan has nodes: {task1, task2}
gantt_views:
  overview:
    lanes:
      main:
        nodes: [task1, task2]  # correct
        # nodes: [task1, task3]  # error, task3 doesn't exist
```

### Field `excludes` in Views

- `excludes` field in `gantt_views` MAY contain:
  - `"weekends"` — affects date calculation algorithm (see "Scheduling" section).
  - Specific dates in `YYYY-MM-DD` format — **core**, affect date calculation algorithm.
  - Other values — **non-core**, MUST be ignored with warning.

```yaml
gantt_views:
  overview:
    excludes:
      - weekends        # core: affects date calculation
      - "2024-03-08"    # core: affects date calculation (holiday)
      - "monday"        # non-core: warning, ignored
```

> **Note:** validator MUST issue warning about presence of non-core values in `excludes`.

## Validation Levels

Validator may operate at different levels:

1. **Syntax** — YAML/JSON correctness.
2. **Schema** — JSON Schema compliance (field types, required fields, formats).
3. **Semantics** — referential integrity, business rules, date correctness.

## Severity Levels

Validator MUST classify issues by severity level:

| Level | Description | Behavior |
|-------|-------------|----------|
| **error** | Critical error making file invalid | Validation fails (exit code ≠ 0) |
| **warn** | Potential issue requiring attention | Validation succeeds, but warning is output |
| **info** | Informational message | Validation succeeds |

### Issue Classification

| Issue | Level |
|-------|-------|
| Missing required fields (`version`, `nodes`, `title`) | error |
| Non-existent references (`parent`, `after`, `status`) | error |
| Circular dependencies (`parent`, `after`) | error |
| Duplicate `node_id` in `nodes` | error |
| Duplicate YAML keys (at any level) | error |
| Invalid `start`, `finish`, or `duration` format | error |
| Invalid `color` format in `statuses` | error |
| Inconsistent `start` + `finish` + `duration` | error |
| `after` chain without anchor (no `start`/`finish` in chain) | warn |
| Explicit `start` before dependency finish (`after`) | warn |
| `start` on excluded day (not milestone) | warn |
| `finish` on excluded day | warn |
| Non-core values in `excludes` | warn |
| Missing `duration` for scheduled node | info |
| Specific dates in `excludes` (core, affect calculation) | info |
| Unscheduled nodes (not displayed on diagram) | info |

## Additional Validation Rules

### Node Identifier Uniqueness

Each `node_id` (key in `nodes` dictionary) MUST be unique.

> **Important:** some YAML parsers (e.g., PyYAML) silently take the last value when keys are duplicated. Validator MUST detect duplicates as much as possible and issue an error.

```yaml
# Error: duplicate node_id
nodes:
  task1:
    title: "First version"
  task1:                    # ERROR: duplicate key!
    title: "Second version"
```

### Duplicate YAML Keys

YAML parsers may silently overwrite duplicate keys. Validators MUST detect duplicate keys and report an error.

**Implementation:** use YAML loader that throws exception on duplicate detection (see Python `yaml.SafeLoader` with custom constructor).

```yaml
# ERROR: duplicate key
nodes:
  task1:
    title: "First"
  task1:  # DUPLICATE
    title: "Second"
```

This rule applies to all levels: root, nodes, statuses, views, etc.

### after Chains Without Anchor

A chain of nodes linked by `after` dependencies MAY not have an anchor (node with explicit `start` or `finish`). In this case:

1. Validator MUST issue a **warning** (warn).
2. Nodes in such chain become **unscheduled**.
3. Unscheduled nodes are **NOT displayed** on Gantt chart.
4. Plan remains **valid** — this allows storing "draft" branches without fake dates.

**When to issue warning:** if recursive traversal of `after` dependencies finds no node with `start` or `finish`.

> **Note:** circular dependencies (`task1 → task2 → task1`) remain an **error**, as this is a structural graph problem, not a scheduling problem.

```yaml
# WARNING: chain without anchor (nodes will be unscheduled)
nodes:
  task1:
    title: "Task 1"
    after: [task2]
    duration: "3d"
  
  task2:
    title: "Task 2"
    # No start, no finish, no after → unscheduled
    # task1 depends on unscheduled task2 → task1 is also unscheduled
    duration: "2d"
    # Both nodes won't appear on Gantt chart
```

**Strict mode:** tools MAY provide `--strict` option, where chains without anchor are treated as error. Useful for CI/CD pipelines where full scheduling is required.

### start and after Conflict

If a node has both `start` and `after`, and explicit `start` is before computed dependency finish — validator MUST issue warning:

```yaml
nodes:
  dependency:
    title: "Dependency"
    start: "2024-03-01"
    duration: "5d"
    # finish = 2024-03-05

  task:
    title: "Task"
    start: "2024-03-03"     # WARN: before dependency finish (2024-03-05)!
    after: [dependency]
    duration: "2d"
```

### Color Format in Statuses

`color` field in `statuses` MUST be a valid hex color:

- Format: regex `^#[0-9a-fA-F]{6}$`.
- Examples of correct values: `#22c55e`, `#9CA3AF`, `#fecaca`.

```yaml
statuses:
  done:
    label: "Done"
    color: "#22c55e"    # correct
  
  invalid:
    label: "Invalid"
    color: "green"      # ERROR: must be hex format
```

## Error Messages

Validator MUST provide clear error messages:

- Path to problematic field (e.g., `nodes.task2.parent`).
- Problem description.
- Expected value or format.

Example output:

```
Error: Invalid reference in nodes.task2.parent
  Value: "nonexistent"
  Expected: existing node ID from nodes
  Available: root, task1
```

```
Error: Invalid duration format in nodes.task1.duration
  Value: "5"
  Expected: format <number><unit> where unit is 'd' or 'w'
  Pattern: ^[1-9][0-9]*[dw]$
```
