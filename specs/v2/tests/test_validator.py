"""
Tests for the validator module.

Tests cover:
- 2.1: Node SHALL contain required field `title`
- 2.4: Node SHALL NOT contain fields `start`, `finish`, `duration`, `excludes`
- 2.5: Effort SHALL be a non-negative number (>= 0)
- 5.2: Validator SHALL check: merge-conflicts, nodes, statuses, schedule, views, effort
- 5.3: Structured errors with file source, expected format, actual value
"""

import unittest

from specs.v2.tools.models import MergedPlan, Node, Meta, Status
from specs.v2.tools.validator import (
    FORBIDDEN_NODE_FIELDS,
    Severity,
    ValidationError,
    ValidationResult,
    format_error,
    validate,
    validate_node_dict,
)


class TestValidationError(unittest.TestCase):
    """Tests for ValidationError dataclass."""
    
    def test_error_with_all_fields(self):
        """ValidationError with all fields."""
        error = ValidationError(
            message="Test error",
            path="nodes.task1.title",
            file_source="test.yaml",
            severity=Severity.ERROR,
        )
        
        self.assertEqual(error.message, "Test error")
        self.assertEqual(error.path, "nodes.task1.title")
        self.assertEqual(error.file_source, "test.yaml")
        self.assertEqual(error.severity, Severity.ERROR)
    
    def test_error_with_message_only(self):
        """ValidationError with message only."""
        error = ValidationError(message="Simple error")
        
        self.assertEqual(error.message, "Simple error")
        self.assertIsNone(error.path)
        self.assertIsNone(error.file_source)
        self.assertEqual(error.severity, Severity.ERROR)
    
    def test_error_str_format(self):
        """ValidationError string format includes all parts."""
        error = ValidationError(
            message="Missing title",
            path="nodes.task1.title",
            file_source="nodes.yaml",
            severity=Severity.ERROR,
        )
        
        error_str = str(error)
        self.assertIn("[error]", error_str)
        self.assertIn("nodes.yaml", error_str)
        self.assertIn("Missing title", error_str)
        self.assertIn("nodes.task1.title", error_str)
    
    def test_warning_severity(self):
        """ValidationError with warning severity."""
        error = ValidationError(
            message="Potential issue",
            severity=Severity.WARNING,
        )
        
        self.assertEqual(error.severity, Severity.WARNING)
        self.assertIn("[warning]", str(error))
    
    def test_error_with_expected_and_actual(self):
        """ValidationError with expected and actual fields (Requirement 5.3)."""
        error = ValidationError(
            message="Invalid effort value",
            path="nodes.task1.effort",
            file_source="nodes.yaml",
            severity=Severity.ERROR,
            expected="number >= 0",
            actual="-5",
        )
        
        self.assertEqual(error.expected, "number >= 0")
        self.assertEqual(error.actual, "-5")
    
    def test_error_with_phase_and_line(self):
        """ValidationError with phase and line number."""
        error = ValidationError(
            message="Test error",
            file_source="test.yaml",
            phase="loading",
            line=15,
        )
        
        self.assertEqual(error.phase, "loading")
        self.assertEqual(error.line, 15)
    
    def test_error_default_phase(self):
        """ValidationError has default phase 'validation'."""
        error = ValidationError(message="Test error")
        
        self.assertEqual(error.phase, "validation")


class TestFormatError(unittest.TestCase):
    """Tests for format_error function (Requirement 5.3)."""
    
    def test_format_error_basic(self):
        """format_error with basic error."""
        error = ValidationError(
            message="Missing title",
            severity=Severity.ERROR,
        )
        
        formatted = format_error(error)
        
        self.assertIn("[error]", formatted)
        self.assertIn("[validation]", formatted)
        self.assertIn("Missing title", formatted)
    
    def test_format_error_with_file_source(self):
        """format_error includes file source."""
        error = ValidationError(
            message="Missing title",
            file_source="nodes.yaml",
            severity=Severity.ERROR,
        )
        
        formatted = format_error(error)
        
        self.assertIn("[nodes.yaml]", formatted)
    
    def test_format_error_with_file_and_line(self):
        """format_error includes file:line format."""
        error = ValidationError(
            message="Missing title",
            file_source="nodes.yaml",
            line=15,
            severity=Severity.ERROR,
        )
        
        formatted = format_error(error)
        
        self.assertIn("[nodes.yaml:15]", formatted)
    
    def test_format_error_with_path(self):
        """format_error includes path on separate line."""
        error = ValidationError(
            message="Missing title",
            path="nodes.task1.title",
            severity=Severity.ERROR,
        )
        
        formatted = format_error(error)
        
        self.assertIn("path: nodes.task1.title", formatted)
        # Path should be on a new line with indentation
        self.assertIn("\n  path:", formatted)
    
    def test_format_error_with_expected(self):
        """format_error includes expected format."""
        error = ValidationError(
            message="Invalid effort",
            expected="number >= 0",
            severity=Severity.ERROR,
        )
        
        formatted = format_error(error)
        
        self.assertIn("expected: number >= 0", formatted)
    
    def test_format_error_with_actual(self):
        """format_error includes actual value."""
        error = ValidationError(
            message="Invalid effort",
            actual="-5",
            severity=Severity.ERROR,
        )
        
        formatted = format_error(error)
        
        self.assertIn("value: -5", formatted)
    
    def test_format_error_full_format(self):
        """format_error with all fields matches design spec format."""
        error = ValidationError(
            message="Invalid effort value",
            path="nodes.task1.effort",
            file_source="nodes.plan.yaml",
            line=15,
            severity=Severity.ERROR,
            expected="number >= 0",
            actual="-5",
            phase="validation",
        )
        
        formatted = format_error(error)
        
        # Check header line format: [severity] [phase] [file:line] message
        lines = formatted.split("\n")
        header = lines[0]
        self.assertIn("[error]", header)
        self.assertIn("[validation]", header)
        self.assertIn("[nodes.plan.yaml:15]", header)
        self.assertIn("Invalid effort value", header)
        
        # Check detail lines
        self.assertIn("  path: nodes.task1.effort", formatted)
        self.assertIn("  value: -5", formatted)
        self.assertIn("  expected: number >= 0", formatted)
    
    def test_format_error_warning_severity(self):
        """format_error with warning severity."""
        error = ValidationError(
            message="Potential issue",
            severity=Severity.WARNING,
        )
        
        formatted = format_error(error)
        
        self.assertIn("[warning]", formatted)
    
    def test_format_error_custom_phase(self):
        """format_error with custom phase."""
        error = ValidationError(
            message="Merge conflict",
            phase="merge",
            severity=Severity.ERROR,
        )
        
        formatted = format_error(error)
        
        self.assertIn("[merge]", formatted)


