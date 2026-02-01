# Scheduling (`start`, `duration`, `after`, `excludes`)

Scheduling fields allow you to set temporal characteristics of nodes and dependencies between them.

## Terms

- **View calendar (calendar(view))** — a function that determines which days are considered workdays for a given view. Depends on the `excludes` parameter in the view.
- **Workday** — a day that is NOT excluded by the view calendar. With `excludes: ["weekends"]`, workdays are Mon–Fri. With empty `excludes`, any calendar day is a workday.
- **Core excludes** — values in `excludes` that affect date calculation: `"weekends"` and dates in `YYYY-MM-DD` format.
- **Non-core excludes** — other values in `excludes` (not standardized); portable tools MUST ignore them with a warning.
- **Scheduled node** — a node for which a start date (`start`) can be computed. Such nodes are displayed on the timeline.
- **Unscheduled node** — a node without explicit `start`, without `finish`, and without computable `start` via `after`. Such nodes are NOT displayed on the timeline.
- **Effective start (effective_start)** — normalized start date used in calculations. If a node's `start` falls on an excluded day (and node is not a milestone), effective start is shifted to the next workday.

> **Important:** schedule is computed for each view separately. The plan stores constraints, views apply calendar rules. The same node may have different computed dates in different views with different `excludes`.

## Scheduling Fields

### `start` *(string, YYYY-MM-DD)*

Planned work start date. Format: ISO 8601 date, e.g. `2024-03-15`.

- If `start` is specified, node is considered **scheduled**.
- `start` MUST be a string in `YYYY-MM-DD` format.

### `duration` *(string)*

Work duration. Format: `<number><unit>`, where:

- `d` — days (e.g., `5d` = 5 workdays)
- `w` — weeks (e.g., `2w` = 2 weeks)

**Semantics of unit `d` (days):**

- `Nd` means N **workdays** according to the view calendar.
- With empty `excludes` → workday = any calendar day (i.e., `5d` = 5 calendar days).
- With `excludes: ["weekends"]` → workday = Mon–Fri (i.e., `5d` = 5 weekdays).

**Semantics of unit `w` (weeks):**

- `1w` = 5 workdays (not 7 calendar days).
- With `excludes: ["weekends"]` in the view, a week remains equal to 5 workdays.
- Example: `2w` = 10 workdays.

**Rules:**

- Number MUST be a positive integer (≥ 1).
- Format MUST match regex: `^[1-9][0-9]*[dw]$`.
- `duration` without `start` or `after` does not define timeline position, but may be used for effort estimation.

**Default value:**

- If `duration` is not specified for a scheduled node (having `start` or computable `start` via `after`), core tools MUST use default value `1d`.
- This ensures ability to compute `finish` and `start from after` for all scheduled nodes.

### `finish` *(string, YYYY-MM-DD)*

Target completion date or deadline. Format: ISO 8601 date, e.g. `2024-03-15`.

**Behavior:**

1. **If `finish` and `duration` are specified, but no `start`:**
   - `start` is computed "backward" from `finish` by subtracting workdays.
   - Example: `finish: 2024-03-15`, `duration: 5d` → `start: 2024-03-11` (or earlier, if there are excludes).

2. **If `start` and `finish` are specified, but no `duration`:**
   - `duration` is computed as the number of workdays between dates.
   - Example: `start: 2024-03-11`, `finish: 2024-03-15` → `duration: 5d` (without excludes).

3. **If all three (`start`, `finish`, `duration`) are specified:**
   - They MUST be consistent (computed `finish` from `start+duration` must match specified `finish`).
   - Inconsistency is an **error**.

**Example:**

```yaml
nodes:
  release_prep:
    title: "Release Preparation"
    finish: "2024-03-15"  # Deadline
    duration: "5d"
    # start is computed backward: 2024-03-11 (5 workdays: 11, 12, 13, 14, 15)
```

### `after` *(list[string])*

List of dependency node IDs.

**Semantics:** node can start only after **all** nodes from the `after` list are completed.

## Date Computation

### Finish Date

Finish date is computed by formula:

```
finish = start + (duration_days - 1)
```

where `duration_days` — duration in workdays.

**Explanation:** start day (`start`) is included in the duration. A node with `duration: 1d` starts and finishes on the same day.

**Examples:**

| start | duration | finish | Explanation |
|-------|----------|--------|-------------|
| 2024-03-01 | 1d | 2024-03-01 | One day of work |
| 2024-03-01 | 5d | 2024-03-05 | Five days: 01, 02, 03, 04, 05 |
| 2024-03-01 (Fri) | 5d (no excludes) | 2024-03-05 | Calendar days |
| 2024-03-01 (Fri) | 5d (with excludes: weekends) | 2024-03-07 | Workdays: Fri, Mon, Tue, Wed, Thu |

