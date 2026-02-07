"""
Tests for the Tree renderer module.

Tests cover:
- 5.6: render_tree(plan: Merged_Plan, view_id: Optional[string]) -> string
- 5.9: Apply filtering and sorting from view if view_id is provided
- 4.7: View filtering with where clause
- 4.8: View sorting with order_by
"""

import unittest

from specs.v2.tools.models import (
    Calendar,
    MergedPlan,
    Meta,
    Node,
    Schedule,
    ScheduleNode,
    View,
    ViewFilter,
)
from specs.v2.tools.render.tree import (
    apply_view_filter,
    render_tree,
    _get_descendants,
    _get_children,
    _sort_nodes,
    _format_node_line,
)
from specs.v2.tools.effort import compute_effort_metrics


class TestGetDescendants(unittest.TestCase):
    """Tests for _get_descendants helper function."""

    def test_no_children(self):
        """Node with no children returns empty set."""
        plan = MergedPlan(
            nodes={
                "root": Node(title="Root"),
                "other": Node(title="Other"),
            }
        )
        
        result = _get_descendants(plan, "root")
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
        
        result = _get_descendants(plan, "root")
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
        
        result = _get_descendants(plan, "root")
        self.assertEqual(result, {"child", "grandchild"})


class TestGetChildren(unittest.TestCase):
    """Tests for _get_children helper function."""

    def test_no_children(self):
        """Node with no children returns empty list."""
        plan = MergedPlan(
            nodes={
                "root": Node(title="Root"),
            }
        )
        
        result = _get_children(plan, "root")
        self.assertEqual(result, [])

    def test_root_nodes(self):
        """None parent returns root nodes."""
        plan = MergedPlan(
            nodes={
                "root1": Node(title="Root 1"),
                "root2": Node(title="Root 2"),
                "child": Node(title="Child", parent="root1"),
            }
        )
        
        result = _get_children(plan, None)
        self.assertIn("root1", result)
        self.assertIn("root2", result)
        self.assertNotIn("child", result)

    def test_direct_children_only(self):
        """Returns only direct children, not grandchildren."""
        plan = MergedPlan(
            nodes={
                "root": Node(title="Root"),
                "child": Node(title="Child", parent="root"),
                "grandchild": Node(title="Grandchild", parent="child"),
            }
        )
        
        result = _get_children(plan, "root")
        self.assertEqual(result, ["child"])


class TestSortNodes(unittest.TestCase):
    """Tests for _sort_nodes helper function."""

    def test_no_order_by(self):
        """No order_by returns nodes unchanged."""
        plan = MergedPlan(
            nodes={
                "b": Node(title="B"),
                "a": Node(title="A"),
                "c": Node(title="C"),
            }
        )
        
        result = _sort_nodes(plan, ["b", "a", "c"], None)
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
        
        result = _sort_nodes(plan, ["b", "a", "c"], "title")
        self.assertEqual(result, ["a", "b", "c"])

    def test_sort_by_status(self):
        """Sort by status."""
        plan = MergedPlan(
            nodes={
                "t1": Node(title="Task 1", status="done"),
                "t2": Node(title="Task 2", status="in_progress"),
                "t3": Node(title="Task 3", status="not_started"),
            }
        )
        
        result = _sort_nodes(plan, ["t1", "t2", "t3"], "status")
        self.assertEqual(result, ["t1", "t2", "t3"])  # done, in_progress, not_started

    def test_sort_by_effort(self):
        """Sort by effort."""
        plan = MergedPlan(
            nodes={
                "t1": Node(title="Task 1", effort=5),
                "t2": Node(title="Task 2", effort=3),
                "t3": Node(title="Task 3", effort=8),
            }
        )
        
        result = _sort_nodes(plan, ["t1", "t2", "t3"], "effort")
        self.assertEqual(result, ["t2", "t1", "t3"])  # 3, 5, 8


