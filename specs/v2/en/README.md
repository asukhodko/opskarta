# opskarta Specification v2

**Status**: Alpha
**Release**: Draft

## Overview

Version 2 of the opskarta specification implements the "overlay schedule" concept — separation of work structure (nodes) and calendar planning (schedule). This allows:

1. Creating plans without calendar dates (structure and dependencies only)
2. Adding calendar planning as an optional layer
3. Splitting large plans into multiple files (Plan Set)
4. Using views only for visualization, without affecting calculations

### Key Principles

- **Separation of Concerns**: work structure is separated from calendar planning
- **Opt-in Scheduling**: only explicitly included nodes participate in schedule calculation
- **Deterministic Merge**: fragment merging is deterministic, conflicts are errors
- **Views are Pure**: views don't affect calculations, only display

## Changes from v1

### New in v2

| Feature | v1 | v2 |
|---------|----|----|
| Multi-file plans | ❌ | ✅ Plan Set |
| Plans without dates | ❌ | ✅ Schedule is optional |
| Effort metrics | ❌ | ✅ effort, rollup, gap |
| Structural filtering | ❌ | ✅ view.where |
| Calendars | In views | In schedule.calendars |

### Moved Fields

| Field | v1 | v2 |
|-------|----|----|
| `start`, `finish`, `duration` | nodes | schedule.nodes |
| `excludes` | views | schedule.calendars |

### New Fields

| Field | Description |
|-------|-------------|
| `nodes.*.effort` | Abstract effort estimate (number ≥ 0) |
| `meta.effort_unit` | Display unit for UI ("sp", "points", "days") |
| `schedule.calendars` | Dictionary of calendars with exclusions |
| `schedule.default_calendar` | Default calendar |
| `view.where` | Structural filter (kind, status, has_schedule, parent) |

## Quick Links

- [Full Specification](SPEC.md)
- [Migration Guide from v1](MIGRATION.md)
- [Examples](examples/)
  - [multi-file/](examples/multi-file/) — multi-file plan
  - [no-schedule/](examples/no-schedule/) — plan without schedule
  - [partial-schedule/](examples/partial-schedule/) — partial schedule
- [JSON Schema](../schemas/)
- [Reference Tools](../tools/)

## Example: Plan without Schedule

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

This plan is valid without a `schedule` block. You can render tree/list/deps, but not Gantt.

## Example: Multi-file Plan

**main.plan.yaml**
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

**nodes.plan.yaml**
```yaml
version: 2

nodes:
  phase1:
    title: "Phase 1: Analysis"
    kind: phase
    effort: 10

  phase2:
    title: "Phase 2: Development"
    kind: phase
    after: [phase1]
    effort: 20
```

**schedule.plan.yaml**
```yaml
version: 2

schedule:
  calendars:
    default:
      excludes: [weekends, "2024-03-08"]

  default_calendar: default

  nodes:
    phase1:
      start: "2024-03-01"
      duration: "10d"

    phase2:
      duration: "20d"
      # start computed from after: [phase1]
```