### Computing start from after

If `start` is not specified but `after` is, start date is computed as:

```
start = max(finish for all dependencies) + 1 workday
```

**Algorithm:**

1. For each dependency in `after`, compute its `finish`.
2. Find maximum `finish` date among all dependencies.
3. Add 1 workday (considering `excludes`, if applicable).

**Example (without excludes — calendar days):**

```yaml
nodes:
  task_a:
    title: "Task A"
    start: "2024-03-04"    # Monday
    duration: "3d"
    # finish = 2024-03-06 (Mon, Tue, Wed)

  task_b:
    title: "Task B"
    after: [task_a]
    duration: "2d"
    # start = 2024-03-07 (Thu), finish = 2024-03-08 (Fri)
```

### Special Rule for Milestones

If a node with `after` is a milestone (`milestone: true`), start date is computed **without adding the next workday**:

```
start = max(finish for all dependencies)
```

This is because a milestone marks the moment of completion of preceding work, not the start of new work.

**Example:**

```yaml
nodes:
  feature:
    title: "Feature Development"
    start: "2024-03-01"
    duration: "5d"
    # finish = 2024-03-05

  release:
    title: "Release"
    milestone: true
    after: [feature]
    # start = 2024-03-05 (NOT 2024-03-06!)
    # Milestone marks the moment of feature completion
```

**Comparison:**

| Node Type | start from after Formula |
|-----------|--------------------------|
| Regular node | `next_workday(max_finish)` |
| Milestone (`milestone: true`) | `max_finish` |

### Simultaneous start and after

If a node has both `start` and `after`:

- **`start` takes priority** — the explicitly specified date is used.
- **`after` becomes a logical dependency** — displayed as a link (arrow) on the diagram, but does not affect start date.

**Example:**

```yaml
nodes:
  dependency:
    title: "Dependency"
    start: "2024-03-01"
    duration: "5d"
    # finish = 2024-03-05

  task_with_both:
    title: "Task with Explicit Start"
    start: "2024-03-04"  # Explicit date (before dependency finish!)
    after: [dependency]   # Logical link for diagram
    duration: "3d"
    # start = 2024-03-04 (explicit start is used, not computed)
    # finish = 2024-03-06
```

In this example, `task_with_both` will start on 03/04, although `dependency` finishes on 03/05. This may be intentional (e.g., parallel work) or a planning error — tools MAY issue a warning.

### Normalizing start on Excluded Day

If a node's `start` falls on an excluded day (e.g., weekend or holiday) and node is NOT a milestone:

1. Scheduler MUST normalize `start` to the next workday.
2. Scheduler MUST issue a warning: "start fell on excluded day, normalized to next workday".
3. For calculations, normalized `effective_start` is used, not the original `start`.

**Example:**

```yaml
# In view: excludes: ["weekends", "2024-03-08"]

nodes:
  task:
    title: "Task Starting on Weekend"
    start: "2024-03-02"  # Saturday
    duration: "3d"
    # Effective start: 2024-03-04 (Monday)
    # Warning: "start 2024-03-02 — excluded day, normalized to 2024-03-04"
    # finish = 2024-03-06 (3 workdays from Monday)
```

**For milestones:** normalization is NOT applied. Milestones can be pinned to any date, including excluded days.

### finish Field on Excluded Day

If a node's `finish` falls on an excluded day (weekend or holiday):

1. **For regular tasks**: tool MUST issue a warning "finish fell on excluded day".
   - `finish` is **NOT automatically normalized** (unlike `start`).
   - This allows using `finish` as a "deadline" on a specific calendar date.

2. **For milestones**: no warning is issued. Milestones can be pinned to any date.

3. **When computing dependencies** (`after`): if a dependency has `finish` on an excluded day, `next_workday(finish)` function will correctly find the next workday, skipping excluded days.

**Example:**

```yaml
# In view: excludes: ["weekends"]

nodes:
  urgent_task:
    title: "Urgent Task"
    start: "2024-03-04"  # Monday
    finish: "2024-03-09"  # Saturday — WARNING: finish on excluded day
    # duration is computed by workdays between 04 and 09 = 5d (Mon-Fri)
    
  next_task:
    title: "Next Task"
    after: [urgent_task]
    duration: "2d"
    # start = next_workday(2024-03-09) = 2024-03-11 (Monday)
```

### Computing start from finish (backward scheduling)

If `start` is not specified but `finish` and `duration` are:

1. Compute number of workdays from `duration`.
2. Subtract workdays from `finish`, going backward.
3. Result is computed `start`.

**Algorithm:**

```
start = sub_workdays(finish, duration_days - 1)
```

