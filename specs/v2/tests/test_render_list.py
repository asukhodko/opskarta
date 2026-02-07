"""
Tests for the List renderer module.

Tests cover:
- 5.7: render_list(plan: Merged_Plan, view_id: Optional[string]) -> string
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
from specs.v2.tools.render.list import (
    render_list,
    _format_list_item,
)
from specs.v2.tools.effort import compute_effort_metrics


class TestFormatListItem(unittest.TestCase):
    """Tests for _format_list_item helper function."""

    def test_simple_node(self):
        """Simple node with just title."""
        plan = MergedPlan(
            nodes={"task1": Node(title="Task 1")}
        )
        
        result = _format_list_item(plan, "task1")
        self.assertEqual(result, "- Task 1")

    def test_node_with_status(self):
        """Node with status shows [status]."""
        plan = MergedPlan(
            nodes={"task1": Node(title="Task 1", status="done")}
        )
        
        result = _format_list_item(plan, "task1")
        self.assertEqual(result, "- Task 1 [done]")

    def test_node_with_effort(self):
        """Node with effort shows (effort)."""
        plan = MergedPlan(
            nodes={"task1": Node(title="Task 1", effort=5)}
        )
        
        result = _format_list_item(plan, "task1")
        self.assertEqual(result, "- Task 1 (5)")

    def test_node_with_effort_unit(self):
        """Node with effort and meta.effort_unit shows unit."""
        plan = MergedPlan(
            meta=Meta(effort_unit="sp"),
            nodes={"task1": Node(title="Task 1", effort=5)}
        )
        
        result = _format_list_item(plan, "task1")
        self.assertEqual(result, "- Task 1 (5 sp)")

    def test_node_with_status_and_effort(self):
        """Node with both status and effort."""
        plan = MergedPlan(
            meta=Meta(effort_unit="sp"),
            nodes={"task1": Node(title="Task 1", status="in_progress", effort=5)}
        )
        
        result = _format_list_item(plan, "task1")
        self.assertEqual(result, "- Task 1 [in_progress] (5 sp)")

    def test_node_with_effort_effective(self):
        """Node with effort_effective uses it over effort."""
        plan = MergedPlan(
            nodes={"task1": Node(title="Task 1", effort=10)}
        )
        # Simulate computed effort_effective
        plan.nodes["task1"].effort_effective = 15
        
        result = _format_list_item(plan, "task1")
        self.assertEqual(result, "- Task 1 (15)")

    def test_nonexistent_node(self):
        """Nonexistent node returns empty string."""
        plan = MergedPlan(nodes={})
        
        result = _format_list_item(plan, "nonexistent")
        self.assertEqual(result, "")


class TestRenderListBasic(unittest.TestCase):
    """Basic tests for render_list function."""

    def test_empty_plan(self):
        """Plan with no nodes returns empty string."""
        plan = MergedPlan(nodes={})
        
        result = render_list(plan)
        self.assertEqual(result, "")

    def test_single_node(self):
        """Single node."""
        plan = MergedPlan(
            nodes={"task1": Node(title="Task 1")}
        )
        
        result = render_list(plan)
        self.assertEqual(result, "- Task 1")

    def test_multiple_nodes(self):
        """Multiple nodes."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1"),
                "task2": Node(title="Task 2"),
                "task3": Node(title="Task 3"),
            }
        )
        
        result = render_list(plan)
        lines = result.split("\n")
        
        # Should have three lines
        self.assertEqual(len(lines), 3)
        # All should start with "- "
        for line in lines:
            self.assertTrue(line.startswith("- "))

    def test_nodes_with_status(self):
        """Nodes with status are displayed."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1", status="done"),
                "task2": Node(title="Task 2", status="in_progress"),
            }
        )
        
        result = render_list(plan)
        self.assertIn("[done]", result)
        self.assertIn("[in_progress]", result)

    def test_nodes_with_effort(self):
        """Nodes with effort are displayed."""
        plan = MergedPlan(
            meta=Meta(effort_unit="sp"),
            nodes={
                "task1": Node(title="Task 1", effort=5),
                "task2": Node(title="Task 2", effort=3),
            }
        )
        
        result = render_list(plan)
        self.assertIn("(5 sp)", result)
        self.assertIn("(3 sp)", result)

    def test_hierarchy_is_flattened(self):
        """Hierarchy is flattened in list view."""
        plan = MergedPlan(
            nodes={
                "phase1": Node(title="Phase 1"),
                "task1": Node(title="Task 1", parent="phase1"),
                "task2": Node(title="Task 2", parent="phase1"),
            }
        )
        
        result = render_list(plan)
        lines = result.split("\n")
        
        # All nodes should be at the same level (no indentation)
        self.assertEqual(len(lines), 3)
        for line in lines:
            self.assertTrue(line.startswith("- "))


class TestRenderListWithView(unittest.TestCase):
    """Tests for render_list with view configuration."""

    def test_view_not_found(self):
        """Non-existent view raises ValueError."""
        plan = MergedPlan(
            nodes={"task1": Node(title="Task 1")}
        )
        
        with self.assertRaises(ValueError) as ctx:
            render_list(plan, "nonexistent")
        
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
        
        result = render_list(plan, "tasks_only")
        
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
        
        result = render_list(plan, "done_only")
        
        self.assertIn("Task 1", result)
        self.assertIn("Task 3", result)
        self.assertNotIn("Task 2", result)

    def test_view_filter_by_has_schedule_true(self):
        """View where.has_schedule=True filters to scheduled nodes."""
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
            ),
            views={"scheduled": View(where=ViewFilter(has_schedule=True))}
        )
        
        result = render_list(plan, "scheduled")
        
        self.assertIn("Task 1", result)
        self.assertIn("Task 3", result)
        self.assertNotIn("Task 2", result)

    def test_view_filter_by_has_schedule_false(self):
        """View where.has_schedule=False filters to unscheduled nodes."""
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
            ),
            views={"unscheduled": View(where=ViewFilter(has_schedule=False))}
        )
        
        result = render_list(plan, "unscheduled")
        
        self.assertIn("Task 2", result)
        self.assertIn("Task 3", result)
        self.assertNotIn("Task 1", result)

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
        
        result = render_list(plan, "root_descendants")
        
        self.assertIn("Phase 1", result)
        self.assertIn("Task 1", result)
        self.assertNotIn("Root", result)  # Parent itself not included
        self.assertNotIn("Other", result)

    def test_view_combined_filters(self):
        """Multiple filter criteria are ANDed."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1", kind="task", status="done"),
                "task2": Node(title="Task 2", kind="task", status="in_progress"),
                "phase1": Node(title="Phase 1", kind="phase", status="done"),
            },
            views={"done_tasks": View(where=ViewFilter(kind=["task"], status=["done"]))}
        )
        
        result = render_list(plan, "done_tasks")
        
        self.assertIn("Task 1", result)
        self.assertNotIn("Task 2", result)
        self.assertNotIn("Phase 1", result)


