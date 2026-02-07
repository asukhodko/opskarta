"""
Tests for the common filtering and sorting module.

This module tests the shared functionality used by all renderers:
- apply_view_filter: Filter nodes based on ViewFilter criteria
- sort_nodes: Sort nodes by a specified field
- get_descendants: Get all descendants of a node

Requirements covered:
- 4.7: View filtering with where clause (kind, status, has_schedule, parent)
- 4.8: View sorting with order_by
- 4.9: Renderer uses calendar from Schedule for date calculations (not View)
"""

import unittest

from specs.v2.tools.models import (
    MergedPlan,
    Node,
    Schedule,
    ScheduleNode,
    ViewFilter,
)
from specs.v2.tools.render.common import (
    apply_view_filter,
    get_descendants,
    sort_nodes,
)


class TestGetDescendants(unittest.TestCase):
    """Tests for get_descendants function."""

    def test_no_children(self):
        """Node with no children returns empty set."""
        plan = MergedPlan(
            nodes={
                "root": Node(title="Root"),
                "other": Node(title="Other"),
            }
        )
        
        result = get_descendants(plan, "root")
        self.assertEqual(result, set())

    def test_direct_children(self):
        """Returns direct children."""
        plan = MergedPlan(
            nodes={
                "root": Node(title="Root"),
                "child1": Node(title="Child 1", parent="root"),
                "child2": Node(title="Child 2", parent="root"),
            }
        )
        
        result = get_descendants(plan, "root")
        self.assertEqual(result, {"child1", "child2"})

    def test_nested_descendants(self):
        """Returns all nested descendants."""
        plan = MergedPlan(
            nodes={
                "root": Node(title="Root"),
                "child": Node(title="Child", parent="root"),
                "grandchild": Node(title="Grandchild", parent="child"),
            }
        )
        
        result = get_descendants(plan, "root")
        self.assertEqual(result, {"child", "grandchild"})

    def test_deep_hierarchy(self):
        """Returns descendants from deep hierarchy."""
        plan = MergedPlan(
            nodes={
                "root": Node(title="Root"),
                "level1": Node(title="Level 1", parent="root"),
                "level2": Node(title="Level 2", parent="level1"),
                "level3": Node(title="Level 3", parent="level2"),
                "level4": Node(title="Level 4", parent="level3"),
            }
        )
        
        result = get_descendants(plan, "root")
        self.assertEqual(result, {"level1", "level2", "level3", "level4"})

    def test_multiple_branches(self):
        """Returns descendants from multiple branches."""
        plan = MergedPlan(
            nodes={
                "root": Node(title="Root"),
                "branch1": Node(title="Branch 1", parent="root"),
                "branch2": Node(title="Branch 2", parent="root"),
                "leaf1a": Node(title="Leaf 1a", parent="branch1"),
                "leaf1b": Node(title="Leaf 1b", parent="branch1"),
                "leaf2a": Node(title="Leaf 2a", parent="branch2"),
            }
        )
        
        result = get_descendants(plan, "root")
        self.assertEqual(result, {"branch1", "branch2", "leaf1a", "leaf1b", "leaf2a"})

    def test_nonexistent_parent(self):
        """Nonexistent parent returns empty set."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1"),
            }
        )
        
        result = get_descendants(plan, "nonexistent")
        self.assertEqual(result, set())


class TestApplyViewFilter(unittest.TestCase):
    """Tests for apply_view_filter function."""

    def test_no_filter(self):
        """No filter returns all nodes."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1"),
                "task2": Node(title="Task 2"),
            }
        )
        
        result = apply_view_filter(plan, ["task1", "task2"], None)
        self.assertEqual(result, ["task1", "task2"])

    def test_empty_filter(self):
        """Empty ViewFilter returns all nodes."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1"),
                "task2": Node(title="Task 2"),
            }
        )
        
        result = apply_view_filter(plan, ["task1", "task2"], ViewFilter())
        self.assertEqual(result, ["task1", "task2"])

    def test_filter_by_kind_single(self):
        """Filter by single kind."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1", kind="task"),
                "phase1": Node(title="Phase 1", kind="phase"),
                "task2": Node(title="Task 2", kind="task"),
            }
        )
        
        view_filter = ViewFilter(kind=["task"])
        result = apply_view_filter(plan, ["task1", "phase1", "task2"], view_filter)
        self.assertEqual(result, ["task1", "task2"])

    def test_filter_by_kind_multiple(self):
        """Filter by multiple kinds."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1", kind="task"),
                "phase1": Node(title="Phase 1", kind="phase"),
                "epic1": Node(title="Epic 1", kind="epic"),
            }
        )
        
        view_filter = ViewFilter(kind=["task", "epic"])
        result = apply_view_filter(plan, ["task1", "phase1", "epic1"], view_filter)
        self.assertEqual(result, ["task1", "epic1"])

    def test_filter_by_status_single(self):
        """Filter by single status."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1", status="done"),
                "task2": Node(title="Task 2", status="in_progress"),
                "task3": Node(title="Task 3", status="done"),
            }
        )
        
        view_filter = ViewFilter(status=["done"])
        result = apply_view_filter(plan, ["task1", "task2", "task3"], view_filter)
        self.assertEqual(result, ["task1", "task3"])

    def test_filter_by_status_multiple(self):
        """Filter by multiple statuses."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1", status="done"),
                "task2": Node(title="Task 2", status="in_progress"),
                "task3": Node(title="Task 3", status="not_started"),
            }
        )
        
        view_filter = ViewFilter(status=["done", "in_progress"])
        result = apply_view_filter(plan, ["task1", "task2", "task3"], view_filter)
        self.assertEqual(result, ["task1", "task2"])

    def test_filter_by_has_schedule_true(self):
        """Filter to only scheduled nodes."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1"),
                "task2": Node(title="Task 2"),
                "task3": Node(title="Task 3"),
            },
            schedule=Schedule(
                nodes={
                    "task1": ScheduleNode(start="2024-03-01"),
                    "task3": ScheduleNode(start="2024-03-05"),
                }
            )
        )
        
        view_filter = ViewFilter(has_schedule=True)
        result = apply_view_filter(plan, ["task1", "task2", "task3"], view_filter)
        self.assertEqual(result, ["task1", "task3"])

    def test_filter_by_has_schedule_false(self):
        """Filter to only unscheduled nodes."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1"),
                "task2": Node(title="Task 2"),
                "task3": Node(title="Task 3"),
            },
            schedule=Schedule(
                nodes={
                    "task1": ScheduleNode(start="2024-03-01"),
                }
            )
        )
        
        view_filter = ViewFilter(has_schedule=False)
        result = apply_view_filter(plan, ["task1", "task2", "task3"], view_filter)
        self.assertEqual(result, ["task2", "task3"])

    def test_filter_by_has_schedule_no_schedule_block(self):
        """Filter by has_schedule when plan has no schedule block."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1"),
                "task2": Node(title="Task 2"),
            }
        )
        
        # has_schedule=True should return empty (no schedule block)
        view_filter = ViewFilter(has_schedule=True)
        result = apply_view_filter(plan, ["task1", "task2"], view_filter)
        self.assertEqual(result, [])
        
        # has_schedule=False should return all (no schedule block)
        view_filter = ViewFilter(has_schedule=False)
        result = apply_view_filter(plan, ["task1", "task2"], view_filter)
        self.assertEqual(result, ["task1", "task2"])

    def test_filter_by_parent(self):
        """Filter to descendants of a parent."""
        plan = MergedPlan(
            nodes={
                "root": Node(title="Root"),
                "phase1": Node(title="Phase 1", parent="root"),
                "task1": Node(title="Task 1", parent="phase1"),
                "other": Node(title="Other"),
            }
        )
        
        view_filter = ViewFilter(parent="root")
        result = apply_view_filter(plan, ["root", "phase1", "task1", "other"], view_filter)
        self.assertEqual(result, ["phase1", "task1"])

    def test_combined_filters_and_logic(self):
        """Multiple filter criteria are ANDed."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1", kind="task", status="done"),
                "task2": Node(title="Task 2", kind="task", status="in_progress"),
                "phase1": Node(title="Phase 1", kind="phase", status="done"),
            }
        )
        
        view_filter = ViewFilter(kind=["task"], status=["done"])
        result = apply_view_filter(plan, ["task1", "task2", "phase1"], view_filter)
        self.assertEqual(result, ["task1"])

    def test_preserves_order(self):
        """Filter preserves original order of node IDs."""
        plan = MergedPlan(
            nodes={
                "c": Node(title="C", kind="task"),
                "a": Node(title="A", kind="task"),
                "b": Node(title="B", kind="task"),
            }
        )
        
        view_filter = ViewFilter(kind=["task"])
        result = apply_view_filter(plan, ["c", "a", "b"], view_filter)
        self.assertEqual(result, ["c", "a", "b"])

    def test_nonexistent_node_skipped(self):
        """Nonexistent nodes in input list are skipped when filter is applied."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1", kind="task"),
            }
        )
        
        # With a filter, nonexistent nodes are skipped
        view_filter = ViewFilter(kind=["task"])
        result = apply_view_filter(plan, ["task1", "nonexistent", "task1"], view_filter)
        self.assertEqual(result, ["task1", "task1"])