class TestValidationResult(unittest.TestCase):
    """Tests for ValidationResult dataclass."""
    
    def test_empty_result_is_valid(self):
        """Empty ValidationResult is valid."""
        result = ValidationResult()
        
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.errors), 0)
        self.assertEqual(len(result.warnings), 0)
    
    def test_result_with_errors_is_invalid(self):
        """ValidationResult with errors is invalid."""
        result = ValidationResult()
        result.add_error("Test error")
        
        self.assertFalse(result.is_valid)
        self.assertEqual(len(result.errors), 1)
    
    def test_result_with_warnings_only_is_valid(self):
        """ValidationResult with only warnings is still valid."""
        result = ValidationResult()
        result.add_warning("Test warning")
        
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.warnings), 1)
        self.assertEqual(len(result.errors), 0)
    
    def test_add_error_with_all_params(self):
        """add_error with all parameters."""
        result = ValidationResult()
        result.add_error(
            message="Error message",
            path="nodes.task1",
            file_source="test.yaml",
        )
        
        self.assertEqual(len(result.errors), 1)
        error = result.errors[0]
        self.assertEqual(error.message, "Error message")
        self.assertEqual(error.path, "nodes.task1")
        self.assertEqual(error.file_source, "test.yaml")
        self.assertEqual(error.severity, Severity.ERROR)
    
    def test_add_warning_with_all_params(self):
        """add_warning with all parameters."""
        result = ValidationResult()
        result.add_warning(
            message="Warning message",
            path="nodes.task1",
            file_source="test.yaml",
        )
        
        self.assertEqual(len(result.warnings), 1)
        warning = result.warnings[0]
        self.assertEqual(warning.message, "Warning message")
        self.assertEqual(warning.severity, Severity.WARNING)
    
    def test_add_error_with_expected_and_actual(self):
        """add_error with expected and actual parameters (Requirement 5.3)."""
        result = ValidationResult()
        result.add_error(
            message="Invalid effort",
            path="nodes.task1.effort",
            file_source="test.yaml",
            expected="number >= 0",
            actual="-5",
        )
        
        self.assertEqual(len(result.errors), 1)
        error = result.errors[0]
        self.assertEqual(error.expected, "number >= 0")
        self.assertEqual(error.actual, "-5")
    
    def test_add_error_with_phase_and_line(self):
        """add_error with phase and line parameters."""
        result = ValidationResult()
        result.add_error(
            message="Error message",
            file_source="test.yaml",
            phase="loading",
            line=42,
        )
        
        self.assertEqual(len(result.errors), 1)
        error = result.errors[0]
        self.assertEqual(error.phase, "loading")
        self.assertEqual(error.line, 42)
    
    def test_add_warning_with_expected_and_actual(self):
        """add_warning with expected and actual parameters."""
        result = ValidationResult()
        result.add_warning(
            message="Potential issue",
            expected="valid format",
            actual="invalid format",
        )
        
        self.assertEqual(len(result.warnings), 1)
        warning = result.warnings[0]
        self.assertEqual(warning.expected, "valid format")
        self.assertEqual(warning.actual, "invalid format")


class TestForbiddenNodeFields(unittest.TestCase):
    """Tests for FORBIDDEN_NODE_FIELDS constant."""
    
    def test_forbidden_fields_contains_required(self):
        """All forbidden fields are in FORBIDDEN_NODE_FIELDS."""
        required = {"start", "finish", "duration", "excludes"}
        self.assertEqual(FORBIDDEN_NODE_FIELDS, required)
    
    def test_forbidden_fields_is_frozenset(self):
        """FORBIDDEN_NODE_FIELDS is immutable."""
        self.assertIsInstance(FORBIDDEN_NODE_FIELDS, frozenset)


class TestValidateEmptyPlan(unittest.TestCase):
    """Tests for validating empty plans."""
    
    def test_empty_plan_is_valid(self):
        """Empty plan (no nodes) is valid."""
        plan = MergedPlan()
        
        result = validate(plan)
        
        self.assertTrue(result.is_valid)
    
    def test_plan_without_schedule_is_valid(self):
        """Plan without schedule block is valid (Requirement 3.2)."""
        plan = MergedPlan(
            nodes={"task1": Node(title="Task 1")},
        )
        
        result = validate(plan)
        
        self.assertTrue(result.is_valid)


