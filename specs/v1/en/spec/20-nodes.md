# Nodes (`nodes`)

A node is a unit of work/meaning in your map.

## Node Identifiers (node_id)

Each node is identified by a key in the `nodes` dictionary. This key (`node_id`) is used for references in `parent`, `after`, and `lanes[].nodes`.

### Requirements

- `node_id` MUST be unique within `nodes`.
- `node_id` MUST be a string.

### Recommendations

- **Recommended format:** `^[a-zA-Z][a-zA-Z0-9._-]*$`
  - Starts with a letter
  - Contains only letters, digits, dots, underscores, hyphens
- **For Mermaid compatibility:** avoid spaces, parentheses, colons in identifiers.

```yaml
# Good identifiers
nodes:
  kickoff: ...
  phase_1: ...
  backend-api: ...
  JIRA.123: ...

# Problematic identifiers (may not work in some renderers)
nodes:
  "task with spaces": ...     # Spaces
  "task:important": ...       # Colon
  123: ...                    # Starts with digit
```

## Required Node Fields

- `title` *(string)* — work name.

## Recommended Fields

- `kind` *(string)* — node type. Recommended values:
  - `summary` — top-level container
  - `phase` — stage/phase
  - `epic` — large entity in the detail system
  - `user_story` — story/value
  - `task` — specific task

- `status` *(string)* — status key from `statuses`.

- `parent` *(string)* — parent node ID (decomposition hierarchy).

- `after` *(list[string])* — "after what" dependencies (graph).  
  Semantics: node can start after all `after` nodes are completed.

- Scheduling:
  - `start` *(YYYY-MM-DD)* — planned start date
  - `finish` *(YYYY-MM-DD)* — target completion date (deadline). See "Scheduling" section.
  - `duration` *(string)* — duration, e.g. `5d`. If not specified for a scheduled node — defaults to `1d`.
  - `milestone` *(boolean)* — if `true`, node is a milestone (point event). See below.

- `issue` *(string)* — reference/key in the detail system (e.g., `JIRA-123`).

- `notes` *(string|multiline)* — notes/context that you don't want to lose.

## Milestones

A milestone is a point event on the timeline, not a task with duration. Used to mark key dates: releases, deadlines, checkpoints.

### Field `milestone`

- `milestone` *(boolean)* — if `true`, node is displayed as a milestone.

### Behavior

- Milestone MUST have `start` or computable `start` via `after`.
- If `duration` is not specified for a milestone, `1d` is used for calculations.
- On Gantt chart, milestone is displayed as a point/diamond, not as a bar.
- Milestones can have dependencies (`after`) and statuses (`status`).

### Example

```yaml
nodes:
  release_v1:
    title: "Release v1.0"
    milestone: true
    start: "2024-03-15"
    status: not_started

  beta_release:
    title: "Beta Release"
    milestone: true
    after: [integration_testing]
    # start is computed from after
```

## Notes

- opskarta does not dictate workflow. `status` is a label for your map.
- Node can exist without `issue` (draft, hypothesis, placeholder).

## Field `finish` (deadline/backward scheduling)

Field `finish` specifies the target completion date or deadline for a node.

- `finish` *(string, YYYY-MM-DD)* — target completion date.

### Behavior

1. **If `finish` + `duration` are specified without `start`:**
   - `start` is computed "backward" from `finish` by subtracting workdays.
   - Formula: `start = sub_workdays(finish, duration - 1)`, where `finish` is included in the duration.
   - Example: `finish: 2024-03-15`, `duration: 5d` → `start: 2024-03-11` (5 workdays: 11, 12, 13, 14, 15).

2. **If `start` + `finish` are specified without `duration`:**
   - `duration` is computed as the number of workdays between dates.

3. **If all three (`start`, `finish`, `duration`) are specified:**
   - They MUST be consistent (computed `finish` from `start+duration` must match specified `finish`).
   - Inconsistency is an **error**.

### Example

```yaml
nodes:
  release_prep:
    title: "Release Preparation"
    finish: "2024-03-15"  # Deadline
    duration: "5d"
    # start is computed backward: 2024-03-11 (5 workdays: 11, 12, 13, 14, 15)
  
  feature_a:
    title: "Feature A"
    start: "2024-03-01"
    finish: "2024-03-05"
    # duration is computed: 5d
```
