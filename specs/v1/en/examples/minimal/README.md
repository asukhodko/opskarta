# Example: Minimal (minimal valid plan)

This example demonstrates the absolute minimum required to create a valid opskarta plan.

## What It Demonstrates

- **Only required fields** — `version` and `nodes`
- **One node** — with only the required field `title`
- **No views file** — views are optional

## Files

| File | Description |
|------|-------------|
| `project.plan.yaml` | Minimal valid plan with one node |

## Plan Structure

```yaml
version: 1

nodes:
  root:
    title: "Minimal Project"
```

## What Is Omitted

This example intentionally omits all optional elements:

- `meta` — plan metadata (id, title)
- `statuses` — custom statuses
- `kind` — node type (defaults to task)
- `status` — node status
- `parent` — parent node
- `start`, `duration`, `after` — scheduling
- `notes` — notes
- `*.views.yaml` file — views

## Usage

### Validation

```bash
cd specs/v1
python tools/validate.py en/examples/minimal/project.plan.yaml
```

## When to Use

This example is useful as a starting point for understanding the format. For real projects, it's recommended to use a more complete structure — see the [hello](../hello/) example.
