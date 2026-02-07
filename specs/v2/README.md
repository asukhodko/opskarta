# opskarta Specification v2

This directory contains the opskarta v2 specification implementing the "overlay schedule" concept.

## Key Concepts

opskarta v2 introduces a fundamental separation between:
- **Nodes** — Work structure (tasks, phases, milestones) without calendar dates
- **Schedule** — Optional calendar planning layer applied on top of nodes

This allows plans to be valid and useful without calendar dates, with scheduling added as an optional overlay.

## Languages

| Language | Directory | Description |
|----------|-----------|-------------|
| **English** | [en/](en/) | English specification |
| **Russian** | [ru/](ru/) | Russian specification (primary) |

## Structure

```
specs/v2/
├── ru/                     # Russian (primary)
│   ├── SPEC.md             # Full specification
│   ├── MIGRATION.md        # Migration guide from v1
│   ├── README.md
│   ├── spec/               # Source sections
│   └── examples/           # Example files
│       ├── multi-file/     # Multi-file plan example
│       ├── no-schedule/    # Plan without schedule
│       └── partial-schedule/ # Partial schedule example
├── schemas/                # JSON Schemas
│   ├── fragment.schema.json    # Schema for individual YAML files
│   └── merged-plan.schema.json # Schema for merged plan
├── tests/                  # Test suite
└── tools/                  # Implementation tools
    ├── models.py           # Data models
    ├── loader.py           # Fragment loading and merging
    ├── validator.py        # Plan validation
    ├── effort.py           # Effort metrics computation
    ├── scheduler.py        # Schedule computation
    ├── cli.py              # Command-line interface
    └── render/             # Renderers (gantt, tree, list, deps)
```

## What's New in v2

### Overlay Schedule
- Nodes define work structure and dependencies (`after`)
- Schedule is an optional layer with calendar dates
- Only nodes explicitly included in `schedule.nodes` are scheduled

### Multi-file Plans (Plan Set)
- Split large plans into multiple YAML files (fragments)
- Deterministic merge with conflict detection
- Track source file for each element

### Effort Metrics
- Abstract effort values (numbers) without calendar binding
- Automatic rollup computation for parent nodes
- Gap detection for incomplete decomposition

### Pure Views
- Views only affect visualization, not scheduling
- `excludes` moved from views to `schedule.calendars`
- Structural filtering with `where` object

## Quick Start

```bash
# Validate a plan (single or multiple files)
python tools/cli.py validate plan.yaml

# Validate multi-file plan
python tools/cli.py validate main.plan.yaml nodes.plan.yaml schedule.plan.yaml

# Render Gantt diagram
python tools/cli.py render gantt plan.yaml --view default

# Render tree view
python tools/cli.py render tree plan.yaml

# Render dependency graph
python tools/cli.py render deps plan.yaml
```

## Migration from v1

See [ru/MIGRATION.md](ru/MIGRATION.md) for detailed migration guide:
- Move `start`, `finish`, `duration` from nodes to `schedule.nodes`
- Move `excludes` from views to `schedule.calendars`
- Convert `duration` to `effort` (manual, if needed)

## Tools

See [tools/](tools/) for implementation:
- `loader.py` — Load and merge plan fragments
- `validator.py` — Validate merged plans
- `scheduler.py` — Compute schedule dates
- `render/` — Various renderers (Gantt, tree, list, deps)
