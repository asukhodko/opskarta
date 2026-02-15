"""
Validator for opskarta v2 plans.

This module provides validation functionality for merged plans,
checking structural correctness, required fields, and forbidden fields.

Key validations:
- Required fields (title in nodes)
- Forbidden fields in nodes (start, finish, duration, excludes)
- Effort format (non-negative number >= 0)

Structured Error Messages:
- ValidationError includes: message, path, file_source, expected, actual
- format_error() formats errors in the standard format:
  [severity] [phase] [file:line] message
    path: element.path
    value: actual_value
    expected: expected_format

Requirements covered:
- 2.1: Node SHALL contain required field `title`
- 2.4: Node SHALL NOT contain fields `start`, `finish`, `duration`, `excludes`
- 2.5: Effort SHALL be a non-negative number (>= 0)
- 5.2: Validator SHALL check: merge-conflicts, nodes, statuses, schedule, views, effort
- 5.3: Validator SHALL return structured errors with file source
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from specs.v2.tools.models import MergedPlan


class Severity(Enum):
    """Severity level for validation messages."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationError:
    """
    Represents a validation error or warning.
    
    Attributes:
        message: Human-readable description of the issue
        path: Path to the element that caused the issue (e.g., "nodes.task1.title")
        file_source: Source file where the element was defined (if known)
        severity: Severity level (error, warning, info)
        expected: Expected format or value (optional)
        actual: Actual value that caused the error (optional)
        phase: Validation phase (e.g., "validation", "loading", "merge")
        line: Line number in source file (optional)
    
    Requirements: 5.2, 5.3 (structured errors with file source)
    """
    message: str
    path: Optional[str] = None
    file_source: Optional[str] = None
    severity: Severity = Severity.ERROR
    expected: Optional[str] = None
    actual: Optional[str] = None
    phase: str = "validation"
    line: Optional[int] = None
    
    def __str__(self) -> str:
        """Format error as string (simple format)."""
        parts = [f"[{self.severity.value}]"]
        if self.file_source:
            parts.append(f"[{self.file_source}]")
        parts.append(self.message)
        if self.path:
            parts.append(f"(path: {self.path})")
        return " ".join(parts)


def format_error(error: ValidationError) -> str:
    """
    Format a ValidationError in the standard structured format.
    
    Format:
        [severity] [phase] [file:line] message
          path: element.path
          value: actual_value
          expected: expected_format
    
    Args:
        error: The ValidationError to format
        
    Returns:
        Formatted error string
    
    Requirements: 5.3 (structured errors with file source)
    """
    # Build the header line: [severity] [phase] [file:line] message
    parts = [f"[{error.severity.value}]", f"[{error.phase}]"]
    
    # Add file:line if available
    if error.file_source:
        if error.line is not None:
            parts.append(f"[{error.file_source}:{error.line}]")
        else:
            parts.append(f"[{error.file_source}]")
    
    parts.append(error.message)
    header = " ".join(parts)
    
    # Build detail lines
    details = []
    if error.path:
        details.append(f"  path: {error.path}")
    if error.actual is not None:
        details.append(f"  value: {error.actual}")
    if error.expected is not None:
        details.append(f"  expected: {error.expected}")
    
    if details:
        return header + "\n" + "\n".join(details)
    return header


@dataclass
class ValidationResult:
    """
    Result of plan validation.
    
    Attributes:
        errors: List of validation errors (severity=ERROR)
        warnings: List of validation warnings (severity=WARNING)
    
    Properties:
        is_valid: True if there are no errors (warnings are allowed)
    """
    errors: list[ValidationError] = field(default_factory=list)
    warnings: list[ValidationError] = field(default_factory=list)
    
    @property
    def is_valid(self) -> bool:
        """Plan is valid if there are no errors."""
        return len(self.errors) == 0
    
    def add_error(
        self,
        message: str,
        path: Optional[str] = None,
        file_source: Optional[str] = None,
        expected: Optional[str] = None,
        actual: Optional[str] = None,
        phase: str = "validation",
        line: Optional[int] = None,
    ) -> None:
        """Add an error to the result."""
        self.errors.append(ValidationError(
            message=message,
            path=path,
            file_source=file_source,
            severity=Severity.ERROR,
            expected=expected,
            actual=actual,
            phase=phase,
            line=line,
        ))
    
    def add_warning(
        self,
        message: str,
        path: Optional[str] = None,
        file_source: Optional[str] = None,
        expected: Optional[str] = None,
        actual: Optional[str] = None,
        phase: str = "validation",
        line: Optional[int] = None,
    ) -> None:
        """Add a warning to the result."""
        self.warnings.append(ValidationError(
            message=message,
            path=path,
            file_source=file_source,
            severity=Severity.WARNING,
            expected=expected,
            actual=actual,
            phase=phase,
            line=line,
        ))


# Fields that are forbidden in nodes (moved to Schedule in v2)
FORBIDDEN_NODE_FIELDS = frozenset({"start", "finish", "duration", "excludes"})

# Required version for v2 tools
REQUIRED_VERSION = 2


