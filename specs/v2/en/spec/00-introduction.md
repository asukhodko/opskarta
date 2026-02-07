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
