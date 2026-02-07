"""
Tests for the loader module.

Tests cover:
- 1.1: Loading files as Fragments
- 1.2: Accepting only allowed top-level blocks
- 1.3: Error reporting with block name and file
- 1.4: Conflict detection for duplicate node_id
- 1.5: Conflict detection for duplicate status_id
- 1.6: Meta block merging with conflict detection
- 1.7: Schedule block merging (calendars and nodes)
- 1.8: schedule.default_calendar conflict
- 1.9: Return MergedPlan with all merged data
- 1.10: Source tracking for each element
"""

import tempfile
import unittest
from pathlib import Path

from specs.v2.tools.loader import (
    ALLOWED_TOP_LEVEL_BLOCKS,
    LoadError,
    MergeConflictError,
    load_fragment,
    load_plan_set,
    merge_fragments,
)
from specs.v2.tools.models import MergedPlan


class TestAllowedBlocks(unittest.TestCase):
    """Tests for ALLOWED_TOP_LEVEL_BLOCKS constant."""
    
    def test_allowed_blocks_contains_required(self):
        """All required blocks are in ALLOWED_TOP_LEVEL_BLOCKS."""
        required = {"version", "meta", "statuses", "nodes", "schedule", "views", "x"}
        self.assertEqual(ALLOWED_TOP_LEVEL_BLOCKS, required)
    
    def test_allowed_blocks_is_frozenset(self):
        """ALLOWED_TOP_LEVEL_BLOCKS is immutable."""
        self.assertIsInstance(ALLOWED_TOP_LEVEL_BLOCKS, frozenset)


class TestLoadFragment(unittest.TestCase):
    """Tests for load_fragment function."""
    
    def setUp(self):
        """Create a temporary directory for test files."""
        self.temp_dir = tempfile.mkdtemp()
    
    def _write_yaml(self, filename: str, content: str) -> str:
        """Write YAML content to a temp file and return path."""
        path = Path(self.temp_dir) / filename
        path.write_text(content, encoding="utf-8")
        return str(path)
    
    def test_load_valid_fragment(self):
        """Load a valid fragment with all allowed blocks."""
        yaml_content = """
version: 2
meta:
  id: test-plan
  title: Test Plan
nodes:
  task1:
    title: Task 1
"""
        path = self._write_yaml("valid.yaml", yaml_content)
        
        fragment = load_fragment(path)
        
        self.assertEqual(fragment["version"], 2)
        self.assertEqual(fragment["meta"]["id"], "test-plan")
        self.assertEqual(fragment["nodes"]["task1"]["title"], "Task 1")
        self.assertEqual(fragment["_source"], path)
    
    def test_load_empty_file(self):
        """Empty file returns empty dict with source."""
        path = self._write_yaml("empty.yaml", "")
        
        fragment = load_fragment(path)
        
        self.assertEqual(fragment, {"_source": path})
    
    def test_load_fragment_with_schedule(self):
        """Load fragment with schedule block."""
        yaml_content = """
version: 2
schedule:
  calendars:
    default:
      excludes:
        - weekends
  default_calendar: default
  nodes:
    task1:
      start: "2024-03-01"
      duration: "5d"
"""
        path = self._write_yaml("schedule.yaml", yaml_content)
        
        fragment = load_fragment(path)
        
        self.assertEqual(fragment["schedule"]["default_calendar"], "default")
        self.assertIn("weekends", fragment["schedule"]["calendars"]["default"]["excludes"])
    
    def test_load_fragment_with_views(self):
        """Load fragment with views block."""
        yaml_content = """
version: 2
views:
  main:
    title: Main View
    where:
      kind: [task, phase]
"""
        path = self._write_yaml("views.yaml", yaml_content)
        
        fragment = load_fragment(path)
        
        self.assertEqual(fragment["views"]["main"]["title"], "Main View")
    
    def test_load_fragment_with_statuses(self):
        """Load fragment with statuses block."""
        yaml_content = """
version: 2
statuses:
  done:
    label: Done
    color: "#22c55e"
"""
        path = self._write_yaml("statuses.yaml", yaml_content)
        
        fragment = load_fragment(path)
        
        self.assertEqual(fragment["statuses"]["done"]["label"], "Done")
    
    def test_load_fragment_with_x_extension(self):
        """Load fragment with x (extension) block."""
        yaml_content = """
version: 2
x:
  custom_field: custom_value
  nested:
    key: value
"""
        path = self._write_yaml("extension.yaml", yaml_content)
        
        fragment = load_fragment(path)
        
        self.assertEqual(fragment["x"]["custom_field"], "custom_value")
    
    def test_source_is_preserved(self):
        """Source file path is preserved in fragment."""
        yaml_content = "version: 2"
        path = self._write_yaml("source.yaml", yaml_content)
        
        fragment = load_fragment(path)
        
        self.assertEqual(fragment["_source"], path)