def _validate_version(plan: MergedPlan, result: ValidationResult) -> None:
    """
    Validate that plan version is 2.
    
    v2 tools require version: 2. Files with version: 1 should use v1 tools.
    Files without explicit version default to 2 (handled by MergedPlan).
    
    Args:
        plan: The merged plan to validate
        result: ValidationResult to add errors to
    """
    if plan.version != REQUIRED_VERSION:
        result.add_error(
            message=f"Invalid version: {plan.version}. v2 tools require 'version: 2'. "
                    f"For version 1 files, use v1 tools instead.",
            path="version",
            expected=str(REQUIRED_VERSION),
            actual=str(plan.version),
        )


def validate(plan: MergedPlan, strict: bool = False) -> ValidationResult:
    """
    Validate a merged plan.

    Performs the following validations:
    - Version: must be 2 for v2 tools
    - Required fields: title in all nodes (Requirement 2.1)
    - Forbidden fields: start, finish, duration, excludes in nodes (Requirement 2.4)
    - Effort format: non-negative number >= 0 (Requirement 2.5)
    - Reference integrity: parent, deps, status references exist (Requirement 2.2)
    - Dep edges: type, lag, hard format validation
    - Cyclic dependencies: parent hierarchy and deps dependencies (Requirement 2.2)
    - Schedule reference integrity: node_id and calendar references (Requirements 3.7, 3.9)
    - Views validation: no excludes field, valid where structure (Requirements 4.2, 4.3)
    - Execution validation: progress range, date consistency
    - Profiles validation: namespace format, uniqueness

    Args:
        plan: The merged plan to validate
        strict: If True, promote certain warnings to errors

    Returns:
        ValidationResult: Contains errors and warnings found during validation

    Requirements: 2.1, 2.2, 2.4, 2.5, 3.7, 3.9, 4.2, 4.3, 5.2, 5.3
    """
    result = ValidationResult()

    # Validate version (must be 2 for v2 tools)
    _validate_version(plan, result)

    # Validate nodes
    _validate_nodes(plan, result)

    # Validate node references (parent, deps, status)
    _validate_node_references(plan, result)

    # Validate dep edges (type, lag, hard format)
    _validate_dep_edges(plan, result)

    # Detect cyclic dependencies
    _detect_parent_cycles(plan, result)
    _detect_dep_cycles(plan, result)

    # Validate schedule references (node_id and calendar)
    _validate_schedule_references(plan, result)

    # Validate views (no excludes, valid where structure)
    _validate_views(plan, result)

    # Validate execution overlay
    _validate_execution(plan, result, strict)

    # Validate profiles
    _validate_profiles(plan, result, strict)

    return result


def _validate_nodes(plan: MergedPlan, result: ValidationResult) -> None:
    """
    Validate all nodes in the plan.
    
    Checks:
    - title is present (Requirement 2.1)
    - No forbidden fields (Requirement 2.4)
    - effort is non-negative if present (Requirement 2.5)
    """
    for node_id, node in plan.nodes.items():
        source_key = f"node:{node_id}"
        file_source = plan.sources.get(source_key)
        
        # Check required field: title (Requirement 2.1)
        if not node.title:
            result.add_error(
                message=f"Node '{node_id}' is missing required field 'title'",
                path=f"nodes.{node_id}.title",
                file_source=file_source,
                expected="non-empty string",
                actual=repr(node.title) if node.title is not None else "missing",
            )
        
        # Check forbidden fields (Requirement 2.4)
        # Note: Since we use dataclasses, we need to check if the node
        # was created with forbidden fields. The Node dataclass doesn't
        # have these fields, so we check the raw data if available.
        # For now, we check via hasattr for any dynamically added attributes.
        _check_forbidden_fields(node_id, node, file_source, result)
        
        # Check effort format (Requirement 2.5)
        if node.effort is not None:
            _validate_effort(node_id, node.effort, file_source, result)


def _check_forbidden_fields(
    node_id: str,
    node,
    file_source: Optional[str],
    result: ValidationResult,
) -> None:
    """
    Check that node doesn't have forbidden fields.
    
    Forbidden fields in v2 nodes: start, finish, duration, excludes
    These fields are moved to Schedule.nodes.
    
    Requirement: 2.4
    """
    # Check for forbidden attributes that might have been set dynamically
    for field_name in FORBIDDEN_NODE_FIELDS:
        if hasattr(node, field_name) and getattr(node, field_name) is not None:
            result.add_error(
                message=f"Node '{node_id}' contains forbidden field '{field_name}'. "
                        f"In v2, '{field_name}' should be in schedule.nodes, not in nodes.",
                path=f"nodes.{node_id}.{field_name}",
                file_source=file_source,
                expected="field not present (use schedule.nodes instead)",
                actual=repr(getattr(node, field_name)),
            )


def _validate_effort(
    node_id: str,
    effort: float,
    file_source: Optional[str],
    result: ValidationResult,
) -> None:
    """
    Validate effort value.
    
    Effort must be a non-negative number (>= 0).
    
    Requirement: 2.5
    """
    # Check if effort is a number
    if not isinstance(effort, (int, float)):
        result.add_error(
            message=f"Node '{node_id}' has invalid effort value: expected number, got {type(effort).__name__}",
            path=f"nodes.{node_id}.effort",
            file_source=file_source,
            expected="number >= 0",
            actual=f"{type(effort).__name__}: {repr(effort)}",
        )
        return
    
    # Check if effort is non-negative
    if effort < 0:
        result.add_error(
            message=f"Node '{node_id}' has negative effort value: {effort}. Effort must be >= 0.",
            path=f"nodes.{node_id}.effort",
            file_source=file_source,
            expected="number >= 0",
            actual=str(effort),
        )


