"""
Tests for opskarta v2 CLI.

This module tests the command-line interface for validating
and rendering opskarta v2 plan files.

Requirements covered:
- 5.11: CLI SHALL accept list of files as command line arguments
- 5.12: WHEN CLI receives multiple files THEN CLI SHALL pass them to Loader as Plan_Set
"""

import os
import tempfile
from pathlib import Path
from typing import Generator

import pytest

from specs.v2.tools.cli import (
    create_parser,
    main,
    cmd_validate,
    cmd_render_gantt,
    cmd_render_tree,
    cmd_render_list,
    cmd_render_deps,
)


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def valid_plan_file(temp_dir: Path) -> Path:
    """Create a valid plan file for testing."""
    plan_file = temp_dir / "plan.yaml"
    plan_file.write_text("""
version: 2
meta:
  id: test-plan
  title: Test Plan
  effort_unit: sp

statuses:
  not_started: { label: "Not Started" }
  in_progress: { label: "In Progress" }
  done: { label: "Done" }

nodes:
  task1:
    title: Task 1
    status: not_started
    effort: 5
  task2:
    title: Task 2
    status: in_progress
    after: [task1]
    effort: 3
  task3:
    title: Task 3
    parent: task1
    effort: 2
""")
    return plan_file


@pytest.fixture
def plan_with_schedule(temp_dir: Path) -> Path:
    """Create a plan file with schedule for testing."""
    plan_file = temp_dir / "scheduled_plan.yaml"
    plan_file.write_text("""
version: 2
meta:
  id: scheduled-plan
  title: Scheduled Plan

nodes:
  task1:
    title: Task 1
  task2:
    title: Task 2
    after: [task1]
  milestone1:
    title: Milestone 1
    milestone: true
    after: [task2]

schedule:
  calendars:
    default:
      excludes:
        - weekends
  default_calendar: default
  nodes:
    task1:
      start: "2024-03-01"
      duration: "3d"
    task2:
      duration: "5d"
    milestone1: {}
""")
    return plan_file


@pytest.fixture
def plan_with_views(temp_dir: Path) -> Path:
    """Create a plan file with views for testing."""
    plan_file = temp_dir / "plan_with_views.yaml"
    plan_file.write_text("""
version: 2
meta:
  id: plan-with-views
  title: Plan with Views

statuses:
  backlog: { label: "Backlog" }
  active: { label: "Active" }

nodes:
  epic1:
    title: Epic 1
    kind: epic
    status: active
  task1:
    title: Task 1
    kind: task
    parent: epic1
    status: backlog
  task2:
    title: Task 2
    kind: task
    parent: epic1
    status: active

views:
  backlog:
    title: Backlog View
    where:
      status: [backlog]
  tasks_only:
    title: Tasks Only
    where:
      kind: [task]
    order_by: title
""")
    return plan_file


@pytest.fixture
def invalid_plan_file(temp_dir: Path) -> Path:
    """Create an invalid plan file for testing."""
    plan_file = temp_dir / "invalid_plan.yaml"
    plan_file.write_text("""
version: 2
nodes:
  task1:
    # Missing required title field
    status: active
  task2:
    title: Task 2
    effort: -5  # Invalid negative effort
""")
    return plan_file


@pytest.fixture
def multi_file_main(temp_dir: Path) -> Path:
    """Create main file for multi-file plan."""
    main_file = temp_dir / "main.yaml"
    main_file.write_text("""
version: 2
meta:
  id: multi-file-plan
  title: Multi-File Plan

statuses:
  todo: { label: "To Do" }
  done: { label: "Done" }
""")
    return main_file


@pytest.fixture
def multi_file_nodes(temp_dir: Path) -> Path:
    """Create nodes file for multi-file plan."""
    nodes_file = temp_dir / "nodes.yaml"
    nodes_file.write_text("""
version: 2
nodes:
  task1:
    title: Task 1
    status: todo
  task2:
    title: Task 2
    status: done
    after: [task1]
""")
    return nodes_file


