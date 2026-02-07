"""
Tests for the effort module.

Tests cover:
- 2.6: effort_rollup = sum of effort_effective of direct children
- 2.7: effort_gap = max(0, effort - effort_rollup) when node has effort and children
- 2.8: For leaf nodes, effort_effective = effort
- 2.9: For nodes with children, effort_effective = effort if set, else effort_rollup
"""

import unittest

from specs.v2.tools.effort import compute_effort_metrics
from specs.v2.tools.models import MergedPlan, Node


class TestComputeEffortMetricsEmpty(unittest.TestCase):
    """Tests for empty plans."""
    
    def test_empty_plan(self):
        """Empty plan should not raise errors."""
        plan = MergedPlan()
        
        compute_effort_metrics(plan)
        
        # No nodes to check, just verify no exception
        self.assertEqual(len(plan.nodes), 0)


class TestComputeEffortMetricsLeafNodes(unittest.TestCase):
    """Tests for leaf nodes (Requirement 2.8)."""
    
    def test_leaf_node_with_effort(self):
        """Leaf node: effort_effective = effort (Requirement 2.8)."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1", effort=5.0),
            }
        )
        
        compute_effort_metrics(plan)
        
        node = plan.nodes["task1"]
        self.assertEqual(node.effort_effective, 5.0)
        self.assertIsNone(node.effort_rollup)
        self.assertIsNone(node.effort_gap)
    
    def test_leaf_node_without_effort(self):
        """Leaf node without effort: effort_effective = None."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1"),
            }
        )
        
        compute_effort_metrics(plan)
        
        node = plan.nodes["task1"]
        self.assertIsNone(node.effort_effective)
        self.assertIsNone(node.effort_rollup)
        self.assertIsNone(node.effort_gap)
    
    def test_leaf_node_with_zero_effort(self):
        """Leaf node with zero effort: effort_effective = 0."""
        plan = MergedPlan(
            nodes={
                "milestone": Node(title="Milestone", effort=0),
            }
        )
        
        compute_effort_metrics(plan)
        
        node = plan.nodes["milestone"]
        self.assertEqual(node.effort_effective, 0)
        self.assertIsNone(node.effort_rollup)
    
    def test_multiple_leaf_nodes(self):
        """Multiple independent leaf nodes."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1", effort=5.0),
                "task2": Node(title="Task 2", effort=3.0),
                "task3": Node(title="Task 3"),
            }
        )
        
        compute_effort_metrics(plan)
        
        self.assertEqual(plan.nodes["task1"].effort_effective, 5.0)
        self.assertEqual(plan.nodes["task2"].effort_effective, 3.0)
        self.assertIsNone(plan.nodes["task3"].effort_effective)


class TestComputeEffortMetricsRollup(unittest.TestCase):
    """Tests for effort_rollup computation (Requirement 2.6)."""
    
    def test_parent_with_two_children(self):
        """effort_rollup = sum of children's effort_effective (Requirement 2.6)."""
        plan = MergedPlan(
            nodes={
                "parent": Node(title="Parent"),
                "child1": Node(title="Child 1", parent="parent", effort=5.0),
                "child2": Node(title="Child 2", parent="parent", effort=3.0),
            }
        )
        
        compute_effort_metrics(plan)
        
        parent = plan.nodes["parent"]
        self.assertEqual(parent.effort_rollup, 8.0)  # 5 + 3
    
    def test_parent_with_one_child(self):
        """Parent with single child."""
        plan = MergedPlan(
            nodes={
                "parent": Node(title="Parent"),
                "child": Node(title="Child", parent="parent", effort=7.0),
            }
        )
        
        compute_effort_metrics(plan)
        
        parent = plan.nodes["parent"]
        self.assertEqual(parent.effort_rollup, 7.0)
    
    def test_parent_with_children_without_effort(self):
        """Parent with children that have no effort."""
        plan = MergedPlan(
            nodes={
                "parent": Node(title="Parent"),
                "child1": Node(title="Child 1", parent="parent"),
                "child2": Node(title="Child 2", parent="parent"),
            }
        )
        
        compute_effort_metrics(plan)
        
        parent = plan.nodes["parent"]
        self.assertEqual(parent.effort_rollup, 0.0)
    
    def test_parent_with_mixed_children(self):
        """Parent with some children having effort, some not."""
        plan = MergedPlan(
            nodes={
                "parent": Node(title="Parent"),
                "child1": Node(title="Child 1", parent="parent", effort=5.0),
                "child2": Node(title="Child 2", parent="parent"),  # No effort
                "child3": Node(title="Child 3", parent="parent", effort=3.0),
            }
        )
        
        compute_effort_metrics(plan)
        
        parent = plan.nodes["parent"]
        self.assertEqual(parent.effort_rollup, 8.0)  # 5 + 0 + 3