class TestFormatNodeLine(unittest.TestCase):
    """Tests for _format_node_line helper function."""

    def test_simple_node(self):
        """Simple node with just title."""
        plan = MergedPlan(
            nodes={"task1": Node(title="Task 1")}
        )
        
        result = _format_node_line(plan, "task1", "", False)
        self.assertEqual(result, "├── Task 1")

    def test_last_node(self):
        """Last node uses └── connector."""
        plan = MergedPlan(
            nodes={"task1": Node(title="Task 1")}
        )
        
        result = _format_node_line(plan, "task1", "", True)
        self.assertEqual(result, "└── Task 1")

    def test_node_with_status(self):
        """Node with status shows [status]."""
        plan = MergedPlan(
            nodes={"task1": Node(title="Task 1", status="done")}
        )
        
        result = _format_node_line(plan, "task1", "", False)
        self.assertEqual(result, "├── Task 1 [done]")

    def test_node_with_effort(self):
        """Node with effort shows (effort)."""
        plan = MergedPlan(
            nodes={"task1": Node(title="Task 1", effort=5)}
        )
        
        result = _format_node_line(plan, "task1", "", False)
        self.assertEqual(result, "├── Task 1 (5)")

    def test_node_with_effort_unit(self):
        """Node with effort and meta.effort_unit shows unit."""
        plan = MergedPlan(
            meta=Meta(effort_unit="sp"),
            nodes={"task1": Node(title="Task 1", effort=5)}
        )
        
        result = _format_node_line(plan, "task1", "", False)
        self.assertEqual(result, "├── Task 1 (5 sp)")

    def test_node_with_status_and_effort(self):
        """Node with both status and effort."""
        plan = MergedPlan(
            meta=Meta(effort_unit="sp"),
            nodes={"task1": Node(title="Task 1", status="in_progress", effort=5)}
        )
        
        result = _format_node_line(plan, "task1", "", False)
        self.assertEqual(result, "├── Task 1 [in_progress] (5 sp)")

    def test_node_with_prefix(self):
        """Node with indentation prefix."""
        plan = MergedPlan(
            nodes={"task1": Node(title="Task 1")}
        )
        
        result = _format_node_line(plan, "task1", "│   ", False)
        self.assertEqual(result, "│   ├── Task 1")

    def test_node_with_effort_effective(self):
        """Node with effort_effective uses it over effort."""
        plan = MergedPlan(
            nodes={"task1": Node(title="Task 1", effort=10)}
        )
        # Simulate computed effort_effective
        plan.nodes["task1"].effort_effective = 15
        
        result = _format_node_line(plan, "task1", "", False)
        self.assertEqual(result, "├── Task 1 (15)")


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

    def test_filter_by_kind(self):
        """Filter by kind."""
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

    def test_filter_by_status(self):
        """Filter by status."""
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

    def test_combined_filters(self):
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


