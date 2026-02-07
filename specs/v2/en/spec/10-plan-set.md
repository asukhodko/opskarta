# Plan Set (Multi-file Structure)

A Plan Set is a collection of YAML files (fragments) that are merged into a single plan.

## Concept

Large plans can be split into multiple files for:

- Organization by logical parts (structure, schedule, views)
- Easier collaboration (different people edit different files)
- Component reuse (shared statuses, calendars)

## Fragment Structure

Each fragment is a YAML file with allowed top-level blocks:

```yaml
# Allowed blocks
version: 2
meta: { ... }
statuses: { ... }
nodes: { ... }
schedule: { ... }
views: { ... }
x: { ... }
```

### Rules

- Any top-level block other than those listed is an **error**.
- The `version` block MUST be the same in all fragments (if specified).
- Empty fragments are allowed.

## Fragment Merging

Fragments are merged into a **Merged Plan** according to these rules:

### 1. `version` Block

- Must be the same in all fragments.
- If versions differ — **error**.

### 2. `meta` Block

- Fields are combined.
- Conflicting values for the same field — **error**.

```yaml
# fragment1.yaml
meta:
  id: project-x
  title: "Project X"

# fragment2.yaml
meta:
  id: project-x      # OK: same value
  author: "John"     # OK: new field

# Result
meta:
  id: project-x
  title: "Project X"
  author: "John"
```

### 3. `statuses` Block

- Dictionaries are combined.
- Duplicate key (status_id) — **error** with file indication.

```yaml
# fragment1.yaml
statuses:
  done: { label: "Done" }

# fragment2.yaml
statuses:
  in_progress: { label: "In Progress" }
  done: { label: "Completed" }  # ERROR: done already defined

# Error: status 'done' defined in fragment1.yaml and fragment2.yaml
```

### 4. `nodes` Block

- Dictionaries are combined.
- Duplicate key (node_id) — **error** with file indication.

```yaml
# fragment1.yaml
nodes:
  task1:
    title: "Task 1"

# fragment2.yaml
nodes:
  task2:
    title: "Task 2"
  task1:                    # ERROR: task1 already defined
    title: "Another Task"

# Error: node 'task1' defined in fragment1.yaml and fragment2.yaml
```

### 5. `schedule` Block

Schedule is merged by parts:

#### `schedule.calendars`

- Dictionaries are combined.
- Duplicate key (calendar_id) — **error**.

#### `schedule.nodes`

- Dictionaries are combined.
- Duplicate key (node_id) — **error**.

#### `schedule.default_calendar`

- Allowed in only **one** fragment.
- If specified in multiple fragments — **error**.

```yaml
# fragment1.yaml
schedule:
  default_calendar: work    # OK

# fragment2.yaml
schedule:
  default_calendar: holiday # ERROR: default_calendar already defined
```

### 6. `views` Block

- Dictionaries are combined.
- Duplicate key (view_id) — **error**.

### 7. `x` Block (Extensions)

- Dictionaries are combined.
- Duplicate key — **error**.

## Source Tracking

The Merged Plan preserves source file information for each element:

```python
# Example structure
sources = {
    "node:task1": "nodes.plan.yaml",
    "node:task2": "nodes.plan.yaml",
    "status:done": "main.plan.yaml",
    "calendar:work": "schedule.plan.yaml",
}
```

This allows informative error messages with file indication.

## Multi-file Plan Example

### main.plan.yaml

```yaml
version: 2
meta:
  id: project-x
  title: "Project X"
  effort_unit: "sp"

statuses:
  not_started: { label: "Not Started", color: "#9ca3af" }
  in_progress: { label: "In Progress", color: "#0ea5e9" }
  done: { label: "Done", color: "#22c55e" }
```

### nodes.plan.yaml

```yaml
version: 2

nodes:
  root:
    title: "Project X"
    kind: summary
    status: in_progress
  
  phase1:
    title: "Phase 1: Analysis"
    kind: phase
    parent: root
    effort: 10
  
  phase2:
    title: "Phase 2: Development"
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
    title: "Gantt Chart"
    where:
      has_schedule: true
  
  backlog:
    title: "Backlog"
    where:
      has_schedule: false
    order_by: effort
```

## Loading a Plan Set

Tools load a Plan Set through a function:

```python
def load_plan_set(files: list[str]) -> MergedPlan:
    """
    Loads and merges plan fragments.
    
    Args:
        files: List of paths to YAML files
        
    Returns:
        MergedPlan: Merged plan
        
    Raises:
        LoadError: On file read error
        MergeConflictError: On merge conflict
    """
```

### CLI

```bash
# Load multiple files
opskarta validate main.plan.yaml nodes.plan.yaml schedule.plan.yaml

# Rendering
opskarta render gantt main.plan.yaml nodes.plan.yaml schedule.plan.yaml --view gantt
```

## Merge Determinism

Fragment merging is **deterministic**:

- File order doesn't affect the result (except error order).
- Conflicts are always detected, regardless of order.
- The same set of files always produces the same Merged Plan.

This guarantees reproducible results in CI/CD and collaborative work.
