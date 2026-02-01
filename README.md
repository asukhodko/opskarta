# opskarta

> OpsKarta — Operational map format for complex programs (plan‑as‑code).  
> OpsCarto — Operational cartography for programs: model once, render many views. *(synonym)*

**opskarta** — an open data format (YAML/JSON) for an *operational map of a program/project*: a single artifact where a manager captures their current interpretation of work structure and dependencies, then generates any number of views from it (Gantt, dependency graphs, checklists, reports, etc.).

Key idea: **"source of truth" — not Jira, not Confluence, not "in your head", but your version-controlled plan file**.

## Specification Versions

| Version | Status | Language | Description |
|---------|--------|----------|-------------|
| [v1](specs/v1/) | Alpha | [EN](specs/v1/en/SPEC.md) (canonical) \| [RU](specs/v1/ru/SPEC.md) | Initial specification version |

## What It Looks Like

Plan file (`hello.plan.yaml`):

```yaml
version: 1

meta:
  id: hello-upgrade
  title: "Example: Git Service Upgrade"

statuses:
  not_started: { label: "Not Started", color: "#9ca3af" }
  in_progress: { label: "In Progress", color: "#0ea5e9" }
  done:        { label: "Done",        color: "#22c55e" }
  blocked:     { label: "Blocked",     color: "#fecaca" }

nodes:
  root:
    title: "Git Service Upgrade"
    kind: summary
    status: in_progress

  prep:
    title: "Preparation"
    kind: phase
    parent: root
    start: "2026-02-01"
    duration: "10d"
    status: in_progress

  rollout:
    title: "Rollout"
    kind: phase
    parent: root
    after: [prep]
    duration: "5d"
    status: not_started

  switch:
    title: "Traffic Switch"
    kind: task
    parent: rollout
    after: [rollout]
    duration: "1d"
    status: not_started
    notes: |
      Critical step. Rollback plan needed.
```

From this plan you can generate Gantt charts, dependency graphs, reports — see the [full v1 specification](specs/v1/).

## Quick Start

Current recommended version — **[v1](specs/v1/)**.

```bash
cd specs/v1

# Validate example
python tools/validate.py en/examples/hello/hello.plan.yaml en/examples/hello/hello.views.yaml

# Generate Mermaid Gantt
python -m tools.render.plan2gantt \
    --plan en/examples/hello/hello.plan.yaml \
    --views en/examples/hello/hello.views.yaml \
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

### Main Commands

```bash
# Build SPEC.md from sources (both languages)
make spec-all

# Build English spec only
make spec-en

# Build Russian spec only
make spec-ru

# Check if SPEC.md is up-to-date
make check-spec-all

# Validate all examples (both languages)
make validate-examples-all

# Run tests
make test

# All CI checks
make ci

# Help for all commands
make help
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
