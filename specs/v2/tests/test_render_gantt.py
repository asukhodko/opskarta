"""
Tests for the Gantt renderer module.

Tests cover:
- 5.4: render_gantt(plan: Merged_Plan, view_id: string) -> string
- 5.5: Use calendar from schedule for Gantt dates
- 4.7: View filtering with where clause
- 4.8: View format settings (date_format, axis_format, tick_interval)
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
from specs.v2.tools.render.gantt import (
    apply_view_filter,
    render_gantt,
    _escape_mermaid_title,
    _get_descendants,
    _sanitize_task_id,
)
from specs.v2.tools.scheduler import compute_schedule


class TestEscapeMermaidTitle(unittest.TestCase):
    """Tests for _escape_mermaid_title helper function."""

    def test_no_special_chars(self):
        """Title without special characters is unchanged."""
        self.assertEqual(_escape_mermaid_title("Simple Task"), "Simple Task")

    def test_colon_replaced(self):
        """Colon is replaced with dash."""
        self.assertEqual(_escape_mermaid_title("Phase 1: Analysis"), "Phase 1 - Analysis")

    def test_semicolon_replaced(self):
        """Semicolon is replaced with comma."""
        self.assertEqual(_escape_mermaid_title("Task; subtask"), "Task, subtask")

    def test_hash_removed(self):
        """Hash is removed."""
        self.assertEqual(_escape_mermaid_title("Issue #123"), "Issue 123")


class TestSanitizeTaskId(unittest.TestCase):
    """Tests for _sanitize_task_id helper function."""

    def test_simple_id(self):
        """Simple ID is unchanged."""
        self.assertEqual(_sanitize_task_id("task1"), "task1")

    def test_dots_replaced(self):
        """Dots are replaced with underscores."""
        self.assertEqual(_sanitize_task_id("phase.task"), "phase_task")

    def test_dashes_replaced(self):
        """Dashes are replaced with underscores."""
        self.assertEqual(_sanitize_task_id("my-task"), "my_task")


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


class TestRenderGanttBasic(unittest.TestCase):
    """Basic tests for render_gantt function."""

    def test_empty_schedule(self):
        """Plan without schedule returns minimal Gantt."""
        plan = MergedPlan(
            nodes={"task1": Node(title="Task 1")}
        )
        
        result = render_gantt(plan, "")
        
        self.assertIn("gantt", result)
        self.assertIn("dateFormat YYYY-MM-DD", result)

    def test_no_computed_dates(self):
        """Schedule without computed dates returns minimal Gantt."""
        plan = MergedPlan(
            nodes={"task1": Node(title="Task 1")},
            schedule=Schedule(
                nodes={"task1": ScheduleNode()}  # No computed dates
            )
        )
        
        result = render_gantt(plan, "")
        
        self.assertIn("gantt", result)
        # No task lines since no computed dates
        self.assertNotIn("task1", result)

    def test_single_task(self):
        """Single task with computed dates."""
        plan = MergedPlan(
            nodes={"task1": Node(title="Task 1")},
            schedule=Schedule(
                calendars={"default": Calendar(excludes=["weekends"])},
                default_calendar="default",
                nodes={"task1": ScheduleNode(start="2024-03-11", duration="3d")}
            )
        )
        
        # Compute schedule to get dates
        compute_schedule(plan)
        
        result = render_gantt(plan, "")
        
        self.assertIn("gantt", result)
        self.assertIn("Task 1", result)
        self.assertIn("2024-03-11", result)
        self.assertIn("2024-03-13", result)

    def test_multiple_tasks(self):
        """Multiple tasks with dependencies."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1"),
                "task2": Node(title="Task 2", after=["task1"]),
            },
            schedule=Schedule(
                calendars={"default": Calendar(excludes=["weekends"])},
                default_calendar="default",
                nodes={
                    "task1": ScheduleNode(start="2024-03-11", duration="3d"),
                    "task2": ScheduleNode(duration="2d"),
                }
            )
        )
        
        compute_schedule(plan)
        
        result = render_gantt(plan, "")
        
        self.assertIn("Task 1", result)
        self.assertIn("Task 2", result)
        self.assertIn("2024-03-11", result)
        self.assertIn("2024-03-14", result)  # task2 start

    def test_milestone(self):
        """Milestone is rendered with milestone syntax."""
        plan = MergedPlan(
            nodes={"m1": Node(title="Milestone 1", milestone=True)},
            schedule=Schedule(
                calendars={"default": Calendar(excludes=["weekends"])},
                default_calendar="default",
                nodes={"m1": ScheduleNode(start="2024-03-15")}
            )
        )
        
        compute_schedule(plan)
        
        result = render_gantt(plan, "")
        
        self.assertIn("Milestone 1", result)
        self.assertIn("milestone", result)


