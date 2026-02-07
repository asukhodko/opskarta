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
