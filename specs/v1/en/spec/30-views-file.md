# Views File (`*.views.yaml`)

The views file describes *how* to look at the plan.

## Root Fields

- `version` *(int)*
- `project` *(string)* — must match `meta.id` of the plan
- `gantt_views` *(object)* — set of Gantt views (optional)

## Gantt View

### Core Fields

- `title` *(string)* — view title
- `excludes` *(list[string])* — calendar exclusions
  - `"weekends"` — exclude Saturday and Sunday (core)
  - Specific dates in `YYYY-MM-DD` format — **core**, affect date calculation algorithm
- `lanes` *(object)* — lanes/tracks
  - `<lane_id>.title` *(string)*
  - `<lane_id>.nodes` *(list[string])* — list of node_ids to show in this lane

### Mermaid Renderer Fields (non-core)

The following fields are extensions for Mermaid Gantt renderer and do NOT affect the core date calculation algorithm:

- `date_format` *(string)* — input date format for Mermaid (default `YYYY-MM-DD`)
- `axis_format` *(string)* — date display format on X axis
- `tick_interval` *(string)* — tick interval on X axis (e.g., `1week`, `1day`, `1month`)

> **Note:** these fields are documented here for compatibility with existing files. For detailed mapping to Mermaid directives see "Renderer profile: Mermaid Gantt" section.

## Example

### Minimal

```yaml
version: 1
project: demo

gantt_views:
  overview:
    title: "Overview"
    excludes: ["weekends"]
    lanes:
      main:
        title: "Main"
        nodes: [root, task1]
```

### Extended (with Mermaid fields)

```yaml
version: 1
project: demo

gantt_views:
  overview:
    title: "Project Overview"
    date_format: "YYYY-MM-DD"
    axis_format: "%d %b"
    tick_interval: "1week"
    excludes:
      - weekends
      - "2024-03-08"    # Holiday
    lanes:
      development:
        title: "Development"
        nodes: [backend, frontend, integration]
      testing:
        title: "Testing"
        nodes: [unit_tests, e2e_tests]
```