class TestRenderGanttWithView(unittest.TestCase):
    """Tests for render_gantt with view configuration."""

    def test_view_not_found(self):
        """Non-existent view raises ValueError."""
        plan = MergedPlan(
            nodes={"task1": Node(title="Task 1")}
        )
        
        with self.assertRaises(ValueError) as ctx:
            render_gantt(plan, "nonexistent")
        
        self.assertIn("nonexistent", str(ctx.exception))

    def test_view_title(self):
        """View title is used in Gantt."""
        plan = MergedPlan(
            nodes={"task1": Node(title="Task 1")},
            schedule=Schedule(
                calendars={"default": Calendar(excludes=["weekends"])},
                default_calendar="default",
                nodes={"task1": ScheduleNode(start="2024-03-11", duration="1d")}
            ),
            views={"main": View(title="Project Timeline")}
        )
        
        compute_schedule(plan)
        
        result = render_gantt(plan, "main")
        
        self.assertIn("title Project Timeline", result)

    def test_view_date_format(self):
        """View date_format is used."""
        plan = MergedPlan(
            nodes={"task1": Node(title="Task 1")},
            schedule=Schedule(
                nodes={"task1": ScheduleNode(start="2024-03-11", duration="1d")}
            ),
            views={"main": View(date_format="DD-MM-YYYY")}
        )
        
        compute_schedule(plan)
        
        result = render_gantt(plan, "main")
        
        self.assertIn("dateFormat DD-MM-YYYY", result)

    def test_view_axis_format(self):
        """View axis_format is included."""
        plan = MergedPlan(
            nodes={"task1": Node(title="Task 1")},
            schedule=Schedule(
                nodes={"task1": ScheduleNode(start="2024-03-11", duration="1d")}
            ),
            views={"main": View(axis_format="%d/%m")}
        )
        
        compute_schedule(plan)
        
        result = render_gantt(plan, "main")
        
        self.assertIn("axisFormat %d/%m", result)

    def test_view_tick_interval(self):
        """View tick_interval is included."""
        plan = MergedPlan(
            nodes={"task1": Node(title="Task 1")},
            schedule=Schedule(
                nodes={"task1": ScheduleNode(start="2024-03-11", duration="1d")}
            ),
            views={"main": View(tick_interval="1week")}
        )
        
        compute_schedule(plan)
        
        result = render_gantt(plan, "main")
        
        self.assertIn("tickInterval 1week", result)

    def test_view_filter_by_kind(self):
        """View where.kind filters tasks."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1", kind="task"),
                "phase1": Node(title="Phase 1", kind="phase"),
            },
            schedule=Schedule(
                calendars={"default": Calendar(excludes=["weekends"])},
                default_calendar="default",
                nodes={
                    "task1": ScheduleNode(start="2024-03-11", duration="1d"),
                    "phase1": ScheduleNode(start="2024-03-11", duration="5d"),
                }
            ),
            views={"tasks_only": View(where=ViewFilter(kind=["task"]))}
        )
        
        compute_schedule(plan)
        
        result = render_gantt(plan, "tasks_only")
        
        self.assertIn("Task 1", result)
        self.assertNotIn("Phase 1", result)

    def test_view_filter_has_schedule(self):
        """View where.has_schedule filters to scheduled nodes."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1"),
                "task2": Node(title="Task 2"),
            },
            schedule=Schedule(
                calendars={"default": Calendar(excludes=["weekends"])},
                default_calendar="default",
                nodes={
                    "task1": ScheduleNode(start="2024-03-11", duration="1d"),
                    # task2 not scheduled
                }
            ),
            views={"scheduled": View(where=ViewFilter(has_schedule=True))}
        )
        
        compute_schedule(plan)
        
        result = render_gantt(plan, "scheduled")
        
        self.assertIn("Task 1", result)
        self.assertNotIn("Task 2", result)