class TestComputeEffortMetricsEffective(unittest.TestCase):
    """Tests for effort_effective computation (Requirement 2.9)."""
    
    def test_parent_without_own_effort(self):
        """Parent without effort: effort_effective = effort_rollup (Requirement 2.9)."""
        plan = MergedPlan(
            nodes={
                "parent": Node(title="Parent"),  # No effort
                "child1": Node(title="Child 1", parent="parent", effort=5.0),
                "child2": Node(title="Child 2", parent="parent", effort=3.0),
            }
        )
        
        compute_effort_metrics(plan)
        
        parent = plan.nodes["parent"]
        self.assertEqual(parent.effort_effective, 8.0)  # = rollup
    
    def test_parent_with_own_effort(self):
        """Parent with effort: effort_effective = effort (Requirement 2.9)."""
        plan = MergedPlan(
            nodes={
                "parent": Node(title="Parent", effort=20.0),
                "child1": Node(title="Child 1", parent="parent", effort=5.0),
                "child2": Node(title="Child 2", parent="parent", effort=3.0),
            }
        )
        
        compute_effort_metrics(plan)
        
        parent = plan.nodes["parent"]
        self.assertEqual(parent.effort_effective, 20.0)  # = own effort


class TestComputeEffortMetricsGap(unittest.TestCase):
    """Tests for effort_gap computation (Requirement 2.7)."""
    
    def test_gap_when_effort_greater_than_rollup(self):
        """effort_gap = effort - rollup when effort > rollup (Requirement 2.7)."""
        plan = MergedPlan(
            nodes={
                "epic": Node(title="Epic", effort=20.0),
                "story1": Node(title="Story 1", parent="epic", effort=5.0),
                "story2": Node(title="Story 2", parent="epic", effort=8.0),
            }
        )
        
        compute_effort_metrics(plan)
        
        epic = plan.nodes["epic"]
        self.assertEqual(epic.effort_rollup, 13.0)  # 5 + 8
        self.assertEqual(epic.effort_effective, 20.0)
        self.assertEqual(epic.effort_gap, 7.0)  # max(0, 20 - 13) = 7
    
    def test_gap_when_effort_equals_rollup(self):
        """effort_gap = 0 when effort = rollup (complete decomposition)."""
        plan = MergedPlan(
            nodes={
                "epic": Node(title="Epic", effort=13.0),
                "story1": Node(title="Story 1", parent="epic", effort=5.0),
                "story2": Node(title="Story 2", parent="epic", effort=8.0),
            }
        )
        
        compute_effort_metrics(plan)
        
        epic = plan.nodes["epic"]
        self.assertEqual(epic.effort_rollup, 13.0)
        self.assertEqual(epic.effort_gap, 0.0)  # max(0, 13 - 13) = 0
    
    def test_gap_when_effort_less_than_rollup(self):
        """effort_gap = 0 when effort < rollup (over-decomposition)."""
        plan = MergedPlan(
            nodes={
                "epic": Node(title="Epic", effort=10.0),
                "story1": Node(title="Story 1", parent="epic", effort=5.0),
                "story2": Node(title="Story 2", parent="epic", effort=8.0),
            }
        )
        
        compute_effort_metrics(plan)
        
        epic = plan.nodes["epic"]
        self.assertEqual(epic.effort_rollup, 13.0)
        self.assertEqual(epic.effort_gap, 0.0)  # max(0, 10 - 13) = 0
    
    def test_no_gap_when_no_own_effort(self):
        """No effort_gap when parent has no own effort."""
        plan = MergedPlan(
            nodes={
                "parent": Node(title="Parent"),  # No effort
                "child": Node(title="Child", parent="parent", effort=5.0),
            }
        )
        
        compute_effort_metrics(plan)
        
        parent = plan.nodes["parent"]
        self.assertIsNone(parent.effort_gap)
    
    def test_no_gap_for_leaf_nodes(self):
        """Leaf nodes have no effort_gap."""
        plan = MergedPlan(
            nodes={
                "task": Node(title="Task", effort=5.0),
            }
        )
        
        compute_effort_metrics(plan)
        
        task = plan.nodes["task"]
        self.assertIsNone(task.effort_gap)


