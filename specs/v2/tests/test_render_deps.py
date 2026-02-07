"""
Tests for the Dependency graph renderer module.

Tests cover:
- 5.8: render_deps(plan: Merged_Plan, view_id: Optional[string]) -> string
- 5.9: Apply filtering from view if view_id is provided
- 4.7: View filtering with where clause
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
from specs.v2.tools.render.deps import (
    render_deps,
    _escape_mermaid_label,
    _sanitize_node_id,
)


class TestEscapeMermaidLabel(unittest.TestCase):
    """Tests for _escape_mermaid_label helper function."""

    def test_simple_text(self):
        """Simple text passes through unchanged."""
        result = _escape_mermaid_label("Task 1")
        self.assertEqual(result, "Task 1")

    def test_double_quotes_escaped(self):
        """Double quotes are replaced with single quotes."""
        result = _escape_mermaid_label('Task "Important"')
        self.assertEqual(result, "Task 'Important'")

    def test_backslash_escaped(self):
        """Backslashes are escaped."""
        result = _escape_mermaid_label("Path\\to\\file")
        self.assertEqual(result, "Path\\\\to\\\\file")

    def test_unicode_preserved(self):
        """Unicode characters are preserved."""
        result = _escape_mermaid_label("Задача 1")
        self.assertEqual(result, "Задача 1")


class TestSanitizeNodeId(unittest.TestCase):
    """Tests for _sanitize_node_id helper function."""

    def test_simple_id(self):
        """Simple alphanumeric ID passes through unchanged."""
        result = _sanitize_node_id("task1")
        self.assertEqual(result, "task1")

    def test_underscore_preserved(self):
        """Underscores are preserved."""
        result = _sanitize_node_id("task_1")
        self.assertEqual(result, "task_1")

    def test_hyphen_replaced(self):
        """Hyphens are replaced with underscores."""
        result = _sanitize_node_id("task-1")
        self.assertEqual(result, "task_1")

    def test_dot_replaced(self):
        """Dots are replaced with underscores."""
        result = _sanitize_node_id("task.1")
        self.assertEqual(result, "task_1")

    def test_mixed_special_chars(self):
        """Multiple special characters are replaced."""
        result = _sanitize_node_id("task-1.2")
        self.assertEqual(result, "task_1_2")


class TestRenderDepsBasic(unittest.TestCase):
    """Basic tests for render_deps function."""

    def test_empty_plan(self):
        """Plan with no nodes returns minimal flowchart."""
        plan = MergedPlan(nodes={})
        
        result = render_deps(plan)
        self.assertEqual(result, "flowchart LR")

    def test_single_node_no_deps(self):
        """Single node without dependencies."""
        plan = MergedPlan(
            nodes={"task1": Node(title="Task 1")}
        )
        
        result = render_deps(plan)
        
        self.assertIn("flowchart LR", result)
        self.assertIn('task1["Task 1"]', result)
        # No edges
        self.assertNotIn("-->", result)

    def test_two_nodes_no_deps(self):
        """Two nodes without dependencies."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1"),
                "task2": Node(title="Task 2"),
            }
        )
        
        result = render_deps(plan)
        
        self.assertIn("flowchart LR", result)
        self.assertIn('task1["Task 1"]', result)
        self.assertIn('task2["Task 2"]', result)
        # No edges
        self.assertNotIn("-->", result)

    def test_simple_dependency(self):
        """Simple A --> B dependency."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1"),
                "task2": Node(title="Task 2", after=["task1"]),
            }
        )
        
        result = render_deps(plan)
        
        self.assertIn("flowchart LR", result)
        self.assertIn('task1["Task 1"]', result)
        self.assertIn('task2["Task 2"]', result)
        self.assertIn("task1 --> task2", result)

    def test_chain_dependency(self):
        """Chain A --> B --> C."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1"),
                "task2": Node(title="Task 2", after=["task1"]),
                "task3": Node(title="Task 3", after=["task2"]),
            }
        )
        
        result = render_deps(plan)
        
        self.assertIn("task1 --> task2", result)
        self.assertIn("task2 --> task3", result)

    def test_multiple_dependencies(self):
        """Node with multiple dependencies."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1"),
                "task2": Node(title="Task 2"),
                "task3": Node(title="Task 3", after=["task1", "task2"]),
            }
        )
        
        result = render_deps(plan)
        
        self.assertIn("task1 --> task3", result)
        self.assertIn("task2 --> task3", result)

    def test_diamond_dependency(self):
        """Diamond pattern: A --> B, A --> C, B --> D, C --> D."""
        plan = MergedPlan(
            nodes={
                "a": Node(title="A"),
                "b": Node(title="B", after=["a"]),
                "c": Node(title="C", after=["a"]),
                "d": Node(title="D", after=["b", "c"]),
            }
        )
        
        result = render_deps(plan)
        
        self.assertIn("a --> b", result)
        self.assertIn("a --> c", result)
        self.assertIn("b --> d", result)
        self.assertIn("c --> d", result)


class TestRenderDepsNodeIdSanitization(unittest.TestCase):
    """Tests for node ID sanitization in render_deps."""

    def test_hyphenated_id(self):
        """Node IDs with hyphens are sanitized."""
        plan = MergedPlan(
            nodes={
                "task-1": Node(title="Task 1"),
                "task-2": Node(title="Task 2", after=["task-1"]),
            }
        )
        
        result = render_deps(plan)
        
        # IDs should be sanitized
        self.assertIn('task_1["Task 1"]', result)
        self.assertIn('task_2["Task 2"]', result)
        self.assertIn("task_1 --> task_2", result)

    def test_dotted_id(self):
        """Node IDs with dots are sanitized."""
        plan = MergedPlan(
            nodes={
                "phase.task1": Node(title="Task 1"),
                "phase.task2": Node(title="Task 2", after=["phase.task1"]),
            }
        )
        
        result = render_deps(plan)
        
        self.assertIn('phase_task1["Task 1"]', result)
        self.assertIn('phase_task2["Task 2"]', result)
        self.assertIn("phase_task1 --> phase_task2", result)


class TestRenderDepsLabelEscaping(unittest.TestCase):
    """Tests for label escaping in render_deps."""

    def test_quotes_in_title(self):
        """Titles with quotes are escaped."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title='Task "Important"'),
            }
        )
        
        result = render_deps(plan)
        
        # Double quotes should be replaced with single quotes
        self.assertIn("task1[\"Task 'Important'\"]", result)

    def test_unicode_in_title(self):
        """Unicode titles are preserved."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Задача 1"),
            }
        )
        
        result = render_deps(plan)
        
        self.assertIn('task1["Задача 1"]', result)


class TestRenderDepsWithView(unittest.TestCase):
    """Tests for render_deps with view configuration."""

    def test_view_not_found(self):
        """Non-existent view raises ValueError."""
        plan = MergedPlan(
            nodes={"task1": Node(title="Task 1")}
        )
        
        with self.assertRaises(ValueError) as ctx:
            render_deps(plan, "nonexistent")
        
        self.assertIn("nonexistent", str(ctx.exception))

    def test_view_filter_by_kind(self):
        """View where.kind filters nodes."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1", kind="task"),
                "phase1": Node(title="Phase 1", kind="phase"),
                "task2": Node(title="Task 2", kind="task", after=["task1"]),
            },
            views={"tasks_only": View(where=ViewFilter(kind=["task"]))}
        )
        
        result = render_deps(plan, "tasks_only")
        
        self.assertIn('task1["Task 1"]', result)
        self.assertIn('task2["Task 2"]', result)
        self.assertNotIn("Phase 1", result)
        self.assertIn("task1 --> task2", result)

    def test_view_filter_by_status(self):
        """View where.status filters nodes."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1", status="done"),
                "task2": Node(title="Task 2", status="in_progress", after=["task1"]),
                "task3": Node(title="Task 3", status="done", after=["task2"]),
            },
            views={"done_only": View(where=ViewFilter(status=["done"]))}
        )
        
        result = render_deps(plan, "done_only")
        
        self.assertIn('task1["Task 1"]', result)
        self.assertIn('task3["Task 3"]', result)
        self.assertNotIn("Task 2", result)
        # Edge task1 --> task2 should not appear (task2 filtered out)
        # Edge task2 --> task3 should not appear (task2 filtered out)
        self.assertNotIn("-->", result)

    def test_view_filter_by_has_schedule_true(self):
        """View where.has_schedule=True filters to scheduled nodes."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1"),
                "task2": Node(title="Task 2", after=["task1"]),
                "task3": Node(title="Task 3", after=["task2"]),
            },
            schedule=Schedule(
                nodes={
                    "task1": ScheduleNode(start="2024-03-01"),
                    "task3": ScheduleNode(start="2024-03-05"),
                }
            ),
            views={"scheduled": View(where=ViewFilter(has_schedule=True))}
        )
        
        result = render_deps(plan, "scheduled")
        
        self.assertIn('task1["Task 1"]', result)
        self.assertIn('task3["Task 3"]', result)
        self.assertNotIn("Task 2", result)
        # No edges because task2 is filtered out
        self.assertNotIn("-->", result)

    def test_view_filter_by_has_schedule_false(self):
        """View where.has_schedule=False filters to unscheduled nodes."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1"),
                "task2": Node(title="Task 2", after=["task1"]),
                "task3": Node(title="Task 3"),
            },
            schedule=Schedule(
                nodes={
                    "task1": ScheduleNode(start="2024-03-01"),
                }
            ),
            views={"unscheduled": View(where=ViewFilter(has_schedule=False))}
        )
        
        result = render_deps(plan, "unscheduled")
        
        self.assertIn('task2["Task 2"]', result)
        self.assertIn('task3["Task 3"]', result)
        self.assertNotIn("Task 1", result)
        # Edge task1 --> task2 should not appear (task1 filtered out)
        self.assertNotIn("-->", result)

    def test_view_filter_by_parent(self):
        """View where.parent filters to descendants."""
        plan = MergedPlan(
            nodes={
                "root": Node(title="Root"),
                "phase1": Node(title="Phase 1", parent="root"),
                "task1": Node(title="Task 1", parent="phase1"),
                "task2": Node(title="Task 2", parent="phase1", after=["task1"]),
                "other": Node(title="Other"),
            },
            views={"root_descendants": View(where=ViewFilter(parent="root"))}
        )
        
        result = render_deps(plan, "root_descendants")
        
        self.assertIn('phase1["Phase 1"]', result)
        self.assertIn('task1["Task 1"]', result)
        self.assertIn('task2["Task 2"]', result)
        self.assertNotIn("Root", result)  # Parent itself not included
        self.assertNotIn("Other", result)
        self.assertIn("task1 --> task2", result)


class TestRenderDepsFilteredEdges(unittest.TestCase):
    """Tests for edge filtering when nodes are filtered."""

    def test_edge_excluded_when_source_filtered(self):
        """Edge is excluded when source node is filtered out."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1", kind="phase"),
                "task2": Node(title="Task 2", kind="task", after=["task1"]),
            },
            views={"tasks_only": View(where=ViewFilter(kind=["task"]))}
        )
        
        result = render_deps(plan, "tasks_only")
        
        self.assertIn('task2["Task 2"]', result)
        self.assertNotIn("Task 1", result)
        # Edge should not appear because task1 is filtered out
        self.assertNotIn("-->", result)

    def test_edge_excluded_when_target_filtered(self):
        """Edge is excluded when target node is filtered out."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1", kind="task"),
                "task2": Node(title="Task 2", kind="phase", after=["task1"]),
            },
            views={"tasks_only": View(where=ViewFilter(kind=["task"]))}
        )
        
        result = render_deps(plan, "tasks_only")
        
        self.assertIn('task1["Task 1"]', result)
        self.assertNotIn("Task 2", result)
        # Edge should not appear because task2 is filtered out
        self.assertNotIn("-->", result)

    def test_partial_edges_preserved(self):
        """Only edges between filtered nodes are preserved."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1", kind="task"),
                "phase1": Node(title="Phase 1", kind="phase", after=["task1"]),
                "task2": Node(title="Task 2", kind="task", after=["phase1"]),
                "task3": Node(title="Task 3", kind="task", after=["task1"]),
            },
            views={"tasks_only": View(where=ViewFilter(kind=["task"]))}
        )
        
        result = render_deps(plan, "tasks_only")
        
        # task1 --> task3 should be preserved
        self.assertIn("task1 --> task3", result)
        # task1 --> phase1 should not appear (phase1 filtered)
        # phase1 --> task2 should not appear (phase1 filtered)
        self.assertNotIn("phase1", result)