class TestRenderTreeBasic(unittest.TestCase):
    """Basic tests for render_tree function."""

    def test_empty_plan(self):
        """Plan with no nodes returns empty string."""
        plan = MergedPlan(nodes={})
        
        result = render_tree(plan)
        self.assertEqual(result, "")

    def test_single_node(self):
        """Single root node."""
        plan = MergedPlan(
            nodes={"task1": Node(title="Task 1")}
        )
        
        result = render_tree(plan)
        self.assertEqual(result, "└── Task 1")

    def test_two_root_nodes(self):
        """Two root nodes."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1"),
                "task2": Node(title="Task 2"),
            }
        )
        
        result = render_tree(plan)
        lines = result.split("\n")
        
        # Should have two lines
        self.assertEqual(len(lines), 2)
        # First uses ├──, last uses └──
        self.assertTrue(lines[0].startswith("├──"))
        self.assertTrue(lines[1].startswith("└──"))

    def test_parent_child_hierarchy(self):
        """Parent-child hierarchy."""
        plan = MergedPlan(
            nodes={
                "phase1": Node(title="Phase 1"),
                "task1": Node(title="Task 1", parent="phase1"),
            }
        )
        
        result = render_tree(plan)
        lines = result.split("\n")
        
        self.assertEqual(len(lines), 2)
        self.assertIn("Phase 1", lines[0])
        self.assertIn("Task 1", lines[1])
        # Child should be indented
        self.assertIn("    └── Task 1", lines[1])

    def test_multiple_children(self):
        """Multiple children under one parent."""
        plan = MergedPlan(
            nodes={
                "phase1": Node(title="Phase 1"),
                "task1": Node(title="Task 1", parent="phase1"),
                "task2": Node(title="Task 2", parent="phase1"),
            }
        )
        
        result = render_tree(plan)
        lines = result.split("\n")
        
        self.assertEqual(len(lines), 3)
        self.assertIn("Phase 1", lines[0])
        # First child uses ├──
        self.assertIn("├── Task", lines[1])
        # Last child uses └──
        self.assertIn("└── Task", lines[2])

    def test_deep_hierarchy(self):
        """Deep hierarchy with grandchildren."""
        plan = MergedPlan(
            nodes={
                "root": Node(title="Root"),
                "phase1": Node(title="Phase 1", parent="root"),
                "task1": Node(title="Task 1", parent="phase1"),
            }
        )
        
        result = render_tree(plan)
        lines = result.split("\n")
        
        self.assertEqual(len(lines), 3)
        self.assertIn("Root", lines[0])
        self.assertIn("Phase 1", lines[1])
        self.assertIn("Task 1", lines[2])
        # Task should have double indentation
        self.assertIn("        └── Task 1", lines[2])

    def test_node_with_status(self):
        """Node with status is displayed."""
        plan = MergedPlan(
            nodes={"task1": Node(title="Task 1", status="done")}
        )
        
        result = render_tree(plan)
        self.assertIn("[done]", result)

    def test_node_with_effort(self):
        """Node with effort is displayed."""
        plan = MergedPlan(
            meta=Meta(effort_unit="sp"),
            nodes={"task1": Node(title="Task 1", effort=5)}
        )
        
        result = render_tree(plan)
        self.assertIn("(5 sp)", result)


class TestRenderTreeWithView(unittest.TestCase):
    """Tests for render_tree with view configuration."""

    def test_view_not_found(self):
        """Non-existent view raises ValueError."""
        plan = MergedPlan(
            nodes={"task1": Node(title="Task 1")}
        )
        
        with self.assertRaises(ValueError) as ctx:
            render_tree(plan, "nonexistent")
        
        self.assertIn("nonexistent", str(ctx.exception))

    def test_view_filter_by_kind(self):
        """View where.kind filters nodes."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1", kind="task"),
                "phase1": Node(title="Phase 1", kind="phase"),
                "task2": Node(title="Task 2", kind="task"),
            },
            views={"tasks_only": View(where=ViewFilter(kind=["task"]))}
        )
        
        result = render_tree(plan, "tasks_only")
        
        self.assertIn("Task 1", result)
        self.assertIn("Task 2", result)
        self.assertNotIn("Phase 1", result)

    def test_view_filter_by_status(self):
        """View where.status filters nodes."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1", status="done"),
                "task2": Node(title="Task 2", status="in_progress"),
                "task3": Node(title="Task 3", status="done"),
            },
            views={"done_only": View(where=ViewFilter(status=["done"]))}
        )
        
        result = render_tree(plan, "done_only")
        
        self.assertIn("Task 1", result)
        self.assertIn("Task 3", result)
        self.assertNotIn("Task 2", result)

    def test_view_filter_by_has_schedule(self):
        """View where.has_schedule filters nodes."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1"),
                "task2": Node(title="Task 2"),
            },
            schedule=Schedule(
                nodes={"task1": ScheduleNode(start="2024-03-01")}
            ),
            views={"scheduled": View(where=ViewFilter(has_schedule=True))}
        )
        
        result = render_tree(plan, "scheduled")
        
        self.assertIn("Task 1", result)
        self.assertNotIn("Task 2", result)

    def test_view_filter_by_parent(self):
        """View where.parent filters to descendants."""
        plan = MergedPlan(
            nodes={
                "root": Node(title="Root"),
                "phase1": Node(title="Phase 1", parent="root"),
                "task1": Node(title="Task 1", parent="phase1"),
                "other": Node(title="Other"),
            },
            views={"root_descendants": View(where=ViewFilter(parent="root"))}
        )
        
        result = render_tree(plan, "root_descendants")
        
        self.assertIn("Phase 1", result)
        self.assertIn("Task 1", result)
        self.assertNotIn("Root", result)  # Parent itself not included
        self.assertNotIn("Other", result)

    def test_view_order_by_title(self):
        """View order_by sorts nodes."""
        plan = MergedPlan(
            nodes={
                "c": Node(title="Charlie"),
                "a": Node(title="Alpha"),
                "b": Node(title="Beta"),
            },
            views={"sorted": View(order_by="title")}
        )
        
        result = render_tree(plan, "sorted")
        lines = result.split("\n")
        
        # Should be sorted alphabetically
        self.assertIn("Alpha", lines[0])
        self.assertIn("Beta", lines[1])
        self.assertIn("Charlie", lines[2])

    def test_view_order_by_effort(self):
        """View order_by=effort sorts by effort."""
        plan = MergedPlan(
            nodes={
                "t1": Node(title="Task 1", effort=5),
                "t2": Node(title="Task 2", effort=3),
                "t3": Node(title="Task 3", effort=8),
            },
            views={"by_effort": View(order_by="effort")}
        )
        
        result = render_tree(plan, "by_effort")
        lines = result.split("\n")
        
        # Should be sorted by effort: 3, 5, 8
        self.assertIn("Task 2", lines[0])  # effort=3
        self.assertIn("Task 1", lines[1])  # effort=5
        self.assertIn("Task 3", lines[2])  # effort=8


