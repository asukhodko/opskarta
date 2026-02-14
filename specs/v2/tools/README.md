# opskarta v2 Reference Tools

This directory contains reference tools for working with the opskarta v2 format.
The tools implement the "overlay schedule" concept where work structure (nodes) is
separated from calendar planning (schedule).

## Installing Dependencies

```bash
pip install -r requirements.txt
```

## Tools Overview

| Tool                          | Description                                                  |
|-------------------------------|--------------------------------------------------------------|
| `cli.py`                      | Command-line interface for validation and rendering          |
| `loader.py`                   | Fragment loading and merging (Plan Set)                      |
| `validator.py`                | Plan validation with structured error messages               |
| `scheduler.py`                | Schedule computation with calendar support                   |
| `effort.py`                   | Effort metrics computation (rollup, effective, gap)          |
| `render/`                     | Renderers (gantt, tree, list, deps)                          |
| `build_spec.py`               | Assembles spec parts (`<lang>/spec/*.md`) into `SPEC.md`    |
| `migrate_opskarta_v1_to_v2.py`| Migrates v1 plan/views files to v2 format                   |

---

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

# Render dependency graph (Mermaid flowchart, simple mode)
python -m tools.cli render deps plan.yaml

# Render dependency graph (hierarchical mode with subgraphs and status styling)
python -m tools.cli render deps plan.yaml --mode hierarchical --track epic-core --direction LR --wrap-column 28

# Render Gantt diagram (requires schedule and --view)
python -m tools.cli render gantt plan.yaml --view gantt-full --style plain

# Render Gantt with status decorations (emoji, Mermaid theme colors)
python -m tools.cli render gantt plan.yaml --view gantt-full --style status
```

Notes:
- `render gantt` requires `--view` (v2 spec behavior).
- `render deps` defaults to `--mode simple`; use `--mode hierarchical` for structured graph rendering.
- `--track` is only supported in `hierarchical` mode and can be repeated.

---

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

The loader performs:
- YAML parsing with `yaml.safe_load`
- Top-level block validation (only `version`, `meta`, `statuses`, `nodes`, `schedule`, `views`, `x` allowed)
- Deterministic merging with conflict detection (duplicate node_id, status_id, calendar_id, etc.)
- Forbidden field detection in nodes (`start`, `finish`, `duration`, `excludes` — moved to schedule)
- Source tracking: `plan.sources["node:task1"]` → `"nodes.plan.yaml"`

Exceptions:
- `LoadError` — file I/O, YAML parse errors, invalid top-level blocks
- `MergeConflictError` — duplicate IDs, meta field conflicts, multiple `default_calendar`

### Validation

```python
from tools.loader import load_plan_set
from tools.validator import validate, format_error

plan = load_plan_set(["plan.yaml"])
result = validate(plan)

if result.is_valid:
    print("Plan is valid!")
else:
    for error in result.errors:
        print(format_error(error))
```

The validator checks:
- Version must be `2`
- Required fields: `title` in every node
- Forbidden fields in nodes: `start`, `finish`, `duration`, `excludes`
- Effort format: must be a non-negative number (≥ 0)
- Reference integrity: `parent`, `after`, `status` must reference existing IDs
- Cyclic dependency detection in both `parent` hierarchy and `after` graph (DFS)
- Schedule references: every `schedule.nodes` key must exist in `nodes`; calendar references must exist
- `default_calendar` must reference an existing calendar
- Views: no `excludes` field; `where` filter type validation (`kind`, `status` as `list[str]`, `has_schedule` as `bool`, `parent` as existing node_id)
- Lanes validation: structure, required `nodes` field, node reference integrity

Structured error format via `format_error()`:
```
[error] [validation] [nodes.plan.yaml] Node 'task1' is missing required field 'title'
  path: nodes.task1.title
  value: missing
  expected: non-empty string
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

Algorithm (bottom-up tree traversal):
- Leaf nodes: `effort_effective = effort`
- Parent nodes: `effort_rollup = sum(child.effort_effective for each direct child)`
- `effort_effective = effort if set, else effort_rollup`
- `effort_gap = max(0, effort - effort_rollup)` — shows incomplete decomposition

### Schedule Computation

```python
from tools.loader import load_plan_set
from tools.scheduler import compute_schedule

plan = load_plan_set(["plan.yaml"])
compute_schedule(plan)

if plan.schedule:
    for node_id, sn in plan.schedule.nodes.items():
        print(f"{node_id}: {sn.computed_start} - {sn.computed_finish}")
    for warning in plan.schedule.warnings:
        print(f"Warning: {warning}")
```