class TestRenderDepsNoViewId(unittest.TestCase):
    """Tests for render_deps without view_id (Requirement 5.10)."""

    def test_no_view_shows_all_nodes(self):
        """Without view_id, all nodes are shown."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1", kind="task"),
                "phase1": Node(title="Phase 1", kind="phase"),
                "task2": Node(title="Task 2", kind="task"),
            }
        )
        
        result = render_deps(plan)  # No view_id
        
        self.assertIn("Task 1", result)
        self.assertIn("Phase 1", result)
        self.assertIn("Task 2", result)

    def test_no_view_shows_all_edges(self):
        """Without view_id, all edges are shown."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1"),
                "task2": Node(title="Task 2", after=["task1"]),
            },
            views={"filtered": View(where=ViewFilter(kind=["phase"]))}
        )
        
        # Without view_id, edge should appear
        result = render_deps(plan)
        
        self.assertIn("task1 --> task2", result)


class TestRenderDepsDesignExamples(unittest.TestCase):
    """Tests based on examples from design.md."""

    def test_backlog_example(self):
        """
        Example from design.md: backlog without schedule.
        
        Plan without schedule should render correctly as deps graph.
        """
        plan = MergedPlan(
            meta=Meta(id="backlog", title="Бэклог продукта", effort_unit="sp"),
            nodes={
                "epic1": Node(title="Авторизация", kind="epic", effort=13),
                "story1": Node(title="Вход по email", kind="user_story", parent="epic1", effort=5),
                "story2": Node(title="Вход через OAuth", kind="user_story", parent="epic1", after=["story1"], effort=8),
            }
        )
        
        result = render_deps(plan)
        
        # All nodes should be present
        self.assertIn("Авторизация", result)
        self.assertIn("Вход по email", result)
        self.assertIn("Вход через OAuth", result)
        
        # Dependency edge should be present
        self.assertIn("story1 --> story2", result)

    def test_partial_schedule_example(self):
        """
        Example from design.md: partial schedule.
        
        Deps graph should show all nodes and their dependencies.
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
        
        result = render_deps(plan)
        
        # All nodes should appear
        self.assertIn("MVP", result)
        self.assertIn("Backend API", result)
        self.assertIn("Frontend", result)
        self.assertIn("Documentation", result)
        
        # Dependencies should be shown
        self.assertIn("task1 --> task2", result)
        self.assertIn("task2 --> milestone1", result)

    def test_filter_scheduled_only(self):
        """Filter to show only scheduled nodes in deps graph."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Backend API"),
                "task2": Node(title="Frontend", after=["task1"]),
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
        
        result = render_deps(plan, "scheduled")
        
        self.assertIn("Backend API", result)
        self.assertIn("Frontend", result)
        self.assertNotIn("Documentation", result)
        self.assertIn("task1 --> task2", result)