def validate_node_dict(
    node_id: str,
    node_data: dict,
    file_source: Optional[str],
    result: ValidationResult,
) -> None:
    """
    Validate a node from raw dictionary data.
    
    This function is useful for validating nodes before they are
    converted to Node dataclass, allowing detection of forbidden fields.
    
    Args:
        node_id: The node identifier
        node_data: Raw dictionary data for the node
        file_source: Source file path
        result: ValidationResult to add errors to
    """
    # Check required field: title (Requirement 2.1)
    if "title" not in node_data or not node_data["title"]:
        result.add_error(
            message=f"Node '{node_id}' is missing required field 'title'",
            path=f"nodes.{node_id}.title",
            file_source=file_source,
            expected="non-empty string",
            actual=repr(node_data.get("title")) if "title" in node_data else "missing",
        )
    
    # Check forbidden fields (Requirement 2.4)
    for field_name in FORBIDDEN_NODE_FIELDS:
        if field_name in node_data:
            result.add_error(
                message=f"Node '{node_id}' contains forbidden field '{field_name}'. "
                        f"In v2, '{field_name}' should be in schedule.nodes, not in nodes.",
                path=f"nodes.{node_id}.{field_name}",
                file_source=file_source,
                expected="field not present (use schedule.nodes instead)",
                actual=repr(node_data[field_name]),
            )
    
    # Check effort format (Requirement 2.5)
    if "effort" in node_data and node_data["effort"] is not None:
        effort = node_data["effort"]
        if not isinstance(effort, (int, float)):
            result.add_error(
                message=f"Node '{node_id}' has invalid effort value: expected number, got {type(effort).__name__}",
                path=f"nodes.{node_id}.effort",
                file_source=file_source,
                expected="number >= 0",
                actual=f"{type(effort).__name__}: {repr(effort)}",
            )
        elif effort < 0:
            result.add_error(
                message=f"Node '{node_id}' has negative effort value: {effort}. Effort must be >= 0.",
                path=f"nodes.{node_id}.effort",
                file_source=file_source,
                expected="number >= 0",
                actual=str(effort),
            )


def _validate_node_references(plan: MergedPlan, result: ValidationResult) -> None:
    """
    Validate reference integrity for all nodes.

    Checks:
    - parent references an existing node_id
    - all deps[].id references exist as node_ids
    - status references an existing status_id in statuses

    Requirements: 2.1, 2.2
    """
    node_ids = set(plan.nodes.keys())
    status_ids = set(plan.statuses.keys())

    for node_id, node in plan.nodes.items():
        source_key = f"node:{node_id}"
        file_source = plan.sources.get(source_key)

        # Check parent reference
        if node.parent is not None:
            if node.parent not in node_ids:
                result.add_error(
                    message=f"Node '{node_id}' references non-existent parent '{node.parent}'",
                    path=f"nodes.{node_id}.parent",
                    file_source=file_source,
                    expected="existing node_id",
                    actual=node.parent,
                )

        # Check deps references
        if node.deps is not None:
            for i, dep in enumerate(node.deps):
                if dep.id not in node_ids:
                    result.add_error(
                        message=f"Node '{node_id}' deps[{i}] references non-existent node '{dep.id}'",
                        path=f"nodes.{node_id}.deps[{i}].id",
                        file_source=file_source,
                        expected="existing node_id",
                        actual=dep.id,
                    )

        # Check status reference
        if node.status is not None:
            if node.status not in status_ids:
                result.add_error(
                    message=f"Node '{node_id}' references non-existent status '{node.status}'",
                    path=f"nodes.{node_id}.status",
                    file_source=file_source,
                    expected="existing status_id",
                    actual=node.status,
                )


def _detect_parent_cycles(plan: MergedPlan, result: ValidationResult) -> None:
    """
    Detect cyclic dependencies in parent hierarchy.
    
    Uses DFS to detect cycles in the parent-child relationship.
    A cycle exists if following parent references leads back to the starting node.
    
    Requirements: 2.2 (parent field validation)
    """
    # Build parent map for quick lookup
    node_ids = set(plan.nodes.keys())
    
    # Track visited nodes and nodes in current path
    visited: set[str] = set()
    in_path: set[str] = set()
    
    def has_cycle(node_id: str, path: list[str]) -> Optional[list[str]]:
        """
        Check if there's a cycle starting from node_id.
        Returns the cycle path if found, None otherwise.
        """
        if node_id in in_path:
            # Found a cycle - return the cycle path
            cycle_start = path.index(node_id)
            return path[cycle_start:] + [node_id]
        
        if node_id in visited:
            return None
        
        visited.add(node_id)
        in_path.add(node_id)
        path.append(node_id)
        
        node = plan.nodes.get(node_id)
        if node and node.parent and node.parent in node_ids:
            cycle = has_cycle(node.parent, path)
            if cycle:
                return cycle
        
        path.pop()
        in_path.remove(node_id)
        return None
    
    # Check each node for cycles
    for node_id in plan.nodes:
        if node_id not in visited:
            cycle = has_cycle(node_id, [])
            if cycle:
                source_key = f"node:{cycle[0]}"
                file_source = plan.sources.get(source_key)
                cycle_str = " -> ".join(cycle)
                result.add_error(
                    message=f"Cyclic parent dependency detected: {cycle_str}",
                    path=f"nodes.{cycle[0]}.parent",
                    file_source=file_source,
                )
                # Reset visited to continue checking other potential cycles
                # but mark cycle nodes as visited to avoid duplicate errors
                for cid in cycle[:-1]:  # Exclude the repeated last element
                    visited.add(cid)


