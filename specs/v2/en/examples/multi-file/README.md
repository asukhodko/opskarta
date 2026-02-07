# Example: Multi-file (multi-file plan)

This example demonstrates the **Plan Set** concept — splitting a plan into multiple files (fragments) that merge into a single plan.

## What It Demonstrates

### Plan Set Concept

- **Separation of concerns**: structure, schedule, and views in separate files
- **Deterministic merge**: file order doesn't affect the result
- **Source tracking**: errors indicate the source file

### Key v2 Features

- **Overlay Schedule**: schedule as a separate layer on top of structure
- **Dependencies in nodes**: `after` field is defined in nodes, not in schedule
- **Pure views**: views don't contain `excludes` (moved to calendars)
- **Effort without dates**: effort is estimated independently of calendar

## Files

| File | Content | Description |
|------|---------|-------------|
| `main.plan.yaml` | `meta`, `statuses`, `x` | Project metadata and statuses |
| `nodes.plan.yaml` | `nodes` | Work structure with hierarchy and dependencies |
| `schedule.plan.yaml` | `schedule` | Calendars and node scheduling |
| `views.plan.yaml` | `views` | Views for visualization |

## Plan Structure

```
project (Web Platform v1.0)
│
├── backend (Backend)
│   ├── api (REST API)
│   │   ├── api-auth
│   │   ├── api-tasks
│   │   └── api-projects
│   └── database (Database)
│       ├── db-schema
│       ├── db-migrations
│       └── db-indexes
│
├── frontend (Frontend)
│   ├── ui-components (UI Components)
│   │   ├── ui-design-system
│   │   ├── ui-forms
│   │   └── ui-tables
│   └── pages (Pages)
│       ├── page-dashboard
│       ├── page-tasks
│       └── page-settings
│
├── testing (Testing)
│   ├── e2e-tests
│   └── performance-tests
│
└── release-v1 (Release v1.0) [milestone]
```

## Usage

```bash
cd specs/v2

# Validate all plan files
python -m tools.cli validate en/examples/multi-file/*.plan.yaml

# Render Gantt
python -m tools.cli render gantt en/examples/multi-file/*.plan.yaml --view gantt-full

# Render tree
python -m tools.cli render tree en/examples/multi-file/*.plan.yaml

# Render dependencies
python -m tools.cli render deps en/examples/multi-file/*.plan.yaml --view deps
```

## See Also

- [Plan Set Specification](../../spec/10-plan-set.md)
- [Schedule Specification](../../spec/30-schedule.md)
- [Migration Guide from v1](../../MIGRATION.md)
