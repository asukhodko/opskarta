# Migration Guide from opskarta v1 to v2

This guide describes the process of migrating plans from opskarta v1 format to v2.

## Table of Contents

- [Overview of Changes](#overview-of-changes)
- [Key Differences in v2](#key-differences-in-v2)
- [Step-by-Step Migration Process](#step-by-step-migration-process)
- [Moving Calendar Fields from nodes to schedule.nodes](#moving-calendar-fields-from-nodes-to-schedulenodes)
- [Moving excludes from views to schedule.calendars](#moving-excludes-from-views-to-schedulecalendars)
- [Before/After Examples](#beforeafter-examples)
- [Common Problems and Solutions](#common-problems-and-solutions)
- [Validating Migrated Plans](#validating-migrated-plans)

---

## Overview of Changes

opskarta v2 implements the **overlay schedule** concept — separating work structure from calendar planning. This allows:

1. Creating plans without date binding (structure and dependencies only)
2. Adding calendar planning as an optional layer
3. Splitting large plans into multiple files (Plan Set)

### Comparison of v1 and v2

| Aspect | v1 | v2 |
|--------|----|----|
| Dates in nodes | `start`, `finish`, `duration` in `nodes` | Only in `schedule.nodes` |
| Calendar | `excludes` in `views` (gantt_views) | `excludes` in `schedule.calendars` |
| Plan without dates | Not possible for Gantt | Fully valid |
| Dependencies | `after` in `nodes` | `after` in `nodes` (unchanged) |
| Multi-file support | Separate plan/views files | Unified Plan Set with fragments |
| Effort estimation | Not supported | `effort` field (number) |

---

## Key Differences in v2

### 1. Fields `start`, `finish`, `duration` moved from nodes to schedule.nodes

**v1:** Calendar fields were directly in nodes.

```yaml
# v1
nodes:
  task1:
    title: "Task 1"
    start: "2024-03-01"
    duration: "5d"
```

**v2:** Calendar fields are in a separate `schedule.nodes` block.

```yaml
# v2
nodes:
  task1:
    title: "Task 1"

schedule:
  nodes:
    task1:
      start: "2024-03-01"
      duration: "5d"
```

### 2. Field `excludes` moved from views to schedule.calendars

**v1:** Calendar exclusions were set in views.

```yaml
# v1 (views.yaml)
gantt_views:
  main:
    excludes:
      - weekends
      - "2024-03-08"
```

**v2:** Exclusions are set in calendars within schedule.

```yaml
# v2
schedule:
  calendars:
    default:
      excludes:
        - weekends
        - "2024-03-08"
  default_calendar: default
```

### 3. Field `duration` removed from nodes

In v1, the `duration` field in nodes was used for date calculation. In v2, a separate `effort` field (number) is used for effort estimation, and `duration` is only available in `schedule.nodes`.

**v1:**
```yaml
nodes:
  task1:
    title: "Task"
    duration: "5d"  # Used for date calculation
```

**v2:**
```yaml
nodes:
  task1:
    title: "Task"
    effort: 5  # Abstract estimate (number)

schedule:
  nodes:
    task1:
      duration: "5d"  # For date calculation
```

### 4. Dependencies remain in nodes

The `after` field is still defined in `nodes`, **not** in `schedule.nodes`. This is important: dependency structure is separated from calendar planning.

```yaml
# v2 — correct
nodes:
  task1:
    title: "Task 1"
  task2:
    title: "Task 2"
    after: [task1]  # Dependencies in nodes

schedule:
  nodes:
    task1:
      start: "2024-03-01"
      duration: "3d"
    task2:
      duration: "5d"  # start computed from after in nodes
```

---

## Step-by-Step Migration Process

### Step 1: Update the version

Change `version: 1` to `version: 2` in the plan file.

```yaml
# Before
version: 1

# After
version: 2
```

### Step 2: Create the schedule block

Add an empty `schedule` block with `calendars` and `nodes` sub-blocks:

```yaml
schedule:
  calendars: {}
  nodes: {}
```

### Step 3: Move excludes from views to schedule.calendars

1. Find all `excludes` in your views (gantt_views)
2. Create a calendar in `schedule.calendars`
3. Specify `default_calendar`

**Before (v1):**
```yaml
# views.yaml
gantt_views:
  main:
    excludes:
      - weekends
      - "2024-03-08"
```

**After (v2):**
```yaml
schedule:
  calendars:
    default:
      excludes:
        - weekends
        - "2024-03-08"
  default_calendar: default
```

### Step 4: Move start/finish/duration from nodes to schedule.nodes

For each node with calendar fields:

1. Copy `start`, `finish`, `duration` to `schedule.nodes.<node_id>`
2. Remove these fields from `nodes.<node_id>`

**Before (v1):**
```yaml
nodes:
  task1:
    title: "Task 1"
    start: "2024-03-01"
    duration: "5d"
  task2:
    title: "Task 2"
    after: [task1]
    duration: "3d"
```

**After (v2):**
```yaml
nodes:
  task1:
    title: "Task 1"
  task2:
    title: "Task 2"
    after: [task1]  # Dependencies remain in nodes

schedule:
  nodes:
    task1:
      start: "2024-03-01"
      duration: "5d"
    task2:
      duration: "3d"
```

### Step 5: Remove excludes from views

Remove the `excludes` field from all views. In v2, this field is forbidden in views.

**Before (v1):**
```yaml
views:
  gantt:
    title: "Gantt Chart"
    excludes: [weekends]  # Remove!
```

**After (v2):**
```yaml
views:
  gantt:
    title: "Gantt Chart"
    # excludes removed — calendar is in schedule.calendars
```

### Step 6: (Optional) Add effort

If you want to use effort estimation, add the `effort` field (number) to nodes:

```yaml
meta:
  effort_unit: "sp"  # Unit of measure for UI

nodes:
  task1:
    title: "Task 1"
    effort: 5  # Story points, days, or other units
```

### Step 7: Merge files (optional)

In v2, you can merge `*.plan.yaml` and `*.views.yaml` into one file or split into multiple fragments by logic.

---

## Moving Calendar Fields from nodes to schedule.nodes

### Transfer Rules

| v1 Field (in nodes) | v2 Field (in schedule.nodes) |
|---------------------|------------------------------|
| `start` | `start` |
| `finish` | `finish` |
| `duration` | `duration` |

### Transfer Example

**v1:**
```yaml
nodes:
  design:
    title: "Design"
    start: "2024-03-01"
    duration: "5d"
  
  implementation:
    title: "Implementation"
    after: [design]
    duration: "10d"
  
  release:
    title: "Release"
    milestone: true
    after: [implementation]
```

**v2:**
```yaml
nodes:
  design:
    title: "Design"
  
  implementation:
    title: "Implementation"
    after: [design]  # Dependencies remain here
  
  release:
    title: "Release"
    milestone: true  # Milestone flag remains here
    after: [implementation]

schedule:
  calendars:
    default:
      excludes: [weekends]
  default_calendar: default
  
  nodes:
    design:
      start: "2024-03-01"
      duration: "5d"
    implementation:
      duration: "10d"
      # start computed from after: [design]
    release:
      # start computed from after: [implementation]
      # milestone: true is taken from nodes
```

### Important Notes

1. **`after` field remains in nodes** — don't move it to schedule.nodes
2. **`milestone` field remains in nodes** — it's a node characteristic, not schedule
3. **Nodes without dates** — if a node didn't have `start`/`duration` in v1, you don't need to add it to schedule.nodes

---

## Moving excludes from views to schedule.calendars

### Transfer Rules

1. Create a calendar in `schedule.calendars`
2. Move `excludes` values from views
3. Specify `default_calendar`
4. Remove `excludes` from views

### Transfer Example

**v1 (two files):**

```yaml
# project.plan.yaml
version: 1
meta:
  id: project
  title: "Project"

nodes:
  task1:
    title: "Task 1"
    start: "2024-03-01"
    duration: "5d"
```

```yaml
# project.views.yaml
version: 1
project: project

gantt_views:
  main:
    title: "Main View"
    excludes:
      - weekends
      - "2024-03-08"
      - "2024-05-01"
    lanes:
      dev:
        title: "Development"
        nodes: [task1]
```

**v2 (one file):**

```yaml
version: 2
meta:
  id: project
  title: "Project"

nodes:
  task1:
    title: "Task 1"

schedule:
  calendars:
    default:
      excludes:
        - weekends
        - "2024-03-08"
        - "2024-05-01"
  
  default_calendar: default
  
  nodes:
    task1:
      start: "2024-03-01"
      duration: "5d"

views:
  main:
    title: "Main View"
    # excludes removed!
    lanes:
      dev:
        title: "Development"
        nodes: [task1]
```

### Multiple Calendars

If different views in v1 had different `excludes`, create multiple calendars:

**v1:**
```yaml
gantt_views:
  team_a:
    excludes: [weekends]
  team_b:
    excludes:
      - weekends
      - "2024-03-08"
```

**v2:**
```yaml
schedule:
  calendars:
    standard:
      excludes: [weekends]
    with_holidays:
      excludes:
        - weekends
        - "2024-03-08"
  
  default_calendar: standard
  
  nodes:
    task_a:
      start: "2024-03-01"
      duration: "5d"
      calendar: standard
    task_b:
      start: "2024-03-01"
      duration: "5d"
      calendar: with_holidays
```

---

## Before/After Examples

### Example 1: Simple Plan

**v1:**
```yaml
version: 1
meta:
  id: simple
  title: "Simple Project"

statuses:
  not_started: { label: "Not Started" }
  done: { label: "Done" }

nodes:
  task1:
    title: "Analysis"
    status: not_started
    start: "2024-03-01"
    duration: "3d"
  
  task2:
    title: "Development"
    after: [task1]
    duration: "5d"
  
  task3:
    title: "Testing"
    after: [task2]
    duration: "2d"
```

```yaml
# simple.views.yaml
version: 1
project: simple

gantt_views:
  main:
    title: "Project Plan"
    excludes: [weekends]
    lanes:
      all:
        title: "All Tasks"
        nodes: [task1, task2, task3]
```

**v2:**
```yaml
version: 2
meta:
  id: simple
  title: "Simple Project"

statuses:
  not_started: { label: "Not Started" }
  done: { label: "Done" }

nodes:
  task1:
    title: "Analysis"
    status: not_started
  
  task2:
    title: "Development"
    after: [task1]
  
  task3:
    title: "Testing"
    after: [task2]

schedule:
  calendars:
    default:
      excludes: [weekends]
  
  default_calendar: default
  
  nodes:
    task1:
      start: "2024-03-01"
      duration: "3d"
    task2:
      duration: "5d"
    task3:
      duration: "2d"

views:
  main:
    title: "Project Plan"
    lanes:
      all:
        title: "All Tasks"
        nodes: [task1, task2, task3]
```

### Example 2: Plan with Milestones and Backward Planning

**v1:**
```yaml
version: 1
meta:
  id: release
  title: "Product Release"

nodes:
  prep:
    title: "Preparation"
    finish: "2024-03-15"
    duration: "5d"
  
  review:
    title: "Review"
    after: [prep]
    duration: "2d"
  
  release:
    title: "Release"
    milestone: true
    after: [review]
```

```yaml
# release.views.yaml
version: 1
project: release

gantt_views:
  timeline:
    excludes:
      - weekends
      - "2024-03-08"
```

**v2:**
```yaml
version: 2
meta:
  id: release
  title: "Product Release"

nodes:
  prep:
    title: "Preparation"
  
  review:
    title: "Review"
    after: [prep]
  
  release:
    title: "Release"
    milestone: true
    after: [review]

schedule:
  calendars:
    default:
      excludes:
        - weekends
        - "2024-03-08"
  
  default_calendar: default
  
  nodes:
    prep:
      finish: "2024-03-15"
      duration: "5d"
    review:
      duration: "2d"
    release:
      # start computed from after

views:
  timeline:
    title: "Release Timeline"
```

### Example 3: Plan with Partial Schedule

**v1:** In v1, all nodes with dates appeared on Gantt.

**v2:** You can have nodes without schedule — they won't appear on Gantt but will be in tree/list.

```yaml
version: 2
meta:
  id: backlog
  title: "Backlog with Partial Planning"
  effort_unit: "sp"

nodes:
  # Scheduled tasks
  sprint_task1:
    title: "Sprint Task 1"
    effort: 3
  
  sprint_task2:
    title: "Sprint Task 2"
    after: [sprint_task1]
    effort: 5
  
  # Unscheduled tasks (backlog)
  backlog_task1:
    title: "Future Idea"
    effort: 8
  
  backlog_task2:
    title: "Tech Debt"
    effort: 13

schedule:
  calendars:
    default:
      excludes: [weekends]
  default_calendar: default
  
  nodes:
    # Only current sprint tasks
    sprint_task1:
      start: "2024-03-01"
      duration: "3d"
    sprint_task2:
      duration: "5d"
    # backlog_task1 and backlog_task2 — not in schedule

views:
  gantt:
    title: "Sprint"
    where:
      has_schedule: true  # Only scheduled
  
  backlog:
    title: "Backlog"
    where:
      has_schedule: false  # Only unscheduled
    order_by: effort
```

---

## Common Problems and Solutions

### Problem 1: Error "start is not allowed in nodes"

**Cause:** The `start` field remained in a node after migration.

**Solution:** Move `start` to `schedule.nodes`:

```yaml
# Wrong
nodes:
  task1:
    title: "Task"
    start: "2024-03-01"  # Error!

# Correct
nodes:
  task1:
    title: "Task"

schedule:
  nodes:
    task1:
      start: "2024-03-01"
```

### Problem 2: Error "excludes is not allowed in views"

**Cause:** The `excludes` field remained in a view.

**Solution:** Move `excludes` to `schedule.calendars`:

```yaml
# Wrong
views:
  gantt:
    excludes: [weekends]  # Error!

# Correct
schedule:
  calendars:
    default:
      excludes: [weekends]
  default_calendar: default

views:
  gantt:
    title: "Gantt"
```

### Problem 3: Error "node 'X' in schedule.nodes does not exist in nodes"

**Cause:** A node is specified in `schedule.nodes` that doesn't exist in `nodes`.

**Solution:** Ensure all nodes in `schedule.nodes` are defined in `nodes`:

```yaml
# Wrong
nodes:
  task1:
    title: "Task 1"

schedule:
  nodes:
    task1:
      start: "2024-03-01"
    task2:  # Error: task2 not defined in nodes!
      start: "2024-03-05"

# Correct
nodes:
  task1:
    title: "Task 1"
  task2:
    title: "Task 2"

schedule:
  nodes:
    task1:
      start: "2024-03-01"
    task2:
      start: "2024-03-05"
```

### Problem 4: Error "calendar 'X' does not exist"

**Cause:** A non-existent calendar is specified in `schedule.nodes` or `default_calendar`.

**Solution:** Create the calendar in `schedule.calendars`:

```yaml
# Wrong
schedule:
  default_calendar: work  # Error: calendar 'work' not defined!
  nodes:
    task1:
      start: "2024-03-01"

# Correct
schedule:
  calendars:
    work:
      excludes: [weekends]
  default_calendar: work
  nodes:
    task1:
      start: "2024-03-01"
```

### Problem 5: Node doesn't appear on Gantt

**Cause:** The node is not added to `schedule.nodes`.

**Solution:** Add the node to `schedule.nodes` with dates:

```yaml
nodes:
  task1:
    title: "Task 1"

schedule:
  nodes:
    task1:  # Add node here
      start: "2024-03-01"
      duration: "5d"
```

### Problem 6: Dates are computed incorrectly

**Cause:** Dependencies `after` are specified in `schedule.nodes` instead of `nodes`.

**Solution:** Dependencies must be in `nodes`:

```yaml
# Wrong
nodes:
  task1:
    title: "Task 1"
  task2:
    title: "Task 2"

schedule:
  nodes:
    task1:
      start: "2024-03-01"
      duration: "3d"
    task2:
      after: [task1]  # Error: after is forbidden in schedule.nodes!
      duration: "5d"

# Correct
nodes:
  task1:
    title: "Task 1"
  task2:
    title: "Task 2"
    after: [task1]  # Dependencies in nodes

schedule:
  nodes:
    task1:
      start: "2024-03-01"
      duration: "3d"
    task2:
      duration: "5d"  # start computed from after in nodes
```

---

## Validating Migrated Plans

After migration, validate the plan using CLI:

### Validation Check

```bash
# Validate single file
opskarta validate plan.yaml

# Validate multiple files (Plan Set)
opskarta validate main.yaml nodes.yaml schedule.yaml
```

### Rendering Check

```bash
# Render tree (works without schedule)
opskarta render tree plan.yaml

# Render list
opskarta render list plan.yaml

# Render Gantt (requires schedule)
opskarta render gantt plan.yaml --view gantt

# Render dependency graph
opskarta render deps plan.yaml
```

### Migration Checklist

- [ ] Version changed to `2`
- [ ] Fields `start`, `finish`, `duration` moved from `nodes` to `schedule.nodes`
- [ ] Field `excludes` moved from `views` to `schedule.calendars`
- [ ] Created `default_calendar` (if using schedule)
- [ ] Dependencies `after` remain in `nodes`
- [ ] Flag `milestone` remains in `nodes`
- [ ] All `excludes` removed from `views`
- [ ] Plan passes validation (`opskarta validate`)
- [ ] Gantt renders correctly (`opskarta render gantt`)
- [ ] Dates are computed correctly

### Example Validator Output

**Successful validation:**
```
✓ Plan is valid
  Nodes: 5
  Scheduled nodes: 3
  Calendars: 1
```

**Validation errors:**
```
✗ Validation failed

[error] [validation] plan.yaml
  Node 'task1' contains forbidden field 'start'
  Expected: start should be in schedule.nodes.task1

[error] [validation] plan.yaml
  View 'gantt' contains forbidden field 'excludes'
  Expected: excludes should be in schedule.calendars
```

---

## Conclusion

Migration from v1 to v2 requires:

1. **Moving calendar fields** (`start`, `finish`, `duration`) from `nodes` to `schedule.nodes`
2. **Moving exclusions** (`excludes`) from `views` to `schedule.calendars`
3. **Keeping dependencies** (`after`) and flags (`milestone`) in `nodes`

The key advantage of v2 is the ability to work with plans without calendar planning. Work structure and dependencies exist independently of dates, simplifying early planning and backlog management.

For questions, refer to the [full v2 specification](SPEC.md).