def _detect_dep_cycles(plan: MergedPlan, result: ValidationResult) -> None:
    """
    Detect cyclic dependencies in deps relationships.

    Uses DFS to detect cycles in the dependency graph formed by deps references.
    A cycle exists if following deps references leads back to the starting node.
    Both hard and soft deps are checked (cycles forbidden everywhere).

    Requirements: 2.2 (deps field validation)
    """
    node_ids = set(plan.nodes.keys())

    # Track visited nodes and nodes in current path
    visited: set[str] = set()
    in_path: set[str] = set()
    reported_cycles: set[frozenset[str]] = set()

    def find_cycle(node_id: str, path: list[str]) -> Optional[list[str]]:
        """
        Check if there's a cycle starting from node_id in deps.
        Returns the cycle path if found, None otherwise.
        """
        if node_id in in_path:
            cycle_start = path.index(node_id)
            return path[cycle_start:] + [node_id]

        if node_id in visited:
            return None

        visited.add(node_id)
        in_path.add(node_id)
        path.append(node_id)

        node = plan.nodes.get(node_id)
        if node and node.deps:
            for dep in node.deps:
                if dep.id in node_ids:
                    cycle = find_cycle(dep.id, path)
                    if cycle:
                        return cycle

        path.pop()
        in_path.remove(node_id)
        return None

    # Check each node for cycles
    for node_id in plan.nodes:
        if node_id not in visited:
            cycle = find_cycle(node_id, [])
            if cycle:
                cycle_set = frozenset(cycle[:-1])
                if cycle_set not in reported_cycles:
                    reported_cycles.add(cycle_set)
                    source_key = f"node:{cycle[0]}"
                    file_source = plan.sources.get(source_key)
                    cycle_str = " -> ".join(cycle)
                    result.add_error(
                        message=f"Cyclic dependency detected: {cycle_str}",
                        path=f"nodes.{cycle[0]}.deps",
                        file_source=file_source,
                    )


def _validate_schedule_references(plan: MergedPlan, result: ValidationResult) -> None:
    """
    Validate schedule reference integrity.
    
    Checks:
    - All node_ids in schedule.nodes exist in nodes (Requirement 3.7)
    - All calendar references in schedule.nodes exist in schedule.calendars (Requirement 3.9)
    - default_calendar (if set) exists in schedule.calendars
    
    Requirements: 3.7, 3.9
    """
    # Skip if no schedule block
    if plan.schedule is None:
        return
    
    node_ids = set(plan.nodes.keys())
    calendar_ids = set(plan.schedule.calendars.keys())
    
    # Check default_calendar reference
    if plan.schedule.default_calendar is not None:
        if plan.schedule.default_calendar not in calendar_ids:
            # Try to find source for schedule
            source_key = "schedule:default_calendar"
            file_source = plan.sources.get(source_key)
            result.add_error(
                message=f"Schedule references non-existent default_calendar '{plan.schedule.default_calendar}'",
                path="schedule.default_calendar",
                file_source=file_source,
                expected="existing calendar_id",
                actual=plan.schedule.default_calendar,
            )
    
    # Check each schedule node
    for schedule_node_id, schedule_node in plan.schedule.nodes.items():
        # Get source file for this schedule node
        source_key = f"schedule_node:{schedule_node_id}"
        file_source = plan.sources.get(source_key)
        
        # Check that node_id exists in nodes (Requirement 3.7)
        if schedule_node_id not in node_ids:
            result.add_error(
                message=f"Schedule node '{schedule_node_id}' references non-existent node in nodes",
                path=f"schedule.nodes.{schedule_node_id}",
                file_source=file_source,
                expected="existing node_id",
                actual=schedule_node_id,
            )
        
        # Check that calendar reference exists (Requirement 3.9)
        if schedule_node.calendar is not None:
            if schedule_node.calendar not in calendar_ids:
                result.add_error(
                    message=f"Schedule node '{schedule_node_id}' references non-existent calendar '{schedule_node.calendar}'",
                    path=f"schedule.nodes.{schedule_node_id}.calendar",
                    file_source=file_source,
                    expected="existing calendar_id",
                    actual=schedule_node.calendar,
                )


