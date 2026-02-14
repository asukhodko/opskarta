"""
Execution metrics computation for opskarta v2.

This module computes progress_rollup and progress_coverage
for all nodes in a plan using a bottom-up tree traversal,
weighted by effort_effective.

Key concepts:
- progress_rollup: weighted average of child progress by effort_effective
- progress_coverage: fraction of total effort_effective covered by progress data

Requires effort_metrics to be computed first.
"""

from collections import defaultdict
from typing import Optional

from specs.v2.tools.models import MergedPlan


def compute_execution_metrics(plan: MergedPlan) -> None:
    """
    Compute progress_rollup and progress_coverage for all nodes.

    Algorithm:
    1. For leaf nodes with execution data: use execution.progress directly
    2. For parent nodes: weighted rollup by effort_effective
       progress_rollup = sum(effort_effective_i * progress_i) / sum(effort_effective_i)
       progress_coverage = sum(effort_effective with data) / sum(all effort_effective)
    3. Bottom-up traversal (post-order)

    Requires compute_effort_metrics() to have been called first.

    Args:
        plan: MergedPlan with nodes and execution data. Nodes are
              modified in-place with progress_rollup and progress_coverage.
    """
    if plan.execution is None or not plan.nodes:
        return

    # Build parent-child tree
    children: dict[str, list[str]] = defaultdict(list)
    for node_id, node in plan.nodes.items():
        if node.parent and node.parent in plan.nodes:
            children[node.parent].append(node_id)

    visited: set[str] = set()

    def compute(node_id: str) -> tuple[Optional[float], Optional[float]]:
        """
        Recursively compute execution metrics.

        Returns (progress, coverage) for the node.
        - progress: weighted progress value or None
        - coverage: fraction of effort covered (0..1) or None
        """
        if node_id in visited:
            node = plan.nodes[node_id]
            return node.progress_rollup, node.progress_coverage

        visited.add(node_id)
        node = plan.nodes[node_id]
        child_ids = children.get(node_id, [])

        if not child_ids:
            # Leaf node — use execution data directly
            en = plan.execution.nodes.get(node_id)
            if en and en.progress is not None:
                node.progress_rollup = en.progress
                node.progress_coverage = 1.0
                return en.progress, 1.0
            else:
                node.progress_rollup = None
                node.progress_coverage = None
                return None, None

        # Parent node — aggregate from children
        weighted_sum = 0.0
        total_effort = 0.0
        covered_effort = 0.0

        for child_id in child_ids:
            child_progress, child_coverage = compute(child_id)
            child_node = plan.nodes[child_id]
            effort = child_node.effort_effective
            if effort is None or effort <= 0:
                continue

            total_effort += effort
            if child_progress is not None:
                weighted_sum += effort * child_progress
                if child_coverage is not None:
                    covered_effort += effort * child_coverage
                else:
                    covered_effort += effort

        if total_effort > 0 and covered_effort > 0:
            node.progress_rollup = weighted_sum / total_effort
            node.progress_coverage = covered_effort / total_effort
        else:
            node.progress_rollup = None
            node.progress_coverage = None

        return node.progress_rollup, node.progress_coverage

    # Find root nodes
    root_ids = [
        node_id for node_id, node in plan.nodes.items()
        if not node.parent or node.parent not in plan.nodes
    ]

    for root_id in root_ids:
        compute(root_id)

    # Handle orphans
    for node_id in plan.nodes:
        if node_id not in visited:
            compute(node_id)
