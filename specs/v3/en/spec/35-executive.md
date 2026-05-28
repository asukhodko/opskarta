# Executive Overlay (`x.exec`)

`x.exec` is a built-in extension profile for management and operational views. It does not replace `nodes`, `schedule`, or `execution`; it builds a short map on top of them for syncs, leadership views, and program status documents.

## Structure

```yaml
x:
  exec:
    program: { ... }
    defaults: { ... }
    blocks: { ... }
    edges: [ ... ]
    views: { ... }
```

### `program`

Optional program-level goal:

| Field | Description |
|-------|-------------|
| `committed_date` | Committed date in `YYYY-MM-DD` format. |
| `nearest_goal` | Current nearest goal in human language. |
| `success_by_next_sync` | What should be true by the next sync. |

### `blocks`

`blocks` is a dictionary of `block_id -> block`.

Each block must define exactly one scope field:

| Field | Description |
|-------|-------------|
| `scope_nodes` | Regular `node_id` values used to calculate block progress. |
| `source_blocks` | Other `block_id` values when this block aggregates executive blocks. |

Common block fields:

| Field | Description |
|-------|-------------|
| `title` | Short card title. |
| `target_gate` | `node_id` of the nearest calendar gate; the node must be in `schedule.nodes`. |
| `kind` | Block semantics, such as `main`, `feeder`, `risk_sidecar`, `aggregate`. |
| `progress_override` | Manual progress `0..1` when automatic calculation is not useful. |
| `mgmt.health` | `green`, `yellow`, `red`, or `neutral`. |
| `mgmt.sync_note` | What is happening now. |
| `mgmt.next_sync_goal` | What should move by the next sync. |
| `mgmt.blocker_note` | External dependency or blocker. |
| `mgmt.owner` | Person or team, when useful in a report. |

### `edges`

Edges connect executive blocks:

```yaml
edges:
  - from: prep
    to: cutover
    type: required
  - from: post
    to: cutover
    type: context
    label: "after window"
```

Allowed types:

| Type | Meaning |
|------|---------|
| `required` | Required path. |
| `risk_reduction` | Risk-reduction path, usually dashed. |
| `context` | Context relation, not the main path. |

`views.*.edges` may override the global `edges` list for a specific map.

### `views`

An executive view defines visible blocks and Mermaid flowchart settings:

```yaml
views:
  exec-top:
    direction: LR
    color_mode: mgmt_hybrid
    highlight_current: true
    show_progress: false
    show_gate_date: true
    wrap_title_lines: 2
    blocks: [prep, cutover, post]
```

Supported fields:

| Field | Description |
|-------|-------------|
| `direction` | Mermaid flowchart direction: `LR`, `TB`, `BT`, `RL`. |
| `color_mode` | `status` or `mgmt_hybrid`. |
| `highlight_current` | Highlight the current main block. |
| `show_progress` | Show progress percentage in the card. |
| `show_gate_date` | Show the `target_gate` date. |
| `show_owner` | Show `mgmt.owner`. |
| `wrap_title_lines` | Split a long title into lines. |
| `respect_mgmt_health_for_done` | Use `mgmt.health` color even for done blocks. |
| `reduce_transitive_required_edges` | Hide transitive `required` edges. |
| `caption` | Text caption that Markdown updater can pick up. |
| `blocks` | List of visible `block_id` values. |
| `edges` | View-local edge list. |

## Rendering

```bash
python -m specs.v3.tools.cli render executive plan.yaml exec.yaml --view exec-top
python -m specs.v3.tools.cli render executive-report plan.yaml exec.yaml --section status
python -m specs.v3.tools.cli render executive-report plan.yaml exec.yaml --section tracks
python -m specs.v3.tools.cli render executive-report plan.yaml exec.yaml --section signals
```