class TestLoadFragmentInvalidBlocks(unittest.TestCase):
    """Tests for invalid top-level block detection (Requirement 1.2, 1.3)."""
    
    def setUp(self):
        """Create a temporary directory for test files."""
        self.temp_dir = tempfile.mkdtemp()
    
    def _write_yaml(self, filename: str, content: str) -> str:
        """Write YAML content to a temp file and return path."""
        path = Path(self.temp_dir) / filename
        path.write_text(content, encoding="utf-8")
        return str(path)
    
    def test_invalid_block_raises_error(self):
        """Invalid top-level block raises LoadError."""
        yaml_content = """
version: 2
invalid_block: some_value
"""
        path = self._write_yaml("invalid.yaml", yaml_content)
        
        with self.assertRaises(LoadError) as ctx:
            load_fragment(path)
        
        self.assertIn("invalid_block", str(ctx.exception))
        self.assertEqual(ctx.exception.block_name, "invalid_block")
        self.assertEqual(ctx.exception.file_path, path)
    
    def test_multiple_invalid_blocks_reports_first(self):
        """Multiple invalid blocks - first one is reported."""
        yaml_content = """
version: 2
bad_block1: value1
bad_block2: value2
"""
        path = self._write_yaml("multi_invalid.yaml", yaml_content)
        
        with self.assertRaises(LoadError) as ctx:
            load_fragment(path)
        
        # At least one invalid block is reported
        self.assertTrue(
            ctx.exception.block_name in ("bad_block1", "bad_block2")
        )
    
    def test_error_message_contains_file_path(self):
        """Error message contains file path (Requirement 1.3)."""
        yaml_content = """
unknown: value
"""
        path = self._write_yaml("error_path.yaml", yaml_content)
        
        with self.assertRaises(LoadError) as ctx:
            load_fragment(path)
        
        self.assertIn(path, str(ctx.exception))
    
    def test_error_message_contains_block_name(self):
        """Error message contains block name (Requirement 1.3)."""
        yaml_content = """
forbidden_block: value
"""
        path = self._write_yaml("error_block.yaml", yaml_content)
        
        with self.assertRaises(LoadError) as ctx:
            load_fragment(path)
        
        self.assertIn("forbidden_block", str(ctx.exception))


class TestLoadFragmentErrors(unittest.TestCase):
    """Tests for error handling in load_fragment."""
    
    def setUp(self):
        """Create a temporary directory for test files."""
        self.temp_dir = tempfile.mkdtemp()
    
    def _write_yaml(self, filename: str, content: str) -> str:
        """Write YAML content to a temp file and return path."""
        path = Path(self.temp_dir) / filename
        path.write_text(content, encoding="utf-8")
        return str(path)
    
    def test_file_not_found(self):
        """Non-existent file raises LoadError."""
        with self.assertRaises(LoadError) as ctx:
            load_fragment("/nonexistent/path/file.yaml")
        
        self.assertIn("not found", str(ctx.exception).lower())
    
    def test_invalid_yaml_syntax(self):
        """Invalid YAML syntax raises LoadError."""
        yaml_content = """
version: 2
nodes:
  - invalid: yaml
    syntax: [
"""
        path = self._write_yaml("invalid_yaml.yaml", yaml_content)
        
        with self.assertRaises(LoadError) as ctx:
            load_fragment(path)
        
        self.assertIn("YAML", str(ctx.exception))
    
    def test_non_mapping_yaml(self):
        """YAML that is not a mapping raises LoadError."""
        yaml_content = """
- item1
- item2
"""
        path = self._write_yaml("list.yaml", yaml_content)
        
        with self.assertRaises(LoadError) as ctx:
            load_fragment(path)
        
        self.assertIn("mapping", str(ctx.exception).lower())
    
    def test_scalar_yaml(self):
        """YAML that is a scalar raises LoadError."""
        yaml_content = "just a string"
        path = self._write_yaml("scalar.yaml", yaml_content)
        
        with self.assertRaises(LoadError) as ctx:
            load_fragment(path)
        
        self.assertIn("mapping", str(ctx.exception).lower())


class TestLoadErrorException(unittest.TestCase):
    """Tests for LoadError exception class."""
    
    def test_error_with_all_attributes(self):
        """LoadError with all attributes."""
        error = LoadError(
            message="Test error",
            file_path="test.yaml",
            block_name="invalid_block",
        )
        
        self.assertEqual(error.message, "Test error")
        self.assertEqual(error.file_path, "test.yaml")
        self.assertEqual(error.block_name, "invalid_block")
        self.assertIn("test.yaml", str(error))
        self.assertIn("Test error", str(error))
        self.assertIn("invalid_block", str(error))
    
    def test_error_with_message_only(self):
        """LoadError with message only."""
        error = LoadError(message="Simple error")
        
        self.assertEqual(error.message, "Simple error")
        self.assertIsNone(error.file_path)
        self.assertIsNone(error.block_name)
        self.assertEqual(str(error), "Simple error")
    
    def test_error_with_file_path(self):
        """LoadError with file path."""
        error = LoadError(
            message="File error",
            file_path="path/to/file.yaml",
        )
        
        self.assertIn("path/to/file.yaml", str(error))
        self.assertIn("File error", str(error))


if __name__ == "__main__":
    unittest.main()


class TestMergeConflictError(unittest.TestCase):
    """Tests for MergeConflictError exception class."""
    
    def test_error_with_all_attributes(self):
        """MergeConflictError with all attributes."""
        error = MergeConflictError(
            message="Duplicate node",
            element_type="node",
            element_id="task1",
            files=["file1.yaml", "file2.yaml"],
        )
        
        self.assertEqual(error.message, "Duplicate node")
        self.assertEqual(error.element_type, "node")
        self.assertEqual(error.element_id, "task1")
        self.assertEqual(error.files, ["file1.yaml", "file2.yaml"])
        self.assertIn("file1.yaml", str(error))
        self.assertIn("file2.yaml", str(error))
    
    def test_error_with_message_only(self):
        """MergeConflictError with message only."""
        error = MergeConflictError(message="Simple conflict")
        
        self.assertEqual(error.message, "Simple conflict")
        self.assertIsNone(error.element_type)
        self.assertIsNone(error.element_id)
        self.assertEqual(error.files, [])