class TestValidateNodeTitle(unittest.TestCase):
    """Tests for node title validation (Requirement 2.1)."""
    
    def test_node_with_title_is_valid(self):
        """Node with title is valid."""
        plan = MergedPlan(
            nodes={"task1": Node(title="Task 1")},
        )
        
        result = validate(plan)
        
        self.assertTrue(result.is_valid)
    
    def test_node_without_title_is_invalid(self):
        """Node without title is invalid."""
        plan = MergedPlan(
            nodes={"task1": Node(title="")},
        )
        
        result = validate(plan)
        
        self.assertFalse(result.is_valid)
        self.assertEqual(len(result.errors), 1)
        self.assertIn("title", result.errors[0].message)
        self.assertIn("task1", result.errors[0].message)
    
    def test_multiple_nodes_without_title(self):
        """Multiple nodes without title generate multiple errors."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title=""),
                "task2": Node(title="Valid Title"),
                "task3": Node(title=""),
            },
        )
        
        result = validate(plan)
        
        self.assertFalse(result.is_valid)
        self.assertEqual(len(result.errors), 2)
    
    def test_error_includes_file_source(self):
        """Error includes file source when available."""
        plan = MergedPlan(
            nodes={"task1": Node(title="")},
            sources={"node:task1": "nodes.yaml"},
        )
        
        result = validate(plan)
        
        self.assertFalse(result.is_valid)
        self.assertEqual(result.errors[0].file_source, "nodes.yaml")
    
    def test_error_includes_path(self):
        """Error includes path to the element."""
        plan = MergedPlan(
            nodes={"my_task": Node(title="")},
        )
        
        result = validate(plan)
        
        self.assertFalse(result.is_valid)
        self.assertEqual(result.errors[0].path, "nodes.my_task.title")


class TestValidateEffort(unittest.TestCase):
    """Tests for effort validation (Requirement 2.5)."""
    
    def test_node_with_positive_effort_is_valid(self):
        """Node with positive effort is valid."""
        plan = MergedPlan(
            nodes={"task1": Node(title="Task 1", effort=5.0)},
        )
        
        result = validate(plan)
        
        self.assertTrue(result.is_valid)
    
    def test_node_with_zero_effort_is_valid(self):
        """Node with zero effort is valid (>= 0)."""
        plan = MergedPlan(
            nodes={"task1": Node(title="Task 1", effort=0)},
        )
        
        result = validate(plan)
        
        self.assertTrue(result.is_valid)
    
    def test_node_with_integer_effort_is_valid(self):
        """Node with integer effort is valid."""
        plan = MergedPlan(
            nodes={"task1": Node(title="Task 1", effort=10)},
        )
        
        result = validate(plan)
        
        self.assertTrue(result.is_valid)
    
    def test_node_with_float_effort_is_valid(self):
        """Node with float effort is valid."""
        plan = MergedPlan(
            nodes={"task1": Node(title="Task 1", effort=3.5)},
        )
        
        result = validate(plan)
        
        self.assertTrue(result.is_valid)
    
    def test_node_with_negative_effort_is_invalid(self):
        """Node with negative effort is invalid."""
        plan = MergedPlan(
            nodes={"task1": Node(title="Task 1", effort=-5)},
        )
        
        result = validate(plan)
        
        self.assertFalse(result.is_valid)
        self.assertEqual(len(result.errors), 1)
        self.assertIn("effort", result.errors[0].message.lower())
        self.assertIn("-5", result.errors[0].message)
        self.assertIn(">= 0", result.errors[0].message)
    
    def test_node_without_effort_is_valid(self):
        """Node without effort (None) is valid."""
        plan = MergedPlan(
            nodes={"task1": Node(title="Task 1", effort=None)},
        )
        
        result = validate(plan)
        
        self.assertTrue(result.is_valid)
    
    def test_effort_error_includes_path(self):
        """Effort error includes path to the element."""
        plan = MergedPlan(
            nodes={"my_task": Node(title="Task", effort=-1)},
        )
        
        result = validate(plan)
        
        self.assertFalse(result.is_valid)
        self.assertEqual(result.errors[0].path, "nodes.my_task.effort")
    
    def test_effort_error_includes_file_source(self):
        """Effort error includes file source when available."""
        plan = MergedPlan(
            nodes={"task1": Node(title="Task", effort=-1)},
            sources={"node:task1": "tasks.yaml"},
        )
        
        result = validate(plan)
        
        self.assertFalse(result.is_valid)
        self.assertEqual(result.errors[0].file_source, "tasks.yaml")
    
    def test_effort_error_includes_expected_and_actual(self):
        """Effort error includes expected format and actual value (Requirement 5.3)."""
        plan = MergedPlan(
            nodes={"task1": Node(title="Task", effort=-5)},
        )
        
        result = validate(plan)
        
        self.assertFalse(result.is_valid)
        error = result.errors[0]
        self.assertEqual(error.expected, "number >= 0")
        self.assertEqual(error.actual, "-5")


class TestStructuredErrorMessages(unittest.TestCase):
    """Tests for structured error messages (Requirements 5.2, 5.3)."""
    
    def test_title_error_includes_expected_and_actual(self):
        """Missing title error includes expected and actual."""
        plan = MergedPlan(
            nodes={"task1": Node(title="")},
        )
        
        result = validate(plan)
        
        self.assertFalse(result.is_valid)
        error = result.errors[0]
        self.assertEqual(error.expected, "non-empty string")
        self.assertIn("''", error.actual)  # Empty string representation
    
    def test_parent_reference_error_includes_expected_and_actual(self):
        """Parent reference error includes expected and actual."""
        plan = MergedPlan(
            nodes={"task1": Node(title="Task", parent="nonexistent")},
        )
        
        result = validate(plan)
        
        self.assertFalse(result.is_valid)
        error = result.errors[0]
        self.assertEqual(error.expected, "existing node_id")
        self.assertEqual(error.actual, "nonexistent")
    
    def test_status_reference_error_includes_expected_and_actual(self):
        """Status reference error includes expected and actual."""
        plan = MergedPlan(
            nodes={"task1": Node(title="Task", status="unknown")},
            statuses={"done": Status(label="Done")},
        )
        
        result = validate(plan)
        
        self.assertFalse(result.is_valid)
        error = result.errors[0]
        self.assertEqual(error.expected, "existing status_id")
        self.assertEqual(error.actual, "unknown")
    
    def test_after_reference_error_includes_expected_and_actual(self):
        """After reference error includes expected and actual."""
        plan = MergedPlan(
            nodes={"task1": Node(title="Task", after=["missing"])},
        )
        
        result = validate(plan)
        
        self.assertFalse(result.is_valid)
        error = result.errors[0]
        self.assertEqual(error.expected, "existing node_id")
        self.assertEqual(error.actual, "missing")
    
    def test_formatted_error_matches_design_spec(self):
        """Formatted error matches design spec format."""
        plan = MergedPlan(
            nodes={"task1": Node(title="Task", effort=-5)},
            sources={"node:task1": "nodes.plan.yaml"},
        )
        
        result = validate(plan)
        
        self.assertFalse(result.is_valid)
        error = result.errors[0]
        formatted = format_error(error)
        
        # Check format: [severity] [phase] [file] message
        self.assertIn("[error]", formatted)
        self.assertIn("[validation]", formatted)
        self.assertIn("[nodes.plan.yaml]", formatted)
        self.assertIn("path: nodes.task1.effort", formatted)
        self.assertIn("value: -5", formatted)
        self.assertIn("expected: number >= 0", formatted)


class TestValidateNodeDictForbiddenFields(unittest.TestCase):
    """Tests for forbidden fields validation using validate_node_dict (Requirement 2.4)."""
    
    def test_node_with_start_is_invalid(self):
        """Node with 'start' field is invalid."""
        result = ValidationResult()
        node_data = {"title": "Task 1", "start": "2024-03-01"}
        
        validate_node_dict("task1", node_data, "test.yaml", result)
        
        self.assertFalse(result.is_valid)
        self.assertEqual(len(result.errors), 1)
        self.assertIn("start", result.errors[0].message)
        self.assertIn("forbidden", result.errors[0].message.lower())
    
    def test_node_with_finish_is_invalid(self):
        """Node with 'finish' field is invalid."""
        result = ValidationResult()
        node_data = {"title": "Task 1", "finish": "2024-03-10"}
        
        validate_node_dict("task1", node_data, "test.yaml", result)
        
        self.assertFalse(result.is_valid)
        self.assertIn("finish", result.errors[0].message)
    
    def test_node_with_duration_is_invalid(self):
        """Node with 'duration' field is invalid."""
        result = ValidationResult()
        node_data = {"title": "Task 1", "duration": "5d"}
        
        validate_node_dict("task1", node_data, "test.yaml", result)
        
        self.assertFalse(result.is_valid)
        self.assertIn("duration", result.errors[0].message)
    
    def test_node_with_excludes_is_invalid(self):
        """Node with 'excludes' field is invalid."""
        result = ValidationResult()
        node_data = {"title": "Task 1", "excludes": ["weekends"]}
        
        validate_node_dict("task1", node_data, "test.yaml", result)
        
        self.assertFalse(result.is_valid)
        self.assertIn("excludes", result.errors[0].message)
    
    def test_node_with_multiple_forbidden_fields(self):
        """Node with multiple forbidden fields generates multiple errors."""
        result = ValidationResult()
        node_data = {
            "title": "Task 1",
            "start": "2024-03-01",
            "finish": "2024-03-10",
            "duration": "5d",
        }
        
        validate_node_dict("task1", node_data, "test.yaml", result)
        
        self.assertFalse(result.is_valid)
        self.assertEqual(len(result.errors), 3)
    
    def test_forbidden_field_error_suggests_schedule(self):
        """Error message suggests using schedule.nodes instead."""
        result = ValidationResult()
        node_data = {"title": "Task 1", "start": "2024-03-01"}
        
        validate_node_dict("task1", node_data, "test.yaml", result)
        
        self.assertIn("schedule.nodes", result.errors[0].message)
    
    def test_forbidden_field_error_includes_path(self):
        """Forbidden field error includes path."""
        result = ValidationResult()
        node_data = {"title": "Task 1", "start": "2024-03-01"}
        
        validate_node_dict("task1", node_data, "test.yaml", result)
        
        self.assertEqual(result.errors[0].path, "nodes.task1.start")


class TestValidateNodeDictTitle(unittest.TestCase):
    """Tests for title validation using validate_node_dict."""
    
    def test_missing_title_is_invalid(self):
        """Node without title field is invalid."""
        result = ValidationResult()
        node_data = {"kind": "task"}
        
        validate_node_dict("task1", node_data, "test.yaml", result)
        
        self.assertFalse(result.is_valid)
        self.assertIn("title", result.errors[0].message)
    
    def test_empty_title_is_invalid(self):
        """Node with empty title is invalid."""
        result = ValidationResult()
        node_data = {"title": ""}
        
        validate_node_dict("task1", node_data, "test.yaml", result)
        
        self.assertFalse(result.is_valid)
        self.assertIn("title", result.errors[0].message)


class TestValidateNodeDictEffort(unittest.TestCase):
    """Tests for effort validation using validate_node_dict."""
    
    def test_negative_effort_is_invalid(self):
        """Node with negative effort is invalid."""
        result = ValidationResult()
        node_data = {"title": "Task 1", "effort": -5}
        
        validate_node_dict("task1", node_data, "test.yaml", result)
        
        self.assertFalse(result.is_valid)
        self.assertIn("effort", result.errors[0].message.lower())
    
    def test_string_effort_is_invalid(self):
        """Node with string effort is invalid."""
        result = ValidationResult()
        node_data = {"title": "Task 1", "effort": "5d"}
        
        validate_node_dict("task1", node_data, "test.yaml", result)
        
        self.assertFalse(result.is_valid)
        self.assertIn("effort", result.errors[0].message.lower())
        self.assertIn("number", result.errors[0].message.lower())
    
    def test_valid_effort_is_accepted(self):
        """Node with valid effort is accepted."""
        result = ValidationResult()
        node_data = {"title": "Task 1", "effort": 5.5}
        
        validate_node_dict("task1", node_data, "test.yaml", result)
        
        self.assertTrue(result.is_valid)


class TestValidateComplexPlan(unittest.TestCase):
    """Integration tests for validating complex plans."""
    
    def test_valid_plan_with_multiple_nodes(self):
        """Valid plan with multiple nodes passes validation."""
        plan = MergedPlan(
            nodes={
                "root": Node(title="Project", kind="summary"),
                "phase1": Node(title="Phase 1", parent="root", effort=10),
                "task1": Node(title="Task 1", parent="phase1", effort=5),
                "task2": Node(title="Task 2", parent="phase1", after=["task1"], effort=5),
            },
        )
        
        result = validate(plan)
        
        self.assertTrue(result.is_valid)
    
    def test_plan_with_mixed_errors(self):
        """Plan with multiple types of errors."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="", effort=-5),  # Missing title + negative effort
                "task2": Node(title="Valid Task"),
            },
        )
        
        result = validate(plan)
        
        self.assertFalse(result.is_valid)
        self.assertEqual(len(result.errors), 2)  # title + effort errors
    
    def test_plan_with_effort_zero(self):
        """Plan with zero effort is valid."""
        plan = MergedPlan(
            nodes={
                "milestone": Node(title="Milestone", milestone=True, effort=0),
            },
        )
        
        result = validate(plan)
        
        self.assertTrue(result.is_valid)


