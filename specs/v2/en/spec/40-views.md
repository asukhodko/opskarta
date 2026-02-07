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