Scheduler features:
- Only nodes present in `schedule.nodes` participate in calculation
- Dependencies (`after`) come from `nodes`, not `schedule.nodes`
- Only scheduled dependencies are considered for date propagation
- Calendar support: `weekends` exclusion and specific date exclusions (`YYYY-MM-DD`)
- Duration parsing: `Nd` (days), `Nw` (weeks = 5 working days)
- Backward scheduling: `finish` + `duration` → computed `start`
- Forward scheduling: `start` + `duration` → computed `finish`
- Dependency-driven scheduling: `start` = next workday after latest dependency `finish`
- Milestones: zero-duration, can land on dependency finish date
- Memoized computation to avoid redundant calculations
- Unschedulable node detection with warnings

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

# Dependency graph — simple mode (Mermaid flowchart)
print(render_deps(plan))

# Dependency graph — hierarchical mode
print(render_deps(plan, mode="hierarchical", tracks=["epic-core"], direction="LR", wrap_column=28))

# Gantt diagram — plain style (Mermaid)
print(render_gantt(plan, view_id="gantt-full", style="plain"))

# Gantt diagram — status style (with Mermaid init block and emoji)
print(render_gantt(plan, view_id="gantt-full", style="status"))
```

#### Tree Renderer (`render/tree.py`)

Generates hierarchical text output using Unicode box-drawing characters:
```
├── Phase 1 [in_progress] (10 sp)
│   ├── Task 1.1 [done]
│   └── Task 1.2 [in_progress]
└── Phase 2
    └── Task 2.1
```
- Shows status and effort (with `effort_unit` from meta) per node
- Applies `where` filter and `order_by` sorting from view

#### List Renderer (`render/list.py`)

Generates a flat list:
```
- Task 1 [done] (5 sp)
- Task 2 [in_progress] (3 sp)
- Task 3 (8 sp)
```
- Same filtering and sorting as tree

#### Dependency Renderer (`render/deps.py`)

Generates Mermaid flowcharts in two modes:

**Simple mode** (default): flat graph with `-->` edges for `after` dependencies.

**Hierarchical mode**: rich structured graph with:
- `subgraph` blocks for parent nodes that have visible children
- Dashed arrows (`-.->`) for parent decomposition
- Solid arrows (`-->`) for `after` dependencies
- Status-based `classDef` styling with colors from `statuses` or defaults
- Emoji prefixes for status (✅ done, 🔄 in_progress, ⛔ blocked)
- Issue reference in labels (shown below title)
- `--track` scoping: limits graph to a track node + its ancestors and descendants
- `--wrap-column` for label line wrapping via `<br/>`
- `--direction` (LR, TB, BT, RL)

#### Gantt Renderer (`render/gantt.py`)

Generates Mermaid Gantt diagrams with two styles:

**`plain` style**: neutral Gantt output.

**`status` style**: adds a `%%{init: ...}%%` block with theme colors mapped to statuses, plus emoji in task titles.

Additional features:
- `excludes` line from schedule calendar (weekends and specific dates)
- View format settings: `date_format`, `axis_format`, `tick_interval`
- `group_by: parent` — sections grouped by parent node title
- `lanes` — explicit lane-based sections with `title` and `nodes` list (no implicit "Other" section)
- Milestones rendered with `0d` duration

---

## Spec Builder (`build_spec.py`)

Assembles specification parts from `<lang>/spec/` into a single `SPEC.md`.

```bash
# Generate en/SPEC.md (default)
python tools/build_spec.py

# Generate ru/SPEC.md
python tools/build_spec.py --lang ru

# Check if SPEC.md is up-to-date (CI-friendly)
python tools/build_spec.py --lang en --check
```

Features:
- Finds `NN-*.md` files in `<lang>/spec/`, sorted by numeric prefix
- Extracts first-level headings for auto-generated table of contents
- Generates GitHub-compatible anchor links
- Duplicate prefix detection (fail-fast)
- Localized output (en/ru)
- `--check` mode for CI: exits with code 1 if `SPEC.md` is outdated

---

## Migration Tool (`migrate_opskarta_v1_to_v2.py`)

Converts v1 plan/views files to v2 format.

```bash
# Migrate to new files
python migrate_opskarta_v1_to_v2.py \
  --plan-in old.plan.yaml \
  --views-in old.views.yaml \
  --plan-out new.plan.yaml \
  --views-out new.views.yaml