class TestRenderGanttGrouping(unittest.TestCase):
    """Tests for render_gantt with grouping options."""

    def test_group_by_parent(self):
        """group_by=parent creates sections."""
        plan = MergedPlan(
            nodes={
                "phase1": Node(title="Phase 1"),
                "task1": Node(title="Task 1", parent="phase1"),
                "task2": Node(title="Task 2", parent="phase1"),
            },
            schedule=Schedule(
                calendars={"default": Calendar(excludes=["weekends"])},
                default_calendar="default",
                nodes={
                    "task1": ScheduleNode(start="2024-03-11", duration="2d"),
                    "task2": ScheduleNode(start="2024-03-13", duration="2d"),
                }
            ),
            views={"grouped": View(group_by="parent")}
        )
        
        compute_schedule(plan)
        
        result = render_gantt(plan, "grouped")
        
        self.assertIn("section Phase 1", result)
        self.assertIn("Task 1", result)
        self.assertIn("Task 2", result)

    def test_lanes(self):
        """Lanes create custom sections."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Backend Task"),
                "task2": Node(title="Frontend Task"),
            },
            schedule=Schedule(
                calendars={"default": Calendar(excludes=["weekends"])},
                default_calendar="default",
                nodes={
                    "task1": ScheduleNode(start="2024-03-11", duration="2d"),
                    "task2": ScheduleNode(start="2024-03-11", duration="3d"),
                }
            ),
            views={
                "lanes_view": View(
                    lanes={
                        "backend": {"title": "Backend", "nodes": ["task1"]},
                        "frontend": {"title": "Frontend", "nodes": ["task2"]},
                    }
                )
            }
        )
        
        compute_schedule(plan)
        
        result = render_gantt(plan, "lanes_view")
        
        self.assertIn("section Backend", result)
        self.assertIn("section Frontend", result)
        self.assertIn("Backend Task", result)
        self.assertIn("Frontend Task", result)


class TestRenderGanttUsesScheduleCalendar(unittest.TestCase):
    """Tests verifying that Gantt uses calendar from schedule (Requirement 5.5)."""

    def test_dates_respect_calendar_weekends(self):
        """Computed dates respect weekend exclusions from calendar."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1"),
                "task2": Node(title="Task 2", after=["task1"]),
            },
            schedule=Schedule(
                calendars={"work": Calendar(excludes=["weekends"])},
                default_calendar="work",
                nodes={
                    # Friday start, 3 days duration
                    "task1": ScheduleNode(start="2024-03-15", duration="3d"),
                    "task2": ScheduleNode(duration="2d"),
                }
            )
        )
        
        compute_schedule(plan)
        
        result = render_gantt(plan, "")
        
        # task1: Fri-Tue (skips weekend)
        self.assertIn("2024-03-15", result)  # task1 start
        self.assertIn("2024-03-19", result)  # task1 finish (Tue)
        
        # task2: starts Wed (next workday after Tue)
        self.assertIn("2024-03-20", result)  # task2 start

    def test_dates_respect_calendar_holidays(self):
        """Computed dates respect holiday exclusions from calendar."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1"),
            },
            schedule=Schedule(
                calendars={
                    "work": Calendar(excludes=["weekends", "2024-03-12"])
                },
                default_calendar="work",
                nodes={
                    # Monday start, 3 days duration, but Tue is holiday
                    "task1": ScheduleNode(start="2024-03-11", duration="3d"),
                }
            )
        )
        
        compute_schedule(plan)
        
        result = render_gantt(plan, "")
        
        # task1: Mon, (skip Tue holiday), Wed, Thu
        self.assertIn("2024-03-11", result)  # start
        self.assertIn("2024-03-14", result)  # finish (Thu, not Wed)


class TestRenderGanttMetaTitle(unittest.TestCase):
    """Tests for title from meta when view has no title."""

    def test_meta_title_used(self):
        """Meta title is used when view has no title."""
        plan = MergedPlan(
            meta=Meta(title="Project X"),
            nodes={"task1": Node(title="Task 1")},
            schedule=Schedule(
                nodes={"task1": ScheduleNode(start="2024-03-11", duration="1d")}
            ),
            views={"main": View()}  # No title in view
        )
        
        compute_schedule(plan)
        
        result = render_gantt(plan, "main")
        
        self.assertIn("title Project X", result)

    def test_view_title_overrides_meta(self):
        """View title takes precedence over meta title."""
        plan = MergedPlan(
            meta=Meta(title="Project X"),
            nodes={"task1": Node(title="Task 1")},
            schedule=Schedule(
                nodes={"task1": ScheduleNode(start="2024-03-11", duration="1d")}
            ),
            views={"main": View(title="Custom View Title")}
        )
        
        compute_schedule(plan)
        
        result = render_gantt(plan, "main")
        
        self.assertIn("title Custom View Title", result)
        self.assertNotIn("Project X", result)


class TestRenderGanttDesignExamples(unittest.TestCase):
    """Tests based on examples from design.md."""

    def test_partial_schedule_example(self):
        """
        Example from design.md: partial schedule.
        
        task1, task2, milestone1 are scheduled
        task3 is not scheduled (should not appear in Gantt)
        """
        plan = MergedPlan(
            nodes={
                "milestone1": Node(title="MVP", milestone=True, after=["task2"]),
                "task1": Node(title="Backend API"),
                "task2": Node(title="Frontend", after=["task1"]),
                "task3": Node(title="Documentation"),  # Not scheduled
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
        
        compute_schedule(plan)
        
        result = render_gantt(plan, "")
        
        # Scheduled tasks appear
        self.assertIn("Backend API", result)
        self.assertIn("Frontend", result)
        self.assertIn("MVP", result)
        
        # Unscheduled task does not appear
        self.assertNotIn("Documentation", result)
        
        # Milestone has milestone syntax
        self.assertIn("milestone", result)


if __name__ == "__main__":
    unittest.main()
