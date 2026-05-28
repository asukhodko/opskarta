import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[3]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from specs.v3.tools.markdown import update_markdown_files


class UpdateMarkdownDiagramsTests(unittest.TestCase):
    def test_updates_multiple_markdown_files(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            plan_path = tmp / "plan.yaml"
            plan_path.write_text(
                textwrap.dedent(
                    """
                    version: 3
                    statuses:
                      planned:
                        label: Planned
                    nodes:
                      root:
                        title: Root
                      task:
                        parent: root
                        title: Task
                        kind: task
                        status: planned
                    views:
                      list_view:
                        title: List
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )

            markdown_template = textwrap.dedent(
                f"""
                <!--
                Перегенерить:
                env PYTHONPATH={BASE_DIR} python3 -m specs.v3.tools.cli validate plan.yaml
                env PYTHONPATH={BASE_DIR} python3 -m specs.v3.tools.cli render list plan.yaml --view list_view
                -->
                ```mermaid
                old
                ```
                """
            ).strip() + "\n"

            md_one = tmp / "one.md"
            md_two = tmp / "two.md"
            md_one.write_text(markdown_template, encoding="utf-8")
            md_two.write_text(markdown_template, encoding="utf-8")

            updated = update_markdown_files([md_one, md_two])
            self.assertEqual(updated, 2)
            self.assertIn("Task", md_one.read_text(encoding="utf-8"))
            self.assertIn("Task", md_two.read_text(encoding="utf-8"))
            self.assertNotIn("old", md_one.read_text(encoding="utf-8"))

    def test_updates_generated_markdown_block(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            plan_path = tmp / "plan.yaml"
            plan_path.write_text(
                textwrap.dedent(
                    """
                    version: 3
                    statuses:
                      not_started:
                        label: Not started
                    nodes:
                      gate:
                        title: Gate
                        kind: milestone
                        milestone: true
                        status: not_started
                    schedule:
                      default_calendar: ru
                      calendars:
                        ru:
                          excludes: [weekends]
                      nodes:
                        gate:
                          start: "2026-05-01"
                          duration: 1d
                    x:
                      exec:
                        program:
                          committed_date: "2026-04-26"
                        blocks:
                          prod:
                            title: Prod
                            scope_nodes: [gate]
                            target_gate: gate
                            kind: main
                            mgmt:
                              health: green
                        views:
                          exec-top:
                            blocks: [prod]
                          exec-active-tracks:
                            blocks: [prod]
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )

            md = tmp / "exec.md"
            md.write_text(
                textwrap.dedent(
                    f"""
                    <!--
                    Перегенерить:
                    env PYTHONPATH={BASE_DIR} python3 -m specs.v3.tools.cli validate plan.yaml
                    env PYTHONPATH={BASE_DIR} python3 -m specs.v3.tools.cli render executive-report plan.yaml --section status
                    -->
                    <!-- GENERATED:START -->
                    old
                    <!-- GENERATED:END -->
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )

            updated = update_markdown_files([md])
            text = md.read_text(encoding="utf-8")
            self.assertEqual(updated, 1)
            self.assertIn("Обещанная дата", text)
            self.assertNotIn("old", text)

    def test_updates_executive_caption_from_view_config(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            plan_path = tmp / "plan.yaml"
            plan_path.write_text(
                textwrap.dedent(
                    """
                    version: 3
                    statuses:
                      not_started:
                        label: Not started
                    nodes:
                      gate:
                        title: Gate
                        kind: milestone
                        milestone: true
                        status: not_started
                      phase:
                        title: Phase
                        kind: phase
                        status: not_started
                      task:
                        parent: phase
                        title: Task
                        kind: task
                        status: not_started
                    schedule:
                      default_calendar: ru
                      calendars:
                        ru:
                          excludes: [weekends]
                      nodes:
                        gate:
                          start: "2026-05-01"
                          duration: 1d
                        task:
                          start: "2026-04-30"
                          duration: 1d
                    x:
                      exec:
                        blocks:
                          phase_block:
                            title: Phase
                            scope_nodes: [phase]
                            target_gate: gate
                        views:
                          exec-top:
                            blocks: [phase_block]
                            caption: "Новая подпись из YAML."
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )

            md = tmp / "exec.md"
            md.write_text(
                textwrap.dedent(
                    f"""
                    <!--
                    Перегенерить:
                    env PYTHONPATH={BASE_DIR} python3 -m specs.v3.tools.cli validate plan.yaml
                    env PYTHONPATH={BASE_DIR} python3 -m specs.v3.tools.cli render executive plan.yaml --view exec-top
                    -->
                    ```mermaid
                    old
                    ```

                    Старая подпись.
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )

            updated = update_markdown_files([md])
            text = md.read_text(encoding="utf-8")
            self.assertEqual(updated, 1)
            self.assertIn("Новая подпись из YAML.", text)
            self.assertNotIn("Старая подпись.", text)

    def test_does_not_cross_sections_to_find_generated_block(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            plan_path = tmp / "plan.yaml"
            plan_path.write_text(
                textwrap.dedent(
                    """
                    version: 3
                    nodes:
                      root:
                        title: Root
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )

            md = tmp / "report.md"
            md.write_text(
                textwrap.dedent(
                    f"""
                    ## Section A
                    <!--
                    Перегенерить:
                    env PYTHONPATH={BASE_DIR} python3 -m specs.v3.tools.cli validate plan.yaml
                    env PYTHONPATH={BASE_DIR} python3 -m specs.v3.tools.cli render tree plan.yaml
                    -->

                    Text without a generated block in this section.

                    ## Section B
                    <!-- GENERATED:START -->
                    old section b
                    <!-- GENERATED:END -->
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                update_markdown_files([md])

            text = md.read_text(encoding="utf-8")
            self.assertIn("old section b", text)
            self.assertIn("Text without a generated block", text)


if __name__ == "__main__":
    unittest.main()
