# Example: Partial-schedule

This example demonstrates a key capability of opskarta v2: **some nodes are scheduled for the current sprint, while others remain in the backlog without calendar dates**.

## What It Demonstrates

### Key Idea: Opt-in Scheduling

In v2, only nodes explicitly listed in `schedule.nodes` participate in calendar planning. Other nodes:

- ✅ Exist in the plan structure
- ✅ Have effort estimates
- ✅ Have dependencies (after)
- ✅ Appear in tree/list/deps views
- ❌ Have no calendar dates
- ❌ Don't appear on Gantt (unless filtered)

### When to Use Partial Scheduling

| Scenario | Description |
|----------|-------------|
| **Sprint planning** | Current sprint is scheduled, backlog is not |
| **Iterative development** | Near-term iterations are detailed, distant ones are not |
| **Planning horizon** | Detailed dates only for 2-4 weeks ahead |
| **Flexible planning** | Some work is fixed, some is floating |

## Files

| File | Description |
|------|-------------|
| `sprint.plan.yaml` | Sprint plan with partial schedule |

## Structure Overview

```
project (Mobile App) [89 sp]
│
├── auth (Authentication) [21 sp] — ENTIRE EPIC IN SPRINT
│   ├── auth-ui [3 sp]        ✓ scheduled
│   ├── auth-api [5 sp]       ✓ scheduled
│   ├── auth-oauth [8 sp]     ✓ scheduled
│   └── auth-2fa [5 sp]       ✓ scheduled
│
├── profile (User Profile) [13 sp] — PARTIALLY IN SPRINT
│   ├── profile-view [3 sp]   ✓ scheduled
│   ├── profile-edit [5 sp]   ✓ scheduled
│   ├── profile-privacy [3 sp] ✗ backlog
│   └── profile-export [2 sp]  ✗ backlog
│
├── notifications (Notifications) [21 sp] — ENTIRE EPIC IN BACKLOG
│   ├── notif-push [8 sp]     ✗ backlog
│   ├── notif-email [5 sp]    ✗ backlog
│   ├── notif-settings [3 sp] ✗ backlog
│   └── notif-history [5 sp]  ✗ backlog
│
├── social (Social Features) [34 sp] — ENTIRE EPIC IN BACKLOG
│   ├── social-friends [8 sp]  ✗ backlog
│   ├── social-feed [13 sp]    ✗ backlog
│   ├── social-sharing [8 sp]  ✗ backlog
│   └── social-comments [5 sp] ✗ backlog
│
└── mvp-release (Milestone)   ✓ scheduled
```

## Key Feature: `has_schedule` Filter

Views can filter nodes by schedule presence:

```yaml
views:
  # Only scheduled tasks (current sprint)
  sprint:
    title: "Current Sprint"
    where:
      has_schedule: true  # ONLY nodes from schedule.nodes

  # Only unscheduled tasks (backlog)
  backlog:
    title: "Backlog"
    where:
      has_schedule: false  # ONLY nodes NOT in schedule.nodes
```

This allows:
- Showing Gantt only for scheduled tasks
- Viewing backlog separately
- Tracking sprint progress vs overall progress

## Example Highlights

### Three Categories of Nodes

1. **Fully in sprint** — `auth` epic (all 4 tasks scheduled)
2. **Partially in sprint** — `profile` epic (2 of 4 tasks scheduled)
3. **Fully in backlog** — `notifications` and `social` epics

### Dependencies Between Scheduled and Unscheduled

```yaml
nodes:
  profile-edit:
    after: [profile-view]  # scheduled → scheduled ✓
  
  profile-privacy:
    after: [profile-edit]  # unscheduled → scheduled
    # profile-privacy is in backlog but depends on scheduled task
```

When `profile-privacy` is added to schedule, its start will be computed from `profile-edit.finish`.

### MVP Milestone

```yaml
nodes:
  mvp-release:
    after: [auth, profile]
    milestone: true

schedule:
  nodes:
    mvp-release: {}  # start computed from dependencies
```

The `mvp-release` milestone is scheduled and its date is computed from completion of `auth` and `profile` epics.

## Usage

### Validation

```bash
cd specs/v2

# Validate partial-schedule plan
python tools/cli.py validate en/examples/partial-schedule/sprint.plan.yaml
```

### Rendering Sprint

```bash
cd specs/v2

# Gantt diagram for sprint (only scheduled nodes)
python tools/cli.py render gantt en/examples/partial-schedule/sprint.plan.yaml --view gantt

# Sprint task list
python tools/cli.py render list en/examples/partial-schedule/sprint.plan.yaml --view sprint

# Sprint tree
python tools/cli.py render tree en/examples/partial-schedule/sprint.plan.yaml --view sprint
```

### Rendering Backlog

```bash
cd specs/v2

# Backlog task list
python tools/cli.py render list en/examples/partial-schedule/sprint.plan.yaml --view backlog

# Backlog tree
python tools/cli.py render tree en/examples/partial-schedule/sprint.plan.yaml --view backlog
```

### Full Plan

```bash
cd specs/v2

# Full project tree (all nodes)
python tools/cli.py render tree en/examples/partial-schedule/sprint.plan.yaml --view tree

# Dependency graph
python tools/cli.py render deps en/examples/partial-schedule/sprint.plan.yaml --view deps
```

## Typical Sprint Planning Workflow

### 1. Sprint Start

```yaml
# Add tasks to schedule.nodes
schedule:
  nodes:
    task-1:
      start: "2024-03-01"
      duration: "3d"
    task-2:
      duration: "5d"
```

### 2. During Sprint

- Use `sprint` view to track progress
- Use `backlog` view for grooming next sprint
- Gantt shows only current sprint

### 3. Sprint End

- Incomplete tasks remain in schedule (carried over)
- Or removed from schedule (returned to backlog)

### 4. Planning Next Sprint

```yaml
# Add new tasks from backlog
schedule:
  nodes:
    # Existing...
    
    # New from backlog:
    profile-privacy:
      duration: "3d"
    notif-push:
      duration: "6d"
```

## View Comparison

| View | has_schedule | What It Shows |
|------|--------------|---------------|
| `sprint` | `true` | Only current sprint tasks |
| `backlog` | `false` | Only backlog tasks |
| `tree` | not set | All project tasks |
| `gantt` | `true` | Gantt for sprint only |

## Effort Metrics

Even for unscheduled tasks, effort metrics are computed:

```yaml
# notifications epic (all in backlog):
# effort = 21 (explicitly set)
# effort_rollup = 8 + 5 + 3 + 5 = 21
# effort_gap = 0 (decomposition is complete)
```

This allows:
- Estimating backlog volume
- Planning capacity for next sprints
- Tracking progress by effort

## See Also

- [Schedule Specification](../../spec/30-schedule.md)
- [Views Specification](../../spec/40-views.md)
- [no-schedule example](../no-schedule/) — Plan without schedule
- [multi-file example](../multi-file/) — Multi-file plan
- [Migration guide from v1](../../MIGRATION.md)
