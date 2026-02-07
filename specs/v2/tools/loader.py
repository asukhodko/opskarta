"""
Loader module for opskarta v2.

This module provides functionality for loading and validating YAML plan fragments.
It implements the first stage of the Plan Set processing pipeline.

Key functions:
- load_fragment(file_path): Load a single YAML file as a Fragment
- merge_fragments(fragments): Merge multiple fragments into a MergedPlan

Requirements covered:
- 1.1: Load each file as Fragment
- 1.2: Accept only allowed top-level blocks
- 1.3: Return error with block name and file for invalid blocks
- 1.4: Conflict detection for duplicate node_id
- 1.5: Conflict detection for duplicate status_id
- 1.6: Meta block merging with conflict detection
- 1.7: Schedule block merging (calendars and nodes)
- 1.8: schedule.default_calendar conflict (only one fragment allowed)
- 1.9: Return MergedPlan with all merged data
- 1.10: Source tracking for each element
"""

from pathlib import Path
from typing import Any

import yaml

from specs.v2.tools.models import (
    Calendar,
    Meta,
    MergedPlan,
    Node,
    Schedule,
    ScheduleNode,
    Status,
    View,
    ViewFilter,
)


# Allowed top-level blocks in a Fragment (Requirement 1.2)
ALLOWED_TOP_LEVEL_BLOCKS: frozenset[str] = frozenset({
    "version",
    "meta",
    "statuses",
    "nodes",
    "schedule",
    "views",
    "x",
})


class LoadError(Exception):
    """
    Exception raised when loading a fragment fails.
    
    This exception is raised for:
    - File read errors (file not found, permission denied, etc.)
    - YAML parsing errors
    - Invalid top-level blocks in the fragment
    
    Attributes:
        message: Human-readable error description
        file_path: Path to the file that caused the error
        block_name: Name of the invalid block (if applicable)
    """
    
    def __init__(
        self,
        message: str,
        file_path: str | None = None,
        block_name: str | None = None,
    ) -> None:
        self.message = message
        self.file_path = file_path
        self.block_name = block_name
        
        # Build full error message
        parts = []
        if file_path:
            parts.append(f"[{file_path}]")
        parts.append(message)
        if block_name:
            parts.append(f"(block: '{block_name}')")
        
        super().__init__(" ".join(parts))


class MergeConflictError(Exception):
    """
    Exception raised when merging fragments results in a conflict.
    
    This exception is raised for:
    - Duplicate node_id across fragments (Requirement 1.4)
    - Duplicate status_id across fragments (Requirement 1.5)
    - Conflicting meta field values (Requirement 1.6)
    - Duplicate calendar_id or schedule node_id (Requirement 1.7)
    - Multiple fragments with schedule.default_calendar (Requirement 1.8)
    - Duplicate view_id across fragments
    - Duplicate x key across fragments
    
    Attributes:
        message: Human-readable error description
        element_type: Type of conflicting element (node, status, meta, calendar, etc.)
        element_id: ID of the conflicting element
        files: List of files containing the conflict
    """
    
    def __init__(
        self,
        message: str,
        element_type: str | None = None,
        element_id: str | None = None,
        files: list[str] | None = None,
    ) -> None:
        self.message = message
        self.element_type = element_type
        self.element_id = element_id
        self.files = files or []
        
        # Build full error message
        parts = [message]
        if files:
            parts.append(f"(files: {', '.join(files)})")
        
        super().__init__(" ".join(parts))


def load_fragment(file_path: str) -> dict[str, Any]:
    """
    Load a single YAML file as a Fragment.
    
    Reads and parses a YAML file, validates that all top-level blocks
    are allowed, and returns the parsed data with source file information.
    
    Args:
        file_path: Path to the YAML file to load
        
    Returns:
        Dictionary containing:
        - All parsed YAML data
        - '_source': Path to the source file (added by loader)
        
    Raises:
        LoadError: If file cannot be read, YAML is invalid, or
                   fragment contains invalid top-level blocks
    
    Requirements:
        - 1.1: Load file as Fragment
        - 1.2: Accept only allowed blocks (version, meta, statuses, nodes, schedule, views, x)
        - 1.3: Return error with block name and file for invalid blocks
    
    Example:
        >>> fragment = load_fragment("plan.yaml")
        >>> fragment["_source"]
        'plan.yaml'
        >>> fragment.get("version")
        2
    """
    path = Path(file_path)
    
    # Read file content
    try:
        content = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise LoadError(
            f"File not found: {file_path}",
            file_path=file_path,
        )
    except PermissionError:
        raise LoadError(
            f"Permission denied: {file_path}",
            file_path=file_path,
        )
    except OSError as e:
        raise LoadError(
            f"Cannot read file: {e}",
            file_path=file_path,
        )
    
    # Parse YAML
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError as e:
        raise LoadError(
            f"Invalid YAML: {e}",
            file_path=file_path,
        )
    
    # Handle empty files
    if data is None:
        data = {}
    
    # Validate that data is a dictionary
    if not isinstance(data, dict):
        raise LoadError(
            f"Fragment must be a YAML mapping, got {type(data).__name__}",
            file_path=file_path,
        )
    
    # Validate top-level blocks (Requirement 1.2, 1.3)
    for block_name in data.keys():
        if block_name not in ALLOWED_TOP_LEVEL_BLOCKS:
            raise LoadError(
                f"Invalid top-level block: '{block_name}'. "
                f"Allowed blocks: {', '.join(sorted(ALLOWED_TOP_LEVEL_BLOCKS))}",
                file_path=file_path,
                block_name=block_name,
            )
    
    # Add source file information
    result = dict(data)
    result["_source"] = file_path
    
    return result


