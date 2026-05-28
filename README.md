# opskarta

> OpsKarta — Operational map format for complex programs (plan‑as‑code).  
> OpsCarto — Operational cartography for programs: model once, render many views. *(synonym)*

**opskarta** — an open data format (YAML/JSON) for an *operational map of a program/project*: a single artifact where a manager captures their current interpretation of work structure and dependencies, then generates any number of views from it (Gantt, dependency graphs, checklists, reports, etc.).

Key idea: **"source of truth" — not Jira, not Confluence, not "in your head", but your version-controlled plan file**.

## Specification Versions

| Version | Status | Spec | Spec (compact) | Description |
|---------|--------|------|----------------|-------------|
| [v3](specs/v3/) | Alpha | [EN](specs/v3/en/SPEC.md) \| [RU](specs/v3/ru/SPEC.md) | [EN](specs/v3/en/SPEC.min.md) \| [RU](specs/v3/ru/SPEC.min.md) | Operational overlays: executive maps, report sections, Gantt windows, Markdown refresh tooling |
| [v2](specs/v2/) | Alpha | [EN](specs/v2/en/SPEC.md) \| [RU](specs/v2/ru/SPEC.md) | [EN](specs/v2/en/SPEC.min.md) \| [RU](specs/v2/ru/SPEC.min.md) | Overlay schedule concept — separation of work structure and calendar planning |
| [v1](specs/v1/) | Alpha | [EN](specs/v1/en/SPEC.md) \| [RU](specs/v1/ru/SPEC.md) | [EN](specs/v1/en/SPEC.min.md) \| [RU](specs/v1/ru/SPEC.min.md) | Initial specification version |

## What It Looks Like

Plan file (v3 format with separate structure and schedule):

```yaml
version: 3

meta:
  id: hello-upgrade
  title: "Example: Git Service Upgrade"

statuses:
  not_started: { label: "Not Started", color: "#9ca3af" }
  in_progress: { label: "In Progress", color: "#0ea5e9" }
  done:        { label: "Done",        color: "#22c55e" }

nodes:
  # Work structure — NO dates here, only hierarchy and dependencies
  root:
    title: "Git Service Upgrade"
    kind: summary
    status: in_progress

  prep:
    title: "Preparation"
    kind: phase
    parent: root
    status: in_progress
    effort: 10

  rollout:
    title: "Rollout"
    kind: phase
    parent: root
    deps: [prep]
    status: not_started
    effort: 5

  switch:
    title: "Traffic Switch"
    kind: task
    parent: rollout
    deps: [rollout]
    status: not_started
    notes: |
      Critical step. Rollback plan needed.

schedule:
  # Calendar planning — separate layer
  calendars:
    work:
      excludes: [weekends, "2026-02-16"]  # holiday
  
  default_calendar: work
  
  nodes:
    prep:
      start: "2026-02-02"
      duration: 10d
    rollout:
      duration: 5d
    switch:
      duration: 1d
```

Key concept: **work structure** (nodes with hierarchy, dependencies, effort) is separated from **calendar planning** (schedule with dates and calendars). This allows using the same plan for backlog management (no schedule), Gantt charts (with schedule), and v3 executive views (`x.exec`).

See the [full v3 specification](specs/v3/) for details.

## Quick Start

> All commands run from the **project root directory**.

### v3 (operational programs)

Use v3 when the plan is becoming a working center for syncs, executive views,
status documents, and focused Gantt windows. For simple plan-as-code with
tree/list/Gantt renders only, v2 remains a smaller starting point.

```bash
# Validate example
python -m specs.v3.tools.cli validate specs/v3/ru/examples/executive/release.plan.yaml

# Render executive flowchart
python -m specs.v3.tools.cli render executive specs/v3/ru/examples/executive/release.plan.yaml --view exec-top

# Render executive Markdown section
python -m specs.v3.tools.cli render executive-report specs/v3/ru/examples/executive/release.plan.yaml --section status --lang ru

# Render clipped Gantt diagram
python -m specs.v3.tools.cli render gantt specs/v3/ru/examples/executive/release.plan.yaml --view release-window --style status
```