class TestParser:
    """Tests for argument parser creation."""
    
    def test_create_parser(self):
        """Parser should be created successfully."""
        parser = create_parser()
        assert parser is not None
        assert parser.prog == "opskarta"
    
    def test_validate_command_parsing(self):
        """Validate command should parse files correctly."""
        parser = create_parser()
        args = parser.parse_args(["validate", "file1.yaml", "file2.yaml"])
        assert args.command == "validate"
        assert args.files == ["file1.yaml", "file2.yaml"]
    
    def test_render_gantt_parsing(self):
        """Render gantt command should parse correctly."""
        parser = create_parser()
        args = parser.parse_args(["render", "gantt", "plan.yaml"])
        assert args.command == "render"
        assert args.format == "gantt"
        assert args.files == ["plan.yaml"]
        assert args.view is None
    
    def test_render_gantt_with_view(self):
        """Render gantt with --view should parse correctly."""
        parser = create_parser()
        args = parser.parse_args(["render", "gantt", "plan.yaml", "--view", "main"])
        assert args.command == "render"
        assert args.format == "gantt"
        assert args.view == "main"
    
    def test_render_tree_parsing(self):
        """Render tree command should parse correctly."""
        parser = create_parser()
        args = parser.parse_args(["render", "tree", "plan.yaml", "--view", "backlog"])
        assert args.command == "render"
        assert args.format == "tree"
        assert args.view == "backlog"
    
    def test_render_list_parsing(self):
        """Render list command should parse correctly."""
        parser = create_parser()
        args = parser.parse_args(["render", "list", "plan.yaml"])
        assert args.command == "render"
        assert args.format == "list"
    
    def test_render_deps_parsing(self):
        """Render deps command should parse correctly."""
        parser = create_parser()
        args = parser.parse_args(["render", "deps", "plan.yaml"])
        assert args.command == "render"
        assert args.format == "deps"
    
    def test_multiple_files_parsing(self):
        """Multiple files should be parsed correctly."""
        parser = create_parser()
        args = parser.parse_args(["validate", "main.yaml", "nodes.yaml", "schedule.yaml"])
        assert args.files == ["main.yaml", "nodes.yaml", "schedule.yaml"]


class TestValidateCommand:
    """Tests for the validate command."""
    
    def test_validate_valid_plan(self, valid_plan_file: Path):
        """Valid plan should return 0 and print OK."""
        result = cmd_validate([str(valid_plan_file)])
        assert result == 0
    
    def test_validate_invalid_plan(self, invalid_plan_file: Path):
        """Invalid plan should return 1."""
        result = cmd_validate([str(invalid_plan_file)])
        assert result == 1
    
    def test_validate_nonexistent_file(self):
        """Non-existent file should return 1."""
        result = cmd_validate(["nonexistent.yaml"])
        assert result == 1
    
    def test_validate_multiple_files(
        self,
        multi_file_main: Path,
        multi_file_nodes: Path
    ):
        """Multiple valid files should be merged and validated."""
        result = cmd_validate([str(multi_file_main), str(multi_file_nodes)])
        assert result == 0
    
    def test_validate_via_main(self, valid_plan_file: Path):
        """Validate command via main() should work."""
        result = main(["validate", str(valid_plan_file)])
        assert result == 0


class TestRenderGanttCommand:
    """Tests for the render gantt command."""
    
    def test_render_gantt_basic(self, plan_with_schedule: Path, capsys):
        """Render gantt should produce Mermaid output."""
        result = cmd_render_gantt([str(plan_with_schedule)], None)
        assert result == 0
        
        captured = capsys.readouterr()
        assert "gantt" in captured.out
        assert "Task 1" in captured.out
    
    def test_render_gantt_with_view(self, plan_with_views: Path, capsys):
        """Render gantt with view should apply filtering."""
        # This plan doesn't have schedule, so gantt will be minimal
        result = cmd_render_gantt([str(plan_with_views)], "tasks_only")
        assert result == 0
    
    def test_render_gantt_invalid_view(self, plan_with_schedule: Path):
        """Render gantt with non-existent view should fail."""
        result = cmd_render_gantt([str(plan_with_schedule)], "nonexistent")
        assert result == 1
    
    def test_render_gantt_via_main(self, plan_with_schedule: Path, capsys):
        """Render gantt via main() should work."""
        result = main(["render", "gantt", str(plan_with_schedule)])
        assert result == 0
        
        captured = capsys.readouterr()
        assert "gantt" in captured.out


class TestRenderTreeCommand:
    """Tests for the render tree command."""
    
    def test_render_tree_basic(self, valid_plan_file: Path, capsys):
        """Render tree should produce hierarchical output."""
        result = cmd_render_tree([str(valid_plan_file)], None)
        assert result == 0
        
        captured = capsys.readouterr()
        assert "Task 1" in captured.out
        # Task 3 is a child of Task 1, should be indented
        assert "Task 3" in captured.out
    
    def test_render_tree_with_view(self, plan_with_views: Path, capsys):
        """Render tree with view should apply filtering."""
        result = cmd_render_tree([str(plan_with_views)], "backlog")
        assert result == 0
        
        captured = capsys.readouterr()
        # Only backlog items should be shown
        assert "Task 1" in captured.out
        # Task 2 has status=active, should not be shown
        assert "Task 2" not in captured.out
    
    def test_render_tree_invalid_view(self, valid_plan_file: Path):
        """Render tree with non-existent view should fail."""
        result = cmd_render_tree([str(valid_plan_file)], "nonexistent")
        assert result == 1
    
    def test_render_tree_via_main(self, valid_plan_file: Path, capsys):
        """Render tree via main() should work."""
        result = main(["render", "tree", str(valid_plan_file)])
        assert result == 0