class TestSortNodes(unittest.TestCase):
    """Tests for sort_nodes function."""

    def test_no_order_by(self):
        """No order_by returns nodes unchanged."""
        plan = MergedPlan(
            nodes={
                "b": Node(title="B"),
                "a": Node(title="A"),
                "c": Node(title="C"),
            }
        )
        
        result = sort_nodes(plan, ["b", "a", "c"], None)
        self.assertEqual(result, ["b", "a", "c"])

    def test_sort_by_title(self):
        """Sort by title."""
        plan = MergedPlan(
            nodes={
                "b": Node(title="Beta"),
                "a": Node(title="Alpha"),
                "c": Node(title="Charlie"),
            }
        )
        
        result = sort_nodes(plan, ["b", "a", "c"], "title")
        self.assertEqual(result, ["a", "b", "c"])

    def test_sort_by_status(self):
        """Sort by status."""
        plan = MergedPlan(
            nodes={
                "t1": Node(title="Task 1", status="not_started"),
                "t2": Node(title="Task 2", status="done"),
                "t3": Node(title="Task 3", status="in_progress"),
            }
        )
        
        result = sort_nodes(plan, ["t1", "t2", "t3"], "status")
        # Alphabetical: done, in_progress, not_started
        self.assertEqual(result, ["t2", "t3", "t1"])

    def test_sort_by_kind(self):
        """Sort by kind."""
        plan = MergedPlan(
            nodes={
                "t1": Node(title="Task 1", kind="task"),
                "p1": Node(title="Phase 1", kind="phase"),
                "e1": Node(title="Epic 1", kind="epic"),
            }
        )
        
        result = sort_nodes(plan, ["t1", "p1", "e1"], "kind")
        # Alphabetical: epic, phase, task
        self.assertEqual(result, ["e1", "p1", "t1"])

    def test_sort_by_effort(self):
        """Sort by effort."""
        plan = MergedPlan(
            nodes={
                "t1": Node(title="Task 1", effort=5),
                "t2": Node(title="Task 2", effort=3),
                "t3": Node(title="Task 3", effort=8),
            }
        )
        
        result = sort_nodes(plan, ["t1", "t2", "t3"], "effort")
        self.assertEqual(result, ["t2", "t1", "t3"])  # 3, 5, 8

    def test_sort_by_effort_uses_effort_effective(self):
        """Sort by effort uses effort_effective when available."""
        plan = MergedPlan(
            nodes={
                "t1": Node(title="Task 1", effort=10),
                "t2": Node(title="Task 2", effort=5),
            }
        )
        # Simulate computed effort_effective
        plan.nodes["t1"].effort_effective = 2  # Lower than t2's effort
        
        result = sort_nodes(plan, ["t1", "t2"], "effort")
        self.assertEqual(result, ["t1", "t2"])  # 2, 5

    def test_sort_by_effort_effective(self):
        """Sort by effort_effective field."""
        plan = MergedPlan(
            nodes={
                "t1": Node(title="Task 1"),
                "t2": Node(title="Task 2"),
            }
        )
        plan.nodes["t1"].effort_effective = 10
        plan.nodes["t2"].effort_effective = 5
        
        result = sort_nodes(plan, ["t1", "t2"], "effort_effective")
        self.assertEqual(result, ["t2", "t1"])  # 5, 10

    def test_sort_handles_none_values(self):
        """Sort handles None values gracefully."""
        plan = MergedPlan(
            nodes={
                "t1": Node(title="Task 1", status="done"),
                "t2": Node(title="Task 2"),  # No status
                "t3": Node(title="Task 3", status="in_progress"),
            }
        )
        
        result = sort_nodes(plan, ["t1", "t2", "t3"], "status")
        # Empty string sorts before other values
        self.assertEqual(result, ["t2", "t1", "t3"])

    def test_sort_handles_none_effort(self):
        """Sort handles None effort values."""
        plan = MergedPlan(
            nodes={
                "t1": Node(title="Task 1", effort=5),
                "t2": Node(title="Task 2"),  # No effort
                "t3": Node(title="Task 3", effort=3),
            }
        )
        
        result = sort_nodes(plan, ["t1", "t2", "t3"], "effort")
        # None effort treated as 0
        self.assertEqual(result, ["t2", "t3", "t1"])  # 0, 3, 5

    def test_sort_dynamic_attribute(self):
        """Sort by dynamic attribute."""
        plan = MergedPlan(
            nodes={
                "t1": Node(title="Task 1", issue="PROJ-3"),
                "t2": Node(title="Task 2", issue="PROJ-1"),
                "t3": Node(title="Task 3", issue="PROJ-2"),
            }
        )
        
        result = sort_nodes(plan, ["t1", "t2", "t3"], "issue")
        self.assertEqual(result, ["t2", "t3", "t1"])  # PROJ-1, PROJ-2, PROJ-3


