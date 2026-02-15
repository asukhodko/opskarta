# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

opskarta is an open data format (YAML/JSON) and reference Python toolset for operational planning. It provides a "plan-as-code" approach: work structure and dependencies are stored in version-controlled YAML files, separate from task trackers like Jira. Two specification versions exist (v1 and v2); v2 is the active development target.

The core v2 innovation is the **overlay schedule** — nodes define work structure (hierarchy, dependencies, effort, status) without dates, and an optional schedule layer adds calendar planning on top.

Primary language of documentation is Russian; English translations are maintained in parallel.

## Build & Test Commands

Requires Python 3.12+, make, and WSL on Windows.

```bash
# Setup
make venv                # Create virtual environment
make deps                # Install runtime deps (pyyaml, jsonschema)
make deps-dev            # Install dev deps (pytest, pytest-cov, ruff)

# Tests
make test-v2             # Run v2 tests (502 tests) — primary
make test-v1             # Run v1 tests (31 tests)
make test-all            # Run both

# Run a single test file or test
PYTHONPATH=. python -m pytest specs/v2/tests/test_loader.py -v --tb=short
PYTHONPATH=. python -m pytest specs/v2/tests/test_validator.py::TestClassName::test_name -v

# CI (spec check + schema validation + example validation + tests)
make ci-v2               # v2 CI pipeline
make ci-v1               # v1 CI pipeline
make ci-all              # Both

# Build specs from section files
make spec-v2             # Assemble v2 SPEC.md (en + ru) from specs/v2/{en,ru}/spec/*.md
make spec-v1             # Assemble v1 SPEC.md

# Lint
ruff check .
ruff format .
```

## CLI Usage (v2)

```bash
python -m specs.v2.tools.cli validate plan.yaml
python -m specs.v2.tools.cli render tree plan.yaml
python -m specs.v2.tools.cli render gantt plan.yaml --view gantt-view-id
python -m specs.v2.tools.cli render list plan.yaml
python -m specs.v2.tools.cli render deps plan.yaml --mode hierarchical
```

Multiple files can be passed; they are merged into a single plan.

## Architecture

### Guiding Principle

**Specification is the core. Tools are plugins.** The YAML format spec drives everything; tooling is reference implementation.

### v2 Tools Pipeline (`specs/v2/tools/`)

Data flows through a strict pipeline: **Load → Merge → Validate → Compute → Render**

- **`loader.py`** — Loads YAML fragments via `load_fragment()`, merges multiple files into a `MergedPlan` via `merge_fragments()`. Tracks source file for every element. Entry point: `load_plan_set(files)`.
- **`models.py`** — Dataclasses for all domain objects: `Node`, `Schedule`, `ScheduleNode`, `Calendar`, `View`, `ViewFilter`, `Meta`, `Status`, `MergedPlan`. Node has NO date fields; dates live in `ScheduleNode` (overlay pattern).
- **`validator.py`** — `validate(plan: MergedPlan) -> ValidationResult`. Checks: version, required fields, reference integrity (parent/after/status), cycle detection (both parent and after graphs), schedule references, view validity.
- **`effort.py`** — `compute_effort_metrics(plan)`. Bottom-up tree traversal computing three per-node metrics: `effort_rollup`, `effort_effective`, `effort_gap`.
- **`scheduler.py`** — `compute_schedule(plan)`. Memoized date calculation with calendar-aware workday logic. Sets `computed_start`/`computed_finish` on `ScheduleNode` objects.
- **`cli.py`** — argparse-based CLI orchestrating the pipeline. Commands: `validate`, `render {gantt,tree,list,deps}`.
- **`render/`** — Four renderers (`gantt.py`, `tree.py`, `list.py`, `deps.py`) plus shared utilities in `common.py`. All accept a `MergedPlan` and optional `view_id` for filtering/sorting. Gantt and deps output Mermaid syntax.

### Spec Documentation Structure

Specs are assembled from numbered markdown sections in `specs/v{1,2}/{en,ru}/spec/`:
- `00-introduction.md`, `10-plan-set.md`, `20-nodes.md`, `30-schedule.md`, `40-views.md`, `50-validation.md`
- Built into `SPEC.md` by `build_spec.py`; CI checks that generated SPEC.md is up-to-date
- `SPEC.min.md` is a compact version maintained manually

### v1 vs v2

v1 integrates scheduling into nodes directly. v2 separates structure from schedule via the overlay pattern. v2 is the recommended version and has substantially more tooling and test coverage.

## Code Conventions

- Python >= 3.11, formatting/lint with `ruff`
- Tests use `unittest.TestCase` with `tempfile.mkdtemp()` for file-based tests and direct dataclass construction for in-memory tests
- New format fields must be optional (unless major version bump), have clear semantics, and be documented in the spec
- Small PRs preferred; contributions are Apache-2.0