def load_plan_set(files: list[str]) -> MergedPlan:
    """
    Load and merge plan fragments from multiple files.
    
    This is the main entry point for loading a Plan Set. It combines
    load_fragment and merge_fragments into a single convenient function.
    
    Args:
        files: List of paths to YAML files to load
        
    Returns:
        MergedPlan: The merged plan containing all data from all fragments
        
    Raises:
        LoadError: If any file cannot be read or contains invalid YAML/blocks
        MergeConflictError: If there are conflicts between fragments
    
    Requirements:
        - 5.1: Provide function load_plan_set(files: list[string]) -> Merged_Plan
    
    Example:
        >>> plan = load_plan_set(["main.yaml", "nodes.yaml", "schedule.yaml"])
        >>> plan.nodes["task1"].title
        'Task 1'
    """
    # Load all fragments
    fragments = [load_fragment(file_path) for file_path in files]
    
    # Merge and return
    return merge_fragments(fragments)


def merge_fragments(fragments: list[dict[str, Any]]) -> MergedPlan:
    """
    Merge multiple fragments into a single MergedPlan.
    
    Performs deterministic merging of fragments with conflict detection.
    Each element is tracked to its source file for error reporting.
    
    Merge rules:
    1. version: Must be the same in all fragments (or absent)
    2. meta: Merge fields, conflict on different values for same key
    3. statuses: Merge dicts, duplicate key is an error
    4. nodes: Merge dicts, duplicate key is an error
    5. schedule.calendars: Merge dicts, duplicate key is an error
    6. schedule.nodes: Merge dicts, duplicate key is an error
    7. schedule.default_calendar: Must be in only one fragment
    8. views: Merge dicts, duplicate key is an error
    9. x: Merge dicts, duplicate key is an error
    
    Args:
        fragments: List of fragment dicts (from load_fragment)
        
    Returns:
        MergedPlan with all merged data and sources tracking
        
    Raises:
        MergeConflictError: When any merge conflict is detected
    
    Requirements:
        - 1.4: Conflict detection for duplicate node_id
        - 1.5: Conflict detection for duplicate status_id
        - 1.6: Meta block merging with conflict detection
        - 1.7: Schedule block merging (calendars and nodes)
        - 1.8: schedule.default_calendar conflict
        - 1.9: Return MergedPlan with all merged data
        - 1.10: Source tracking for each element
    
    Example:
        >>> f1 = load_fragment("main.yaml")
        >>> f2 = load_fragment("nodes.yaml")
        >>> plan = merge_fragments([f1, f2])
        >>> plan.sources["node:task1"]
        'nodes.yaml'
    """
    result = MergedPlan()
    sources: dict[str, str] = {}
    
    # Track version and default_calendar sources
    version_source: str | None = None
    default_calendar_source: str | None = None
    
    # Track meta field sources for conflict detection
    meta_sources: dict[str, str] = {}
    
    for fragment in fragments:
        source = fragment.get("_source", "<unknown>")
        
        # 1. Merge version
        if "version" in fragment:
            frag_version = fragment["version"]
            if version_source is not None and result.version != frag_version:
                raise MergeConflictError(
                    f"Version mismatch: {result.version} vs {frag_version}",
                    element_type="version",
                    files=[version_source, source],
                )
            result.version = frag_version
            version_source = source
        
        # 2. Merge meta (Requirement 1.6)
        if "meta" in fragment and fragment["meta"]:
            frag_meta = fragment["meta"]
            for key, value in frag_meta.items():
                existing_value = getattr(result.meta, key, None)
                if key in meta_sources and existing_value != value:
                    raise MergeConflictError(
                        f"Meta field '{key}' conflict: '{existing_value}' vs '{value}'",
                        element_type="meta",
                        element_id=key,
                        files=[meta_sources[key], source],
                    )
                setattr(result.meta, key, value)
                meta_sources[key] = source
                sources[f"meta:{key}"] = source
        
        # 3. Merge statuses (Requirement 1.5)
        if "statuses" in fragment and fragment["statuses"]:
            for status_id, status_data in fragment["statuses"].items():
                if status_id in result.statuses:
                    raise MergeConflictError(
                        f"Duplicate status_id '{status_id}'",
                        element_type="status",
                        element_id=status_id,
                        files=[sources[f"status:{status_id}"], source],
                    )
                result.statuses[status_id] = Status(
                    label=status_data.get("label", ""),
                    color=status_data.get("color"),
                )
                sources[f"status:{status_id}"] = source
        
        # 4. Merge nodes (Requirement 1.4)
        if "nodes" in fragment and fragment["nodes"]:
            for node_id, node_data in fragment["nodes"].items():
                if node_id in result.nodes:
                    raise MergeConflictError(
                        f"Duplicate node_id '{node_id}'",
                        element_type="node",
                        element_id=node_id,
                        files=[sources[f"node:{node_id}"], source],
                    )
                result.nodes[node_id] = Node(
                    title=node_data.get("title", ""),
                    kind=node_data.get("kind"),
                    status=node_data.get("status"),
                    parent=node_data.get("parent"),
                    after=node_data.get("after"),
                    milestone=node_data.get("milestone", False),
                    issue=node_data.get("issue"),
                    notes=node_data.get("notes"),
                    effort=node_data.get("effort"),
                    x=node_data.get("x"),
                )
                sources[f"node:{node_id}"] = source
        
        # 5-7. Merge schedule (Requirements 1.7, 1.8)
        if "schedule" in fragment and fragment["schedule"]:
            frag_schedule = fragment["schedule"]
            
            # Initialize schedule if not exists
            if result.schedule is None:
                result.schedule = Schedule()
            
            # 5. Merge calendars (Requirement 1.7)
            if "calendars" in frag_schedule and frag_schedule["calendars"]:
                for cal_id, cal_data in frag_schedule["calendars"].items():
                    if cal_id in result.schedule.calendars:
                        raise MergeConflictError(
                            f"Duplicate calendar_id '{cal_id}'",
                            element_type="calendar",
                            element_id=cal_id,
                            files=[sources[f"calendar:{cal_id}"], source],
                        )
                    result.schedule.calendars[cal_id] = Calendar(
                        excludes=cal_data.get("excludes", []),
                    )
                    sources[f"calendar:{cal_id}"] = source
            
            # 6. Merge schedule.nodes (Requirement 1.7)
            if "nodes" in frag_schedule and frag_schedule["nodes"]:
                for sn_id, sn_data in frag_schedule["nodes"].items():
                    if sn_id in result.schedule.nodes:
                        raise MergeConflictError(
                            f"Duplicate schedule node_id '{sn_id}'",
                            element_type="schedule_node",
                            element_id=sn_id,
                            files=[sources[f"schedule_node:{sn_id}"], source],
                        )
                    result.schedule.nodes[sn_id] = ScheduleNode(
                        start=sn_data.get("start"),
                        finish=sn_data.get("finish"),
                        duration=sn_data.get("duration"),
                        calendar=sn_data.get("calendar"),
                    )
                    sources[f"schedule_node:{sn_id}"] = source
            
            # 7. Check default_calendar (Requirement 1.8)
            if "default_calendar" in frag_schedule and frag_schedule["default_calendar"]:
                if default_calendar_source is not None:
                    raise MergeConflictError(
                        f"Multiple fragments define schedule.default_calendar",
                        element_type="default_calendar",
                        files=[default_calendar_source, source],
                    )
                result.schedule.default_calendar = frag_schedule["default_calendar"]
                default_calendar_source = source
                sources["schedule:default_calendar"] = source
        
        # 8. Merge views
        if "views" in fragment and fragment["views"]:
            for view_id, view_data in fragment["views"].items():
                if view_id in result.views:
                    raise MergeConflictError(
                        f"Duplicate view_id '{view_id}'",
                        element_type="view",
                        element_id=view_id,
                        files=[sources[f"view:{view_id}"], source],
                    )
                
                # Parse where filter if present
                where_filter = None
                if "where" in view_data and view_data["where"]:
                    where_data = view_data["where"]
                    where_filter = ViewFilter(
                        kind=where_data.get("kind"),
                        status=where_data.get("status"),
                        has_schedule=where_data.get("has_schedule"),
                        parent=where_data.get("parent"),
                    )
                
                result.views[view_id] = View(
                    title=view_data.get("title"),
                    where=where_filter,
                    order_by=view_data.get("order_by"),
                    group_by=view_data.get("group_by"),
                    lanes=view_data.get("lanes"),
                    date_format=view_data.get("date_format"),
                    axis_format=view_data.get("axis_format"),
                    tick_interval=view_data.get("tick_interval"),
                )
                sources[f"view:{view_id}"] = source
        
        # 9. Merge x (extensions)
        if "x" in fragment and fragment["x"]:
            for x_key, x_value in fragment["x"].items():
                if x_key in result.x:
                    raise MergeConflictError(
                        f"Duplicate extension key '{x_key}'",
                        element_type="x",
                        element_id=x_key,
                        files=[sources[f"x:{x_key}"], source],
                    )
                result.x[x_key] = x_value
                sources[f"x:{x_key}"] = source
    
    # Store sources in result (Requirement 1.10)
    result.sources = sources
    
    return result