class TestMergeFragmentsBasic(unittest.TestCase):
    """Basic tests for merge_fragments function."""
    
    def test_merge_empty_list(self):
        """Merging empty list returns empty MergedPlan."""
        result = merge_fragments([])
        
        self.assertIsInstance(result, MergedPlan)
        self.assertEqual(result.version, 2)
        self.assertEqual(result.nodes, {})
        self.assertEqual(result.statuses, {})
        self.assertIsNone(result.schedule)
        self.assertEqual(result.views, {})
        self.assertEqual(result.x, {})
    
    def test_merge_single_fragment(self):
        """Merging single fragment returns its data."""
        fragment = {
            "_source": "test.yaml",
            "version": 2,
            "nodes": {
                "task1": {"title": "Task 1"},
            },
        }
        
        result = merge_fragments([fragment])
        
        self.assertEqual(result.version, 2)
        self.assertEqual(len(result.nodes), 1)
        self.assertEqual(result.nodes["task1"].title, "Task 1")
        self.assertEqual(result.sources["node:task1"], "test.yaml")
    
    def test_merge_two_fragments_no_conflict(self):
        """Merging two fragments without conflicts."""
        f1 = {
            "_source": "file1.yaml",
            "version": 2,
            "nodes": {"task1": {"title": "Task 1"}},
        }
        f2 = {
            "_source": "file2.yaml",
            "version": 2,
            "nodes": {"task2": {"title": "Task 2"}},
        }
        
        result = merge_fragments([f1, f2])
        
        self.assertEqual(len(result.nodes), 2)
        self.assertIn("task1", result.nodes)
        self.assertIn("task2", result.nodes)
        self.assertEqual(result.sources["node:task1"], "file1.yaml")
        self.assertEqual(result.sources["node:task2"], "file2.yaml")


class TestMergeFragmentsNodeConflict(unittest.TestCase):
    """Tests for node_id conflict detection (Requirement 1.4)."""
    
    def test_duplicate_node_id_raises_error(self):
        """Duplicate node_id raises MergeConflictError."""
        f1 = {
            "_source": "file1.yaml",
            "version": 2,
            "nodes": {"task1": {"title": "Task 1 from file1"}},
        }
        f2 = {
            "_source": "file2.yaml",
            "version": 2,
            "nodes": {"task1": {"title": "Task 1 from file2"}},
        }
        
        with self.assertRaises(MergeConflictError) as ctx:
            merge_fragments([f1, f2])
        
        self.assertEqual(ctx.exception.element_type, "node")
        self.assertEqual(ctx.exception.element_id, "task1")
        self.assertIn("file1.yaml", ctx.exception.files)
        self.assertIn("file2.yaml", ctx.exception.files)
        self.assertIn("task1", str(ctx.exception))
    
    def test_same_node_id_in_three_fragments(self):
        """Conflict detected even with three fragments."""
        f1 = {"_source": "f1.yaml", "version": 2, "nodes": {"x": {"title": "X1"}}}
        f2 = {"_source": "f2.yaml", "version": 2, "nodes": {"y": {"title": "Y"}}}
        f3 = {"_source": "f3.yaml", "version": 2, "nodes": {"x": {"title": "X3"}}}
        
        with self.assertRaises(MergeConflictError) as ctx:
            merge_fragments([f1, f2, f3])
        
        self.assertEqual(ctx.exception.element_id, "x")


class TestMergeFragmentsStatusConflict(unittest.TestCase):
    """Tests for status_id conflict detection (Requirement 1.5)."""
    
    def test_duplicate_status_id_raises_error(self):
        """Duplicate status_id raises MergeConflictError."""
        f1 = {
            "_source": "file1.yaml",
            "version": 2,
            "statuses": {"done": {"label": "Done", "color": "#22c55e"}},
        }
        f2 = {
            "_source": "file2.yaml",
            "version": 2,
            "statuses": {"done": {"label": "Completed", "color": "#00ff00"}},
        }
        
        with self.assertRaises(MergeConflictError) as ctx:
            merge_fragments([f1, f2])
        
        self.assertEqual(ctx.exception.element_type, "status")
        self.assertEqual(ctx.exception.element_id, "done")
        self.assertIn("file1.yaml", ctx.exception.files)
        self.assertIn("file2.yaml", ctx.exception.files)
    
    def test_merge_different_statuses(self):
        """Different status_ids merge successfully."""
        f1 = {
            "_source": "file1.yaml",
            "version": 2,
            "statuses": {"done": {"label": "Done"}},
        }
        f2 = {
            "_source": "file2.yaml",
            "version": 2,
            "statuses": {"in_progress": {"label": "In Progress"}},
        }
        
        result = merge_fragments([f1, f2])
        
        self.assertEqual(len(result.statuses), 2)
        self.assertEqual(result.statuses["done"].label, "Done")
        self.assertEqual(result.statuses["in_progress"].label, "In Progress")