def _validate_views(plan: MergedPlan, result: ValidationResult) -> None:
    """
    Validate all views in the plan.
    
    Checks:
    - No excludes field in views (Requirement 4.2)
    - Valid where filter structure (Requirement 4.3):
      - kind: list of strings
      - status: list of strings
      - has_schedule: boolean
      - parent: string (node_id) that exists in nodes
    
    Requirements: 4.2, 4.3
    """
    node_ids = set(plan.nodes.keys())
    
    for view_id, view in plan.views.items():
        source_key = f"view:{view_id}"
        file_source = plan.sources.get(source_key)
        
        # Check for forbidden excludes field (Requirement 4.2)
        # Since View dataclass doesn't have excludes, we check via hasattr
        # for dynamically added attributes
        if hasattr(view, 'excludes') and getattr(view, 'excludes') is not None:
            result.add_error(
                message=f"View '{view_id}' contains forbidden field 'excludes'. "
                        f"In v2, 'excludes' should be in schedule.calendars, not in views.",
                path=f"views.{view_id}.excludes",
                file_source=file_source,
                expected="field not present (use schedule.calendars instead)",
                actual=repr(getattr(view, 'excludes')),
            )
        
        # Validate where filter structure (Requirement 4.3)
        if view.where is not None:
            _validate_view_where(view_id, view.where, node_ids, file_source, result)

        # Validate lanes structure and references (fail-fast for wrong node ids)
        if view.lanes is not None:
            _validate_view_lanes(view_id, view.lanes, node_ids, file_source, result)


def _validate_view_where(
    view_id: str,
    where: "ViewFilter",
    node_ids: set[str],
    file_source: Optional[str],
    result: ValidationResult,
) -> None:
    """
    Validate the where filter structure of a view.
    
    Checks:
    - kind: should be a list of strings
    - status: should be a list of strings
    - has_schedule: should be a boolean
    - parent: should be a string (node_id) that exists in nodes
    
    Requirement: 4.3
    """
    from specs.v2.tools.models import ViewFilter
    
    # Validate kind field (should be list of strings)
    if where.kind is not None:
        if not isinstance(where.kind, list):
            result.add_error(
                message=f"View '{view_id}' has invalid where.kind: expected list of strings, got {type(where.kind).__name__}",
                path=f"views.{view_id}.where.kind",
                file_source=file_source,
                expected="list of strings",
                actual=f"{type(where.kind).__name__}: {repr(where.kind)}",
            )
        else:
            for i, kind_value in enumerate(where.kind):
                if not isinstance(kind_value, str):
                    result.add_error(
                        message=f"View '{view_id}' has invalid where.kind[{i}]: expected string, got {type(kind_value).__name__}",
                        path=f"views.{view_id}.where.kind[{i}]",
                        file_source=file_source,
                        expected="string",
                        actual=f"{type(kind_value).__name__}: {repr(kind_value)}",
                    )
    
    # Validate status field (should be list of strings)
    if where.status is not None:
        if not isinstance(where.status, list):
            result.add_error(
                message=f"View '{view_id}' has invalid where.status: expected list of strings, got {type(where.status).__name__}",
                path=f"views.{view_id}.where.status",
                file_source=file_source,
                expected="list of strings",
                actual=f"{type(where.status).__name__}: {repr(where.status)}",
            )
        else:
            for i, status_value in enumerate(where.status):
                if not isinstance(status_value, str):
                    result.add_error(
                        message=f"View '{view_id}' has invalid where.status[{i}]: expected string, got {type(status_value).__name__}",
                        path=f"views.{view_id}.where.status[{i}]",
                        file_source=file_source,
                        expected="string",
                        actual=f"{type(status_value).__name__}: {repr(status_value)}",
                    )
    
    # Validate has_schedule field (should be boolean)
    if where.has_schedule is not None:
        if not isinstance(where.has_schedule, bool):
            result.add_error(
                message=f"View '{view_id}' has invalid where.has_schedule: expected boolean, got {type(where.has_schedule).__name__}",
                path=f"views.{view_id}.where.has_schedule",
                file_source=file_source,
                expected="boolean",
                actual=f"{type(where.has_schedule).__name__}: {repr(where.has_schedule)}",
            )
    
    # Validate parent field (should be string referencing existing node_id)
    if where.parent is not None:
        if not isinstance(where.parent, str):
            result.add_error(
                message=f"View '{view_id}' has invalid where.parent: expected string (node_id), got {type(where.parent).__name__}",
                path=f"views.{view_id}.where.parent",
                file_source=file_source,
                expected="string (existing node_id)",
                actual=f"{type(where.parent).__name__}: {repr(where.parent)}",
            )
        elif where.parent not in node_ids:
            result.add_error(
                message=f"View '{view_id}' references non-existent node '{where.parent}' in where.parent",
                path=f"views.{view_id}.where.parent",
                file_source=file_source,
                expected="existing node_id",
                actual=where.parent,
            )


