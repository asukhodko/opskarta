# opskarta v3, Compact LLM Context

Purpose: this file is a compact restatement of the full opskarta v3 specification. It is meant to fit entirely into an LLM prompt/context window when the model needs the format rules without reading `SPEC.md`.

## 0. Core Idea

opskarta is a YAML/JSON plan-as-code format for operational maps. v3 keeps the v2 foundation:

- `nodes` = work structure and dependencies;
- `schedule` = optional calendar overlay;
- `execution` = optional actual progress overlay;
- `views` = render configuration that does not affect scheduling;
- `x.exec` = built-in operational/executive profile for syncs, leadership views, and status documents.

Use v3 when a plan is a working center for syncs, executive maps, reports, and focused Gantt windows. For simple tree/list/Gantt use, v2 remains a smaller starting point.

## 1. Top-Level Blocks

Allowed top-level blocks:

- `version: 3`
- `meta`
- `statuses`
- `nodes`
- `schedule`
- `execution`
- `views`
- `profiles`
- `x`

Unknown top-level blocks are invalid.

## 2. Plan Set and Merge

A plan may be split into multiple `*.plan.yaml` fragments. The loader merges them deterministically into one Merged Plan.

Merge rules:

- `version` must be the same in all fragments.
- `meta` fields merge; conflicting values are errors.
- `statuses`, `nodes`, `views`, `schedule.calendars`, `schedule.nodes`, and `x` merge by key; duplicate keys are errors.
- `schedule.default_calendar` may be defined by only one fragment.
- Source file information is preserved for diagnostics.

## 3. Nodes

`nodes` is a dictionary of `node_id -> node`.

Required node field:

- `title` string.

Common optional fields:

- `kind` string;
- `status` string, key in `statuses`;
- `parent` string, existing `node_id`;
- `deps` list of dependency strings or dependency objects;
- `milestone` boolean;
- `effort` number >= 0;
- `issue` string;
- `notes` string;
- `x` object.

Forbidden in `nodes`: `start`, `finish`, `duration`, `excludes`. Dates and calendars belong to `schedule`.

Dependency object fields:

- `id` required target `node_id`;
- `type`: `fs` or `ss`, default `fs`;
- `lag`: non-negative duration like `0d`, `2d`, `1w`, default `0d`;
- `hard` boolean, default `true`;
- `note` string.

Parent cycles and dependency cycles are invalid. Both hard and soft dependency cycles are invalid.

Effort metrics:

- `effort_rollup` = sum of direct children effective effort;
- `effort_effective` = explicit `effort` if present, otherwise `effort_rollup`;
- `effort_gap` = `max(0, effort - effort_rollup)`.

## 4. Statuses

`statuses` is optional unless nodes use `status`.

Status fields:

- `label` string, required;
- `color` optional `#RRGGBB`.

Node `status` must reference an existing status key.

## 5. Schedule

`schedule` is optional. A plan without `schedule` is valid.

Schedule structure:

- `schedule.calendars`
- `schedule.default_calendar`
- `schedule.nodes`

Calendar:

- `excludes`: list of `"weekends"` and/or date strings `YYYY-MM-DD`.

Schedule node fields:

- `start` valid `YYYY-MM-DD`;
- `finish` valid `YYYY-MM-DD`;
- `duration` positive duration `^[1-9][0-9]*[dw]$`;
- `calendar` existing calendar id.

Forbidden in `schedule.nodes`: `deps`. Dependencies live only in `nodes`.

Scheduling semantics:

- only nodes listed in `schedule.nodes` participate in calendar planning;
- unscheduled nodes still appear in tree/list/deps renders;
- start priority: explicit `start`, then `finish + duration` backward planning, then hard scheduled deps;
- `fs` uses dependency finish; `ss` uses dependency start;
- hard deps affect scheduling, soft deps are informational;
- regular tasks start on next workday after an `fs` dependency; milestones may occur on the dependency date;
- `duration` counts the start day inclusively;
- `1w` means 5 working days;
- non-milestone starts on excluded days are normalized to the next workday with warning.

## 6. Execution

`execution` is optional and may live in a separate fragment.

`execution.nodes.<node_id>` fields:

- `progress` number 0..1;
- `actual_start` valid `YYYY-MM-DD`;
- `actual_finish` valid `YYYY-MM-DD`;
- `updated_at` ISO-like timestamp string;
- `confidence` number 0..1;
- `note` string.

`node_id` must exist in `nodes`.

Progress rollup:

- leaf node uses direct `execution.nodes.<id>.progress`;
- parent progress is effort-weighted from children with progress data;
- `progress_coverage` is the fraction of effort that has progress data.

Strict mode may warn about inconsistent execution facts, such as `actual_finish` without `actual_start` or `progress=1.0` without `actual_finish`.

## 7. Views

`views` define render selections and presentation. Views do not affect schedule computation.

View fields:

- `title` string;
- `where` object;
- `order_by` string;
- `group_by` string;
- `lanes` object;
- `date_format` string;
- `axis_format` string;
- `tick_interval` string;
- `window_start` valid `YYYY-MM-DD`;
- `window_finish` valid `YYYY-MM-DD`.