class TestRenderDepsOutputFormat(unittest.TestCase):
    """Tests for the output format of render_deps."""

    def test_flowchart_header(self):
        """Output starts with flowchart LR."""
        plan = MergedPlan(
            nodes={"task1": Node(title="Task 1")}
        )
        
        result = render_deps(plan)
        
        self.assertTrue(result.startswith("flowchart LR"))

    def test_node_definition_format(self):
        """Node definitions use correct format."""
        plan = MergedPlan(
            nodes={"task1": Node(title="Task 1")}
        )
        
        result = render_deps(plan)
        lines = result.split("\n")
        
        # Should have node definition with indentation
        node_line = [l for l in lines if "task1" in l][0]
        self.assertTrue(node_line.startswith("    "))
        self.assertIn('task1["Task 1"]', node_line)

    def test_edge_format(self):
        """Edges use correct format."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1"),
                "task2": Node(title="Task 2", after=["task1"]),
            }
        )
        
        result = render_deps(plan)
        lines = result.split("\n")
        
        # Should have edge with indentation
        edge_line = [l for l in lines if "-->" in l][0]
        self.assertTrue(edge_line.startswith("    "))
        self.assertIn("task1 --> task2", edge_line)

    def test_nodes_sorted_alphabetically(self):
        """Nodes are output in sorted order for deterministic output."""
        plan = MergedPlan(
            nodes={
                "c": Node(title="C"),
                "a": Node(title="A"),
                "b": Node(title="B"),
            }
        )
        
        result = render_deps(plan)
        lines = result.split("\n")
        
        # Find node definition lines
        node_lines = [l for l in lines if '["' in l]
        
        # Should be in alphabetical order
        self.assertIn("a", node_lines[0])
        self.assertIn("b", node_lines[1])
        self.assertIn("c", node_lines[2])


if __name__ == "__main__":
    unittest.main()