def _validate_view_lanes(
    view_id: str,
    lanes: object,
    node_ids: set[str],
    file_source: Optional[str],
    result: ValidationResult,
) -> None:
    """
    Validate view lanes structure and node references.

    Checks:
    - lanes is an object
    - each lane is an object
    - lane.title is string if present
    - lane.nodes is list[string]
    - each lane.nodes[i] references an existing node_id
    """
    if not isinstance(lanes, dict):
        result.add_error(
            message=f"View '{view_id}' has invalid lanes: expected object, got {type(lanes).__name__}",
            path=f"views.{view_id}.lanes",
            file_source=file_source,
            expected="object",
            actual=f"{type(lanes).__name__}: {repr(lanes)}",
        )
        return

    for lane_id, lane_data in lanes.items():
        lane_path = f"views.{view_id}.lanes.{lane_id}"

        if not isinstance(lane_id, str):
            result.add_error(
                message=f"View '{view_id}' has invalid lane id: expected string, got {type(lane_id).__name__}",
                path=f"views.{view_id}.lanes",
                file_source=file_source,
                expected="string lane id",
                actual=f"{type(lane_id).__name__}: {repr(lane_id)}",
            )
            continue

        if not isinstance(lane_data, dict):
            result.add_error(
                message=f"View '{view_id}' lane '{lane_id}' must be an object",
                path=lane_path,
                file_source=file_source,
                expected="object",
                actual=f"{type(lane_data).__name__}: {repr(lane_data)}",
            )
            continue

        if "title" in lane_data and lane_data["title"] is not None and not isinstance(lane_data["title"], str):
            result.add_error(
                message=f"View '{view_id}' lane '{lane_id}' has invalid title: expected string",
                path=f"{lane_path}.title",
                file_source=file_source,
                expected="string",
                actual=f"{type(lane_data['title']).__name__}: {repr(lane_data['title'])}",
            )

        if "nodes" not in lane_data:
            result.add_error(
                message=f"View '{view_id}' lane '{lane_id}' is missing required field 'nodes'",
                path=f"{lane_path}.nodes",
                file_source=file_source,
                expected="list of node ids",
                actual="missing",
            )
            continue

        lane_nodes = lane_data.get("nodes")
        if not isinstance(lane_nodes, list):
            result.add_error(
                message=f"View '{view_id}' lane '{lane_id}' has invalid nodes: expected list",
                path=f"{lane_path}.nodes",
                file_source=file_source,
                expected="list[string]",
                actual=f"{type(lane_nodes).__name__}: {repr(lane_nodes)}",
            )
            continue

        for i, node_id in enumerate(lane_nodes):
            node_path = f"{lane_path}.nodes[{i}]"
            if not isinstance(node_id, str):
                result.add_error(
                    message=f"View '{view_id}' lane '{lane_id}' has invalid node reference type",
                    path=node_path,
                    file_source=file_source,
                    expected="string node_id",
                    actual=f"{type(node_id).__name__}: {repr(node_id)}",
                )
                continue
            if node_id not in node_ids:
                result.add_error(
                    message=f"View '{view_id}' lane '{lane_id}' references non-existent node '{node_id}'",
                    path=node_path,
                    file_source=file_source,
                    expected="existing node_id",
                    actual=node_id,
                )


def validate_view_dict(
    view_id: str,
    view_data: dict,
    node_ids: set[str],
    file_source: Optional[str],
    result: ValidationResult,
) -> None:
    """
    Validate a view from raw dictionary data.
    
    This function is useful for validating views before they are
    converted to View dataclass, allowing detection of forbidden fields.
    
    Args:
        view_id: The view identifier
        view_data: Raw dictionary data for the view
        node_ids: Set of valid node_ids for reference checking
        file_source: Source file path
        result: ValidationResult to add errors to
    
    Requirements: 4.2, 4.3
    """
    # Check for forbidden excludes field (Requirement 4.2)
    if "excludes" in view_data:
        result.add_error(
            message=f"View '{view_id}' contains forbidden field 'excludes'. "
                    f"In v2, 'excludes' should be in schedule.calendars, not in views.",
            path=f"views.{view_id}.excludes",
            file_source=file_source,
            expected="field not present (use schedule.calendars instead)",
            actual=repr(view_data["excludes"]),
        )
    
    # Validate where filter structure (Requirement 4.3)
    if "where" in view_data and view_data["where"] is not None:
        where = view_data["where"]
        
        if not isinstance(where, dict):
            result.add_error(
                message=f"View '{view_id}' has invalid where: expected object, got {type(where).__name__}",
                path=f"views.{view_id}.where",
                file_source=file_source,
                expected="object",
                actual=f"{type(where).__name__}: {repr(where)}",
            )
            return
        
        # Validate kind field (should be list of strings)
        if "kind" in where and where["kind"] is not None:
            kind = where["kind"]
            if not isinstance(kind, list):
                result.add_error(
                    message=f"View '{view_id}' has invalid where.kind: expected list of strings, got {type(kind).__name__}",
                    path=f"views.{view_id}.where.kind",
                    file_source=file_source,
                    expected="list of strings",
                    actual=f"{type(kind).__name__}: {repr(kind)}",
                )
            else:
                for i, kind_value in enumerate(kind):
                    if not isinstance(kind_value, str):
                        result.add_error(
                            message=f"View '{view_id}' has invalid where.kind[{i}]: expected string, got {type(kind_value).__name__}",
                            path=f"views.{view_id}.where.kind[{i}]",
                            file_source=file_source,
                            expected="string",
                            actual=f"{type(kind_value).__name__}: {repr(kind_value)}",
                        )
        
        # Validate status field (should be list of strings)
        if "status" in where and where["status"] is not None:
            status = where["status"]
            if not isinstance(status, list):
                result.add_error(
                    message=f"View '{view_id}' has invalid where.status: expected list of strings, got {type(status).__name__}",
                    path=f"views.{view_id}.where.status",
                    file_source=file_source,
                    expected="list of strings",
                    actual=f"{type(status).__name__}: {repr(status)}",
                )
            else:
                for i, status_value in enumerate(status):
                    if not isinstance(status_value, str):
                        result.add_error(
                            message=f"View '{view_id}' has invalid where.status[{i}]: expected string, got {type(status_value).__name__}",
                            path=f"views.{view_id}.where.status[{i}]",
                            file_source=file_source,
                            expected="string",
                            actual=f"{type(status_value).__name__}: {repr(status_value)}",
                        )
        
        # Validate has_schedule field (should be boolean)
        if "has_schedule" in where and where["has_schedule"] is not None:
            has_schedule = where["has_schedule"]
            if not isinstance(has_schedule, bool):
                result.add_error(
                    message=f"View '{view_id}' has invalid where.has_schedule: expected boolean, got {type(has_schedule).__name__}",
                    path=f"views.{view_id}.where.has_schedule",
                    file_source=file_source,
                    expected="boolean",
                    actual=f"{type(has_schedule).__name__}: {repr(has_schedule)}",
                )
        
        # Validate parent field (should be string referencing existing node_id)
        if "parent" in where and where["parent"] is not None:
            parent = where["parent"]
            if not isinstance(parent, str):
                result.add_error(
                    message=f"View '{view_id}' has invalid where.parent: expected string (node_id), got {type(parent).__name__}",
                    path=f"views.{view_id}.where.parent",
                    file_source=file_source,
                    expected="string (existing node_id)",
                    actual=f"{type(parent).__name__}: {repr(parent)}",
                )
            elif parent not in node_ids:
                result.add_error(
                    message=f"View '{view_id}' references non-existent node '{parent}' in where.parent",
                    path=f"views.{view_id}.where.parent",
                    file_source=file_source,
                    expected="existing node_id",
                    actual=parent,
                )

    # Validate lanes structure and references
    if "lanes" in view_data and view_data["lanes"] is not None:
        _validate_view_lanes(view_id, view_data["lanes"], node_ids, file_source, result)


