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


def validate(plan: MergedPlan) -> ValidationResult:
    """
    Validate a merged plan.
    
    Performs the following validations:
    - Required fields: title in all nodes (Requirement 2.1)
    - Forbidden fields: start, finish, duration, excludes in nodes (Requirement 2.4)
    - Effort format: non-negative number >= 0 (Requirement 2.5)
    - Reference integrity: parent, after, status references exist (Requirement 2.2)
    - Cyclic dependencies: parent hierarchy and after dependencies (Requirement 2.2)
    - Schedule reference integrity: node_id and calendar references (Requirements 3.7, 3.9)
    - Views validation: no excludes field, valid where structure (Requirements 4.2, 4.3)
    
    Args:
        plan: The merged plan to validate
        
    Returns:
        ValidationResult: Contains errors and warnings found during validation
    
    Requirements: 2.1, 2.2, 2.4, 2.5, 3.7, 3.9, 4.2, 4.3, 5.2, 5.3
    """
    result = ValidationResult()
    
    # Validate nodes
    _validate_nodes(plan, result)
    
    # Validate node references (parent, after, status)
    _validate_node_references(plan, result)
    
    # Detect cyclic dependencies
    _detect_parent_cycles(plan, result)
    _detect_after_cycles(plan, result)
    
    # Validate schedule references (node_id and calendar)
    _validate_schedule_references(plan, result)
    
    # Validate views (no excludes, valid where structure)
    _validate_views(plan, result)
    
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
    - all after references exist as node_ids
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
        
        # Check after references
        if node.after is not None:
            for after_id in node.after:
                if after_id not in node_ids:
                    result.add_error(
                        message=f"Node '{node_id}' references non-existent dependency '{after_id}' in after",
                        path=f"nodes.{node_id}.after",
                        file_source=file_source,
                        expected="existing node_id",
                        actual=after_id,
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


def _detect_after_cycles(plan: MergedPlan, result: ValidationResult) -> None:
    """
    Detect cyclic dependencies in after relationships.
    
    Uses DFS to detect cycles in the dependency graph formed by after references.
    A cycle exists if following after references leads back to the starting node.
    
    Requirements: 2.2 (after field validation)
    """
    node_ids = set(plan.nodes.keys())
    
    # Track visited nodes and nodes in current path
    visited: set[str] = set()
    in_path: set[str] = set()
    reported_cycles: set[frozenset[str]] = set()  # Track reported cycles to avoid duplicates
    
    def find_cycle(node_id: str, path: list[str]) -> Optional[list[str]]:
        """
        Check if there's a cycle starting from node_id in after dependencies.
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
        if node and node.after:
            for after_id in node.after:
                if after_id in node_ids:
                    cycle = find_cycle(after_id, path)
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
                # Create a frozenset of cycle nodes to check for duplicates
                cycle_set = frozenset(cycle[:-1])  # Exclude repeated last element
                if cycle_set not in reported_cycles:
                    reported_cycles.add(cycle_set)
                    source_key = f"node:{cycle[0]}"
                    file_source = plan.sources.get(source_key)
                    cycle_str = " -> ".join(cycle)
                    result.add_error(
                        message=f"Cyclic after dependency detected: {cycle_str}",
                        path=f"nodes.{cycle[0]}.after",
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