class TestRenderListSorting(unittest.TestCase):
    """Tests for render_list sorting with order_by."""

    def test_view_order_by_title(self):
        """View order_by=title sorts nodes alphabetically."""
        plan = MergedPlan(
            nodes={
                "c": Node(title="Charlie"),
                "a": Node(title="Alpha"),
                "b": Node(title="Beta"),
            },
            views={"sorted": View(order_by="title")}
        )
        
        result = render_list(plan, "sorted")
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
        
        result = render_list(plan, "by_effort")
        lines = result.split("\n")
        
        # Should be sorted by effort: 3, 5, 8
        self.assertIn("Task 2", lines[0])  # effort=3
        self.assertIn("Task 1", lines[1])  # effort=5
        self.assertIn("Task 3", lines[2])  # effort=8

    def test_view_order_by_status(self):
        """View order_by=status sorts by status."""
        plan = MergedPlan(
            nodes={
                "t1": Node(title="Task 1", status="not_started"),
                "t2": Node(title="Task 2", status="done"),
                "t3": Node(title="Task 3", status="in_progress"),
            },
            views={"by_status": View(order_by="status")}
        )
        
        result = render_list(plan, "by_status")
        lines = result.split("\n")
        
        # Should be sorted alphabetically by status: done, in_progress, not_started
        self.assertIn("done", lines[0])
        self.assertIn("in_progress", lines[1])
        self.assertIn("not_started", lines[2])

    def test_view_order_by_kind(self):
        """View order_by=kind sorts by kind."""
        plan = MergedPlan(
            nodes={
                "t1": Node(title="Task 1", kind="task"),
                "p1": Node(title="Phase 1", kind="phase"),
                "e1": Node(title="Epic 1", kind="epic"),
            },
            views={"by_kind": View(order_by="kind")}
        )
        
        result = render_list(plan, "by_kind")
        lines = result.split("\n")
        
        # Should be sorted alphabetically by kind: epic, phase, task
        self.assertIn("Epic 1", lines[0])
        self.assertIn("Phase 1", lines[1])
        self.assertIn("Task 1", lines[2])