import re

# Lag pattern: non-negative integer followed by d or w
_LAG_PATTERN = re.compile(r"^(0|[1-9][0-9]*)[dw]$")

# Valid dep types
_VALID_DEP_TYPES = frozenset({"fs", "ss"})


def _validate_dep_edges(plan: MergedPlan, result: ValidationResult) -> None:
    """
    Validate dep edge fields: type, lag, hard format.

    Checks:
    - dep.type in ("fs", "ss")
    - dep.lag matches ^(0|[1-9][0-9]*)[dw]$
    - dep.hard is bool
    """
    for node_id, node in plan.nodes.items():
        if not node.deps:
            continue

        source_key = f"node:{node_id}"
        file_source = plan.sources.get(source_key)

        for i, dep in enumerate(node.deps):
            dep_path = f"nodes.{node_id}.deps[{i}]"

            # Validate type
            if not isinstance(dep.type, str):
                result.add_error(
                    message=f"Node '{node_id}' deps[{i}] type must be a string, got {type(dep.type).__name__}",
                    path=f"{dep_path}.type",
                    file_source=file_source,
                    expected="'fs' or 'ss'",
                    actual=f"{type(dep.type).__name__}: {repr(dep.type)}",
                )
            elif dep.type not in _VALID_DEP_TYPES:
                result.add_error(
                    message=f"Node '{node_id}' deps[{i}] has invalid type '{dep.type}'",
                    path=f"{dep_path}.type",
                    file_source=file_source,
                    expected="'fs' or 'ss'",
                    actual=dep.type,
                )

            # Validate lag format
            if not isinstance(dep.lag, str):
                result.add_error(
                    message=f"Node '{node_id}' deps[{i}] lag must be a string, got {type(dep.lag).__name__}",
                    path=f"{dep_path}.lag",
                    file_source=file_source,
                    expected="non-negative duration like '0d', '3d', '1w'",
                    actual=f"{type(dep.lag).__name__}: {repr(dep.lag)}",
                )
            elif not _LAG_PATTERN.match(dep.lag):
                result.add_error(
                    message=f"Node '{node_id}' deps[{i}] has invalid lag '{dep.lag}'",
                    path=f"{dep_path}.lag",
                    file_source=file_source,
                    expected="non-negative duration like '0d', '3d', '1w'",
                    actual=dep.lag,
                )

            # Validate hard is bool
            if not isinstance(dep.hard, bool):
                result.add_error(
                    message=f"Node '{node_id}' deps[{i}] has invalid hard value",
                    path=f"{dep_path}.hard",
                    file_source=file_source,
                    expected="boolean",
                    actual=f"{type(dep.hard).__name__}: {repr(dep.hard)}",
                )