class TestRenderListCommand:
    """Tests for the render list command."""
    
    def test_render_list_basic(self, valid_plan_file: Path, capsys):
        """Render list should produce flat list output."""
        result = cmd_render_list([str(valid_plan_file)], None)
        assert result == 0
        
        captured = capsys.readouterr()
        assert "- Task 1" in captured.out
        assert "- Task 2" in captured.out
    
    def test_render_list_with_view(self, plan_with_views: Path, capsys):
        """Render list with view should apply filtering and sorting."""
        result = cmd_render_list([str(plan_with_views)], "tasks_only")
        assert result == 0
        
        captured = capsys.readouterr()
        # Only tasks should be shown (not epic)
        assert "Task 1" in captured.out
        assert "Task 2" in captured.out
        assert "Epic 1" not in captured.out
    
    def test_render_list_via_main(self, valid_plan_file: Path, capsys):
        """Render list via main() should work."""
        result = main(["render", "list", str(valid_plan_file)])
        assert result == 0


class TestRenderDepsCommand:
    """Tests for the render deps command."""
    
    def test_render_deps_basic(self, valid_plan_file: Path, capsys):
        """Render deps should produce Mermaid flowchart output."""
        result = cmd_render_deps([str(valid_plan_file)], None)
        assert result == 0
        
        captured = capsys.readouterr()
        assert "flowchart LR" in captured.out
        # task2 depends on task1
        assert "task1" in captured.out
        assert "task2" in captured.out
    
    def test_render_deps_with_view(self, plan_with_views: Path, capsys):
        """Render deps with view should apply filtering."""
        result = cmd_render_deps([str(plan_with_views)], "tasks_only")
        assert result == 0
        
        captured = capsys.readouterr()
        assert "flowchart LR" in captured.out
    
    def test_render_deps_via_main(self, valid_plan_file: Path, capsys):
        """Render deps via main() should work."""
        result = main(["render", "deps", str(valid_plan_file)])
        assert result == 0


class TestMultiFileSupport:
    """Tests for multi-file plan support (Requirements 5.11, 5.12)."""
    
    def test_validate_multi_file(
        self,
        multi_file_main: Path,
        multi_file_nodes: Path
    ):
        """
        Validate should accept multiple files and merge them.
        
        Validates: Requirements 5.11, 5.12
        """
        result = main([
            "validate",
            str(multi_file_main),
            str(multi_file_nodes)
        ])
        assert result == 0
    
    def test_render_multi_file(
        self,
        multi_file_main: Path,
        multi_file_nodes: Path,
        capsys
    ):
        """
        Render should accept multiple files and merge them.
        
        Validates: Requirements 5.11, 5.12
        """
        result = main([
            "render", "tree",
            str(multi_file_main),
            str(multi_file_nodes)
        ])
        assert result == 0
        
        captured = capsys.readouterr()
        # Nodes from nodes.yaml should be rendered
        assert "Task 1" in captured.out
        assert "Task 2" in captured.out


class TestErrorHandling:
    """Tests for error handling in CLI."""
    
    def test_load_error_handling(self, temp_dir: Path):
        """Load errors should be reported properly."""
        # Create a file with invalid YAML
        bad_file = temp_dir / "bad.yaml"
        bad_file.write_text("invalid: yaml: content: [")
        
        result = cmd_validate([str(bad_file)])
        assert result == 1
    
    def test_merge_conflict_handling(self, temp_dir: Path):
        """Merge conflicts should be reported properly."""
        # Create two files with conflicting node IDs
        file1 = temp_dir / "file1.yaml"
        file1.write_text("""
version: 2
nodes:
  task1:
    title: Task 1 from file1
""")
        
        file2 = temp_dir / "file2.yaml"
        file2.write_text("""
version: 2
nodes:
  task1:
    title: Task 1 from file2
""")
        
        result = cmd_validate([str(file1), str(file2)])
        assert result == 1
    
    def test_validation_error_handling(self, invalid_plan_file: Path, capsys):
        """Validation errors should be reported properly."""
        result = cmd_validate([str(invalid_plan_file)])
        assert result == 1
        
        captured = capsys.readouterr()
        # Error messages should be in stderr
        assert "error" in captured.err.lower()