class TestMergeFragmentsMetaConflict(unittest.TestCase):
    """Tests for meta block merging (Requirement 1.6)."""
    
    def test_meta_field_conflict_raises_error(self):
        """Conflicting meta field values raise MergeConflictError."""
        f1 = {
            "_source": "file1.yaml",
            "version": 2,
            "meta": {"id": "project-a", "title": "Project A"},
        }
        f2 = {
            "_source": "file2.yaml",
            "version": 2,
            "meta": {"id": "project-b"},  # Different id
        }
        
        with self.assertRaises(MergeConflictError) as ctx:
            merge_fragments([f1, f2])
        
        self.assertEqual(ctx.exception.element_type, "meta")
        self.assertEqual(ctx.exception.element_id, "id")
        self.assertIn("project-a", str(ctx.exception))
        self.assertIn("project-b", str(ctx.exception))
    
    def test_meta_same_values_no_conflict(self):
        """Same meta field values do not conflict."""
        f1 = {
            "_source": "file1.yaml",
            "version": 2,
            "meta": {"id": "project-x"},
        }
        f2 = {
            "_source": "file2.yaml",
            "version": 2,
            "meta": {"id": "project-x"},  # Same value
        }
        
        result = merge_fragments([f1, f2])
        
        self.assertEqual(result.meta.id, "project-x")
    
    def test_meta_different_fields_merge(self):
        """Different meta fields merge successfully."""
        f1 = {
            "_source": "file1.yaml",
            "version": 2,
            "meta": {"id": "project-x"},
        }
        f2 = {
            "_source": "file2.yaml",
            "version": 2,
            "meta": {"title": "Project X"},
        }
        
        result = merge_fragments([f1, f2])
        
        self.assertEqual(result.meta.id, "project-x")
        self.assertEqual(result.meta.title, "Project X")


class TestMergeFragmentsSchedule(unittest.TestCase):
    """Tests for schedule block merging (Requirements 1.7, 1.8)."""
    
    def test_merge_schedule_calendars(self):
        """Calendars from different fragments merge."""
        f1 = {
            "_source": "file1.yaml",
            "version": 2,
            "schedule": {
                "calendars": {"work": {"excludes": ["weekends"]}},
            },
        }
        f2 = {
            "_source": "file2.yaml",
            "version": 2,
            "schedule": {
                "calendars": {"holiday": {"excludes": ["2024-12-25"]}},
            },
        }
        
        result = merge_fragments([f1, f2])
        
        self.assertIsNotNone(result.schedule)
        self.assertEqual(len(result.schedule.calendars), 2)
        self.assertIn("work", result.schedule.calendars)
        self.assertIn("holiday", result.schedule.calendars)
    
    def test_duplicate_calendar_id_raises_error(self):
        """Duplicate calendar_id raises MergeConflictError."""
        f1 = {
            "_source": "file1.yaml",
            "version": 2,
            "schedule": {"calendars": {"default": {"excludes": ["weekends"]}}},
        }
        f2 = {
            "_source": "file2.yaml",
            "version": 2,
            "schedule": {"calendars": {"default": {"excludes": []}}},
        }
        
        with self.assertRaises(MergeConflictError) as ctx:
            merge_fragments([f1, f2])
        
        self.assertEqual(ctx.exception.element_type, "calendar")
        self.assertEqual(ctx.exception.element_id, "default")
    
    def test_merge_schedule_nodes(self):
        """Schedule nodes from different fragments merge."""
        f1 = {
            "_source": "file1.yaml",
            "version": 2,
            "schedule": {
                "nodes": {"task1": {"start": "2024-03-01", "duration": "5d"}},
            },
        }
        f2 = {
            "_source": "file2.yaml",
            "version": 2,
            "schedule": {
                "nodes": {"task2": {"start": "2024-03-10", "duration": "3d"}},
            },
        }
        
        result = merge_fragments([f1, f2])
        
        self.assertEqual(len(result.schedule.nodes), 2)
        self.assertEqual(result.schedule.nodes["task1"].start, "2024-03-01")
        self.assertEqual(result.schedule.nodes["task2"].start, "2024-03-10")
    
    def test_duplicate_schedule_node_raises_error(self):
        """Duplicate schedule node_id raises MergeConflictError."""
        f1 = {
            "_source": "file1.yaml",
            "version": 2,
            "schedule": {"nodes": {"task1": {"start": "2024-03-01"}}},
        }
        f2 = {
            "_source": "file2.yaml",
            "version": 2,
            "schedule": {"nodes": {"task1": {"start": "2024-04-01"}}},
        }
        
        with self.assertRaises(MergeConflictError) as ctx:
            merge_fragments([f1, f2])
        
        self.assertEqual(ctx.exception.element_type, "schedule_node")
        self.assertEqual(ctx.exception.element_id, "task1")
    
    def test_default_calendar_conflict_raises_error(self):
        """Multiple default_calendar definitions raise MergeConflictError (Requirement 1.8)."""
        f1 = {
            "_source": "file1.yaml",
            "version": 2,
            "schedule": {"default_calendar": "work"},
        }
        f2 = {
            "_source": "file2.yaml",
            "version": 2,
            "schedule": {"default_calendar": "holiday"},
        }
        
        with self.assertRaises(MergeConflictError) as ctx:
            merge_fragments([f1, f2])
        
        self.assertEqual(ctx.exception.element_type, "default_calendar")
        self.assertIn("file1.yaml", ctx.exception.files)
        self.assertIn("file2.yaml", ctx.exception.files)
    
    def test_single_default_calendar_allowed(self):
        """Single default_calendar is allowed."""
        f1 = {
            "_source": "file1.yaml",
            "version": 2,
            "schedule": {
                "calendars": {"work": {"excludes": ["weekends"]}},
                "default_calendar": "work",
            },
        }
        f2 = {
            "_source": "file2.yaml",
            "version": 2,
            "schedule": {
                "nodes": {"task1": {"start": "2024-03-01"}},
            },
        }
        
        result = merge_fragments([f1, f2])
        
        self.assertEqual(result.schedule.default_calendar, "work")