class TestRenderListWithEffortMetrics(unittest.TestCase):
    """Tests for render_list with computed effort metrics."""

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
        
        result = render_list(plan)
        
        # Phase 1 should show rollup (5+3=8)
        self.assertIn("Phase 1", result)
        self.assertIn("(8 sp)", result)
        # Tasks show their own effort
        self.assertIn("(5 sp)", result)
        self.assertIn("(3 sp)", result)


class TestRenderListNoViewId(unittest.TestCase):
    """Tests for render_list without view_id (Requirement 5.10)."""

    def test_no_view_shows_all_nodes(self):
        """Without view_id, all nodes are shown."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1", kind="task"),
                "phase1": Node(title="Phase 1", kind="phase"),
                "task2": Node(title="Task 2", kind="task"),
            }
        )
        
        result = render_list(plan)  # No view_id
        
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
        result = render_list(plan)
        
        self.assertIn("Task 1", result)
        self.assertIn("Task 2", result)


class TestRenderListDesignExamples(unittest.TestCase):
    """Tests based on examples from design.md."""

    def test_backlog_example(self):
        """
        Example from design.md: backlog without schedule.
        
        Plan without schedule should render correctly as list.
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
        
        result = render_list(plan)
        
        # All nodes should be present
        self.assertIn("Авторизация", result)
        self.assertIn("Вход по email", result)
        self.assertIn("Вход через OAuth", result)
        
        # Effort should be shown
        self.assertIn("sp", result)

    def test_partial_schedule_example(self):
        """
        Example from design.md: partial schedule.
        
        List should show all nodes regardless of schedule status.
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
        
        result = render_list(plan)
        
        # All nodes should appear in list (including unscheduled)
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
        
        result = render_list(plan, "scheduled")
        
        self.assertIn("Backend API", result)
        self.assertIn("Frontend", result)
        self.assertNotIn("Documentation", result)


class TestRenderListFilterAndSort(unittest.TestCase):
    """Tests for combined filtering and sorting."""

    def test_filter_and_sort_combined(self):
        """Filter and sort can be combined."""
        plan = MergedPlan(
            nodes={
                "t1": Node(title="Task C", kind="task", effort=5),
                "t2": Node(title="Task A", kind="task", effort=3),
                "t3": Node(title="Task B", kind="task", effort=8),
                "p1": Node(title="Phase 1", kind="phase", effort=10),
            },
            views={"tasks_sorted": View(
                where=ViewFilter(kind=["task"]),
                order_by="title"
            )}
        )
        
        result = render_list(plan, "tasks_sorted")
        lines = result.split("\n")
        
        # Should only have tasks, sorted by title
        self.assertEqual(len(lines), 3)
        self.assertIn("Task A", lines[0])
        self.assertIn("Task B", lines[1])
        self.assertIn("Task C", lines[2])
        self.assertNotIn("Phase 1", result)

    def test_empty_filter_result(self):
        """Empty filter result returns empty string."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1", kind="task"),
            },
            views={"no_match": View(where=ViewFilter(kind=["nonexistent"]))}
        )
        
        result = render_list(plan, "no_match")
        self.assertEqual(result, "")


if __name__ == "__main__":
    unittest.main()