where `sub_workdays(finish, n)` goes back n workdays from finish, skipping excluded days.

**Example:**

```yaml
# In view: excludes: ["weekends"]

nodes:
  release_prep:
    title: "Release Preparation"
    finish: "2024-03-15"  # Friday
    duration: "5d"
    # Go back 5 workdays: Fri(15), Thu(14), Wed(13), Tue(12), Mon(11)
    # start = 2024-03-11 (Monday)
```

### Unscheduled Nodes

A node is considered **unscheduled** if:

1. `start` is absent, AND
2. `after` is absent, OR all dependencies in `after` are themselves unscheduled.

**Core behavior:** unscheduled nodes are NOT displayed on the Gantt timeline. This is a normative rule for all tools.

> **Note:** renderers MAY provide extensions (e.g., `x.scheduling.anchor_to_parent_start`) for optional date inheritance from parent nodes. Such extensions are non-core and MUST be documented separately.

## Calendar Exclusions (excludes)

The `excludes` parameter is set at view level (`gantt_views`) and affects date calculation.

### Core excludes (affect calculation)

The following values in `excludes` are **core** and MUST affect date computation in portable tools:

1. `"weekends"` — exclude Saturday and Sunday from workdays.
2. **Specific dates in `YYYY-MM-DD` format** — exclude specified days (holidays, office closures, etc.).

**Example:**

```yaml
gantt_views:
  main:
    excludes:
      - weekends
      - "2024-03-08"  # International Women's Day (holiday)
      - "2024-05-01"  # Labor Day
```

### Non-core excludes

Any other values in `excludes` (e.g., `"monday"`, arbitrary tokens) are **non-core**:

- Portable tools MUST ignore them.
- Portable tools MUST issue a warning: "unknown exclude value '<value>' is non-core and ignored".
- Renderer-specific tools MAY support them as extensions (MUST be documented).

**Why this matters:** this prevents calendar divergence when different tools compute different schedules for the same plan.

### Effect on Calculations

With core excludes:

1. **`"weekends"`**: Saturday and Sunday are skipped in workday calculations.
2. **`YYYY-MM-DD` dates**: specified dates are skipped in workday calculations.
3. **Duration** is counted in workdays (excluding weekends and specified dates).
4. **Finish date** skips excluded days.
5. **Next workday** after dependency skips excluded days.

**Example with holiday:**

```yaml
# In view: excludes: ["weekends", "2024-03-08"]

nodes:
  task:
    title: "Task with Holiday"
    start: "2024-03-07"  # Thursday
    duration: "3d"
    # Workdays: Thu(07), skip Fri(08, holiday), skip Sat-Sun, Mon(11), Tue(12)
    # finish = 2024-03-12 (Tuesday)
```

**Example with weekends:**

```yaml
# In view: excludes: ["weekends"]

nodes:
  friday_task:
    title: "Starting Friday"
    start: "2024-03-01"  # Friday
    duration: "3d"
    # Workdays: Fri (01), Mon (04), Tue (05)
    # finish = 2024-03-05 (Tuesday)

  next_task:
    title: "After friday_task"
    after: [friday_task]
    duration: "2d"
    # start = 2024-03-06 (Wednesday)
    # finish = 2024-03-07 (Thursday)
```

## Examples

### Node with Fixed Start Date

```yaml
nodes:
  kickoff:
    title: "Kickoff"
    start: "2024-03-01"
    duration: "1d"
```

### Node with Dependency

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
```

In this example, `implementation` can start only after `design` is completed.

### Node with Multiple Dependencies

```yaml
nodes:
  backend:
    title: "Backend API"
    start: "2024-03-01"
    duration: "5d"

  frontend:
    title: "Frontend UI"
    start: "2024-03-01"
    duration: "3d"

  integration:
    title: "Integration"
    after: [backend, frontend]
    duration: "2d"
```

Node `integration` waits for completion of **both** `backend` and `frontend`. Its `start` will be computed as the next day after `max(finish(backend), finish(frontend))`.

### Node with Duration in Weeks

```yaml
nodes:
  sprint:
    title: "Development Sprint"
    start: "2024-03-04"  # Monday
    duration: "2w"       # = 10 workdays
    # finish = 2024-03-15 (Friday of second week)
```

## Interaction with Views

Scheduling fields are used by renderers to build timeline diagrams:

- **Gantt charts**: `start` and `duration` determine position and length of node bar on timeline.
- **Dependencies**: `after` is displayed as arrows between nodes.
- **Calendar exclusions**: `excludes` parameter in `gantt_views` affects date calculation when `duration` is present.

## Canonical Scheduling Algorithm (pseudocode)

This section defines the canonical schedule computation algorithm. Independent implementations following this algorithm MUST produce identical results.

### Primitives

```python
def is_workday(d: date, excludes: list) -> bool:
    """Checks if date is a workday (not excluded)."""
    # Check weekends
    if "weekends" in excludes and d.weekday() in [5, 6]:  # Sat=5, Sun=6
        return False
    
    # Check specific dates (YYYY-MM-DD)
    if d.isoformat() in excludes:  # format YYYY-MM-DD
        return False
    
    return True