class TestMergeFragmentsViews(unittest.TestCase):
    """Tests for views block merging."""
    
    def test_merge_views(self):
        """Views from different fragments merge."""
        f1 = {
            "_source": "file1.yaml",
            "version": 2,
            "views": {"main": {"title": "Main View"}},
        }
        f2 = {
            "_source": "file2.yaml",
            "version": 2,
            "views": {"gantt": {"title": "Gantt View"}},
        }
        
        result = merge_fragments([f1, f2])
        
        self.assertEqual(len(result.views), 2)
        self.assertEqual(result.views["main"].title, "Main View")
        self.assertEqual(result.views["gantt"].title, "Gantt View")
    
    def test_duplicate_view_id_raises_error(self):
        """Duplicate view_id raises MergeConflictError."""
        f1 = {
            "_source": "file1.yaml",
            "version": 2,
            "views": {"main": {"title": "Main 1"}},
        }
        f2 = {
            "_source": "file2.yaml",
            "version": 2,
            "views": {"main": {"title": "Main 2"}},
        }
        
        with self.assertRaises(MergeConflictError) as ctx:
            merge_fragments([f1, f2])
        
        self.assertEqual(ctx.exception.element_type, "view")
        self.assertEqual(ctx.exception.element_id, "main")
    
    def test_view_with_where_filter(self):
        """View with where filter is parsed correctly."""
        fragment = {
            "_source": "test.yaml",
            "version": 2,
            "views": {
                "tasks": {
                    "title": "Tasks",
                    "where": {
                        "kind": ["task"],
                        "status": ["in_progress"],
                        "has_schedule": True,
                        "parent": "root",
                    },
                },
            },
        }
        
        result = merge_fragments([fragment])
        
        view = result.views["tasks"]
        self.assertIsNotNone(view.where)
        self.assertEqual(view.where.kind, ["task"])
        self.assertEqual(view.where.status, ["in_progress"])
        self.assertTrue(view.where.has_schedule)
        self.assertEqual(view.where.parent, "root")


class TestMergeFragmentsExtensions(unittest.TestCase):
    """Tests for x (extensions) block merging."""
    
    def test_merge_extensions(self):
        """Extensions from different fragments merge."""
        f1 = {
            "_source": "file1.yaml",
            "version": 2,
            "x": {"custom1": "value1"},
        }
        f2 = {
            "_source": "file2.yaml",
            "version": 2,
            "x": {"custom2": "value2"},
        }
        
        result = merge_fragments([f1, f2])
        
        self.assertEqual(len(result.x), 2)
        self.assertEqual(result.x["custom1"], "value1")
        self.assertEqual(result.x["custom2"], "value2")
    
    def test_duplicate_extension_key_raises_error(self):
        """Duplicate extension key raises MergeConflictError."""
        f1 = {
            "_source": "file1.yaml",
            "version": 2,
            "x": {"custom": "value1"},
        }
        f2 = {
            "_source": "file2.yaml",
            "version": 2,
            "x": {"custom": "value2"},
        }
        
        with self.assertRaises(MergeConflictError) as ctx:
            merge_fragments([f1, f2])
        
        self.assertEqual(ctx.exception.element_type, "x")
        self.assertEqual(ctx.exception.element_id, "custom")


class TestMergeFragmentsVersion(unittest.TestCase):
    """Tests for version merging."""
    
    def test_version_mismatch_raises_error(self):
        """Version mismatch raises MergeConflictError."""
        f1 = {"_source": "file1.yaml", "version": 2}
        f2 = {"_source": "file2.yaml", "version": 1}
        
        with self.assertRaises(MergeConflictError) as ctx:
            merge_fragments([f1, f2])
        
        self.assertEqual(ctx.exception.element_type, "version")
        self.assertIn("file1.yaml", ctx.exception.files)
        self.assertIn("file2.yaml", ctx.exception.files)
    
    def test_same_version_no_conflict(self):
        """Same version in all fragments is OK."""
        f1 = {"_source": "file1.yaml", "version": 2}
        f2 = {"_source": "file2.yaml", "version": 2}
        f3 = {"_source": "file3.yaml", "version": 2}
        
        result = merge_fragments([f1, f2, f3])
        
        self.assertEqual(result.version, 2)


class TestMergeFragmentsSourceTracking(unittest.TestCase):
    """Tests for source tracking (Requirement 1.10)."""
    
    def test_all_elements_have_sources(self):
        """All merged elements have source tracking."""
        fragment = {
            "_source": "complete.yaml",
            "version": 2,
            "meta": {"id": "test", "title": "Test"},
            "statuses": {"done": {"label": "Done"}},
            "nodes": {"task1": {"title": "Task 1"}},
            "schedule": {
                "calendars": {"work": {"excludes": []}},
                "default_calendar": "work",
                "nodes": {"task1": {"start": "2024-03-01"}},
            },
            "views": {"main": {"title": "Main"}},
            "x": {"custom": "value"},
        }
        
        result = merge_fragments([fragment])
        
        # Check all sources are tracked
        self.assertEqual(result.sources["meta:id"], "complete.yaml")
        self.assertEqual(result.sources["meta:title"], "complete.yaml")
        self.assertEqual(result.sources["status:done"], "complete.yaml")
        self.assertEqual(result.sources["node:task1"], "complete.yaml")
        self.assertEqual(result.sources["calendar:work"], "complete.yaml")
        self.assertEqual(result.sources["schedule:default_calendar"], "complete.yaml")
        self.assertEqual(result.sources["schedule_node:task1"], "complete.yaml")
        self.assertEqual(result.sources["view:main"], "complete.yaml")
        self.assertEqual(result.sources["x:custom"], "complete.yaml")
    
    def test_sources_from_multiple_files(self):
        """Sources correctly track elements from multiple files."""
        f1 = {
            "_source": "nodes.yaml",
            "version": 2,
            "nodes": {"task1": {"title": "Task 1"}},
        }
        f2 = {
            "_source": "schedule.yaml",
            "version": 2,
            "schedule": {"nodes": {"task1": {"start": "2024-03-01"}}},
        }
        
        result = merge_fragments([f1, f2])
        
        self.assertEqual(result.sources["node:task1"], "nodes.yaml")
        self.assertEqual(result.sources["schedule_node:task1"], "schedule.yaml")


