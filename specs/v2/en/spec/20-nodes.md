# Nodes (`nodes`)

A node is a unit of work in the plan structure. In v2, nodes describe **structure and dependencies** without calendar fields.

## Node Identifiers (node_id)

Each node is identified by a key in the `nodes` dictionary. This key (`node_id`) is used for references in `parent`, `after`, `schedule.nodes`, `views`.

### Requirements

- `node_id` MUST be unique within `nodes`.
- `node_id` MUST be a string.

### Recommendations

- **Recommended format:** `^[a-zA-Z][a-zA-Z0-9._-]*$`
  - Starts with a letter
  - Contains only letters, digits, dots, underscores, hyphens
- **For Mermaid compatibility:** avoid spaces, parentheses, colons.

```yaml
# Good identifiers
nodes:
  kickoff: ...
  phase_1: ...
  backend-api: ...
  JIRA.123: ...

# Problematic identifiers
nodes:
  "task with spaces": ...     # Spaces
  "task:important": ...       # Colon
  123: ...                    # Starts with digit
```

## Node Fields

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Work item name |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `kind` | string | Node type (summary, phase, epic, task, etc.) |
| `status` | string | Status key from `statuses` |
| `parent` | string | Parent node ID (hierarchy) |
| `after` | list[string] | Dependencies "after what" (graph) |
| `milestone` | boolean | Whether the node is a milestone |
| `effort` | number | Work estimate (≥ 0) |
| `issue` | string | Link to issue tracker |
| `notes` | string | Notes/context |
| `x` | object | Extensions |

### Forbidden Fields (moved to schedule)

In v2, the following fields are **forbidden** in `nodes`:

| Field | Moved to |
|-------|----------|
| `start` | `schedule.nodes.<id>.start` |
| `finish` | `schedule.nodes.<id>.finish` |
| `duration` | `schedule.nodes.<id>.duration` |
| `excludes` | `schedule.calendars.<id>.excludes` |

```yaml
# ERROR in v2
nodes:
  task1:
    title: "Task"
    start: "2024-03-01"    # ERROR: start forbidden in nodes
    duration: "5d"          # ERROR: duration forbidden in nodes
```

## `kind` Field

Node type for classification. Recommended values:

| Value | Description |
|-------|-------------|
| `summary` | Top-level container |
| `phase` | Project stage/phase |
| `epic` | Large entity |
| `user_story` | Story/value |
| `task` | Specific task |

```yaml
nodes:
  root:
    title: "Project"
    kind: summary
  
  phase1:
    title: "Analysis"
    kind: phase
    parent: root
```

## `parent` Field (Hierarchy)

Defines the parent node for building a decomposition tree.

```yaml
nodes:
  root:
    title: "Project"
  
  phase1:
    title: "Phase 1"
    parent: root
  
  task1:
    title: "Task 1"
    parent: phase1
```

### Rules

- The `parent` value MUST be an existing `node_id`.
- Circular references through `parent` are **forbidden**.

## `after` Field (Dependencies)

List of nodes after whose completion this node can start.

```yaml
nodes:
  design:
    title: "Design"
  
  implementation:
    title: "Implementation"
    after: [design]
  
  testing:
    title: "Testing"
    after: [implementation]
```

### Semantics

- A node can start after **all** nodes in `after` are completed.
- Dependencies are defined in `nodes`, **not** in `schedule.nodes`.
- When computing schedule, only **scheduled** dependencies are considered.

### Rules

- Each element in `after` MUST be an existing `node_id`.
- Circular dependencies through `after` are **forbidden**.

## `milestone` Field (Milestones)

A milestone is a point-in-time event on the timeline, not a task with duration.

```yaml
nodes:
  release_v1:
    title: "Release v1.0"
    milestone: true
    after: [testing]
```

### Behavior

- A milestone is displayed as a point/diamond on the Gantt chart.
- When computing `start` from `after` for a milestone, the next workday is **not added**:
  - Regular node: `start = next_workday(max_finish)`
  - Milestone: `start = max_finish`

## `effort` Field (Work Estimation)

Abstract work estimate in relative units.

```yaml
meta:
  effort_unit: "sp"  # story points — for UI only

nodes:
  epic:
    title: "Authentication"
    effort: 13
  
  story1:
    title: "Email Login"
    parent: epic
    effort: 5
  
  story2:
    title: "OAuth Login"
    parent: epic
    effort: 8
```

### Requirements

- `effort` MUST be a **non-negative number** (≥ 0).
- The unit of measure is set in `meta.effort_unit` (for display only).

### Computed Metrics

For nodes with children, the following are automatically computed:

| Metric | Description |
|--------|-------------|
| `effort_rollup` | Sum of `effort_effective` of all direct children |
| `effort_effective` | `effort` if set, otherwise `effort_rollup` |
| `effort_gap` | `max(0, effort - effort_rollup)` — incomplete decomposition |

```yaml
# Computation example
nodes:
  epic:
    title: "Authentication"
    effort: 13
    # effort_rollup = 5 + 8 = 13
    # effort_effective = 13 (explicitly set)
    # effort_gap = max(0, 13 - 13) = 0
  
  story1:
    title: "Email Login"
    parent: epic
    effort: 5
    # effort_effective = 5 (leaf node)
  
  story2:
    title: "OAuth Login"
    parent: epic
    effort: 8
    # effort_effective = 8 (leaf node)
```

### Computation Algorithm

```python
def compute_effort(node_id):
    node = nodes[node_id]
    children = [n for n in nodes if nodes[n].parent == node_id]
    
    if not children:
        # Leaf node
        node.effort_effective = node.effort
        return
    
    # Node with children
    for child in children:
        compute_effort(child)
    
    node.effort_rollup = sum(nodes[c].effort_effective or 0 for c in children)
    
    if node.effort is not None:
        node.effort_effective = node.effort
        node.effort_gap = max(0, node.effort - node.effort_rollup)
    else:
        node.effort_effective = node.effort_rollup
```

## `status` Field

Reference to a status from the `statuses` dictionary.

```yaml
statuses:
  done: { label: "Done", color: "#22c55e" }

nodes:
  task:
    title: "Task"
    status: done
```

### Rules

- The `status` value MUST be a key from `statuses`.
- Non-existent status — **error**.

## `issue` and `notes` Fields

```yaml
nodes:
  task:
    title: "Implement API"
    issue: "JIRA-123"
    notes: |
      Consider:
      - Authentication
      - Rate limiting
```

## `x` Field (Extensions)

Namespace for custom fields not defined in the specification.

```yaml
nodes:
  task:
    title: "Task"
    x:
      assignee: "john"
      priority: high
      custom_field: "value"
```

## Example: Plan Without Schedule

A plan can be fully valid without calendar planning:

```yaml
version: 2
meta:
  id: backlog
  title: "Product Backlog"
  effort_unit: "sp"

nodes:
  epic1:
    title: "Authentication"
    kind: epic
    effort: 13
  
  story1:
    title: "Email Login"
    kind: user_story
    parent: epic1
    effort: 5
  
  story2:
    title: "OAuth Login"
    kind: user_story
    parent: epic1
    after: [story1]
    effort: 8
```

Such a plan can be rendered as tree, list, deps, but not as Gantt (no dates).
