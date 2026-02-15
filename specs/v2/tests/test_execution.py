"""
Tests for the execution module (compute_execution_metrics).

Tests cover:
- Leaf node with progress data
- Leaf node without execution data
- Parent node with full coverage weighted rollup
- Parent node with partial coverage (denominator = covered_effort)
- Deep hierarchy (3 levels)
- No execution data → no-op
- Zero effort children skipped
"""

import unittest

from specs.v2.tools.models import (
    Execution,
    ExecutionNode,
    MergedPlan,
    Node,
)
from specs.v2.tools.execution import compute_execution_metrics


class TestComputeExecutionMetrics(unittest.TestCase):
    """Tests for compute_execution_metrics."""

    def test_leaf_with_progress(self):
        """Leaf node with execution data gets progress_rollup = progress."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1", effort=5, effort_effective=5),
            },
            execution=Execution(nodes={
                "task1": ExecutionNode(progress=0.75),
            }),
        )
        compute_execution_metrics(plan)
        self.assertAlmostEqual(plan.nodes["task1"].progress_rollup, 0.75)
        self.assertAlmostEqual(plan.nodes["task1"].progress_coverage, 1.0)

    def test_leaf_without_execution(self):
        """Leaf node without execution data gets None."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1", effort=5, effort_effective=5),
            },
            execution=Execution(nodes={}),
        )
        compute_execution_metrics(plan)
        self.assertIsNone(plan.nodes["task1"].progress_rollup)
        self.assertIsNone(plan.nodes["task1"].progress_coverage)

    def test_parent_full_coverage(self):
        """Parent with all children having progress → weighted rollup, coverage=1.0."""
        plan = MergedPlan(
            nodes={
                "epic": Node(title="Epic", effort=13, effort_effective=13),
                "task1": Node(title="Task 1", parent="epic", effort=5, effort_effective=5),
                "task2": Node(title="Task 2", parent="epic", effort=8, effort_effective=8),
            },
            execution=Execution(nodes={
                "task1": ExecutionNode(progress=1.0),
                "task2": ExecutionNode(progress=0.3),
            }),
        )
        compute_execution_metrics(plan)
        # rollup = (5*1.0 + 8*0.3) / (5+8) = 7.4/13 ≈ 0.569
        self.assertAlmostEqual(plan.nodes["epic"].progress_rollup, 7.4 / 13, places=5)
        self.assertAlmostEqual(plan.nodes["epic"].progress_coverage, 1.0)

    def test_parent_partial_coverage(self):
        """Parent with partial coverage → denominator = covered_effort only."""
        plan = MergedPlan(
            nodes={
                "epic": Node(title="Epic", effort=13, effort_effective=13),
                "task1": Node(title="Task 1", parent="epic", effort=5, effort_effective=5),
                "task2": Node(title="Task 2", parent="epic", effort=8, effort_effective=8),
            },
            execution=Execution(nodes={
                "task1": ExecutionNode(progress=1.0),
                # task2 has no execution data
            }),
        )
        compute_execution_metrics(plan)
        # Only task1 has data: rollup = (5*1.0) / 5 = 1.0
        # coverage = 5 / 13 ≈ 0.385
        self.assertAlmostEqual(plan.nodes["epic"].progress_rollup, 1.0, places=5)
        self.assertAlmostEqual(plan.nodes["epic"].progress_coverage, 5.0 / 13.0, places=5)

    def test_deep_hierarchy(self):
        """Three-level hierarchy rolls up correctly."""
        plan = MergedPlan(
            nodes={
                "root": Node(title="Root", effort=10, effort_effective=10),
                "mid": Node(title="Mid", parent="root", effort=10, effort_effective=10),
                "leaf1": Node(title="Leaf 1", parent="mid", effort=4, effort_effective=4),
                "leaf2": Node(title="Leaf 2", parent="mid", effort=6, effort_effective=6),
            },
            execution=Execution(nodes={
                "leaf1": ExecutionNode(progress=0.5),
                "leaf2": ExecutionNode(progress=1.0),
            }),
        )
        compute_execution_metrics(plan)
        # mid = (4*0.5 + 6*1.0) / (4+6) = 8.0/10 = 0.8
        self.assertAlmostEqual(plan.nodes["mid"].progress_rollup, 0.8, places=5)
        self.assertAlmostEqual(plan.nodes["mid"].progress_coverage, 1.0)
        # root only has mid as child, which itself has rollup 0.8
        self.assertAlmostEqual(plan.nodes["root"].progress_rollup, 0.8, places=5)
        self.assertAlmostEqual(plan.nodes["root"].progress_coverage, 1.0)

    def test_no_execution(self):
        """No execution data → no-op, progress_rollup stays None."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1", effort=5, effort_effective=5),
            },
            execution=None,
        )
        compute_execution_metrics(plan)
        self.assertIsNone(plan.nodes["task1"].progress_rollup)

    def test_empty_nodes(self):
        """Empty nodes dict → no-op."""
        plan = MergedPlan(
            nodes={},
            execution=Execution(nodes={}),
        )
        compute_execution_metrics(plan)

    def test_zero_effort_children_skipped(self):
        """Children with zero effort are excluded from rollup."""
        plan = MergedPlan(
            nodes={
                "epic": Node(title="Epic", effort=5, effort_effective=5),
                "task1": Node(title="Task 1", parent="epic", effort=5, effort_effective=5),
                "task2": Node(title="Task 2", parent="epic", effort=0, effort_effective=0),
            },
            execution=Execution(nodes={
                "task1": ExecutionNode(progress=0.6),
                "task2": ExecutionNode(progress=1.0),
            }),
        )
        compute_execution_metrics(plan)
        # task2 has 0 effort → skipped; rollup = 0.6
        self.assertAlmostEqual(plan.nodes["epic"].progress_rollup, 0.6, places=5)

    def test_leaf_progress_zero(self):
        """Leaf with progress=0.0 is still valid data (not None)."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1", effort=5, effort_effective=5),
            },
            execution=Execution(nodes={
                "task1": ExecutionNode(progress=0.0),
            }),
        )
        compute_execution_metrics(plan)
        self.assertAlmostEqual(plan.nodes["task1"].progress_rollup, 0.0)
        self.assertAlmostEqual(plan.nodes["task1"].progress_coverage, 1.0)


if __name__ == "__main__":
    unittest.main()