# Date pattern for execution validation
_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _validate_execution(
    plan: MergedPlan,
    result: ValidationResult,
    strict: bool,
) -> None:
    """
    Validate execution overlay data.

    Checks:
    - node_id references existing node
    - progress in [0, 1]
    - confidence in [0, 1]
    - actual_start / actual_finish are valid YYYY-MM-DD
    - Consistency warnings (actual_finish without actual_start, etc.)
    """
    if plan.execution is None:
        return

    node_ids = set(plan.nodes.keys())

    for en_id, en in plan.execution.nodes.items():
        source_key = f"execution_node:{en_id}"
        file_source = plan.sources.get(source_key)
        base_path = f"execution.nodes.{en_id}"

        # Check node reference
        if en_id not in node_ids:
            result.add_error(
                message=f"Execution node '{en_id}' references non-existent node",
                path=base_path,
                file_source=file_source,
                expected="existing node_id",
                actual=en_id,
            )

        # Validate progress range
        if en.progress is not None:
            if not isinstance(en.progress, (int, float)):
                result.add_error(
                    message=f"Execution node '{en_id}' has invalid progress type",
                    path=f"{base_path}.progress",
                    file_source=file_source,
                    expected="number in [0, 1]",
                    actual=f"{type(en.progress).__name__}: {repr(en.progress)}",
                )
            elif en.progress < 0 or en.progress > 1:
                result.add_error(
                    message=f"Execution node '{en_id}' progress {en.progress} is out of range [0, 1]",
                    path=f"{base_path}.progress",
                    file_source=file_source,
                    expected="number in [0, 1]",
                    actual=str(en.progress),
                )

        # Validate confidence range
        if en.confidence is not None:
            if not isinstance(en.confidence, (int, float)):
                result.add_error(
                    message=f"Execution node '{en_id}' has invalid confidence type",
                    path=f"{base_path}.confidence",
                    file_source=file_source,
                    expected="number in [0, 1]",
                    actual=f"{type(en.confidence).__name__}: {repr(en.confidence)}",
                )
            elif en.confidence < 0 or en.confidence > 1:
                result.add_error(
                    message=f"Execution node '{en_id}' confidence {en.confidence} is out of range [0, 1]",
                    path=f"{base_path}.confidence",
                    file_source=file_source,
                    expected="number in [0, 1]",
                    actual=str(en.confidence),
                )

        # Validate actual_start format
        if en.actual_start is not None and not _DATE_PATTERN.match(str(en.actual_start)):
            result.add_error(
                message=f"Execution node '{en_id}' has invalid actual_start format",
                path=f"{base_path}.actual_start",
                file_source=file_source,
                expected="YYYY-MM-DD",
                actual=str(en.actual_start),
            )

        # Validate actual_finish format
        if en.actual_finish is not None and not _DATE_PATTERN.match(str(en.actual_finish)):
            result.add_error(
                message=f"Execution node '{en_id}' has invalid actual_finish format",
                path=f"{base_path}.actual_finish",
                file_source=file_source,
                expected="YYYY-MM-DD",
                actual=str(en.actual_finish),
            )

        # Consistency warnings
        if en.actual_finish is not None and en.actual_start is None:
            result.add_warning(
                message=f"Execution node '{en_id}' has actual_finish but no actual_start",
                path=base_path,
                file_source=file_source,
            )

        if en.progress is not None and isinstance(en.progress, (int, float)):
            if en.progress == 1.0 and en.actual_finish is None:
                result.add_warning(
                    message=f"Execution node '{en_id}' has progress=1.0 but no actual_finish",
                    path=base_path,
                    file_source=file_source,
                )
            if en.actual_finish is not None and en.progress != 1.0:
                result.add_warning(
                    message=f"Execution node '{en_id}' has actual_finish but progress is not 1.0",
                    path=base_path,
                    file_source=file_source,
                )
            if en.progress > 0 and en.actual_start is None:
                result.add_warning(
                    message=f"Execution node '{en_id}' has progress > 0 but no actual_start",
                    path=base_path,
                    file_source=file_source,
                )


# Profile namespace pattern
_NAMESPACE_PATTERN = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


def _validate_profiles(
    plan: MergedPlan,
    result: ValidationResult,
    strict: bool,
) -> None:
    """
    Validate profiles declarations.

    Checks:
    - namespace format: ^[a-zA-Z_][a-zA-Z0-9_]*$
    - No duplicate namespaces between profiles
    - Undeclared x namespaces → warn (strict: error)
    """
    if not plan.profiles:
        return

    seen_namespaces: dict[str, str] = {}  # namespace -> profile_id

    for profile in plan.profiles:
        source_key = f"profile:{profile.id}"
        file_source = plan.sources.get(source_key)

        # Validate namespace format
        if not _NAMESPACE_PATTERN.match(profile.namespace):
            result.add_error(
                message=f"Profile '{profile.id}' has invalid namespace '{profile.namespace}'",
                path=f"profiles.{profile.id}.namespace",
                file_source=file_source,
                expected="^[a-zA-Z_][a-zA-Z0-9_]*$",
                actual=profile.namespace,
            )

        # Check duplicate namespaces
        if profile.namespace in seen_namespaces:
            result.add_error(
                message=f"Profile '{profile.id}' duplicates namespace '{profile.namespace}' "
                        f"(already declared by '{seen_namespaces[profile.namespace]}')",
                path=f"profiles.{profile.id}.namespace",
                file_source=file_source,
            )
        seen_namespaces[profile.namespace] = profile.id

    # Check undeclared x namespaces
    declared_ns = set(seen_namespaces.keys())

    # Check plan-level x
    for x_key in plan.x:
        if x_key not in declared_ns:
            msg = f"Extension key 'x.{x_key}' is not declared by any profile"
            if strict:
                result.add_error(message=msg, path=f"x.{x_key}")
            else:
                result.add_warning(message=msg, path=f"x.{x_key}")

    # Check node-level x
    for node_id, node in plan.nodes.items():
        if node.x:
            for x_key in node.x:
                if x_key not in declared_ns:
                    msg = f"Extension key 'nodes.{node_id}.x.{x_key}' is not declared by any profile"
                    if strict:
                        result.add_error(message=msg, path=f"nodes.{node_id}.x.{x_key}")
                    else:
                        result.add_warning(message=msg, path=f"nodes.{node_id}.x.{x_key}")
