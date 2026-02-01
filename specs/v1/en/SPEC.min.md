opskarta v1 (draft) — ultra-compact spec (LLM-paste), core-complete + anti-ambiguity

0) General
- Serialization: YAML (recommended) or JSON; root has version (int).
- Node identifiers are string keys in nodes map.
- Core vs non-core: Core MUST implement; Non-core MAY implement.
- Core components: plan/views structure, node fields (title, kind, status, parent, after, start, finish, duration, milestone), scheduling algorithm, core excludes, default duration=1d for scheduled, validation + referential integrity.
- Non-core components: extensions (x:), renderer profiles, view renderer fields (date_format/axis_format/tick_interval), non-core excludes, default status colors.

1) *.plan.yaml (plan)
- Root fields: version (int), meta (object: id string, title string), statuses (object), nodes (object {node_id: node}).
- nodes keys MUST be unique strings.

2) nodes.* (nodes)
- node_id requirements: MUST be unique string; recommended regex ^[a-zA-Z][a-zA-Z0-9._-]*$; avoid spaces/parentheses/colons for Mermaid compatibility.
- Required: title (string).
- Fields: kind (string), status (string), parent (string), after (list[string]), start (YYYY-MM-DD string), finish (YYYY-MM-DD string), duration (string), milestone (bool), issue (string), notes (string|multiline).
- Milestone rules: milestone=true is point event; MUST have start or computable start via after; if duration absent, use 1d; start-from-after uses max_finish (no +1 workday).
- Unscheduled: no explicit start, no finish, no computable start via after.

3) statuses
- statuses optional unless any node has status; then statuses is required.
- Referential integrity: node.status MUST be key in statuses.
- Status fields: label (string, recommended), color (string, optional).
- color format regex ^#[0-9a-fA-F]{6}$; invalid color is error.
- If label absent, renderer MAY use status key.

4) *.views.yaml (views)
- Root fields: version (int), project (string), gantt_views (object, optional).
- project MUST match plan.meta.id; if plan.meta.id missing, link validation fails.
- gantt_view core fields: title (string), excludes (list[string]), lanes (object).
- lanes.<lane>.title (string); lanes.<lane>.nodes (list[node_id]); each node_id MUST exist in plan.

5) Scheduling (core) — per-view
- View calendar calendar(view) depends on view.excludes; schedule computed per view.
- Core excludes: "weekends" and YYYY-MM-DD dates; non-core excludes MUST be ignored with WARN.
- Workday: not excluded by calendar(view).
- duration: regex ^[1-9][0-9]*[dw]$; d=workdays; w=5 workdays (1w=5d, 2w=10d); number ≥1.
- Default duration: if node is scheduled (explicit start or computable start via after) and duration absent, MUST use 1d.
- finish inclusive: finish = start + (duration_days - 1) workdays.
- start_from_finish: if finish + duration given and start absent, start = sub_workdays(finish, duration_days - 1).
- duration_from_dates: if start + finish given and duration absent, duration = count of workdays between inclusive dates.
- Consistency: if start+finish+duration all present, MUST match computed finish; inconsistency is error.
- after: start from after uses all dependencies; compute each dependency finish, take max_finish.
  - Regular node: start = next_workday(max_finish).
  - Milestone: start = max_finish (no +1 day).
- Priority: explicit start overrides after (after becomes logical link only).
- WARN if explicit start < finish(deps).
- Normalization of start: if start on excluded day and not milestone, MUST normalize to next workday and WARN; effective_start used for calculations.
- finish on excluded day: for regular nodes, WARN; no normalization; for milestones, no warning.
- Dependencies use all plan nodes, even if not shown in current view.
- Unscheduled nodes are not shown on Gantt (core rule).

6) Migration from end(exclusive)
- When migrating from end(exclusive): finish = prev_workday(end_exclusive, calendar(view)). finish is inclusive.

7) YAML/JSON types and normalization (core)
- YAML 1.1 can auto-type dates; normalize start/finish/excludes to "YYYY-MM-DD" strings.
- nodes keys are strings; duration is string.
- start/finish format regex ^\d{4}-\d{2}-\d{2}$; RECOMMENDED validate real calendar date.

8) Validation (core) + severity
- Severity: error (invalid), warn (valid with warning), info (valid).
- Typical errors: missing required fields (version, nodes, title); non-existent references (parent/after/status); circular dependencies (parent/after); duplicate node_id; duplicate YAML keys; invalid start/finish/duration format; invalid status color; inconsistent start+finish+duration.
- Typical warnings: after-chain without anchor (no start/finish in chain); explicit start before dependency finish; start on excluded day (non-milestone); finish on excluded day; non-core excludes.
- Typical info: missing duration for scheduled node; specific date excludes (core); unscheduled nodes.
- Validator MUST report path, problem, expected value/format.

9) Extensibility (core-compatible)
- Unknown fields MUST be ignored and preserved in parse→emit.
- Recommended namespace x: for extensions; allowed anywhere extensions listed (plan root, meta, statuses.*, nodes.*, views root, gantt_views.*, lanes.*).
- Extensions MUST NOT affect core semantics; renderer-specific extensions should be documented in renderer profile.

10) Renderer profile: Mermaid Gantt (non-core, reference)
- Renderer MUST precompute core schedule and output explicit dates; pass only core excludes to Mermaid; ignore non-core excludes with WARN.
- Weeks converted to days: 1w → 5d.
- Lanes map to Mermaid sections; parent hierarchy flattened (no nested sections).
- Milestone: milestone=true mapped to Mermaid milestone tag; if duration absent use 1d.
- Status mapping: done→done (✅), in_progress→active (🔄), blocked→crit (⛔), not_started→no tag; default colors if statuses.color absent: not_started #9ca3af, in_progress #0ea5e9, done #22c55e, blocked #fecaca.
- Renderer fields in view: date_format→dateFormat, axis_format→axisFormat, tick_interval→tickInterval.
- Extension x.scheduling.anchor_to_parent_start:
  - If no start and no after: effective_start(child)=effective_start(parent).
  - If after but no start: effective_start=max(start_from_after, effective_start(parent)).
  - If explicit start: use it.
- Unscheduled nodes are skipped; renderer MAY info-warn.
- Multiple dependencies: renderer uses core algorithm to compute start, outputs explicit date (not Mermaid after syntax).
- Anti-ambiguity:
  - If finish+duration specified and start absent, start is computed from finish even if after exists; after does not shift dates (only logical/WARN).
  - finish without start and without duration does not define timeline position; node may remain unscheduled.