class TestComputeEffortMetricsDeepHierarchy(unittest.TestCase):
    """Tests for deep hierarchies (multi-level trees)."""
    
    def test_three_level_hierarchy(self):
        """Three-level hierarchy: grandparent -> parent -> child."""
        plan = MergedPlan(
            nodes={
                "root": Node(title="Root"),
                "phase": Node(title="Phase", parent="root"),
                "task1": Node(title="Task 1", parent="phase", effort=5.0),
                "task2": Node(title="Task 2", parent="phase", effort=3.0),
            }
        )
        
        compute_effort_metrics(plan)
        
        # Leaf nodes
        self.assertEqual(plan.nodes["task1"].effort_effective, 5.0)
        self.assertEqual(plan.nodes["task2"].effort_effective, 3.0)
        
        # Phase (middle level)
        phase = plan.nodes["phase"]
        self.assertEqual(phase.effort_rollup, 8.0)
        self.assertEqual(phase.effort_effective, 8.0)
        
        # Root (top level)
        root = plan.nodes["root"]
        self.assertEqual(root.effort_rollup, 8.0)
        self.assertEqual(root.effort_effective, 8.0)
    
    def test_three_level_with_effort_at_all_levels(self):
        """Three-level hierarchy with effort at all levels."""
        plan = MergedPlan(
            nodes={
                "root": Node(title="Root", effort=50.0),
                "phase": Node(title="Phase", parent="root", effort=20.0),
                "task1": Node(title="Task 1", parent="phase", effort=5.0),
                "task2": Node(title="Task 2", parent="phase", effort=3.0),
            }
        )
        
        compute_effort_metrics(plan)
        
        # Phase
        phase = plan.nodes["phase"]
        self.assertEqual(phase.effort_rollup, 8.0)  # 5 + 3
        self.assertEqual(phase.effort_effective, 20.0)  # own effort
        self.assertEqual(phase.effort_gap, 12.0)  # max(0, 20 - 8)
        
        # Root - uses phase's effort_effective (20), not rollup (8)
        root = plan.nodes["root"]
        self.assertEqual(root.effort_rollup, 20.0)  # phase.effort_effective
        self.assertEqual(root.effort_effective, 50.0)  # own effort
        self.assertEqual(root.effort_gap, 30.0)  # max(0, 50 - 20)
    
    def test_multiple_branches(self):
        """Tree with multiple branches."""
        plan = MergedPlan(
            nodes={
                "root": Node(title="Root"),
                "branch1": Node(title="Branch 1", parent="root"),
                "branch2": Node(title="Branch 2", parent="root"),
                "leaf1a": Node(title="Leaf 1a", parent="branch1", effort=2.0),
                "leaf1b": Node(title="Leaf 1b", parent="branch1", effort=3.0),
                "leaf2a": Node(title="Leaf 2a", parent="branch2", effort=4.0),
            }
        )
        
        compute_effort_metrics(plan)
        
        # Branch 1
        branch1 = plan.nodes["branch1"]
        self.assertEqual(branch1.effort_rollup, 5.0)  # 2 + 3
        self.assertEqual(branch1.effort_effective, 5.0)
        
        # Branch 2
        branch2 = plan.nodes["branch2"]
        self.assertEqual(branch2.effort_rollup, 4.0)
        self.assertEqual(branch2.effort_effective, 4.0)
        
        # Root
        root = plan.nodes["root"]
        self.assertEqual(root.effort_rollup, 9.0)  # 5 + 4
        self.assertEqual(root.effort_effective, 9.0)


class TestComputeEffortMetricsMultipleRoots(unittest.TestCase):
    """Tests for plans with multiple root nodes."""
    
    def test_multiple_independent_trees(self):
        """Multiple independent trees (no common root)."""
        plan = MergedPlan(
            nodes={
                "tree1_root": Node(title="Tree 1 Root"),
                "tree1_child": Node(title="Tree 1 Child", parent="tree1_root", effort=5.0),
                "tree2_root": Node(title="Tree 2 Root"),
                "tree2_child": Node(title="Tree 2 Child", parent="tree2_root", effort=3.0),
            }
        )
        
        compute_effort_metrics(plan)
        
        # Tree 1
        self.assertEqual(plan.nodes["tree1_root"].effort_rollup, 5.0)
        self.assertEqual(plan.nodes["tree1_root"].effort_effective, 5.0)
        
        # Tree 2
        self.assertEqual(plan.nodes["tree2_root"].effort_rollup, 3.0)
        self.assertEqual(plan.nodes["tree2_root"].effort_effective, 3.0)