class TestRenderTreeFilteredHierarchy(unittest.TestCase):
    """Tests for render_tree with filtered hierarchies."""

    def test_filtered_parent_promotes_children(self):
        """When parent is filtered out, children become roots."""
        plan = MergedPlan(
            nodes={
                "phase1": Node(title="Phase 1", kind="phase"),
                "task1": Node(title="Task 1", kind="task", parent="phase1"),
                "task2": Node(title="Task 2", kind="task", parent="phase1"),
            },
            views={"tasks_only": View(where=ViewFilter(kind=["task"]))}
        )
        
        result = render_tree(plan, "tasks_only")
        lines = result.split("\n")
        
        # Both tasks should be at root level (no indentation)
        self.assertEqual(len(lines), 2)
        self.assertTrue(lines[0].startswith("├──") or lines[0].startswith("└──"))
        self.assertTrue(lines[1].startswith("├──") or lines[1].startswith("└──"))

    def test_partial_hierarchy_preserved(self):
        """Partial hierarchy is preserved when some nodes pass filter."""
        plan = MergedPlan(
            nodes={
                "phase1": Node(title="Phase 1", kind="phase", status="in_progress"),
                "task1": Node(title="Task 1", kind="task", status="in_progress", parent="phase1"),
                "task2": Node(title="Task 2", kind="task", status="done", parent="phase1"),
            },
            views={"in_progress": View(where=ViewFilter(status=["in_progress"]))}
        )
        
        result = render_tree(plan, "in_progress")
        lines = result.split("\n")
        
        # Phase 1 and Task 1 should be shown, Task 2 filtered out
        self.assertEqual(len(lines), 2)
        self.assertIn("Phase 1", lines[0])
        self.assertIn("Task 1", lines[1])
        self.assertNotIn("Task 2", result)


class TestRenderTreeWithEffortMetrics(unittest.TestCase):
    """Tests for render_tree with computed effort metrics."""

    def test_effort_effective_displayed(self):
        """effort_effective is displayed when computed."""
        plan = MergedPlan(
            meta=Meta(effort_unit="sp"),
            nodes={
                "phase1": Node(title="Phase 1"),
                "task1": Node(title="Task 1", effort=5, parent="phase1"),
                "task2": Node(title="Task 2", effort=3, parent="phase1"),
            }
        )
        
        # Compute effort metrics
        compute_effort_metrics(plan)
        
        result = render_tree(plan)
        
        # Phase 1 should show rollup (5+3=8)
        self.assertIn("Phase 1", result)
        self.assertIn("(8 sp)", result)
        # Tasks show their own effort
        self.assertIn("(5 sp)", result)
        self.assertIn("(3 sp)", result)