class TestMergeFragmentsNodeFields(unittest.TestCase):
    """Tests for correct parsing of node fields."""
    
    def test_all_node_fields_parsed(self):
        """All node fields are correctly parsed."""
        fragment = {
            "_source": "test.yaml",
            "version": 2,
            "nodes": {
                "task1": {
                    "title": "Task 1",
                    "kind": "task",
                    "status": "in_progress",
                    "parent": "root",
                    "after": ["task0"],
                    "milestone": True,
                    "issue": "PROJ-123",
                    "notes": "Some notes",
                    "effort": 5.5,
                    "x": {"custom": "value"},
                },
            },
        }
        
        result = merge_fragments([fragment])
        node = result.nodes["task1"]
        
        self.assertEqual(node.title, "Task 1")
        self.assertEqual(node.kind, "task")
        self.assertEqual(node.status, "in_progress")
        self.assertEqual(node.parent, "root")
        self.assertEqual(node.after, ["task0"])
        self.assertTrue(node.milestone)
        self.assertEqual(node.issue, "PROJ-123")
        self.assertEqual(node.notes, "Some notes")
        self.assertEqual(node.effort, 5.5)
        self.assertEqual(node.x, {"custom": "value"})
    
    def test_node_with_minimal_fields(self):
        """Node with only required fields is parsed correctly."""
        fragment = {
            "_source": "test.yaml",
            "version": 2,
            "nodes": {"task1": {"title": "Task 1"}},
        }
        
        result = merge_fragments([fragment])
        node = result.nodes["task1"]
        
        self.assertEqual(node.title, "Task 1")
        self.assertIsNone(node.kind)
        self.assertIsNone(node.status)
        self.assertIsNone(node.parent)
        self.assertIsNone(node.after)
        self.assertFalse(node.milestone)
        self.assertIsNone(node.issue)
        self.assertIsNone(node.notes)
        self.assertIsNone(node.effort)
        self.assertIsNone(node.x)


