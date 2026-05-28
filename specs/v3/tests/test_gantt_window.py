import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from specs.v3.tools.loader import load_plan_set
from specs.v3.tools.render.gantt import render_gantt
from specs.v3.tools.scheduler import compute_schedule
from specs.v3.tools.validator import validate


def build_plan(nodes_yaml: str, schedule_yaml: str, views_yaml: str) -> str:
    nodes_block = textwrap.indent(textwrap.dedent(nodes_yaml).strip(), "  ")
    schedule_block = textwrap.indent(textwrap.dedent(schedule_yaml).strip(), "    ")
    views_block = textwrap.indent(textwrap.dedent(views_yaml).strip(), "  ")
    return (
        "version: 3\n"
        "nodes:\n"
        f"{nodes_block}\n"
        "schedule:\n"
        "  default_calendar: ru\n"
        "  calendars:\n"
        "    ru:\n"
        "      excludes: [weekends]\n"
        "  nodes:\n"
        f"{schedule_block}\n"
        "views:\n"
        f"{views_block}\n"
    )


class GanttWindowTests(unittest.TestCase):
    def load_rendered(self, plan_text: str, *, view_id: str = "month") -> str:
        with tempfile.TemporaryDirectory() as tmp_dir:
            plan_path = Path(tmp_dir) / "plan.yaml"
            plan_path.write_text(plan_text, encoding="utf-8")
            plan = load_plan_set([str(plan_path)])
            compute_schedule(plan)
            return render_gantt(plan, view_id=view_id, style="plain")

    def load_validation_messages(self, plan_text: str) -> list[str]:
        with tempfile.TemporaryDirectory() as tmp_dir:
            plan_path = Path(tmp_dir) / "plan.yaml"
            plan_path.write_text(plan_text, encoding="utf-8")
            plan = load_plan_set([str(plan_path)])
            result = validate(plan)
            return [error.message for error in result.errors]

    def test_render_gantt_clips_tasks_to_window_and_skips_outside(self):
        plan = build_plan(
            """
            root:
              title: Root
            a:
              parent: root
              kind: task
              issue: DPVCS-1
              status: planned
              title: A
            b:
              parent: root
              kind: task
              issue: DPVCS-2
              status: planned
              title: B
            c:
              parent: root
              kind: task
              issue: DPVCS-3
              status: planned
              title: C
            d:
              parent: root
              kind: task
              issue: DPVCS-4
              status: planned
              title: D
            """,
            """
            a:
              start: "2026-03-20"
              duration: 6d
            b:
              start: "2026-03-30"
              duration: 1d
            c:
              start: "2026-03-31"
              duration: 3d
            d:
              start: "2026-04-10"
              duration: 1d
            """,
            """
            month:
              title: Window
              date_format: "YYYY-MM-DD"
              axis_format: "%d.%m"
              window_start: "2026-03-25"
              window_finish: "2026-04-01"
              lanes:
                lane:
                  title: Lane
                  nodes: [a, b, c, d]
                hidden:
                  title: Hidden
                  nodes: [d]
            """,
        )
        rendered = self.load_rendered(plan)
        self.assertIn("A  :a,    2026-03-25, 2026-03-27", rendered)
        self.assertIn("B  :b,    2026-03-30, 1d", rendered)
        self.assertIn("C  :c,    2026-03-31, 2026-04-01", rendered)
        self.assertNotIn("D  :d,", rendered)
        self.assertIn("section Lane", rendered)
        self.assertNotIn("section Hidden", rendered)

    def test_render_gantt_prefers_duration_for_unclipped_same_day_task(self):
        plan = build_plan(
            """
            root:
              title: Root
            runbook:
              parent: root
              kind: task
              status: in_progress
              title: Runbook
            """,
            """
            runbook:
              start: "2026-03-27"
              duration: 1d
            """,
            """
            month:
              title: Window
              window_start: "2026-03-25"
              window_finish: "2026-03-31"
              lanes:
                lane:
                  title: Lane
                  nodes: [runbook]
            """,
        )
        rendered = self.load_rendered(plan)
        self.assertIn("Runbook  :runbook,    2026-03-27, 1d", rendered)
        self.assertNotIn("Runbook  :runbook,    2026-03-27, 2026-03-27", rendered)

    def test_validate_rejects_inverted_window(self):
        plan = build_plan(
            """
            root:
              title: Root
            a:
              parent: root
              kind: task
              issue: DPVCS-1
              status: planned
              title: A
            """,
            """
            a:
              duration: 1d
            """,
            """
            month:
              title: Window
              window_start: "2026-04-02"
              window_finish: "2026-04-01"
              lanes:
                lane:
                  title: Lane
                  nodes: [a]
            """,
        )
        messages = self.load_validation_messages(plan)
        self.assertTrue(
            any("window_start must be <= window_finish" in message for message in messages)
        )

    def test_render_gantt_expands_lane_nodes_to_leaves_only(self):
        plan = build_plan(
            """
            root:
              title: Root
            parent:
              parent: root
              kind: phase
              status: planned
              title: Parent
            child-a:
              parent: parent
              kind: task
              issue: DPVCS-10
              status: planned
              title: Child A
            child-b:
              parent: parent
              kind: milestone
              milestone: true
              status: planned
              title: Child B
            """,
            """
            child-a:
              start: "2026-03-25"
              duration: 2d
            child-b:
              start: "2026-03-27"
              duration: 0d
            """,
            """
            month:
              title: Window
              date_format: "YYYY-MM-DD"
              window_start: "2026-03-25"
              window_finish: "2026-03-31"
              lanes:
                lane:
                  title: Lane
                  expand_descendants: leaves
                  nodes: [parent]
            """,
        )
        rendered = self.load_rendered(plan)
        self.assertNotIn("Parent  :", rendered)
        self.assertIn("Child A  :child_a,", rendered)
        self.assertIn("Child B  :milestone, child_b,", rendered)

    def test_render_gantt_filters_by_x_ops_attention_class(self):
        plan = build_plan(
            """
            root:
              title: Root
            holder:
              parent: root
              kind: task
              status: planned
              title: Holder
              x:
                ops:
                  attention_class: date_holder
            strategic:
              parent: root
              kind: task
              status: planned
              title: Strategic
              x:
                ops:
                  attention_class: strategic_track
            """,
            """
            holder:
              start: "2026-03-25"
              duration: 1d
            strategic:
              start: "2026-03-26"
              duration: 1d
            """,
            """
            month:
              title: Window
              where:
                x_ops_attention_class: [date_holder]
            """,
        )
        rendered = self.load_rendered(plan)
        self.assertIn("Holder  :holder,", rendered)
        self.assertNotIn("Strategic  :strategic,", rendered)


if __name__ == "__main__":
    unittest.main()