### v2

```bash
# Validate example
python -m specs.v2.tools.cli validate specs/v2/ru/examples/multi-file/*.plan.yaml

# Render tree view
python -m specs.v2.tools.cli render tree specs/v2/ru/examples/no-schedule/backlog.plan.yaml

# Render Gantt diagram
python -m specs.v2.tools.cli render gantt specs/v2/ru/examples/multi-file/*.plan.yaml --view gantt-full
```

### v1

```bash
# Validate example
python specs/v1/tools/validate.py \
    specs/v1/en/examples/hello/hello.plan.yaml \
    specs/v1/en/examples/hello/hello.views.yaml

# Generate Mermaid Gantt
python -m specs.v1.tools.render.plan2gantt \
    --plan specs/v1/en/examples/hello/hello.plan.yaml \
    --views specs/v1/en/examples/hello/hello.views.yaml \
    --view overview
```

## Development Setup

The project uses Python 3.12+ and virtual environment (venv).

### Requirements

- Python 3.12+
- make (for automation)
- WSL (recommended for Windows) or Linux/macOS

### Installation

```bash
# Create virtual environment and install dependencies
make venv
make deps

# Activate venv (required for working with tools)
source venv/bin/activate

# Or one command for quick start
make quickstart
```

### Make Targets

> ⚠️ **Important**: All `make` commands must be run from the **project root directory** (where `Makefile` is located).
> If you get "No rule to make target" or import errors, check your current directory with `pwd`.

#### Setup
```bash
make venv          # Create virtual environment
make deps          # Install dependencies (pyyaml, jsonschema)
make deps-dev      # Install dev dependencies (pytest, ruff)
make quickstart    # Quick start: setup + validate example
```

#### v1 Specification
```bash
make spec-v1       # Build v1 SPEC.md (en + ru)
make check-spec-v1 # Check v1 SPEC.md is up-to-date
make validate-v1   # Validate v1 examples and schemas
make test-v1       # Run v1 tests (31 tests)
make ci-v1         # Full v1 CI: deps + check-spec + validate + test
```

#### v2 Specification
```bash
make spec-v2       # Build v2 SPEC.md (en + ru)
make check-spec-v2 # Check v2 SPEC.md is up-to-date
make validate-v2   # Validate v2 examples and schemas
make test-v2       # Run v2 tests (502 tests)
make ci-v2         # Full v2 CI: check-spec + validate + test
```

#### v3 Specification
```bash
make spec-v3       # Build v3 SPEC.md (en + ru)
make check-spec-v3 # Check v3 SPEC.md is up-to-date
make validate-v3   # Validate v3 examples and schemas
make test-v3       # Run v3 tests
make ci-v3         # Full v3 CI: check-spec + validate + test
```

#### Combined
```bash
make spec-all      # Build all SPEC.md files
make test-all      # Run all tests (v1 + v2 + v3)
make ci-all        # Full CI for all versions
make clean         # Clean generated files
make clean-all     # Clean everything including venv
```

#### Aliases (backward compatibility)
```bash
make spec-en       # Build v1 English spec
make spec-ru       # Build v1 Russian spec
make test          # Alias for test-v1
make ci            # Alias for ci-v1
```

### Important for Windows

Virtual environment is created with Unix structure (`venv/bin/`). For working:

- **Recommended**: use WSL (Windows Subsystem for Linux)
- Execute all `make` and `python` commands inside WSL
- Always activate venv before working: `source venv/bin/activate`

## Documentation

- [Philosophy and Method](docs/method.md) — why opskarta exists and how to use it
- [Contributing](CONTRIBUTING.md) — how to contribute to the project
- [Code of Conduct](CODE_OF_CONDUCT.md) — code of conduct
- [Security](SECURITY.md) — security policy
- [Changelog](CHANGELOG.md) — change history

## License

Apache License 2.0 — see [LICENSE](LICENSE) file.