class TestLoadPlanSet(unittest.TestCase):
    """Tests for load_plan_set function (Requirement 5.1)."""
    
    def setUp(self):
        """Create a temporary directory for test files."""
        self.temp_dir = tempfile.mkdtemp()
    
    def _write_yaml(self, filename: str, content: str) -> str:
        """Write YAML content to a temp file and return path."""
        path = Path(self.temp_dir) / filename
        path.write_text(content, encoding="utf-8")
        return str(path)
    
    def test_load_plan_set_single_file(self):
        """Load plan set with a single file."""
        yaml_content = """
version: 2
meta:
  id: test-plan
  title: Test Plan
nodes:
  task1:
    title: Task 1
"""
        path = self._write_yaml("single.yaml", yaml_content)
        
        result = load_plan_set([path])
        
        self.assertIsInstance(result, MergedPlan)
        self.assertEqual(result.version, 2)
        self.assertEqual(result.meta.id, "test-plan")
        self.assertEqual(result.nodes["task1"].title, "Task 1")
        self.assertEqual(result.sources["node:task1"], path)
    
    def test_load_plan_set_multiple_files(self):
        """Load plan set with multiple files."""
        main_yaml = """
version: 2
meta:
  id: project-x
  title: Project X
statuses:
  done:
    label: Done
    color: "#22c55e"
"""
        nodes_yaml = """
version: 2
nodes:
  task1:
    title: Task 1
  task2:
    title: Task 2
    after: [task1]
"""
        schedule_yaml = """
version: 2
schedule:
  calendars:
    work:
      excludes:
        - weekends
  default_calendar: work
  nodes:
    task1:
      start: "2024-03-01"
      duration: "5d"
"""
        main_path = self._write_yaml("main.yaml", main_yaml)
        nodes_path = self._write_yaml("nodes.yaml", nodes_yaml)
        schedule_path = self._write_yaml("schedule.yaml", schedule_yaml)
        
        result = load_plan_set([main_path, nodes_path, schedule_path])
        
        # Check meta
        self.assertEqual(result.meta.id, "project-x")
        self.assertEqual(result.meta.title, "Project X")
        
        # Check statuses
        self.assertEqual(len(result.statuses), 1)
        self.assertEqual(result.statuses["done"].label, "Done")
        
        # Check nodes
        self.assertEqual(len(result.nodes), 2)
        self.assertEqual(result.nodes["task1"].title, "Task 1")
        self.assertEqual(result.nodes["task2"].title, "Task 2")
        
        # Check schedule
        self.assertIsNotNone(result.schedule)
        self.assertEqual(result.schedule.default_calendar, "work")
        self.assertIn("work", result.schedule.calendars)
        self.assertIn("task1", result.schedule.nodes)
        
        # Check sources
        self.assertEqual(result.sources["meta:id"], main_path)
        self.assertEqual(result.sources["node:task1"], nodes_path)
        self.assertEqual(result.sources["schedule_node:task1"], schedule_path)
    
    def test_load_plan_set_empty_list(self):
        """Load plan set with empty file list."""
        result = load_plan_set([])
        
        self.assertIsInstance(result, MergedPlan)
        self.assertEqual(result.version, 2)
        self.assertEqual(result.nodes, {})
        self.assertEqual(result.statuses, {})
    
    def test_load_plan_set_file_not_found(self):
        """Load plan set with non-existent file raises LoadError."""
        with self.assertRaises(LoadError) as ctx:
            load_plan_set(["/nonexistent/path/file.yaml"])
        
        self.assertIn("not found", str(ctx.exception).lower())
    
    def test_load_plan_set_invalid_yaml(self):
        """Load plan set with invalid YAML raises LoadError."""
        yaml_content = """
version: 2
nodes:
  - invalid: yaml
    syntax: [
"""
        path = self._write_yaml("invalid.yaml", yaml_content)
        
        with self.assertRaises(LoadError) as ctx:
            load_plan_set([path])
        
        self.assertIn("YAML", str(ctx.exception))
    
    def test_load_plan_set_invalid_block(self):
        """Load plan set with invalid top-level block raises LoadError."""
        yaml_content = """
version: 2
invalid_block: value
"""
        path = self._write_yaml("invalid_block.yaml", yaml_content)
        
        with self.assertRaises(LoadError) as ctx:
            load_plan_set([path])
        
        self.assertEqual(ctx.exception.block_name, "invalid_block")
    
    def test_load_plan_set_merge_conflict(self):
        """Load plan set with conflicting nodes raises MergeConflictError."""
        file1_yaml = """
version: 2
nodes:
  task1:
    title: Task 1 from file1
"""
        file2_yaml = """
version: 2
nodes:
  task1:
    title: Task 1 from file2
"""
        path1 = self._write_yaml("file1.yaml", file1_yaml)
        path2 = self._write_yaml("file2.yaml", file2_yaml)
        
        with self.assertRaises(MergeConflictError) as ctx:
            load_plan_set([path1, path2])
        
        self.assertEqual(ctx.exception.element_type, "node")
        self.assertEqual(ctx.exception.element_id, "task1")
        self.assertIn(path1, ctx.exception.files)
        self.assertIn(path2, ctx.exception.files)
    
    def test_load_plan_set_with_views(self):
        """Load plan set with views block."""
        yaml_content = """
version: 2
views:
  main:
    title: Main View
    where:
      kind: [task]
      has_schedule: true
    order_by: title
"""
        path = self._write_yaml("views.yaml", yaml_content)
        
        result = load_plan_set([path])
        
        self.assertEqual(len(result.views), 1)
        self.assertEqual(result.views["main"].title, "Main View")
        self.assertIsNotNone(result.views["main"].where)
        self.assertEqual(result.views["main"].where.kind, ["task"])
        self.assertTrue(result.views["main"].where.has_schedule)
    
    def test_load_plan_set_with_extensions(self):
        """Load plan set with x (extensions) block."""
        yaml_content = """
version: 2
x:
  custom_field: custom_value
  nested:
    key: value
"""
        path = self._write_yaml("extensions.yaml", yaml_content)
        
        result = load_plan_set([path])
        
        self.assertEqual(result.x["custom_field"], "custom_value")
        self.assertEqual(result.x["nested"]["key"], "value")
    
    def test_load_plan_set_preserves_order(self):
        """Load plan set processes files in order."""
        # First file defines meta.id
        file1_yaml = """
version: 2
meta:
  id: project-x
"""
        # Second file adds meta.title (no conflict)
        file2_yaml = """
version: 2
meta:
  title: Project X Title
"""
        path1 = self._write_yaml("file1.yaml", file1_yaml)
        path2 = self._write_yaml("file2.yaml", file2_yaml)
        
        result = load_plan_set([path1, path2])
        
        self.assertEqual(result.meta.id, "project-x")
        self.assertEqual(result.meta.title, "Project X Title")
        self.assertEqual(result.sources["meta:id"], path1)
        self.assertEqual(result.sources["meta:title"], path2)