class TestRenderTreeDesignExamples(unittest.TestCase):
    """Tests based on examples from design.md."""

    def test_backlog_example(self):
        """
        Example from design.md: backlog without schedule.
        
        Plan without schedule should render correctly as tree.
        """
        plan = MergedPlan(
            meta=Meta(id="backlog", title="Бэклог продукта", effort_unit="sp"),
            nodes={
                "epic1": Node(title="Авторизация", kind="epic", effort=13),
                "story1": Node(title="Вход по email", kind="user_story", parent="epic1", effort=5),
                "story2": Node(title="Вход через OAuth", kind="user_story", parent="epic1", after=["story1"], effort=8),
            }
        )
        
        # Compute effort metrics
        compute_effort_metrics(plan)
        
        result = render_tree(plan)
        
        # All nodes should be present
        self.assertIn("Авторизация", result)
        self.assertIn("Вход по email", result)
        self.assertIn("Вход через OAuth", result)
        
        # Effort should be shown
        self.assertIn("sp", result)

    def test_partial_schedule_example(self):
        """
        Example from design.md: partial schedule.
        
        Tree should show all nodes regardless of schedule status.
        """
        plan = MergedPlan(
            nodes={
                "milestone1": Node(title="MVP", milestone=True, after=["task2"]),
                "task1": Node(title="Backend API", effort=3),
                "task2": Node(title="Frontend", after=["task1"], effort=5),
                "task3": Node(title="Documentation", effort=2),  # Not scheduled
            },
            schedule=Schedule(
                calendars={"work": Calendar(excludes=["weekends"])},
                default_calendar="work",
                nodes={
                    "task1": ScheduleNode(start="2024-03-01", duration="3d"),
                    "task2": ScheduleNode(duration="5d"),
                    "milestone1": ScheduleNode(),
                }
            )
        )
        
        result = render_tree(plan)
        
        # All nodes should appear in tree (including unscheduled)
        self.assertIn("MVP", result)
        self.assertIn("Backend API", result)
        self.assertIn("Frontend", result)
        self.assertIn("Documentation", result)

    def test_filter_scheduled_only(self):
        """Filter to show only scheduled nodes."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Backend API"),
                "task2": Node(title="Frontend"),
                "task3": Node(title="Documentation"),  # Not scheduled
            },
            schedule=Schedule(
                nodes={
                    "task1": ScheduleNode(start="2024-03-01"),
                    "task2": ScheduleNode(start="2024-03-05"),
                }
            ),
            views={"scheduled": View(where=ViewFilter(has_schedule=True))}
        )
        
        result = render_tree(plan, "scheduled")
        
        self.assertIn("Backend API", result)
        self.assertIn("Frontend", result)
        self.assertNotIn("Documentation", result)


class TestRenderTreeNoViewId(unittest.TestCase):
    """Tests for render_tree without view_id (Requirement 5.10)."""

    def test_no_view_shows_all_nodes(self):
        """Without view_id, all nodes are shown."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1", kind="task"),
                "phase1": Node(title="Phase 1", kind="phase"),
                "task2": Node(title="Task 2", kind="task"),
            }
        )
        
        result = render_tree(plan)  # No view_id
        
        self.assertIn("Task 1", result)
        self.assertIn("Phase 1", result)
        self.assertIn("Task 2", result)

    def test_no_view_no_filtering(self):
        """Without view_id, no filtering is applied."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1", status="done"),
                "task2": Node(title="Task 2", status="in_progress"),
            },
            views={"done_only": View(where=ViewFilter(status=["done"]))}
        )
        
        # Without view_id, both should appear
        result = render_tree(plan)
        
        self.assertIn("Task 1", result)
        self.assertIn("Task 2", result)


if __name__ == "__main__":
    unittest.main()