# Migrate in-place with backup
python migrate_opskarta_v1_to_v2.py \
  --plan-in plan.yaml \
  --views-in views.yaml \
  --in-place --backup
```

What it does:
- **Plan file**:
  - `version: 1` → `2`
  - Moves `start`, `finish`, `duration` from `nodes.*` to `schedule.nodes.*`
  - Keeps `after` in nodes (dependencies stay in nodes in v2)
  - Creates `schedule.nodes` entry for any node that had `start`/`finish`/`duration`/`after`
  - Fail-fast on deprecated field `end` (v2 uses `finish`)
- **Views file**:
  - `version: 1` → `2`
  - `gantt_views` → `views`
  - Drops top-level `project`
  - Moves `excludes` to `plan.schedule.calendars.default.excludes`
  - Adds `where.has_schedule: true` to every migrated view
- **Cross-file validation**: checks that lane node references are valid after migration
- **YAML fidelity**: uses `ruamel.yaml` (if available) to preserve comments and formatting; falls back to PyYAML
- `--backup` creates timestamped `.bak` files before overwriting

---

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
  gantt-full:
    title: "Project Gantt"
    where:
      has_schedule: true
    group_by: parent
    date_format: "YYYY-MM-DD"
    axis_format: "%Y-%m"
  gantt-lanes:
    title: "Gantt by Team"
    where:
      has_schedule: true
    lanes:
      backend:
        title: "Backend Team"
        nodes: [api-design, api-impl, api-tests]
      frontend:
        title: "Frontend Team"
        nodes: [ui-design, ui-impl]
```

---

## Data Models (`models.py`)

| Class          | Description                                                    |
|----------------|----------------------------------------------------------------|
| `Meta`         | Plan metadata: `id`, `title`, `effort_unit`                    |
| `Status`       | Status definition: `label`, `color`                            |
| `Node`         | Work item: `title`, `kind`, `status`, `parent`, `after`, `milestone`, `issue`, `notes`, `effort`, `x` + computed effort fields |
| `ScheduleNode` | Scheduling info: `start`, `finish`, `duration`, `calendar` + computed dates |
| `Calendar`     | Calendar definition: `excludes` (weekends, specific dates)     |
| `Schedule`     | Schedule layer: `calendars`, `default_calendar`, `nodes`, `warnings` |
| `ViewFilter`   | Filter criteria: `kind`, `status`, `has_schedule`, `parent`    |
| `View`         | View config: `title`, `where`, `order_by`, `group_by`, `lanes`, format settings |
| `MergedPlan`   | Merged result: `version`, `meta`, `statuses`, `nodes`, `schedule`, `views`, `x`, `sources` |

---

## Dependencies

| Dependency   | Version | Purpose                | Required |
|--------------|---------|------------------------|----------|
| PyYAML       | >=6.0   | YAML file parsing      | Yes      |
| ruamel.yaml  | any     | Comment-preserving YAML (migration tool) | Optional |
| jsonschema   | >=4.0   | JSON Schema validation | Optional |
| pytest       | >=8.0   | Testing                | Dev only |

---

## Examples

Example files are in language-specific directories:

**Russian:**
- [`specs/v2/ru/examples/multi-file`](https://github.com/asukhodko/opskarta/tree/main/specs/v2/ru/examples/multi-file) — Multi-file plan
- [`specs/v2/ru/examples/no-schedule`](https://github.com/asukhodko/opskarta/tree/main/specs/v2/ru/examples/no-schedule) — Plan without schedule
- [`specs/v2/ru/examples/partial-schedule`](https://github.com/asukhodko/opskarta/tree/main/specs/v2/ru/examples/partial-schedule) — Partial schedule

**English:**
- [`specs/v2/en/examples/multi-file`](https://github.com/asukhodko/opskarta/tree/main/specs/v2/en/examples/multi-file) — Multi-file plan
- [`specs/v2/en/examples/no-schedule`](https://github.com/asukhodko/opskarta/tree/main/specs/v2/en/examples/no-schedule) — Plan without schedule
- [`specs/v2/en/examples/partial-schedule`](https://github.com/asukhodko/opskarta/tree/main/specs/v2/en/examples/partial-schedule) — Partial schedule

---

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
python -m tools.cli render gantt ru/examples/multi-file/*.plan.yaml --view gantt-full --style plain

# Render dependency graph (hierarchical)
python -m tools.cli render deps ru/examples/multi-file/*.plan.yaml --mode hierarchical --direction TB

# Run tests
python -m pytest tests/ -v
```