class TestComputeEffortMetricsEdgeCases(unittest.TestCase):
    """Tests for edge cases."""
    
    def test_float_effort_values(self):
        """Float effort values are handled correctly."""
        plan = MergedPlan(
            nodes={
                "parent": Node(title="Parent", effort=10.5),
                "child1": Node(title="Child 1", parent="parent", effort=3.5),
                "child2": Node(title="Child 2", parent="parent", effort=2.5),
            }
        )
        
        compute_effort_metrics(plan)
        
        parent = plan.nodes["parent"]
        self.assertEqual(parent.effort_rollup, 6.0)  # 3.5 + 2.5
        self.assertEqual(parent.effort_effective, 10.5)
        self.assertEqual(parent.effort_gap, 4.5)  # 10.5 - 6.0
    
    def test_zero_effort_children(self):
        """Children with zero effort contribute to rollup."""
        plan = MergedPlan(
            nodes={
                "parent": Node(title="Parent", effort=10.0),
                "child1": Node(title="Child 1", parent="parent", effort=0),
                "child2": Node(title="Child 2", parent="parent", effort=5.0),
            }
        )
        
        compute_effort_metrics(plan)
        
        parent = plan.nodes["parent"]
        self.assertEqual(parent.effort_rollup, 5.0)  # 0 + 5
        self.assertEqual(parent.effort_gap, 5.0)  # 10 - 5
    
    def test_orphan_node_with_nonexistent_parent(self):
        """Node with non-existent parent is treated as root."""
        plan = MergedPlan(
            nodes={
                "orphan": Node(title="Orphan", parent="nonexistent", effort=5.0),
            }
        )
        
        compute_effort_metrics(plan)
        
        orphan = plan.nodes["orphan"]
        self.assertEqual(orphan.effort_effective, 5.0)
        self.assertIsNone(orphan.effort_rollup)  # No children


class TestComputeEffortMetricsDesignExample(unittest.TestCase):
    """Tests based on examples from design.md."""
    
    def test_design_example_incomplete_decomposition(self):
        """
        Example from design.md: effort_gap shows incomplete decomposition.
        
        epic.effort = 20
        story1.effort = 5
        story2.effort = 8
        
        Expected:
        - epic.effort_rollup = 13 (5 + 8)
        - epic.effort_effective = 20 (explicitly set)
        - epic.effort_gap = 7 (max(0, 20 - 13) = 7, incomplete decomposition)
        """
        plan = MergedPlan(
            nodes={
                "epic": Node(title="Epic", effort=20.0),
                "story1": Node(title="Story 1", parent="epic", effort=5.0),
                "story2": Node(title="Story 2", parent="epic", effort=8.0),
            }
        )
        
        compute_effort_metrics(plan)
        
        epic = plan.nodes["epic"]
        self.assertEqual(epic.effort_rollup, 13.0)
        self.assertEqual(epic.effort_effective, 20.0)
        self.assertEqual(epic.effort_gap, 7.0)
    
    def test_design_example_complete_decomposition(self):
        """
        Complete decomposition: effort_gap = 0.
        
        epic.effort = 13
        story1.effort = 5
        story2.effort = 8
        
        Expected:
        - epic.effort_rollup = 13 (5 + 8)
        - epic.effort_effective = 13
        - epic.effort_gap = 0 (complete decomposition)
        """
        plan = MergedPlan(
            nodes={
                "epic": Node(title="Epic", effort=13.0),
                "story1": Node(title="Story 1", parent="epic", effort=5.0),
                "story2": Node(title="Story 2", parent="epic", effort=8.0),
            }
        )
        
        compute_effort_metrics(plan)
        
        epic = plan.nodes["epic"]
        self.assertEqual(epic.effort_rollup, 13.0)
        self.assertEqual(epic.effort_effective, 13.0)
        self.assertEqual(epic.effort_gap, 0.0)
    
    def test_design_example_no_own_effort(self):
        """
        Parent without own effort: effort_effective = effort_rollup.
        """
        plan = MergedPlan(
            nodes={
                "epic": Node(title="Epic"),  # No effort
                "story1": Node(title="Story 1", parent="epic", effort=5.0),
                "story2": Node(title="Story 2", parent="epic", effort=8.0),
            }
        )
        
        compute_effort_metrics(plan)
        
        epic = plan.nodes["epic"]
        self.assertEqual(epic.effort_rollup, 13.0)
        self.assertEqual(epic.effort_effective, 13.0)  # = rollup
        self.assertIsNone(epic.effort_gap)  # No gap when no own effort


if __name__ == "__main__":
    unittest.main()
