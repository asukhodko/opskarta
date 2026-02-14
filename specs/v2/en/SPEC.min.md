opskarta v2 (draft) — ultra-compact spec (LLM-paste), core-complete + anti-ambiguity

0) General
- Serialization: YAML (recommended) or JSON; root has version: 2.
- Node identifiers are string keys in nodes map.
- Key v2 difference: overlay schedule — work structure (nodes) separated from calendar planning (schedule).
- Plan without schedule is fully valid.

1) Plan Set (Multi-file Structure)
- Plan can be split into multiple *.plan.yaml files (fragments).
- Fragments merged into single Merged Plan deterministically.
- Allowed top-level blocks: version, meta, statuses, nodes, schedule, views, x.
- Any other top-level block is error.
- version: must be same in all fragments; conflict is error.
- meta: fields combined; conflicting values for same field is error.
- statuses/nodes/views: dictionaries combined; duplicate key is error with file indication.
- schedule.calendars/schedule.nodes: dictionaries combined; duplicate key is error.
- schedule.default_calendar: allowed in only ONE fragment; multiple definitions is error.
- x: dictionaries combined; duplicate key is error.

2) nodes (Work Structure)
- node_id: unique string key in nodes map; recommended regex ^[a-zA-Z][a-zA-Z0-9._-]*$; avoid spaces/parentheses/colons for Mermaid.
- Required: title (string).
- Optional: kind (string), status (string), parent (string), after (list[string]), milestone (bool), effort (number ≥0), issue (string), notes (string), x (object).
- FORBIDDEN in v2 nodes: start, finish, duration, excludes — moved to schedule.
- parent: existing node_id; circular references forbidden.
- after: list of node_ids; circular dependencies forbidden; dependencies defined in nodes, NOT in schedule.nodes.
- milestone: true = point event; when computing start from after, no +1 workday added.
- effort: non-negative number; unit in meta.effort_unit (display only).
- effort_rollup: sum of effort_effective of direct children.
- effort_effective: effort if set, else effort_rollup.
- effort_gap: max(0, effort - effort_rollup).
- status: must be key in statuses; non-existent status is error.

3) statuses
- Optional unless any node has status; then statuses required.
- Status fields: label (string, recommended), color (string, optional).
- color format: ^#[0-9a-fA-F]{6}$; invalid color is error.

4) schedule (Calendar Planning Layer)
- Optional block; plan valid without schedule.
- Structure: schedule.calendars, schedule.default_calendar, schedule.nodes.

4.1) schedule.calendars
- calendar_id: unique string key.
- excludes: list of "weekends" and/or "YYYY-MM-DD" dates.

4.2) schedule.default_calendar
- Reference to existing calendar_id.
- Used for nodes without explicit calendar.

4.3) schedule.nodes
- node_id: must exist in nodes.
- Fields: start (YYYY-MM-DD), finish (YYYY-MM-DD), duration (Nd or Nw), calendar (calendar_id).
- after FORBIDDEN in schedule.nodes — dependencies only in nodes.
- Node states: unscheduled (not in schedule.nodes), scheduled (in schedule.nodes), computed (scheduled + dates computed).

4.4) Date Computation
- start priority: 1) explicit start, 2) finish + duration (backward), 3) after dependencies.
- after algorithm: get deps from nodes.<id>.after; filter only scheduled deps; compute max(finish); regular node: start = next_workday(max_finish); milestone: start = max_finish.
- Unschedulable: no explicit start, no finish+duration, all after deps unscheduled/unschedulable.
- duration format: ^[1-9][0-9]*[dw]$; d=workdays; w=5 workdays (1w=5d).
- finish = add_workdays(start, duration - 1, calendar); start day included.
- Backward planning: start = sub_workdays(finish, duration - 1, calendar).
- Consistency: if start+finish+duration all present, must match; inconsistency is error.
- Start normalization: if start on excluded day and not milestone, normalize to next workday + warning; milestones not normalized.

5) views (Representations)
- Views define visualization, do NOT affect schedule computation.
- FORBIDDEN in v2 views: excludes — calendar only in schedule.calendars.
- View fields: title (string), where (object), order_by (string), group_by (string), lanes (object), date_format, axis_format, tick_interval.

5.1) where (Filter)
- kind: list[string] — nodes with specified kind.
- status: list[string] — nodes with specified status.
- has_schedule: bool — only scheduled (true) or unscheduled (false) nodes.
- parent: string — descendants of specified node.
- All conditions combined with AND.

5.2) lanes (for Gantt)
- lane_id: { title: string, nodes: list[node_id] }.

6) Validation
- Severity: error (invalid), warn (valid with warning), info (valid).
- Errors: missing required fields; non-existent references (parent/after/status/calendar); circular dependencies; duplicate keys; invalid formats; inconsistent dates; forbidden fields in wrong blocks.
- Warnings: unschedulable nodes; start on excluded day; all deps unscheduled.
- Info: unscheduled nodes; computed dates.

7) Extensibility
- Unknown fields MUST be ignored and preserved in parse→emit.
- Namespace x: for extensions; allowed in plan root, meta, statuses.*, nodes.*, schedule, views.*, lanes.*.
- Extensions MUST NOT affect core semantics.

8) Migration from v1
- nodes: remove start/finish/duration/excludes; move to schedule.nodes.
- views: remove excludes; move to schedule.calendars.
- after: keep in nodes (unchanged).
- finish (v1 inclusive) → finish (v2 inclusive): no change.

9) Anti-ambiguity
- Dependencies (after) defined ONLY in nodes, never in schedule.nodes.
- Calendar (excludes) defined ONLY in schedule.calendars, never in views.
- Plan without schedule is valid — structure exists independently of calendar.
- Unscheduled nodes not shown on Gantt but exist in tree/list/deps.
- Multiple dependencies: compute start from max(finish) of scheduled deps only.
