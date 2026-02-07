# opskarta v2 Reference Tools

This directory contains reference tools for working with the opskarta v2 format.
The tools implement the "overlay schedule" concept where work structure (nodes) is
separated from calendar planning (schedule).

## Installing Dependencies

```bash
pip install -r requirements.txt
```

## Tools Overview

| Tool | Description |
|------|-------------|
| `cli.py` | Command-line interface for validation and rendering |
| `loader.py` | Fragment loading and merging (Plan Set) |
| `validator.py` | Plan validation with structured error messages |
| `scheduler.py` | Schedule computation with calendar support |
| `effort.py` | Effort metrics computation (rollup, effective, gap) |
| `render/` | Renderers (gantt, tree, list, deps) |

## CLI Usage

### Validation

```bash
# Validate single file
python -m tools.cli validate plan.yaml

# Validate multi-file plan (Plan Set)
python -m tools.cli validate main.plan.yaml nodes.plan.yaml schedule.plan.yaml

# Validate with glob pattern
python -m tools.cli validate examples/multi-file/*.plan.yaml
```

### Rendering

```bash
# Render tree view (hierarchical structure)
python -m tools.cli render tree plan.yaml

# Render tree with view filter
python -m tools.cli render tree plan.yaml --view backlog

# Render list view (flat list)
python -m tools.cli render list plan.yaml

# Render list with sorting
python -m tools.cli render list plan.yaml --view sorted-by-effort

# Render dependency graph (Mermaid flowchart)
python -m tools.cli render deps plan.yaml

# Render Gantt diagram (requires schedule)
python -m tools.cli render gantt plan.yaml --view gantt-full
```

## Module Usage

### Loading Plans

```python
from tools.loader import load_plan_set

# Load single file
plan = load_plan_set(["plan.yaml"])

# Load multi-file plan
plan = load_plan_set([
    "main.plan.yaml",
    "nodes.plan.yaml", 
    "schedule.plan.yaml"
])

# Access merged data
print(plan.nodes)      # All nodes from all fragments
print(plan.schedule)   # Merged schedule (if any)
print(plan.sources)    # Source file for each element
```

### Validation

```python
from tools.loader import load_plan_set
from tools.validator import validate

plan = load_plan_set(["plan.yaml"])
result = validate(plan)

if result.is_valid:
    print("Plan is valid!")
else:
    for error in result.errors:
        print(f"Error: {error}")
```

### Effort Metrics

```python
from tools.loader import load_plan_set
from tools.effort import compute_effort_metrics

plan = load_plan_set(["plan.yaml"])
compute_effort_metrics(plan)

for node_id, node in plan.nodes.items():
    print(f"{node_id}:")
    print(f"  effort: {node.effort}")
    print(f"  effort_rollup: {node.effort_rollup}")
    print(f"  effort_effective: {node.effort_effective}")
    print(f"  effort_gap: {node.effort_gap}")
```

### Schedule Computation

```python
from tools.loader import load_plan_set
from tools.scheduler import compute_schedule

plan = load_plan_set(["plan.yaml"])
compute_schedule(plan)

if plan.schedule:
    for node_id, sn in plan.schedule.nodes.items():
        print(f"{node_id}: {sn.computed_start} - {sn.computed_finish}")
```

### Rendering

```python
from tools.loader import load_plan_set
from tools.render import render_tree, render_list, render_deps, render_gantt

plan = load_plan_set(["plan.yaml"])

# Tree view
print(render_tree(plan))

# Tree with view filter
print(render_tree(plan, view_id="backlog"))

# List view
print(render_list(plan))

# Dependency graph (Mermaid)
print(render_deps(plan))

# Gantt diagram (Mermaid)
print(render_gantt(plan, view_id="gantt-full"))
```

## Key Concepts

### Plan Set (Multi-file Plans)

v2 supports splitting plans into multiple YAML files (fragments):

```
project/
├── main.plan.yaml      # meta, statuses
├── nodes.plan.yaml     # work structure
├── schedule.plan.yaml  # calendar planning
└── views.plan.yaml     # visualization config
```

Fragments are merged deterministically. Conflicts (duplicate IDs) result in errors.

### Overlay Schedule

Nodes define work structure without calendar dates:

```yaml
nodes:
  task1:
    title: "Task 1"
    effort: 5
  task2:
    title: "Task 2"
    after: [task1]  # Dependencies in nodes
    effort: 3
```

Schedule is an optional layer:

```yaml
schedule:
  calendars:
    default:
      excludes: [weekends]
  default_calendar: default
  nodes:
    task1:
      start: "2024-03-01"
      duration: "5d"
    task2:
      duration: "3d"  # start computed from after
```

### Effort Metrics

- `effort` — Abstract effort estimate (number ≥ 0)
- `effort_rollup` — Sum of children's effort_effective
- `effort_effective` — effort if set, otherwise rollup
- `effort_gap` — max(0, effort - rollup), shows incomplete decomposition

### Pure Views

Views only affect visualization, not scheduling:

```yaml
views:
  backlog:
    title: "Backlog"
    where:
      has_schedule: false  # Only unscheduled nodes
    order_by: effort
```

## Dependencies

| Dependency | Version | Purpose | Required |
|------------|---------|---------|----------|
| PyYAML | >=6.0 | YAML file parsing | Yes |
| jsonschema | >=4.0 | JSON Schema validation | Optional |
| pytest | >=8.0 | Testing | Dev only |

## Examples

Example files are in language-specific directories:

**Russian:**
- [`../ru/examples/multi-file/`](../ru/examples/multi-file/) — Multi-file plan
- [`../ru/examples/no-schedule/`](../ru/examples/no-schedule/) — Plan without schedule
- [`../ru/examples/partial-schedule/`](../ru/examples/partial-schedule/) — Partial schedule

**English:**
- [`../en/examples/multi-file/`](../en/examples/multi-file/) — Multi-file plan
- [`../en/examples/no-schedule/`](../en/examples/no-schedule/) — Plan without schedule
- [`../en/examples/partial-schedule/`](../en/examples/partial-schedule/) — Partial schedule

## Quick Start

```bash
# Navigate to v2 directory
cd specs/v2

# Install dependencies
pip install -r tools/requirements.txt

# Validate example
python -m tools.cli validate ru/examples/multi-file/*.plan.yaml

# Render tree
python -m tools.cli render tree ru/examples/no-schedule/backlog.plan.yaml

# Render Gantt
python -m tools.cli render gantt ru/examples/multi-file/*.plan.yaml --view gantt-full

# Run tests
python -m pytest tests/ -v
```
