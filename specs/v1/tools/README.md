# opskarta v1 Reference Tools

This directory contains reference tools for working with the opskarta v1 format.
The tools are standalone and do not require package installation.

## Installing Dependencies

```bash
pip install -r requirements.txt
```

## Tools

### validate.py - Validator

Validates plan and views files against the specification.

**Usage:**

```bash
# Validate plan
python validate.py plan.yaml

# Validate plan and views
python validate.py plan.yaml views.yaml

# Validate with JSON Schema (requires jsonschema)
python validate.py --schema plan.yaml

# Specify custom schemas
python validate.py --schema --plan-schema custom.schema.json plan.yaml
```

**Validation levels:**

1. **Syntax** - YAML correctness
2. **Schema** - JSON Schema compliance (optional, with `--schema` flag)
3. **Semantics** - referential integrity, business rules

**Validated rules:**

- Required fields (`version`, `nodes`, `title` for nodes)
- Referential integrity (`parent`, `after`, `status`)
- No cyclic dependencies
- Scheduling field formats (`start`, `duration`)
- Matching `project` and `meta.id` for views

### build_spec.py - Specification Builder

Assembles specification parts from `<lang>/spec/` into a single `<lang>/SPEC.md` file.

**Usage:**

```bash
# Generate English SPEC.md (default)
python build_spec.py --lang en

# Generate Russian SPEC.md
python build_spec.py --lang ru

# Check if SPEC.md is up-to-date (for CI/CD)
python build_spec.py --lang en --check
python build_spec.py --lang ru --check
```

**Algorithm:**

1. Finds all `*.md` files in `spec/` with naming format `NN-*.md`
2. Sorts by numeric prefix
3. Extracts first-level headings for table of contents
4. Assembles into single file with automatic TOC

### render/plan2gantt.py - Mermaid Gantt Renderer

Generates Gantt diagrams in Mermaid format based on plan and views files.

**Usage:**

```bash
# Render diagram to stdout
python -m render.plan2gantt --plan plan.yaml --views views.yaml --view overview

# List available views
python -m render.plan2gantt --plan plan.yaml --views views.yaml --list-views

# Save to file
python -m render.plan2gantt --plan plan.yaml --views views.yaml --view overview --output gantt.md

# Output with markdown fence wrapper
python -m render.plan2gantt --plan plan.yaml --views views.yaml --view overview --markdown

# Combine: save to file with markdown fence
python -m render.plan2gantt --plan plan.yaml --views views.yaml --view overview --output gantt.md --markdown
```

**Features:**

- Automatic date calculation based on dependencies (`after`)
- Weekend exclusion support (`excludes: weekends`)
- Status-based color coding
- Emoji prefixes for visual status distinction
- Title fallback chain: view.title -> plan.meta.title -> "opskarta gantt"
- Extension support: `x.scheduling.anchor_to_parent_start` for parent-anchored scheduling

**Core scheduling algorithm:**

1. Explicit `start` (normalized to next workday if falls on excluded day)
2. `finish` + `duration` (backward planning)
3. `after` dependencies (start = next_workday(max_finish_deps))
4. Extension: `anchor_to_parent_start` (non-core, opt-in)
5. Otherwise: node is unscheduled (not rendered on Gantt)

### render/plan2dag.py - Mermaid DAG Renderer

Generates dependency graphs (DAG) as Mermaid flowcharts from plan files.

**Usage:**

```bash
# Render DAG flowchart to stdout
python -m render.plan2dag --plan plan.yaml

# Specify graph direction
python -m render.plan2dag --plan plan.yaml --direction LR

# Wrap node labels at specific column
python -m render.plan2dag --plan plan.yaml --wrap-column 26

# Filter to specific track(s)
python -m render.plan2dag --plan plan.yaml --track track-spirit-code

# Multiple tracks
python -m render.plan2dag --plan plan.yaml --track track-backend --track track-frontend

# Combined options
python -m render.plan2dag --plan plan.yaml --direction LR --wrap-column 26 --track track-spirit-code
```

**CLI options:**

| Option | Description |
|--------|-------------|
| `--plan` | Path to *.plan.yaml (required) |
| `--direction` | Graph direction: LR, TB, BT, RL (default: LR) |
| `--wrap-column` | Wrap node labels at this column (0 = no wrap) |
| `--track` | Limit diagram to specific track(s), can be repeated |

**Features:**

- Visualizes both decomposition hierarchy (parent-child) and dependency graph (after)
- Dashed arrows for parent relationships (structure)
- Solid arrows for after dependencies (flow)
- Status-based coloring with emoji prefixes
- Owner display (reads from `node.x.owner` or legacy `node.owner`)
- Smart arrow rendering that avoids redundant parent arrows when sibling dependencies exist
- Warnings for after-chains without anchor (no start/finish/end in closure)

## Dependencies

| Dependency | Version | Purpose | Required |
|------------|---------|---------|----------|
| PyYAML | >=6.0 | YAML file parsing | Yes |
| jsonschema | >=4.0 | JSON Schema validation | Optional |

## Examples

Example plan and views files are located in the language-specific directories:

**English (canonical):**
- [`../en/examples/minimal/`](../en/examples/minimal/) - minimal example (plan only)
- [`../en/examples/hello/`](../en/examples/hello/) - basic example with plan and views
- [`../en/examples/advanced/`](../en/examples/advanced/) - advanced example with multiple tracks

**Russian:**
- [`../ru/examples/minimal/`](../ru/examples/minimal/) - minimal example (plan only)
- [`../ru/examples/hello/`](../ru/examples/hello/) - basic example with plan and views
- [`../ru/examples/advanced/`](../ru/examples/advanced/) - advanced example with multiple tracks

### Quick Start

```bash
# Navigate to tools directory
cd specs/v1/tools

# Install dependencies
pip install -r requirements.txt

# Validate example (English)
python validate.py ../en/examples/hello/hello.plan.yaml ../en/examples/hello/hello.views.yaml

# Generate Gantt diagram
python -m render.plan2gantt \
    --plan ../en/examples/hello/hello.plan.yaml \
    --views ../en/examples/hello/hello.views.yaml \
    --view overview

# Generate DAG flowchart
python -m render.plan2dag \
    --plan ../en/examples/hello/hello.plan.yaml \
    --direction LR
```
