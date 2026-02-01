# Example: Hello (basic plan with views)

This example demonstrates basic usage of the opskarta format with a plan file and views file.

## What It Demonstrates

- **Plan file** (`hello.plan.yaml`) — project description with nodes, statuses, and dependencies
- **Views file** (`hello.views.yaml`) — Gantt view definition for plan visualization

## Files

| File | Description |
|------|-------------|
| `hello.plan.yaml` | Plan for "Git Service Upgrade" project with phases and tasks |
| `hello.views.yaml` | Gantt view definition with one lane |

## Plan Structure

The plan describes a simple service upgrade project:

```
root (Git Service Upgrade)
├── prep (Preparation) — 10 days
├── rollout (Rollout) — 5 days, after prep
└── switch (Traffic Switch) — 1 day, after rollout
```

## Usage

### Validation

```bash
cd specs/v1
python tools/validate.py en/examples/hello/hello.plan.yaml en/examples/hello/hello.views.yaml
```

### Generate Mermaid Gantt

```bash
cd specs/v1
python -m tools.render.plan2gantt \
  --plan en/examples/hello/hello.plan.yaml \
  --views en/examples/hello/hello.views.yaml \
  --view overview
```

## Example Features

- Uses custom statuses with colors
- Demonstrates dependencies between nodes (`after`)
- Shows usage of `duration` and `start` for scheduling
- Includes notes (`notes`) for critical tasks
