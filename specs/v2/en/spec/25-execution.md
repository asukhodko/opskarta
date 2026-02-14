# Execution (Progress Tracking)

Execution is an **optional** overlay for tracking plan-vs-fact data: actual progress, dates, and confidence.

## Concept

The execution block mirrors the schedule overlay pattern:

- **Nodes** describe work structure
- **Schedule** adds calendar planning
- **Execution** adds progress tracking on top

A plan can exist without execution data. Execution data can be maintained in a separate fragment file.

## Execution Block Structure

```yaml
execution:
  nodes:
    <node_id>:
      progress: 0.75
      actual_start: "2024-03-01"
      actual_finish: "2024-03-15"
      updated_at: "2024-03-15T10:30:00Z"
      confidence: 0.9
      note: "On track"
```

## execution.nodes Fields

| Field | Type | Description |
|-------|------|-------------|
| `progress` | number | Completion from 0.0 to 1.0 |
| `actual_start` | string | Actual start date (YYYY-MM-DD) |
| `actual_finish` | string | Actual finish date (YYYY-MM-DD) |
| `updated_at` | string | Timestamp of last update (ISO 8601) |
| `confidence` | number | Confidence level from 0.0 to 1.0 |
| `note` | string | Optional annotation |

## Progress Rollup

For parent nodes, progress is automatically computed using effort-weighted rollup:

```
progress_rollup = sum(effort_effective_i * progress_i) / sum(effort_effective_i)
```

Only children with execution data participate in the rollup.

### Progress Coverage

`progress_coverage` indicates what fraction of total effort has progress data:

```
progress_coverage = sum(effort_effective with data) / sum(total effort_effective)
```

### Computation Algorithm

```python
def compute_execution_metrics(node_id):
    children = [n for n in nodes if nodes[n].parent == node_id]

    if not children:
        # Leaf node: use direct execution data
        if execution.nodes.get(node_id):
            node.progress_rollup = execution.nodes[node_id].progress
        return

    # Parent node: weighted rollup
    total_effort = 0
    covered_effort = 0
    weighted_sum = 0

    for child in children:
        compute_execution_metrics(child)
        effort = child.effort_effective or 0
        total_effort += effort

        if child.progress_rollup is not None:
            covered_effort += effort
            weighted_sum += effort * child.progress_rollup

    if covered_effort > 0:
        node.progress_rollup = weighted_sum / covered_effort
        node.progress_coverage = covered_effort / total_effort if total_effort > 0 else None
```

## Rules

- `node_id` in `execution.nodes` MUST exist in `nodes`.
- `progress` MUST be in range [0.0, 1.0].
- `confidence` MUST be in range [0.0, 1.0].
- `actual_start` and `actual_finish` MUST be valid `YYYY-MM-DD` dates.

## Example

```yaml
version: 2

nodes:
  epic:
    title: "Authentication"
    effort: 13
  login:
    title: "Email Login"
    parent: epic
    effort: 5
  oauth:
    title: "OAuth Login"
    parent: epic
    effort: 8

execution:
  nodes:
    login:
      progress: 1.0
      actual_start: "2024-03-01"
      actual_finish: "2024-03-05"
      confidence: 1.0
    oauth:
      progress: 0.3
      actual_start: "2024-03-06"
      confidence: 0.7
      note: "Provider API integration delayed"
```

In this example:
- `login`: 100% complete, effort 5
- `oauth`: 30% complete, effort 8
- `epic` rollup: (5 × 1.0 + 8 × 0.3) / (5 + 8) = 7.4 / 13 ≈ 0.57 (57%)
- `epic` coverage: (5 + 8) / 13 = 1.0 (100%)