Forbidden in views: `excludes`.

Allowed `where` filters:

- `kind`: list of strings;
- `status`: list of strings;
- `has_schedule`: boolean;
- `parent`: existing node id, selects descendants;
- `x_ops_attention_class`: list of strings, matches `nodes.*.x.ops.attention_class`.

Lane fields:

- `title` string;
- `nodes` list of node ids, required;
- `expand_descendants: leaves` to render scheduled leaf descendants of listed lane nodes.

Gantt windows:

- `window_start` and `window_finish` clip the rendered output only;
- source dates in `schedule.nodes` are unchanged;
- `window_start` must be <= `window_finish`.

Renderer rules:

- Gantt requires a `--view`.
- Tree/list/deps may render without a view.
- `where`, ordering, lanes, and windows are render-time concerns only.

## 8. Executive Overlay: `x.exec`

`x.exec` is a built-in extension profile for operational and executive views. It does not replace `nodes`, `schedule`, or `execution`; it creates a short management map on top.

Structure:

- `program`
- `defaults`
- `blocks`
- `edges`
- `views`

`program` common fields:

- `committed_date` valid `YYYY-MM-DD`;
- `nearest_goal` string;
- `success_by_next_sync` string.

Each executive block defines exactly one of:

- `scope_nodes`: list of regular node ids;
- `source_blocks`: list of executive block ids.

Block fields:

- `title` string;
- `target_gate` node id;
- `kind` such as `main` or `risk_sidecar`;
- `progress_override` number 0..1;
- `mgmt.health`: `green`, `yellow`, `red`, or `neutral`;
- `mgmt.sync_note`;
- `mgmt.next_sync_goal`;
- `mgmt.owner`;
- `mgmt.health_note`;
- `mgmt.blocker_note`.

Executive edges:

- `from` block id;
- `to` block id;
- `type`: `required`, `risk_reduction`, or `context`;
- `label` optional string.

Executive views:

- `blocks` list of visible block ids;
- `direction` Mermaid direction, such as `LR` or `TB`;
- `color_mode`;
- `highlight_current`;
- `show_progress`;
- `show_gate_date`;
- `wrap_title_lines`;
- `caption`;
- optional view-local `edges` override.

Renderers:

- `render executive` emits Mermaid flowchart syntax.
- `render executive-report` emits Markdown sections: `status`, `tracks`, `signals`.
- `executive-report status` defaults to `exec-top`.
- `tracks` and `signals` default to `exec-active-tracks`.
- `--view` overrides the default report view.
- `--lang ru|en` selects built-in report labels and date formatting.

## 9. Profiles and Extensions

`profiles` declares extension namespaces used under `x`.

Profile fields:

- `id` string;
- `version` integer;
- `namespace` matching `^[a-zA-Z_][a-zA-Z0-9_]*$`.

Duplicate profile namespaces are invalid.

`x` may hold arbitrary extension data at the root and inside nodes. Extensions must not change core semantics unless the relevant profile explicitly defines such behavior.

## 10. Validation

Severity levels:

- `error`: invalid;
- `warning`: valid but suspicious;
- `info`: valid informational result.

Invalid examples:

- missing required fields;
- unknown top-level blocks;
- unsupported view or `where` keys;
- duplicate keys across fragments;
- non-existent references;
- parent/dependency cycles;
- invalid date/duration/lag formats;
- forbidden fields in wrong blocks;
- inconsistent schedule dates;
- invalid execution progress/confidence;
- invalid `x.exec` references.

Warnings include unscheduled or unschedulable nodes, start normalization, and some execution consistency issues.

## 11. Markdown Refresh

`update-markdown` refreshes generated Mermaid or Markdown blocks from embedded commands.

The command comment format is:

```markdown
<!--
Перегенерить:
python -m specs.v3.tools.cli validate plan.yaml exec.yaml
python -m specs.v3.tools.cli render executive plan.yaml exec.yaml --view exec-top
-->
```

Only the immediately following Mermaid block or `<!-- GENERATED:START -->` / `<!-- GENERATED:END -->` block is replaced.

## 12. CLI

```bash
python -m specs.v3.tools.cli validate plan.yaml
python -m specs.v3.tools.cli render tree plan.yaml --view backlog
python -m specs.v3.tools.cli render list plan.yaml --view tasks
python -m specs.v3.tools.cli render deps plan.yaml
python -m specs.v3.tools.cli render gantt plan.yaml --view release-window --style status
python -m specs.v3.tools.cli render executive plan.yaml exec.yaml --view exec-top
python -m specs.v3.tools.cli render executive-report plan.yaml exec.yaml --section status --lang en
python -m specs.v3.tools.cli update-markdown plan.md exec.md
```

## 13. Minimal v2 to v3 Migration

For a valid v2 plan:

1. Change `version: 2` to `version: 3`.
2. Run v3 validation.
3. Keep v2-style views if they are valid.
4. Add `x.exec`, Gantt windows, attention filters, and Markdown refresh only when useful.