if __name__ == "__main__":
    unittest.main()


class TestValidateNodeReferences(unittest.TestCase):
    """Tests for node reference integrity validation (Requirements 2.1, 2.2)."""
    
    def test_valid_parent_reference(self):
        """Node with valid parent reference is valid."""
        plan = MergedPlan(
            nodes={
                "root": Node(title="Root"),
                "child": Node(title="Child", parent="root"),
            },
        )
        
        result = validate(plan)
        
        self.assertTrue(result.is_valid)
    
    def test_invalid_parent_reference(self):
        """Node with non-existent parent reference is invalid."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1", parent="nonexistent"),
            },
        )
        
        result = validate(plan)
        
        self.assertFalse(result.is_valid)
        self.assertEqual(len(result.errors), 1)
        self.assertIn("parent", result.errors[0].message)
        self.assertIn("nonexistent", result.errors[0].message)
        self.assertEqual(result.errors[0].path, "nodes.task1.parent")
    
    def test_valid_after_references(self):
        """Node with valid after references is valid."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1"),
                "task2": Node(title="Task 2"),
                "task3": Node(title="Task 3", after=["task1", "task2"]),
            },
        )
        
        result = validate(plan)
        
        self.assertTrue(result.is_valid)
    
    def test_invalid_after_reference(self):
        """Node with non-existent after reference is invalid."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1", after=["nonexistent"]),
            },
        )
        
        result = validate(plan)
        
        self.assertFalse(result.is_valid)
        self.assertEqual(len(result.errors), 1)
        self.assertIn("after", result.errors[0].message)
        self.assertIn("nonexistent", result.errors[0].message)
        self.assertEqual(result.errors[0].path, "nodes.task1.after")
    
    def test_multiple_invalid_after_references(self):
        """Node with multiple non-existent after references generates multiple errors."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1", after=["missing1", "missing2"]),
            },
        )
        
        result = validate(plan)
        
        self.assertFalse(result.is_valid)
        self.assertEqual(len(result.errors), 2)
    
    def test_valid_status_reference(self):
        """Node with valid status reference is valid."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1", status="in_progress"),
            },
            statuses={
                "in_progress": Status(label="In Progress"),
            },
        )
        
        result = validate(plan)
        
        self.assertTrue(result.is_valid)
    
    def test_invalid_status_reference(self):
        """Node with non-existent status reference is invalid."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1", status="nonexistent"),
            },
            statuses={
                "done": Status(label="Done"),
            },
        )
        
        result = validate(plan)
        
        self.assertFalse(result.is_valid)
        self.assertEqual(len(result.errors), 1)
        self.assertIn("status", result.errors[0].message)
        self.assertIn("nonexistent", result.errors[0].message)
        self.assertEqual(result.errors[0].path, "nodes.task1.status")
    
    def test_reference_error_includes_file_source(self):
        """Reference error includes file source when available."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1", parent="missing"),
            },
            sources={"node:task1": "nodes.yaml"},
        )
        
        result = validate(plan)
        
        self.assertFalse(result.is_valid)
        self.assertEqual(result.errors[0].file_source, "nodes.yaml")
    
    def test_node_without_references_is_valid(self):
        """Node without any references is valid."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1"),
            },
        )
        
        result = validate(plan)
        
        self.assertTrue(result.is_valid)
    
    def test_empty_after_list_is_valid(self):
        """Node with empty after list is valid."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1", after=[]),
            },
        )
        
        result = validate(plan)
        
        self.assertTrue(result.is_valid)


class TestDetectParentCycles(unittest.TestCase):
    """Tests for parent cycle detection (Requirement 2.2)."""
    
    def test_no_parent_cycle(self):
        """Plan without parent cycles is valid."""
        plan = MergedPlan(
            nodes={
                "root": Node(title="Root"),
                "child1": Node(title="Child 1", parent="root"),
                "child2": Node(title="Child 2", parent="child1"),
            },
        )
        
        result = validate(plan)
        
        self.assertTrue(result.is_valid)
    
    def test_self_referencing_parent(self):
        """Node referencing itself as parent is invalid."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1", parent="task1"),
            },
        )
        
        result = validate(plan)
        
        self.assertFalse(result.is_valid)
        # Should have error for cycle
        cycle_errors = [e for e in result.errors if "Cyclic parent" in e.message]
        self.assertEqual(len(cycle_errors), 1)
        self.assertIn("task1", cycle_errors[0].message)
    
    def test_two_node_parent_cycle(self):
        """Two nodes forming a parent cycle is invalid."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1", parent="task2"),
                "task2": Node(title="Task 2", parent="task1"),
            },
        )
        
        result = validate(plan)
        
        self.assertFalse(result.is_valid)
        cycle_errors = [e for e in result.errors if "Cyclic parent" in e.message]
        self.assertGreaterEqual(len(cycle_errors), 1)
    
    def test_three_node_parent_cycle(self):
        """Three nodes forming a parent cycle is invalid."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1", parent="task3"),
                "task2": Node(title="Task 2", parent="task1"),
                "task3": Node(title="Task 3", parent="task2"),
            },
        )
        
        result = validate(plan)
        
        self.assertFalse(result.is_valid)
        cycle_errors = [e for e in result.errors if "Cyclic parent" in e.message]
        self.assertGreaterEqual(len(cycle_errors), 1)
        # Check that cycle path is in the error message
        error_msg = cycle_errors[0].message
        self.assertIn("->", error_msg)
    
    def test_parent_cycle_error_includes_path(self):
        """Parent cycle error includes path."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1", parent="task2"),
                "task2": Node(title="Task 2", parent="task1"),
            },
        )
        
        result = validate(plan)
        
        self.assertFalse(result.is_valid)
        cycle_errors = [e for e in result.errors if "Cyclic parent" in e.message]
        self.assertTrue(any("parent" in e.path for e in cycle_errors))
    
    def test_parent_cycle_with_valid_nodes(self):
        """Plan with both valid nodes and a cycle reports only the cycle."""
        plan = MergedPlan(
            nodes={
                "root": Node(title="Root"),
                "valid_child": Node(title="Valid Child", parent="root"),
                "cycle1": Node(title="Cycle 1", parent="cycle2"),
                "cycle2": Node(title="Cycle 2", parent="cycle1"),
            },
        )
        
        result = validate(plan)
        
        self.assertFalse(result.is_valid)
        cycle_errors = [e for e in result.errors if "Cyclic parent" in e.message]
        self.assertGreaterEqual(len(cycle_errors), 1)


class TestDetectAfterCycles(unittest.TestCase):
    """Tests for after dependency cycle detection (Requirement 2.2)."""
    
    def test_no_after_cycle(self):
        """Plan without after cycles is valid."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1"),
                "task2": Node(title="Task 2", after=["task1"]),
                "task3": Node(title="Task 3", after=["task2"]),
            },
        )
        
        result = validate(plan)
        
        self.assertTrue(result.is_valid)
    
    def test_self_referencing_after(self):
        """Node referencing itself in after is invalid."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1", after=["task1"]),
            },
        )
        
        result = validate(plan)
        
        self.assertFalse(result.is_valid)
        cycle_errors = [e for e in result.errors if "Cyclic after" in e.message]
        self.assertEqual(len(cycle_errors), 1)
        self.assertIn("task1", cycle_errors[0].message)
    
    def test_two_node_after_cycle(self):
        """Two nodes forming an after cycle is invalid."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1", after=["task2"]),
                "task2": Node(title="Task 2", after=["task1"]),
            },
        )
        
        result = validate(plan)
        
        self.assertFalse(result.is_valid)
        cycle_errors = [e for e in result.errors if "Cyclic after" in e.message]
        self.assertGreaterEqual(len(cycle_errors), 1)
    
    def test_three_node_after_cycle(self):
        """Three nodes forming an after cycle is invalid."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1", after=["task3"]),
                "task2": Node(title="Task 2", after=["task1"]),
                "task3": Node(title="Task 3", after=["task2"]),
            },
        )
        
        result = validate(plan)
        
        self.assertFalse(result.is_valid)
        cycle_errors = [e for e in result.errors if "Cyclic after" in e.message]
        self.assertGreaterEqual(len(cycle_errors), 1)
        # Check that cycle path is in the error message
        error_msg = cycle_errors[0].message
        self.assertIn("->", error_msg)
    
    def test_after_cycle_error_includes_path(self):
        """After cycle error includes path."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1", after=["task2"]),
                "task2": Node(title="Task 2", after=["task1"]),
            },
        )
        
        result = validate(plan)
        
        self.assertFalse(result.is_valid)
        cycle_errors = [e for e in result.errors if "Cyclic after" in e.message]
        self.assertTrue(any("after" in e.path for e in cycle_errors))
    
    def test_multiple_after_with_one_cycle(self):
        """Node with multiple after dependencies where one forms a cycle."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1"),
                "task2": Node(title="Task 2", after=["task1", "task3"]),
                "task3": Node(title="Task 3", after=["task2"]),
            },
        )
        
        result = validate(plan)
        
        self.assertFalse(result.is_valid)
        cycle_errors = [e for e in result.errors if "Cyclic after" in e.message]
        self.assertGreaterEqual(len(cycle_errors), 1)
    
    def test_after_cycle_with_valid_nodes(self):
        """Plan with both valid nodes and an after cycle reports only the cycle."""
        plan = MergedPlan(
            nodes={
                "valid1": Node(title="Valid 1"),
                "valid2": Node(title="Valid 2", after=["valid1"]),
                "cycle1": Node(title="Cycle 1", after=["cycle2"]),
                "cycle2": Node(title="Cycle 2", after=["cycle1"]),
            },
        )
        
        result = validate(plan)
        
        self.assertFalse(result.is_valid)
        cycle_errors = [e for e in result.errors if "Cyclic after" in e.message]
        self.assertGreaterEqual(len(cycle_errors), 1)
    
    def test_diamond_dependency_is_valid(self):
        """Diamond dependency pattern (not a cycle) is valid."""
        plan = MergedPlan(
            nodes={
                "start": Node(title="Start"),
                "left": Node(title="Left", after=["start"]),
                "right": Node(title="Right", after=["start"]),
                "end": Node(title="End", after=["left", "right"]),
            },
        )
        
        result = validate(plan)
        
        self.assertTrue(result.is_valid)


class TestCombinedReferenceValidation(unittest.TestCase):
    """Integration tests for combined reference validation."""
    
    def test_valid_complex_plan(self):
        """Complex plan with valid references is valid."""
        plan = MergedPlan(
            nodes={
                "root": Node(title="Project", kind="summary", status="in_progress"),
                "phase1": Node(title="Phase 1", parent="root", status="done"),
                "task1": Node(title="Task 1", parent="phase1", effort=5),
                "task2": Node(title="Task 2", parent="phase1", after=["task1"], effort=3),
                "phase2": Node(title="Phase 2", parent="root", after=["phase1"]),
                "task3": Node(title="Task 3", parent="phase2", after=["task2"]),
            },
            statuses={
                "in_progress": Status(label="In Progress"),
                "done": Status(label="Done"),
            },
        )
        
        result = validate(plan)
        
        self.assertTrue(result.is_valid)
    
    def test_multiple_reference_errors(self):
        """Plan with multiple reference errors reports all of them."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1", parent="missing_parent", status="missing_status"),
                "task2": Node(title="Task 2", after=["missing_dep"]),
            },
        )
        
        result = validate(plan)
        
        self.assertFalse(result.is_valid)
        # Should have 3 errors: missing parent, missing status, missing after
        self.assertEqual(len(result.errors), 3)
    
    def test_both_parent_and_after_cycles(self):
        """Plan with both parent and after cycles reports both."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1", parent="task2"),
                "task2": Node(title="Task 2", parent="task1"),
                "task3": Node(title="Task 3", after=["task4"]),
                "task4": Node(title="Task 4", after=["task3"]),
            },
        )
        
        result = validate(plan)
        
        self.assertFalse(result.is_valid)
        parent_cycles = [e for e in result.errors if "Cyclic parent" in e.message]
        after_cycles = [e for e in result.errors if "Cyclic after" in e.message]
        self.assertGreaterEqual(len(parent_cycles), 1)
        self.assertGreaterEqual(len(after_cycles), 1)



class TestValidateScheduleReferences(unittest.TestCase):
    """Tests for schedule reference integrity validation (Requirements 3.7, 3.9)."""
    
    def test_plan_without_schedule_is_valid(self):
        """Plan without schedule block is valid (Requirement 3.2)."""
        plan = MergedPlan(
            nodes={"task1": Node(title="Task 1")},
            schedule=None,
        )
        
        result = validate(plan)
        
        self.assertTrue(result.is_valid)
    
    def test_valid_schedule_node_reference(self):
        """Schedule node referencing existing node is valid (Requirement 3.7)."""
        from specs.v2.tools.models import Schedule, ScheduleNode
        
        plan = MergedPlan(
            nodes={"task1": Node(title="Task 1")},
            schedule=Schedule(
                nodes={"task1": ScheduleNode(start="2024-03-01", duration="5d")},
            ),
        )
        
        result = validate(plan)
        
        self.assertTrue(result.is_valid)
    
    def test_invalid_schedule_node_reference(self):
        """Schedule node referencing non-existent node is invalid (Requirement 3.7)."""
        from specs.v2.tools.models import Schedule, ScheduleNode
        
        plan = MergedPlan(
            nodes={"task1": Node(title="Task 1")},
            schedule=Schedule(
                nodes={"nonexistent": ScheduleNode(start="2024-03-01")},
            ),
        )
        
        result = validate(plan)
        
        self.assertFalse(result.is_valid)
        self.assertEqual(len(result.errors), 1)
        self.assertIn("nonexistent", result.errors[0].message)
        self.assertIn("non-existent node", result.errors[0].message)
        self.assertEqual(result.errors[0].path, "schedule.nodes.nonexistent")
    
    def test_multiple_invalid_schedule_node_references(self):
        """Multiple schedule nodes referencing non-existent nodes generate multiple errors."""
        from specs.v2.tools.models import Schedule, ScheduleNode
        
        plan = MergedPlan(
            nodes={"task1": Node(title="Task 1")},
            schedule=Schedule(
                nodes={
                    "missing1": ScheduleNode(start="2024-03-01"),
                    "missing2": ScheduleNode(start="2024-03-05"),
                },
            ),
        )
        
        result = validate(plan)
        
        self.assertFalse(result.is_valid)
        self.assertEqual(len(result.errors), 2)
    
    def test_valid_calendar_reference(self):
        """Schedule node with valid calendar reference is valid (Requirement 3.9)."""
        from specs.v2.tools.models import Schedule, ScheduleNode, Calendar
        
        plan = MergedPlan(
            nodes={"task1": Node(title="Task 1")},
            schedule=Schedule(
                calendars={"work": Calendar(excludes=["weekends"])},
                nodes={"task1": ScheduleNode(start="2024-03-01", calendar="work")},
            ),
        )
        
        result = validate(plan)
        
        self.assertTrue(result.is_valid)
    
    def test_invalid_calendar_reference(self):
        """Schedule node with non-existent calendar reference is invalid (Requirement 3.9)."""
        from specs.v2.tools.models import Schedule, ScheduleNode, Calendar
        
        plan = MergedPlan(
            nodes={"task1": Node(title="Task 1")},
            schedule=Schedule(
                calendars={"work": Calendar(excludes=["weekends"])},
                nodes={"task1": ScheduleNode(start="2024-03-01", calendar="nonexistent")},
            ),
        )
        
        result = validate(plan)
        
        self.assertFalse(result.is_valid)
        self.assertEqual(len(result.errors), 1)
        self.assertIn("calendar", result.errors[0].message)
        self.assertIn("nonexistent", result.errors[0].message)
        self.assertEqual(result.errors[0].path, "schedule.nodes.task1.calendar")
    
    def test_schedule_node_without_calendar_is_valid(self):
        """Schedule node without explicit calendar reference is valid (uses default)."""
        from specs.v2.tools.models import Schedule, ScheduleNode, Calendar
        
        plan = MergedPlan(
            nodes={"task1": Node(title="Task 1")},
            schedule=Schedule(
                calendars={"default": Calendar(excludes=["weekends"])},
                default_calendar="default",
                nodes={"task1": ScheduleNode(start="2024-03-01")},
            ),
        )
        
        result = validate(plan)
        
        self.assertTrue(result.is_valid)
    
    def test_valid_default_calendar_reference(self):
        """Schedule with valid default_calendar reference is valid."""
        from specs.v2.tools.models import Schedule, Calendar
        
        plan = MergedPlan(
            nodes={"task1": Node(title="Task 1")},
            schedule=Schedule(
                calendars={"work": Calendar(excludes=["weekends"])},
                default_calendar="work",
            ),
        )
        
        result = validate(plan)
        
        self.assertTrue(result.is_valid)
    
    def test_invalid_default_calendar_reference(self):
        """Schedule with non-existent default_calendar reference is invalid."""
        from specs.v2.tools.models import Schedule, Calendar
        
        plan = MergedPlan(
            nodes={"task1": Node(title="Task 1")},
            schedule=Schedule(
                calendars={"work": Calendar(excludes=["weekends"])},
                default_calendar="nonexistent",
            ),
        )
        
        result = validate(plan)
        
        self.assertFalse(result.is_valid)
        self.assertEqual(len(result.errors), 1)
        self.assertIn("default_calendar", result.errors[0].message)
        self.assertIn("nonexistent", result.errors[0].message)
        self.assertEqual(result.errors[0].path, "schedule.default_calendar")
    
    def test_schedule_without_default_calendar_is_valid(self):
        """Schedule without default_calendar is valid."""
        from specs.v2.tools.models import Schedule, ScheduleNode
        
        plan = MergedPlan(
            nodes={"task1": Node(title="Task 1")},
            schedule=Schedule(
                nodes={"task1": ScheduleNode(start="2024-03-01")},
            ),
        )
        
        result = validate(plan)
        
        self.assertTrue(result.is_valid)
    
    def test_combined_node_and_calendar_errors(self):
        """Schedule with both invalid node and calendar references reports both errors."""
        from specs.v2.tools.models import Schedule, ScheduleNode, Calendar
        
        plan = MergedPlan(
            nodes={"task1": Node(title="Task 1")},
            schedule=Schedule(
                calendars={"work": Calendar(excludes=["weekends"])},
                nodes={
                    "missing_node": ScheduleNode(start="2024-03-01", calendar="missing_cal"),
                },
            ),
        )
        
        result = validate(plan)
        
        self.assertFalse(result.is_valid)
        self.assertEqual(len(result.errors), 2)
        # One error for missing node, one for missing calendar
        error_messages = [e.message for e in result.errors]
        self.assertTrue(any("non-existent node" in msg for msg in error_messages))
        self.assertTrue(any("non-existent calendar" in msg for msg in error_messages))
    
    def test_schedule_reference_error_includes_file_source(self):
        """Schedule reference error includes file source when available."""
        from specs.v2.tools.models import Schedule, ScheduleNode
        
        plan = MergedPlan(
            nodes={"task1": Node(title="Task 1")},
            schedule=Schedule(
                nodes={"missing": ScheduleNode(start="2024-03-01")},
            ),
            sources={"schedule_node:missing": "schedule.yaml"},
        )
        
        result = validate(plan)
        
        self.assertFalse(result.is_valid)
        self.assertEqual(result.errors[0].file_source, "schedule.yaml")
    
    def test_empty_schedule_is_valid(self):
        """Empty schedule block (no nodes, no calendars) is valid."""
        from specs.v2.tools.models import Schedule
        
        plan = MergedPlan(
            nodes={"task1": Node(title="Task 1")},
            schedule=Schedule(),
        )
        
        result = validate(plan)
        
        self.assertTrue(result.is_valid)
    
    def test_complex_valid_schedule(self):
        """Complex schedule with multiple nodes and calendars is valid."""
        from specs.v2.tools.models import Schedule, ScheduleNode, Calendar
        
        plan = MergedPlan(
            nodes={
                "phase1": Node(title="Phase 1"),
                "task1": Node(title="Task 1", parent="phase1"),
                "task2": Node(title="Task 2", parent="phase1", after=["task1"]),
                "milestone": Node(title="Milestone", milestone=True, after=["task2"]),
            },
            schedule=Schedule(
                calendars={
                    "default": Calendar(excludes=["weekends"]),
                    "holiday": Calendar(excludes=["weekends", "2024-03-08"]),
                },
                default_calendar="default",
                nodes={
                    "task1": ScheduleNode(start="2024-03-01", duration="5d"),
                    "task2": ScheduleNode(duration="3d", calendar="holiday"),
                    "milestone": ScheduleNode(),
                },
            ),
        )
        
        result = validate(plan)
        
        self.assertTrue(result.is_valid)



class TestValidateViews(unittest.TestCase):
    """Tests for views validation (Requirements 4.2, 4.3)."""
    
    def test_plan_without_views_is_valid(self):
        """Plan without views is valid."""
        plan = MergedPlan(
            nodes={"task1": Node(title="Task 1")},
            views={},
        )
        
        result = validate(plan)
        
        self.assertTrue(result.is_valid)
    
    def test_valid_view_without_where(self):
        """View without where filter is valid."""
        from specs.v2.tools.models import View
        
        plan = MergedPlan(
            nodes={"task1": Node(title="Task 1")},
            views={"default": View(title="Default View")},
        )
        
        result = validate(plan)
        
        self.assertTrue(result.is_valid)
    
    def test_valid_view_with_where_kind(self):
        """View with valid where.kind filter is valid."""
        from specs.v2.tools.models import View, ViewFilter
        
        plan = MergedPlan(
            nodes={"task1": Node(title="Task 1", kind="task")},
            views={"tasks": View(
                title="Tasks View",
                where=ViewFilter(kind=["task", "epic"]),
            )},
        )
        
        result = validate(plan)
        
        self.assertTrue(result.is_valid)
    
    def test_valid_view_with_where_status(self):
        """View with valid where.status filter is valid."""
        from specs.v2.tools.models import View, ViewFilter
        
        plan = MergedPlan(
            nodes={"task1": Node(title="Task 1", status="in_progress")},
            statuses={"in_progress": Status(label="In Progress")},
            views={"active": View(
                title="Active Tasks",
                where=ViewFilter(status=["in_progress", "blocked"]),
            )},
        )
        
        result = validate(plan)
        
        self.assertTrue(result.is_valid)
    
    def test_valid_view_with_where_has_schedule(self):
        """View with valid where.has_schedule filter is valid."""
        from specs.v2.tools.models import View, ViewFilter
        
        plan = MergedPlan(
            nodes={"task1": Node(title="Task 1")},
            views={"scheduled": View(
                title="Scheduled Tasks",
                where=ViewFilter(has_schedule=True),
            )},
        )
        
        result = validate(plan)
        
        self.assertTrue(result.is_valid)
    
    def test_valid_view_with_where_parent(self):
        """View with valid where.parent filter referencing existing node is valid."""
        from specs.v2.tools.models import View, ViewFilter
        
        plan = MergedPlan(
            nodes={
                "phase1": Node(title="Phase 1"),
                "task1": Node(title="Task 1", parent="phase1"),
            },
            views={"phase1_tasks": View(
                title="Phase 1 Tasks",
                where=ViewFilter(parent="phase1"),
            )},
        )
        
        result = validate(plan)
        
        self.assertTrue(result.is_valid)
    
    def test_valid_view_with_all_where_filters(self):
        """View with all where filter fields is valid."""
        from specs.v2.tools.models import View, ViewFilter
        
        plan = MergedPlan(
            nodes={
                "phase1": Node(title="Phase 1"),
                "task1": Node(title="Task 1", kind="task", status="in_progress", parent="phase1"),
            },
            statuses={"in_progress": Status(label="In Progress")},
            views={"filtered": View(
                title="Filtered View",
                where=ViewFilter(
                    kind=["task"],
                    status=["in_progress"],
                    has_schedule=False,
                    parent="phase1",
                ),
            )},
        )
        
        result = validate(plan)
        
        self.assertTrue(result.is_valid)


class TestValidateViewsExcludesForbidden(unittest.TestCase):
    """Tests for excludes field being forbidden in views (Requirement 4.2)."""
    
    def test_view_with_excludes_is_invalid(self):
        """View with excludes field is invalid (Requirement 4.2)."""
        from specs.v2.tools.models import View
        from specs.v2.tools.validator import validate_view_dict, ValidationResult
        
        result = ValidationResult()
        view_data = {"title": "Test View", "excludes": ["weekends"]}
        
        validate_view_dict("test_view", view_data, set(), "test.yaml", result)
        
        self.assertFalse(result.is_valid)
        self.assertEqual(len(result.errors), 1)
        self.assertIn("excludes", result.errors[0].message)
        self.assertIn("forbidden", result.errors[0].message.lower())
        self.assertIn("schedule.calendars", result.errors[0].message)
    
    def test_excludes_error_includes_path(self):
        """Excludes error includes correct path."""
        from specs.v2.tools.validator import validate_view_dict, ValidationResult
        
        result = ValidationResult()
        view_data = {"title": "Test View", "excludes": ["2024-03-08"]}
        
        validate_view_dict("my_view", view_data, set(), "views.yaml", result)
        
        self.assertFalse(result.is_valid)
        self.assertEqual(result.errors[0].path, "views.my_view.excludes")
    
    def test_excludes_error_includes_file_source(self):
        """Excludes error includes file source."""
        from specs.v2.tools.validator import validate_view_dict, ValidationResult
        
        result = ValidationResult()
        view_data = {"title": "Test View", "excludes": ["weekends"]}
        
        validate_view_dict("test_view", view_data, set(), "views.yaml", result)
        
        self.assertFalse(result.is_valid)
        self.assertEqual(result.errors[0].file_source, "views.yaml")


class TestValidateViewsWhereStructure(unittest.TestCase):
    """Tests for where filter structure validation (Requirement 4.3)."""
    
    def test_where_kind_not_list_is_invalid(self):
        """where.kind that is not a list is invalid."""
        from specs.v2.tools.validator import validate_view_dict, ValidationResult
        
        result = ValidationResult()
        view_data = {"title": "Test", "where": {"kind": "task"}}  # Should be list
        
        validate_view_dict("test_view", view_data, set(), "test.yaml", result)
        
        self.assertFalse(result.is_valid)
        self.assertEqual(len(result.errors), 1)
        self.assertIn("where.kind", result.errors[0].message)
        self.assertIn("list", result.errors[0].message.lower())
    
    def test_where_kind_with_non_string_element_is_invalid(self):
        """where.kind with non-string element is invalid."""
        from specs.v2.tools.validator import validate_view_dict, ValidationResult
        
        result = ValidationResult()
        view_data = {"title": "Test", "where": {"kind": ["task", 123]}}
        
        validate_view_dict("test_view", view_data, set(), "test.yaml", result)
        
        self.assertFalse(result.is_valid)
        self.assertEqual(len(result.errors), 1)
        self.assertIn("where.kind[1]", result.errors[0].message)
        self.assertIn("string", result.errors[0].message.lower())
    
    def test_where_status_not_list_is_invalid(self):
        """where.status that is not a list is invalid."""
        from specs.v2.tools.validator import validate_view_dict, ValidationResult
        
        result = ValidationResult()
        view_data = {"title": "Test", "where": {"status": "done"}}  # Should be list
        
        validate_view_dict("test_view", view_data, set(), "test.yaml", result)
        
        self.assertFalse(result.is_valid)
        self.assertEqual(len(result.errors), 1)
        self.assertIn("where.status", result.errors[0].message)
        self.assertIn("list", result.errors[0].message.lower())
    
    def test_where_status_with_non_string_element_is_invalid(self):
        """where.status with non-string element is invalid."""
        from specs.v2.tools.validator import validate_view_dict, ValidationResult
        
        result = ValidationResult()
        view_data = {"title": "Test", "where": {"status": ["done", None]}}
        
        validate_view_dict("test_view", view_data, set(), "test.yaml", result)
        
        self.assertFalse(result.is_valid)
        self.assertEqual(len(result.errors), 1)
        self.assertIn("where.status[1]", result.errors[0].message)
    
    def test_where_has_schedule_not_boolean_is_invalid(self):
        """where.has_schedule that is not a boolean is invalid."""
        from specs.v2.tools.validator import validate_view_dict, ValidationResult
        
        result = ValidationResult()
        view_data = {"title": "Test", "where": {"has_schedule": "yes"}}  # Should be bool
        
        validate_view_dict("test_view", view_data, set(), "test.yaml", result)
        
        self.assertFalse(result.is_valid)
        self.assertEqual(len(result.errors), 1)
        self.assertIn("where.has_schedule", result.errors[0].message)
        self.assertIn("boolean", result.errors[0].message.lower())
    
    def test_where_parent_not_string_is_invalid(self):
        """where.parent that is not a string is invalid."""
        from specs.v2.tools.validator import validate_view_dict, ValidationResult
        
        result = ValidationResult()
        view_data = {"title": "Test", "where": {"parent": 123}}  # Should be string
        
        validate_view_dict("test_view", view_data, {"phase1"}, "test.yaml", result)
        
        self.assertFalse(result.is_valid)
        self.assertEqual(len(result.errors), 1)
        self.assertIn("where.parent", result.errors[0].message)
        self.assertIn("string", result.errors[0].message.lower())
    
    def test_where_parent_non_existent_node_is_invalid(self):
        """where.parent referencing non-existent node is invalid."""
        from specs.v2.tools.validator import validate_view_dict, ValidationResult
        
        result = ValidationResult()
        view_data = {"title": "Test", "where": {"parent": "nonexistent"}}
        
        validate_view_dict("test_view", view_data, {"phase1", "task1"}, "test.yaml", result)
        
        self.assertFalse(result.is_valid)
        self.assertEqual(len(result.errors), 1)
        self.assertIn("nonexistent", result.errors[0].message)
        self.assertIn("non-existent node", result.errors[0].message)
    
    def test_where_parent_existing_node_is_valid(self):
        """where.parent referencing existing node is valid."""
        from specs.v2.tools.validator import validate_view_dict, ValidationResult
        
        result = ValidationResult()
        view_data = {"title": "Test", "where": {"parent": "phase1"}}
        
        validate_view_dict("test_view", view_data, {"phase1", "task1"}, "test.yaml", result)
        
        self.assertTrue(result.is_valid)
    
    def test_where_not_object_is_invalid(self):
        """where that is not an object is invalid."""
        from specs.v2.tools.validator import validate_view_dict, ValidationResult
        
        result = ValidationResult()
        view_data = {"title": "Test", "where": "invalid"}  # Should be object
        
        validate_view_dict("test_view", view_data, set(), "test.yaml", result)
        
        self.assertFalse(result.is_valid)
        self.assertEqual(len(result.errors), 1)
        self.assertIn("where", result.errors[0].message)
        self.assertIn("object", result.errors[0].message.lower())
    
    def test_where_error_includes_path(self):
        """Where validation error includes correct path."""
        from specs.v2.tools.validator import validate_view_dict, ValidationResult
        
        result = ValidationResult()
        view_data = {"title": "Test", "where": {"kind": "task"}}
        
        validate_view_dict("my_view", view_data, set(), "test.yaml", result)
        
        self.assertFalse(result.is_valid)
        self.assertEqual(result.errors[0].path, "views.my_view.where.kind")


class TestValidateViewsIntegration(unittest.TestCase):
    """Integration tests for views validation via validate() function."""
    
    def test_view_with_invalid_where_parent_via_validate(self):
        """View with invalid where.parent is detected by validate()."""
        from specs.v2.tools.models import View, ViewFilter
        
        plan = MergedPlan(
            nodes={"task1": Node(title="Task 1")},
            views={"filtered": View(
                title="Filtered",
                where=ViewFilter(parent="nonexistent"),
            )},
        )
        
        result = validate(plan)
        
        self.assertFalse(result.is_valid)
        self.assertEqual(len(result.errors), 1)
        self.assertIn("nonexistent", result.errors[0].message)
        self.assertIn("where.parent", result.errors[0].path)
    
    def test_multiple_views_with_errors(self):
        """Multiple views with errors generate multiple errors."""
        from specs.v2.tools.models import View, ViewFilter
        
        plan = MergedPlan(
            nodes={"task1": Node(title="Task 1")},
            views={
                "view1": View(where=ViewFilter(parent="missing1")),
                "view2": View(where=ViewFilter(parent="missing2")),
            },
        )
        
        result = validate(plan)
        
        self.assertFalse(result.is_valid)
        self.assertEqual(len(result.errors), 2)
    
    def test_view_error_includes_file_source(self):
        """View validation error includes file source when available."""
        from specs.v2.tools.models import View, ViewFilter
        
        plan = MergedPlan(
            nodes={"task1": Node(title="Task 1")},
            views={"filtered": View(where=ViewFilter(parent="missing"))},
            sources={"view:filtered": "views.yaml"},
        )
        
        result = validate(plan)
        
        self.assertFalse(result.is_valid)
        self.assertEqual(result.errors[0].file_source, "views.yaml")
    
    def test_valid_complex_plan_with_views(self):
        """Complex plan with valid views passes validation."""
        from specs.v2.tools.models import View, ViewFilter, Schedule, ScheduleNode
        
        plan = MergedPlan(
            nodes={
                "root": Node(title="Project", kind="summary"),
                "phase1": Node(title="Phase 1", parent="root", kind="phase"),
                "task1": Node(title="Task 1", parent="phase1", kind="task", status="done"),
                "task2": Node(title="Task 2", parent="phase1", kind="task", status="in_progress"),
            },
            statuses={
                "done": Status(label="Done"),
                "in_progress": Status(label="In Progress"),
            },
            schedule=Schedule(
                nodes={"task1": ScheduleNode(start="2024-03-01", duration="5d")},
            ),
            views={
                "all_tasks": View(
                    title="All Tasks",
                    where=ViewFilter(kind=["task"]),
                ),
                "phase1_view": View(
                    title="Phase 1",
                    where=ViewFilter(parent="phase1"),
                ),
                "scheduled": View(
                    title="Scheduled",
                    where=ViewFilter(has_schedule=True),
                ),
                "active": View(
                    title="Active",
                    where=ViewFilter(status=["in_progress"]),
                ),
            },
        )
        
        result = validate(plan)
        
        self.assertTrue(result.is_valid)