def next_workday(d: date, excludes: list) -> date:
    """Finds the next workday after d (d+1, skipping excluded days)."""
    cur = d + timedelta(days=1)
    while not is_workday(cur, excludes):
        cur += timedelta(days=1)
    return cur


def add_workdays(start: date, n: int, excludes: list) -> date:
    """Adds n workdays to start."""
    cur = start
    added = 0
    while added < n:
        cur += timedelta(days=1)
        if is_workday(cur, excludes):
            added += 1
    return cur


def sub_workdays(finish: date, n: int, excludes: list) -> date:
    """Subtracts n workdays from finish (goes backward)."""
    cur = finish
    subtracted = 0
    while subtracted < n:
        cur -= timedelta(days=1)
        if is_workday(cur, excludes):
            subtracted += 1
    return cur


def normalize_start(start: date, excludes: list, is_milestone: bool) -> date:
    """Normalizes start to next workday if it falls on excluded day."""
    if is_milestone:
        return start  # Milestones are not normalized
    if not is_workday(start, excludes):
        # Find next workday
        cur = start
        while not is_workday(cur, excludes):
            cur += timedelta(days=1)
        # SHOULD issue warning: "start fell on excluded day, normalized"
        return cur
    return start


def compute_start_from_after(dependencies_finishes: list[date], excludes: list, is_milestone: bool) -> date:
    """Computes start for node with after dependencies."""
    max_finish = max(dependencies_finishes)
    if is_milestone:
        # Milestones start on the day dependencies finish
        return max_finish
    else:
        # Regular nodes start on the next workday
        return next_workday(max_finish, excludes)
```

### start Computation Priority

When computing `start` for a node, the following priority is used:

1. **Explicit `start`** (if specified): use it (after normalization if fell on excluded day).
2. **Explicit `finish` + `duration`** (if `start` is absent): compute `start = sub_workdays(finish, duration - 1)`.
3. **Dependencies `after`** (if `start` and `finish` are absent):
   - For **regular nodes**: `start = next_workday(max_finish_of_dependencies)`.
   - For **milestones** (`milestone: true`): `start = max_finish_of_dependencies` (without +1 day).
4. **Otherwise**: node is unscheduled (no start).

### Consistency Check

If all three fields (`start`, `finish`, `duration`) are specified:

```python
computed_finish = add_workdays(start, duration - 1, excludes)
if computed_finish != finish:
    # ERROR: inconsistent start/finish/duration
```

### Dependencies Outside View

When computing schedule for a view, dependency resolution (`after`) MUST consider ALL nodes in the plan, even if they are not displayed in the current view.

**Why:** this ensures that "slices" of the plan into multiple views don't break dependency chains.

## Migration from Model with `end` (exclusive)

Some planning systems use `end` as exclusive interval boundary (i.e., work goes UP TO the specified date, but not including it). opskarta uses `finish` as **inclusive** date — work includes the `finish` day.

### Conversion Formula

```
finish_opskarta = prev_workday(end_exclusive, calendar)
```

where `prev_workday` finds the previous workday considering the view calendar (excludes).

**Important:** you cannot simply subtract 1 calendar day. You need to find the **previous workday** considering calendar exclusions.

### Example

| Original Model | opskarta |
|----------------|----------|
| `end: 2024-03-18` (Mon, exclusive) | `finish: 2024-03-15` (Fri, inclusive) |
| Work goes until the 18th, not including | Work finishes on the 15th (Friday) |

With `excludes: ["weekends"]`, if `end = 2024-03-18` (Monday), then `finish = 2024-03-15` (Friday), because 16-17 are weekends.

### Algorithm

```python
def prev_workday(d: date, excludes: list) -> date:
    """Finds the previous workday (d-1, skipping excluded days backward)."""
    cur = d - timedelta(days=1)
    while not is_workday(cur, excludes):
        cur -= timedelta(days=1)
    return cur


def convert_end_to_finish(end_exclusive: date, excludes: list) -> date:
    """Converts end (exclusive) to finish (inclusive)."""
    return prev_workday(end_exclusive, excludes)
```

### Migration Correctness Check

After migration, ensure that:

1. Number of workdays (`duration`) remains unchanged.
2. Dependent tasks (`after`) start on the same day as before.
3. Milestones pinned to deadlines correctly point to the needed date.
