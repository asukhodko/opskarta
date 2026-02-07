<!-- This file is auto-generated. Do not edit manually! -->
<!-- To make changes, edit files in spec/ and run: python tools/build_spec.py --lang en -->

## Table of Contents

- [opskarta v2 Specification](#opskarta-v2-specification)
- [Plan Set (Multi-file Structure)](#plan-set-multi-file-structure)
- [Nodes (`nodes`)](#nodes-nodes)
- [Schedule (Calendar Planning Layer)](#schedule-calendar-planning-layer)
- [Views (Representations)](#views-representations)
- [Validation](#validation)

# opskarta v2 Specification

This specification describes the opskarta v2 format with the **overlay schedule** concept — separating work structure (nodes) from calendar planning (schedule).

- Serialization format: **YAML** (recommended) or JSON.
- Versioning: `version: 2` field in document root.
- Node identifiers: string keys in the `nodes:` map.

> Status: **Draft**. The v2 specification extends and reimagines v1.

## Key Concepts of v2

### Overlay Schedule

The main difference between v2 and v1 is **separating work structure from calendar planning**:

| Aspect | v1 | v2 |
|--------|----|----|
| Dates in nodes | `start`, `finish`, `duration` in `nodes` | Only in `schedule.nodes` |
| Calendar | `excludes` in `views` | `excludes` in `schedule.calendars` |
| Plan without dates | Not possible | Fully valid |
| Dependencies | `after` in `nodes` | `after` in `nodes` (unchanged) |

### Plan Set (Multi-file Structure)

v2 supports splitting a plan into multiple files (fragments):

```
project/
├── main.plan.yaml      # meta, statuses
├── nodes.plan.yaml     # nodes
├── schedule.plan.yaml  # schedule
└── views.plan.yaml     # views
```

Fragments are merged into a single **Merged Plan** deterministically.

### Effort (Work Estimation)

v2 introduces the `effort` field — an abstract work estimate in relative units:

```yaml
nodes:
  epic:
    title: "Authentication"
    effort: 13  # story points, days, or other units
```

The unit of measure is set in `meta.effort_unit` for UI display.

## Document Structure

| File | Description |
|------|-------------|
| `10-plan-set.md` | Plan Set: multi-file structure, fragment merging |
| `20-nodes.md` | Nodes: work structure without calendar fields |
| `30-schedule.md` | Schedule: calendar planning layer |
| `40-views.md` | Views: visualization representations |
| `50-validation.md` | Validation: rules and error messages |

## Allowed Top-Level Blocks

Each YAML file (fragment) can contain the following blocks:

| Block | Description | Required |
|-------|-------------|----------|
| `version` | Schema version (must be `2`) | Recommended |
| `meta` | Plan metadata | Optional |
| `statuses` | Status dictionary | Optional |
| `nodes` | Work node dictionary | Optional |
| `schedule` | Calendar planning layer | Optional |
| `views` | Visualization views | Optional |
| `x` | Extensions (namespace for custom fields) | Optional |

Any other top-level blocks are **errors**.

## Minimal Example

```yaml
version: 2
meta:
  id: demo
  title: "Demo Project"

nodes:
  root:
    title: "Project"
    kind: summary
```

This plan is valid without `schedule` — work structure exists independently of calendar planning.

## Full Example

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
      # start computed from after: [phase1] in nodes

views:
  gantt:
    title: "Gantt Chart"
    where:
      has_schedule: true
```

---

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

---

# Nodes (`nodes`)

A node is a unit of work in the plan structure. In v2, nodes describe **structure and dependencies** without calendar fields.

## Node Identifiers (node_id)

Each node is identified by a key in the `nodes` dictionary. This key (`node_id`) is used for references in `parent`, `after`, `schedule.nodes`, `views`.

### Requirements

- `node_id` MUST be unique within `nodes`.
- `node_id` MUST be a string.

### Recommendations

- **Recommended format:** `^[a-zA-Z][a-zA-Z0-9._-]*$`
  - Starts with a letter
  - Contains only letters, digits, dots, underscores, hyphens
- **For Mermaid compatibility:** avoid spaces, parentheses, colons.

```yaml
# Good identifiers
nodes:
  kickoff: ...
  phase_1: ...
  backend-api: ...
  JIRA.123: ...

# Problematic identifiers
nodes:
  "task with spaces": ...     # Spaces
  "task:important": ...       # Colon
  123: ...                    # Starts with digit
```

## Node Fields

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Work item name |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `kind` | string | Node type (summary, phase, epic, task, etc.) |
| `status` | string | Status key from `statuses` |
| `parent` | string | Parent node ID (hierarchy) |
| `after` | list[string] | Dependencies "after what" (graph) |
| `milestone` | boolean | Whether the node is a milestone |
| `effort` | number | Work estimate (≥ 0) |
| `issue` | string | Link to issue tracker |
| `notes` | string | Notes/context |
| `x` | object | Extensions |

### Forbidden Fields (moved to schedule)

In v2, the following fields are **forbidden** in `nodes`:

| Field | Moved to |
|-------|----------|
| `start` | `schedule.nodes.<id>.start` |
| `finish` | `schedule.nodes.<id>.finish` |
| `duration` | `schedule.nodes.<id>.duration` |
| `excludes` | `schedule.calendars.<id>.excludes` |

```yaml
# ERROR in v2
nodes:
  task1:
    title: "Task"
    start: "2024-03-01"    # ERROR: start forbidden in nodes
    duration: "5d"          # ERROR: duration forbidden in nodes
```

## `kind` Field

Node type for classification. Recommended values:

| Value | Description |
|-------|-------------|
| `summary` | Top-level container |
| `phase` | Project stage/phase |
| `epic` | Large entity |
| `user_story` | Story/value |
| `task` | Specific task |

```yaml
nodes:
  root:
    title: "Project"
    kind: summary
  
  phase1:
    title: "Analysis"
    kind: phase
    parent: root
```

## `parent` Field (Hierarchy)

Defines the parent node for building a decomposition tree.

```yaml
nodes:
  root:
    title: "Project"
  
  phase1:
    title: "Phase 1"
    parent: root
  
  task1:
    title: "Task 1"
    parent: phase1
```

### Rules

- The `parent` value MUST be an existing `node_id`.
- Circular references through `parent` are **forbidden**.

## `after` Field (Dependencies)

List of nodes after whose completion this node can start.

```yaml
nodes:
  design:
    title: "Design"
  
  implementation:
    title: "Implementation"
    after: [design]
  
  testing:
    title: "Testing"
    after: [implementation]
```

### Semantics

- A node can start after **all** nodes in `after` are completed.
- Dependencies are defined in `nodes`, **not** in `schedule.nodes`.
- When computing schedule, only **scheduled** dependencies are considered.

### Rules

- Each element in `after` MUST be an existing `node_id`.
- Circular dependencies through `after` are **forbidden**.

## `milestone` Field (Milestones)

A milestone is a point-in-time event on the timeline, not a task with duration.

```yaml
nodes:
  release_v1:
    title: "Release v1.0"
    milestone: true
    after: [testing]
```

### Behavior

- A milestone is displayed as a point/diamond on the Gantt chart.
- When computing `start` from `after` for a milestone, the next workday is **not added**:
  - Regular node: `start = next_workday(max_finish)`
  - Milestone: `start = max_finish`

## `effort` Field (Work Estimation)

Abstract work estimate in relative units.

```yaml
meta:
  effort_unit: "sp"  # story points — for UI only

nodes:
  epic:
    title: "Authentication"
    effort: 13
  
  story1:
    title: "Email Login"
    parent: epic
    effort: 5
  
  story2:
    title: "OAuth Login"
    parent: epic
    effort: 8
```

### Requirements

- `effort` MUST be a **non-negative number** (≥ 0).
- The unit of measure is set in `meta.effort_unit` (for display only).

### Computed Metrics

For nodes with children, the following are automatically computed:

| Metric | Description |
|--------|-------------|
| `effort_rollup` | Sum of `effort_effective` of all direct children |
| `effort_effective` | `effort` if set, otherwise `effort_rollup` |
| `effort_gap` | `max(0, effort - effort_rollup)` — incomplete decomposition |

```yaml
# Computation example
nodes:
  epic:
    title: "Authentication"
    effort: 13
    # effort_rollup = 5 + 8 = 13
    # effort_effective = 13 (explicitly set)
    # effort_gap = max(0, 13 - 13) = 0
  
  story1:
    title: "Email Login"
    parent: epic
    effort: 5
    # effort_effective = 5 (leaf node)
  
  story2:
    title: "OAuth Login"
    parent: epic
    effort: 8
    # effort_effective = 8 (leaf node)
```

### Computation Algorithm

```python
def compute_effort(node_id):
    node = nodes[node_id]
    children = [n for n in nodes if nodes[n].parent == node_id]
    
    if not children:
        # Leaf node
        node.effort_effective = node.effort
        return
    
    # Node with children
    for child in children:
        compute_effort(child)
    
    node.effort_rollup = sum(nodes[c].effort_effective or 0 for c in children)
    
    if node.effort is not None:
        node.effort_effective = node.effort
        node.effort_gap = max(0, node.effort - node.effort_rollup)
    else:
        node.effort_effective = node.effort_rollup
```

## `status` Field

Reference to a status from the `statuses` dictionary.

```yaml
statuses:
  done: { label: "Done", color: "#22c55e" }

nodes:
  task:
    title: "Task"
    status: done
```

### Rules

- The `status` value MUST be a key from `statuses`.
- Non-existent status — **error**.

## `issue` and `notes` Fields

```yaml
nodes:
  task:
    title: "Implement API"
    issue: "JIRA-123"
    notes: |
      Consider:
      - Authentication
      - Rate limiting
```

## `x` Field (Extensions)

Namespace for custom fields not defined in the specification.

```yaml
nodes:
  task:
    title: "Task"
    x:
      assignee: "john"
      priority: high
      custom_field: "value"
```

## Example: Plan Without Schedule

A plan can be fully valid without calendar planning:

```yaml
version: 2
meta:
  id: backlog
  title: "Product Backlog"
  effort_unit: "sp"

nodes:
  epic1:
    title: "Authentication"
    kind: epic
    effort: 13
  
  story1:
    title: "Email Login"
    kind: user_story
    parent: epic1
    effort: 5
  
  story2:
    title: "OAuth Login"
    kind: user_story
    parent: epic1
    after: [story1]
    effort: 8
```

Such a plan can be rendered as tree, list, deps, but not as Gantt (no dates).

---

# Schedule (Calendar Planning Layer)

Schedule is an **optional** calendar planning layer applied on top of the node structure.

## Concept

In v2, calendar planning is separated from work structure:

- **Nodes** describe *what* needs to be done and in what order (dependencies)
- **Schedule** describes *when* it will be done (dates, calendars)

A plan can exist and be useful **without** the `schedule` block.

## Schedule Block Structure

```yaml
schedule:
  calendars:
    <calendar_id>:
      excludes: [...]
  
  default_calendar: <calendar_id>
  
  nodes:
    <node_id>:
      start: "YYYY-MM-DD"
      finish: "YYYY-MM-DD"
      duration: "Nd"
      calendar: <calendar_id>
```

## Calendars (`schedule.calendars`)

A calendar defines working days with exclusions.

```yaml
schedule:
  calendars:
    work:
      excludes:
        - weekends
        - "2024-03-08"
        - "2024-05-01"
    
    no_weekends:
      excludes:
        - weekends
    
    all_days:
      excludes: []
```

### `excludes` Field

List of exclusions from working days:

| Value | Description |
|-------|-------------|
| `weekends` | Exclude Saturday and Sunday |
| `YYYY-MM-DD` | Exclude specific date (holiday, etc.) |

```yaml
excludes:
  - weekends           # Sat, Sun
  - "2024-03-08"       # International Women's Day
  - "2024-05-01"       # May Day
  - "2024-05-09"       # Victory Day
```

## Default Calendar (`schedule.default_calendar`)

Calendar used for nodes without explicit `calendar` specification.

```yaml
schedule:
  calendars:
    work:
      excludes: [weekends]
  
  default_calendar: work  # Used by default
  
  nodes:
    task1:
      start: "2024-03-01"
      duration: "5d"
      # calendar not specified → uses "work"
```

### Rules

- `default_calendar` MUST reference an existing calendar.
- Allowed in only **one** fragment in multi-file structure.

## Node Schedule (`schedule.nodes`)

Dictionary with planning parameters for specific nodes.

```yaml
schedule:
  nodes:
    task1:
      start: "2024-03-01"
      duration: "5d"
    
    task2:
      duration: "3d"
      # start computed from after in nodes
    
    milestone1:
      # start computed from after in nodes
```

### schedule.nodes Fields

| Field | Type | Description |
|-------|------|-------------|
| `start` | string | Start date (YYYY-MM-DD) |
| `finish` | string | End date (YYYY-MM-DD) |
| `duration` | string | Duration (Nd, Nw) |
| `calendar` | string | Calendar reference |

### Rules

- `node_id` in `schedule.nodes` MUST exist in `nodes`.
- `calendar` MUST exist in `schedule.calendars`.
- The `after` field is **forbidden** in `schedule.nodes` — dependencies only in `nodes`.

## Node States

Nodes have three possible states relative to schedule:

| State | Description |
|-------|-------------|
| **unscheduled** | Node is absent from `schedule.nodes` |
| **scheduled** | Node is present in `schedule.nodes` |
| **computed** | scheduled + dates successfully computed |

```yaml
nodes:
  task1:
    title: "Task 1"
  task2:
    title: "Task 2"
  task3:
    title: "Task 3"
    after: [task2]

schedule:
  nodes:
    task1:
      start: "2024-03-01"
      duration: "5d"
    # task2 — unscheduled (not in schedule.nodes)
    task3:
      duration: "3d"
      # task3 — scheduled, but unschedulable (depends on unscheduled task2)
```

## Date Computation

### Start Computation Priority

1. **Explicit `start`**: use specified date
2. **`finish` + `duration`**: compute `start` backward from `finish`
3. **Dependencies `after`**: compute from dependency completion

### Algorithm for after

When computing `start` from `after`:

1. Get dependencies from `nodes.<id>.after` (not from schedule!)
2. Filter only **scheduled** dependencies
3. Compute `max(finish)` for all scheduled dependencies
4. For regular node: `start = next_workday(max_finish)`
5. For milestone: `start = max_finish`

```yaml
nodes:
  task1:
    title: "Task 1"
  task2:
    title: "Task 2"
    after: [task1]
  task3:
    title: "Task 3"
    after: [task1, task2]

schedule:
  nodes:
    task1:
      start: "2024-03-01"
      duration: "5d"
      # finish = 2024-03-05
    
    # task2 — unscheduled
    
    task3:
      duration: "3d"
      # after = [task1, task2]
      # scheduled dependencies = [task1]
      # start = next_workday(2024-03-05) = 2024-03-06
```

### Unschedulable Nodes

A node becomes **unschedulable** if:

- No explicit `start`
- No `finish` + `duration`
- All `after` dependencies are either unscheduled or unschedulable

```yaml
nodes:
  task1:
    title: "Task 1"
  task2:
    title: "Task 2"
    after: [task1]

schedule:
  nodes:
    # task1 — unscheduled
    task2:
      duration: "3d"
      # task2 — unschedulable: depends on unscheduled task1
      # Warning: "Node 'task2': all dependencies are unschedulable"
```

## Field Formats

### `start` and `finish` Fields

Format: `YYYY-MM-DD` (ISO 8601)

```yaml
start: "2024-03-01"
finish: "2024-03-15"
```

### `duration` Field

Format: `<number><unit>`

| Unit | Description |
|------|-------------|
| `d` | Working days |
| `w` | Weeks (1w = 5 working days) |

```yaml
duration: "5d"   # 5 working days
duration: "2w"   # 2 weeks = 10 working days
```

### Rules

- Number MUST be a positive integer (≥ 1).
- Format: regular expression `^[1-9][0-9]*[dw]$`.

## Finish Computation

```
finish = add_workdays(start, duration - 1, calendar)
```

The start day (`start`) is included in the duration.

| start | duration | finish | Explanation |
|-------|----------|--------|-------------|
| 2024-03-01 | 1d | 2024-03-01 | One day |
| 2024-03-01 | 5d | 2024-03-05 | Five days: 01-05 |
| 2024-03-01 (Fri) | 5d (weekends) | 2024-03-07 | Fri, Mon, Tue, Wed, Thu |

## Backward Planning (finish → start)

If `finish` and `duration` are specified, but not `start`:

```
start = sub_workdays(finish, duration - 1, calendar)
```

```yaml
schedule:
  nodes:
    release_prep:
      finish: "2024-03-15"  # Deadline
      duration: "5d"
      # start = 2024-03-11 (5 working days back)
```

## start/finish/duration Consistency

If all three fields are specified, they MUST be consistent:

```yaml
# Correct
schedule:
  nodes:
    task:
      start: "2024-03-01"
      finish: "2024-03-05"
      duration: "5d"

# ERROR: inconsistency
schedule:
  nodes:
    task:
      start: "2024-03-01"
      finish: "2024-03-10"  # Should be 2024-03-05
      duration: "5d"
```

## Start Normalization

If `start` falls on an excluded day (weekend, holiday):

- **For regular nodes**: normalized to next working day + warning
- **For milestones**: not normalized (milestones can be on any day)

```yaml
# excludes: [weekends]

schedule:
  nodes:
    task:
      start: "2024-03-02"  # Saturday
      duration: "3d"
      # Warning: start normalized to 2024-03-04 (Monday)
      # finish = 2024-03-06
```

## Example: Partial Schedule

```yaml
version: 2

nodes:
  milestone1:
    title: "MVP"
    milestone: true
    after: [task2]
  
  task1:
    title: "Backend API"
    effort: 3
  
  task2:
    title: "Frontend"
    after: [task1]
    effort: 5
  
  task3:
    title: "Documentation"
    effort: 2

schedule:
  calendars:
    work:
      excludes: [weekends]
  
  default_calendar: work
  
  nodes:
    task1:
      start: "2024-03-01"
      duration: "3d"
    
    task2:
      duration: "5d"
      # start from after: [task1]
    
    milestone1:
      # start from after: [task2]
      # milestone: true taken from nodes
```

In this example:

- `task1`, `task2`, `milestone1` — scheduled (will appear on Gantt)
- `task3` — unscheduled (won't appear on Gantt, but exists in tree/list)

---

# Views (Representations)

Views are representations for plan visualization. In v2, views **do not affect** schedule computation.

## Concept

| Aspect | v1 | v2 |
|--------|----|----|
| Calendar | `excludes` in views | `excludes` in `schedule.calendars` |
| Effect on computation | Yes | No |
| Purpose | Visualization + calendar | Visualization only |

Views define **how** to look at the plan, but don't affect **when** work is performed.

## Views Block Structure

```yaml
views:
  <view_id>:
    title: "Name"
    where: { ... }
    order_by: "field"
    group_by: "field"
    lanes: { ... }
    date_format: "YYYY-MM-DD"
    axis_format: "%d %b"
    tick_interval: "1week"
```

## View Fields

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | View title |
| `where` | object | Structural node filter |
| `order_by` | string | Field for sorting |
| `group_by` | string | Field for grouping |
| `lanes` | object | Lanes for Gantt |
| `date_format` | string | Date format (for renderer) |
| `axis_format` | string | X-axis format (for Gantt) |
| `tick_interval` | string | Tick interval (for Gantt) |

### Forbidden Fields

In v2, the `excludes` field is **forbidden** in views:

```yaml
# ERROR in v2
views:
  gantt:
    title: "Gantt"
    excludes: [weekends]  # ERROR: excludes forbidden in views
```

Calendar is defined in `schedule.calendars`.

## Filtering (`where`)

Structural filter for node selection.

```yaml
views:
  scheduled_tasks:
    title: "Scheduled Tasks"
    where:
      kind: [task]
      has_schedule: true
```

### Filter Fields

| Field | Type | Description |
|-------|------|-------------|
| `kind` | list[string] | Nodes with specified kind |
| `status` | list[string] | Nodes with specified status |
| `has_schedule` | boolean | Only scheduled/unscheduled nodes |
| `parent` | string | Descendants of specified node |

### Filter Examples

```yaml
views:
  # Tasks only
  tasks:
    where:
      kind: [task]
  
  # Completed only
  done:
    where:
      status: [done, completed]
  
  # Scheduled only
  scheduled:
    where:
      has_schedule: true
  
  # Unscheduled only (backlog)
  backlog:
    where:
      has_schedule: false
  
  # Descendants of specific node
  phase1_tasks:
    where:
      parent: phase1
  
  # Condition combination (AND)
  scheduled_tasks:
    where:
      kind: [task]
      has_schedule: true
```

### Filtering Logic

- All conditions in `where` are combined with **AND**.
- A node passes the filter if it satisfies **all** conditions.

## Sorting (`order_by`)

Field for sorting nodes in the result.

```yaml
views:
  by_effort:
    title: "By Effort"
    order_by: effort
  
  by_status:
    title: "By Status"
    order_by: status
```

### Available Sort Fields

- `title` — by name (alphabetically)
- `kind` — by type
- `status` — by status
- `effort` — by effort
- `start` — by start date (for scheduled)
- `finish` — by end date (for scheduled)

## Grouping (`group_by`)

Field for grouping nodes.

```yaml
views:
  by_status:
    title: "By Status"
    group_by: status
  
  by_kind:
    title: "By Type"
    group_by: kind
```

## Lanes (`lanes`)

Explicit distribution of nodes across lanes for Gantt.

```yaml
views:
  gantt:
    title: "Gantt Chart"
    lanes:
      development:
        title: "Development"
        nodes: [backend, frontend, integration]
      testing:
        title: "Testing"
        nodes: [unit_tests, e2e_tests]
```

### Lane Structure

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Lane title |
| `nodes` | list[string] | List of node_id in this lane |

## Format Settings (for Renderers)

Fields for configuring display in specific renderers:

```yaml
views:
  gantt:
    title: "Gantt"
    date_format: "YYYY-MM-DD"
    axis_format: "%d %b"
    tick_interval: "1week"
```

### Format Fields

| Field | Description | Example |
|-------|-------------|---------|
| `date_format` | Input date format | `YYYY-MM-DD` |
| `axis_format` | X-axis date format | `%d %b`, `%Y-%m-%d` |
| `tick_interval` | Tick interval | `1day`, `1week`, `1month` |

## Using Views in Renderers

### Gantt

```bash
opskarta render gantt plan.yaml --view gantt
```

- `view_id` is **required** for Gantt.
- Filtering from `where` is applied.
- Calendar from `schedule` is used, **not** from view.

### Tree, List, Deps

```bash
opskarta render tree plan.yaml --view backlog
opskarta render list plan.yaml --view tasks
opskarta render deps plan.yaml
```

- `view_id` is **optional**.
- If specified — filtering and sorting are applied.
- If not specified — all nodes are displayed.

## Examples

### Minimal View

```yaml
views:
  all:
    title: "All Nodes"
```

### View with Filtering

```yaml
views:
  active_tasks:
    title: "Active Tasks"
    where:
      kind: [task]
      status: [in_progress]
    order_by: effort
```

### View for Gantt

```yaml
views:
  project_gantt:
    title: "Project Chart"
    where:
      has_schedule: true
    axis_format: "%d %b"
    tick_interval: "1week"
    lanes:
      main:
        title: "Main Work"
        nodes: [phase1, phase2, phase3]
      milestones:
        title: "Milestones"
        nodes: [mvp, release]
```

### View for Backlog

```yaml
views:
  backlog:
    title: "Backlog"
    where:
      has_schedule: false
    order_by: effort
    group_by: kind
```

## Full Example

```yaml
version: 2

nodes:
  epic1:
    title: "Authentication"
    kind: epic
    effort: 13
  
  task1:
    title: "Backend API"
    kind: task
    parent: epic1
    status: in_progress
    effort: 5
  
  task2:
    title: "Frontend"
    kind: task
    parent: epic1
    status: not_started
    effort: 8

schedule:
  calendars:
    work:
      excludes: [weekends]
  default_calendar: work
  nodes:
    task1:
      start: "2024-03-01"
      duration: "5d"

views:
  # All scheduled nodes
  gantt:
    title: "Gantt"
    where:
      has_schedule: true
  
  # Backlog (unscheduled)
  backlog:
    title: "Backlog"
    where:
      has_schedule: false
    order_by: effort
  
  # Tasks only
  tasks:
    title: "Tasks"
    where:
      kind: [task]
    order_by: status
  
  # Tasks in progress
  in_progress:
    title: "In Progress"
    where:
      status: [in_progress]
```

---

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