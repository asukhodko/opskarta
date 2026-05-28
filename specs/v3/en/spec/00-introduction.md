# opskarta v3 Specification

This specification describes the opskarta v3 format. It keeps the v2 base model — separate work structure (`nodes`), calendar planning (`schedule`), and factual progress (`execution`) — and adds an operational layer for real programs: executive maps, short Markdown report sections, and more useful Gantt slices.

- Serialization format: **YAML** (recommended) or JSON.
- Versioning: `version: 3` field in document root.
- Node identifiers: string keys in the `nodes:` map.

> Status: **Draft**. v3 is a compatible evolution of v2 for operational program work.

## Key Concepts of v3

### Overlay Schedule

The v2 base principle remains unchanged: work structure is separated from calendar planning.

| Aspect | v2/v3 |
|--------|-------|
| Dates | Only in `schedule.nodes` |
| Calendar | In `schedule.calendars` |
| Plan without dates | Fully valid |
| Dependencies | `deps` in `nodes` |

### Plan Set (Multi-file Structure)

Plans can be split into multiple files (fragments):

```
project/
├── main.plan.yaml      # meta, statuses
├── nodes.plan.yaml     # nodes
├── schedule.plan.yaml  # schedule
└── views.plan.yaml     # views
```

Fragments are merged into a single **Merged Plan** deterministically.

### Effort (Work Estimation)

The `effort` field defines an abstract work estimate in relative units:

```yaml
nodes:
  epic:
    title: "Authentication"
    effort: 13  # story points, days, or other units
```

The unit of measure is set in `meta.effort_unit` for UI display.

### Executive Overlay (`x.exec`)

v3 stabilizes a practice that appeared in real rollout plans: a detailed work graph often needs a short management slice next to it. The built-in `x.exec` profile is used for that:

- `blocks` collect high-level tracks on top of regular `nodes`;
- `target_gate` links a block to its nearest calendar gate;
- `mgmt.health` and `mgmt.sync_note` capture manual management signals;
- `views` define executive maps for different audiences.

## Document Structure

| File | Description |
|------|-------------|
| `10-plan-set.md` | Plan Set: multi-file structure, fragment merging |
| `20-nodes.md` | Nodes: work structure without calendar fields |
| `30-schedule.md` | Schedule: calendar planning layer |
| `25-execution.md` | Execution: progress tracking overlay |
| `35-executive.md` | Executive overlay: management maps and reports |
| `40-views.md` | Views: visualization representations |
| `45-profiles.md` | Profiles: extension namespace management |
| `50-validation.md` | Validation: rules and error messages |

## Allowed Top-Level Blocks

Each YAML file (fragment) can contain the following blocks:

| Block | Description | Required |
|-------|-------------|----------|
| `version` | Schema version (must be `3`) | Recommended |
| `meta` | Plan metadata | Optional |
| `statuses` | Status dictionary | Optional |
| `nodes` | Work node dictionary | Optional |
| `schedule` | Calendar planning layer | Optional |
| `views` | Visualization views | Optional |
| `execution` | Execution tracking overlay | Optional |
| `profiles` | Extension profile declarations | Optional |
| `x` | Extensions (namespace for custom fields) | Optional |

Any other top-level blocks are **errors**.

## Minimal Example

```yaml
version: 3
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
version: 3
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
    deps: [{id: phase1}]
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
      # start computed from deps in nodes

views:
  gantt:
    title: "Gantt Chart"
    where:
      has_schedule: true
```
