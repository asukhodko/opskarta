# opskarta v3, Compact

## Core

A file or file set may contain:

- `version: 3`
- `meta`
- `statuses`
- `nodes`
- `schedule`
- `execution`
- `views`
- `profiles`
- `x`

`nodes` describes work structure and dependencies. Dates live only in `schedule.nodes`. Actual progress lives in `execution.nodes`.

## New in v3

### `x.exec`

A built-in profile for executive and operational views:

- `program` — committed date, nearest goal, next-sync success criterion;
- `blocks` — high-level management blocks;
- `edges` — block relations (`required`, `risk_reduction`, `context`);
- `views` — executive views.

Each block defines exactly one of:

- `scope_nodes` — scope from regular `nodes`;
- `source_blocks` — aggregation of other executive blocks.

Common block fields: `title`, `target_gate`, `kind`, `progress_override`, `mgmt.health`, `mgmt.sync_note`, `mgmt.next_sync_goal`, `mgmt.owner`.

### Views

Additions to regular views:

- `window_start`, `window_finish` — output window for Gantt;
- `lanes.*.expand_descendants: leaves` — render leaf descendants of listed lane nodes;
- `where.x_ops_attention_class` — filter by `nodes.*.x.ops.attention_class`.

## CLI

```bash
python -m specs.v3.tools.cli validate plan.yaml
python -m specs.v3.tools.cli render gantt plan.yaml --view release-window --style status
python -m specs.v3.tools.cli render executive plan.yaml exec.yaml --view exec-top
python -m specs.v3.tools.cli render executive-report plan.yaml exec.yaml --section status
python -m specs.v3.tools.cli update-markdown plan.md exec.md
```