class TestFilterAndSortIntegration(unittest.TestCase):
    """Integration tests for combined filtering and sorting."""

    def test_filter_then_sort(self):
        """Filter and sort can be combined."""
        plan = MergedPlan(
            nodes={
                "t1": Node(title="Task C", kind="task", effort=5),
                "t2": Node(title="Task A", kind="task", effort=3),
                "t3": Node(title="Task B", kind="task", effort=8),
                "p1": Node(title="Phase 1", kind="phase", effort=10),
            }
        )
        
        # Filter to tasks only
        view_filter = ViewFilter(kind=["task"])
        filtered = apply_view_filter(plan, ["t1", "t2", "t3", "p1"], view_filter)
        
        # Sort by title
        sorted_result = sort_nodes(plan, filtered, "title")
        
        self.assertEqual(sorted_result, ["t2", "t3", "t1"])  # A, B, C

    def test_empty_filter_result_sort(self):
        """Sorting empty filter result returns empty list."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1", kind="task"),
            }
        )
        
        view_filter = ViewFilter(kind=["nonexistent"])
        filtered = apply_view_filter(plan, ["task1"], view_filter)
        sorted_result = sort_nodes(plan, filtered, "title")
        
        self.assertEqual(sorted_result, [])


if __name__ == "__main__":
    unittest.main()


class TestEscapeMermaidString(unittest.TestCase):
    """Tests for escape_mermaid_string function."""

    def test_escape_hash(self):
        """Hash is escaped to entity code."""
        from specs.v2.tools.render.common import escape_mermaid_string
        
        result = escape_mermaid_string("Task #1")
        self.assertEqual(result, "Task #35;1")

    def test_escape_double_quote(self):
        """Double quote is escaped to entity code."""
        from specs.v2.tools.render.common import escape_mermaid_string
        
        result = escape_mermaid_string('Say "Hello"')
        self.assertEqual(result, "Say #quot;Hello#quot;")

    def test_escape_both(self):
        """Both hash and quote are escaped."""
        from specs.v2.tools.render.common import escape_mermaid_string
        
        result = escape_mermaid_string('Task #1: "Important"')
        self.assertEqual(result, "Task #35;1: #quot;Important#quot;")

    def test_escape_order_matters(self):
        """Hash is escaped before quote (order matters for entity codes)."""
        from specs.v2.tools.render.common import escape_mermaid_string
        
        # If we escaped " first to #quot;, then # would turn it into #35;quot;
        # So we must escape # first
        result = escape_mermaid_string('#"')
        self.assertEqual(result, "#35;#quot;")

    def test_no_special_chars(self):
        """Text without special chars is unchanged."""
        from specs.v2.tools.render.common import escape_mermaid_string
        
        result = escape_mermaid_string("Simple task title")
        self.assertEqual(result, "Simple task title")

    def test_empty_string(self):
        """Empty string returns empty string."""
        from specs.v2.tools.render.common import escape_mermaid_string
        
        result = escape_mermaid_string("")
        self.assertEqual(result, "")


class TestSanitizeMermaidText(unittest.TestCase):
    """Tests for sanitize_mermaid_text function."""

    def test_remove_colon(self):
        """Colon is replaced with space."""
        from specs.v2.tools.render.common import sanitize_mermaid_text
        
        result = sanitize_mermaid_text("Phase 1: Setup")
        self.assertEqual(result, "Phase 1 Setup")

    def test_remove_fullwidth_colon(self):
        """Full-width colon is replaced with space."""
        from specs.v2.tools.render.common import sanitize_mermaid_text
        
        result = sanitize_mermaid_text("Phase 1： Setup")
        self.assertEqual(result, "Phase 1 Setup")

    def test_multiple_colons(self):
        """Multiple colons are all replaced."""
        from specs.v2.tools.render.common import sanitize_mermaid_text
        
        result = sanitize_mermaid_text("A: B: C")
        self.assertEqual(result, "A B C")

    def test_collapse_whitespace(self):
        """Multiple spaces are collapsed to single space."""
        from specs.v2.tools.render.common import sanitize_mermaid_text
        
        result = sanitize_mermaid_text("Task   with   spaces")
        self.assertEqual(result, "Task with spaces")

    def test_no_special_chars(self):
        """Text without special chars is unchanged."""
        from specs.v2.tools.render.common import sanitize_mermaid_text
        
        result = sanitize_mermaid_text("Simple task")
        self.assertEqual(result, "Simple task")

    def test_empty_string(self):
        """Empty string returns empty string."""
        from specs.v2.tools.render.common import sanitize_mermaid_text
        
        result = sanitize_mermaid_text("")
        self.assertEqual(result, "")