class TestForbiddenNodeFields(unittest.TestCase):
    """Tests for forbidden fields in nodes (Requirement 2.4).
    
    In v2, calendar-related fields (start, finish, duration, excludes)
    are forbidden in nodes and must be in schedule.nodes instead.
    """
    
    def test_forbidden_node_fields_constant(self):
        """FORBIDDEN_NODE_FIELDS contains all forbidden fields."""
        from specs.v2.tools.loader import FORBIDDEN_NODE_FIELDS
        
        expected = {"start", "finish", "duration", "excludes"}
        self.assertEqual(FORBIDDEN_NODE_FIELDS, expected)
    
    def test_node_with_start_raises_error(self):
        """Node with 'start' field raises LoadError."""
        fragment = {
            "_source": "test.yaml",
            "version": 2,
            "nodes": {
                "task1": {
                    "title": "Task 1",
                    "start": "2024-03-01",  # Forbidden!
                },
            },
        }
        
        with self.assertRaises(LoadError) as ctx:
            merge_fragments([fragment])
        
        self.assertIn("start", str(ctx.exception))
        self.assertIn("task1", str(ctx.exception))
        self.assertIn("schedule.nodes", str(ctx.exception))
    
    def test_node_with_finish_raises_error(self):
        """Node with 'finish' field raises LoadError."""
        fragment = {
            "_source": "test.yaml",
            "version": 2,
            "nodes": {
                "task1": {
                    "title": "Task 1",
                    "finish": "2024-03-10",  # Forbidden!
                },
            },
        }
        
        with self.assertRaises(LoadError) as ctx:
            merge_fragments([fragment])
        
        self.assertIn("finish", str(ctx.exception))
        self.assertIn("task1", str(ctx.exception))
    
    def test_node_with_duration_raises_error(self):
        """Node with 'duration' field raises LoadError."""
        fragment = {
            "_source": "test.yaml",
            "version": 2,
            "nodes": {
                "task1": {
                    "title": "Task 1",
                    "duration": "5d",  # Forbidden!
                },
            },
        }
        
        with self.assertRaises(LoadError) as ctx:
            merge_fragments([fragment])
        
        self.assertIn("duration", str(ctx.exception))
        self.assertIn("task1", str(ctx.exception))
    
    def test_node_with_excludes_raises_error(self):
        """Node with 'excludes' field raises LoadError."""
        fragment = {
            "_source": "test.yaml",
            "version": 2,
            "nodes": {
                "task1": {
                    "title": "Task 1",
                    "excludes": ["weekends"],  # Forbidden!
                },
            },
        }
        
        with self.assertRaises(LoadError) as ctx:
            merge_fragments([fragment])
        
        self.assertIn("excludes", str(ctx.exception))
        self.assertIn("task1", str(ctx.exception))
    
    def test_error_includes_file_path(self):
        """Error message includes file path."""
        fragment = {
            "_source": "/path/to/plan.yaml",
            "version": 2,
            "nodes": {
                "task1": {
                    "title": "Task 1",
                    "start": "2024-03-01",
                },
            },
        }
        
        with self.assertRaises(LoadError) as ctx:
            merge_fragments([fragment])
        
        self.assertEqual(ctx.exception.file_path, "/path/to/plan.yaml")
    
    def test_error_includes_block_name(self):
        """Error message includes block name with path."""
        fragment = {
            "_source": "test.yaml",
            "version": 2,
            "nodes": {
                "my_task": {
                    "title": "My Task",
                    "duration": "3d",
                },
            },
        }
        
        with self.assertRaises(LoadError) as ctx:
            merge_fragments([fragment])
        
        self.assertEqual(ctx.exception.block_name, "nodes.my_task.duration")
    
    def test_multiple_forbidden_fields_reports_first(self):
        """Multiple forbidden fields - first one is reported."""
        fragment = {
            "_source": "test.yaml",
            "version": 2,
            "nodes": {
                "task1": {
                    "title": "Task 1",
                    "start": "2024-03-01",
                    "duration": "5d",
                    "finish": "2024-03-10",
                },
            },
        }
        
        with self.assertRaises(LoadError) as ctx:
            merge_fragments([fragment])
        
        # At least one forbidden field is reported
        error_msg = str(ctx.exception)
        self.assertTrue(
            "start" in error_msg or "duration" in error_msg or "finish" in error_msg
        )
    
    def test_valid_node_without_forbidden_fields(self):
        """Node without forbidden fields is valid."""
        fragment = {
            "_source": "test.yaml",
            "version": 2,
            "nodes": {
                "task1": {
                    "title": "Task 1",
                    "kind": "task",
                    "status": "in_progress",
                    "parent": "root",
                    "after": ["task0"],
                    "effort": 5,
                },
            },
        }
        
        result = merge_fragments([fragment])
        
        self.assertEqual(len(result.nodes), 1)
        self.assertEqual(result.nodes["task1"].title, "Task 1")
    
    def test_schedule_nodes_can_have_calendar_fields(self):
        """schedule.nodes CAN have start/finish/duration (not forbidden there)."""
        fragment = {
            "_source": "test.yaml",
            "version": 2,
            "nodes": {
                "task1": {"title": "Task 1"},
            },
            "schedule": {
                "nodes": {
                    "task1": {
                        "start": "2024-03-01",
                        "duration": "5d",
                        "finish": "2024-03-08",
                    },
                },
            },
        }
        
        result = merge_fragments([fragment])
        
        self.assertEqual(result.schedule.nodes["task1"].start, "2024-03-01")
        self.assertEqual(result.schedule.nodes["task1"].duration, "5d")
        self.assertEqual(result.schedule.nodes["task1"].finish, "2024-03-08")


class TestLoadPlanSetForbiddenFields(unittest.TestCase):
    """Integration tests for forbidden fields via load_plan_set."""
    
    def setUp(self):
        """Create a temporary directory for test files."""
        self.temp_dir = tempfile.mkdtemp()
    
    def _write_yaml(self, filename: str, content: str) -> str:
        """Write YAML content to a temp file and return path."""
        path = Path(self.temp_dir) / filename
        path.write_text(content, encoding="utf-8")
        return str(path)
    
    def test_load_file_with_forbidden_field_raises_error(self):
        """Loading file with forbidden node field raises LoadError."""
        yaml_content = """
version: 2
nodes:
  task1:
    title: Task 1
    start: "2024-03-01"
"""
        path = self._write_yaml("invalid.yaml", yaml_content)
        
        with self.assertRaises(LoadError) as ctx:
            load_plan_set([path])
        
        self.assertIn("start", str(ctx.exception))
        self.assertIn("task1", str(ctx.exception))
        self.assertIn(path, str(ctx.exception))
    
    def test_load_valid_v2_plan(self):
        """Loading valid v2 plan with schedule.nodes works."""
        yaml_content = """
version: 2
nodes:
  task1:
    title: Task 1
    effort: 5
schedule:
  nodes:
    task1:
      start: "2024-03-01"
      duration: "5d"
"""
        path = self._write_yaml("valid.yaml", yaml_content)
        
        result = load_plan_set([path])
        
        self.assertEqual(result.nodes["task1"].title, "Task 1")
        self.assertEqual(result.nodes["task1"].effort, 5)
        self.assertEqual(result.schedule.nodes["task1"].start, "2024-03-01")
        self.assertEqual(result.schedule.nodes["task1"].duration, "5d")
