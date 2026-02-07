"""
Data models for opskarta v2.

This module defines the core data structures for the opskarta v2 specification,
implementing the "overlay schedule" concept where work structure (nodes) is
separated from calendar scheduling (schedule).

Key concepts:
- Node: Work item without calendar fields (dates moved to Schedule)
- Schedule: Optional layer for calendar planning
- View: Pure visualization configuration (no effect on scheduling)
- MergedPlan: Result of merging multiple plan fragments

Requirements covered:
- 2.1, 2.2, 2.3: Node structure and fields
- 3.3, 3.4, 3.5, 3.6, 3.8: Schedule and Calendar structure
- 4.3, 4.4, 4.5: View and ViewFilter structure
"""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class Meta:
    """
    Plan metadata.
    
    Contains identification and display information for the plan,
    as well as configuration for effort units.
    
    Attributes:
        id: Unique identifier for the plan (used for views.project matching)
        title: Human-readable title of the plan
        effort_unit: Display unit for effort values (e.g., "sp", "points", "дни")
                     Only affects UI display, not calculations
    
    Requirements: 2.10 (effort_unit for UI display)
    """
    id: Optional[str] = None
    title: Optional[str] = None
    effort_unit: Optional[str] = None


@dataclass
class Status:
    """
    Status definition for nodes.
    
    Defines a status that can be assigned to nodes, with display properties.
    
    Attributes:
        label: Human-readable label for the status
        color: Hex color code for display (format: #RRGGBB)
    """
    label: str
    color: Optional[str] = None


@dataclass
class Node:
    """
    Work item in the plan structure (v2).
    
    Represents a unit of work without calendar fields. In v2, scheduling
    information (start, finish, duration) is moved to Schedule.nodes.
    
    Attributes:
        title: Required. Human-readable title of the node
        kind: Optional type/category (e.g., "summary", "phase", "epic", "task")
        status: Optional reference to a status_id defined in statuses
        parent: Optional reference to parent node_id for hierarchy
        after: Optional list of node_ids this node depends on
        milestone: Whether this node is a milestone (default: False)
        issue: Optional issue tracker reference
        notes: Optional notes/description
        effort: Optional effort estimate in abstract units (number >= 0)
        x: Optional extension data (arbitrary key-value pairs)
        
        # Computed fields (not stored in YAML, calculated by validator):
        effort_rollup: Sum of effort_effective of all direct children
        effort_effective: effort if set, otherwise effort_rollup
        effort_gap: max(0, effort - effort_rollup) - shows incomplete decomposition
    
    Requirements:
        - 2.1: title is required
        - 2.2: optional fields (kind, status, parent, after, milestone, issue, notes, x)
        - 2.3: effort field for abstract effort estimation
        - 2.4: NO start, finish, duration, excludes (moved to Schedule)
    """
    title: str
    kind: Optional[str] = None
    status: Optional[str] = None
    parent: Optional[str] = None
    after: Optional[list[str]] = None
    milestone: bool = False
    issue: Optional[str] = None
    notes: Optional[str] = None
    effort: Optional[float] = None
    x: Optional[dict[str, Any]] = None
    
    # Computed fields (not stored in YAML)
    effort_rollup: Optional[float] = None
    effort_effective: Optional[float] = None
    effort_gap: Optional[float] = None


@dataclass
class Calendar:
    """
    Calendar definition for scheduling.
    
    Defines working days by specifying exclusions (non-working days).
    
    Attributes:
        excludes: List of exclusions. Can contain:
                  - "weekends": exclude Saturday and Sunday
                  - "YYYY-MM-DD": exclude specific date
    
    Requirements: 3.4 (excludes field with weekends and dates)
    """
    excludes: list[str] = field(default_factory=list)


@dataclass
class ScheduleNode:
    """
    Scheduling information for a node.
    
    Contains calendar-related fields for a specific node. Only nodes
    present in Schedule.nodes participate in schedule calculation.
    
    Note: Dependencies (after) are defined in Node, not here.
    
    Attributes:
        start: Optional start date (YYYY-MM-DD format)
        finish: Optional finish date (YYYY-MM-DD format)
        duration: Optional duration (Nd for days, Nw for weeks)
        calendar: Optional reference to calendar_id in Schedule.calendars
                  If not set, Schedule.default_calendar is used
        
        # Computed fields (set by scheduler):
        computed_start: Calculated start date
        computed_finish: Calculated finish date
    
    Requirements: 3.8 (start, finish, duration, calendar fields)
    """
    start: Optional[str] = None
    finish: Optional[str] = None
    duration: Optional[str] = None
    calendar: Optional[str] = None
    
    # Computed fields (set by scheduler)
    computed_start: Optional[str] = None
    computed_finish: Optional[str] = None


@dataclass
class Schedule:
    """
    Calendar scheduling layer.
    
    Optional top-level block that adds calendar planning to the plan.
    A plan without schedule is valid and can be rendered as tree/list/deps.
    
    Attributes:
        calendars: Dictionary of calendar_id -> Calendar definitions
        default_calendar: Optional reference to default calendar_id
                          Used when ScheduleNode.calendar is not set
        nodes: Dictionary of node_id -> ScheduleNode
               Only nodes present here participate in schedule calculation
        
        # Runtime fields:
        warnings: List of scheduling warnings (e.g., unschedulable nodes)
    
    Requirements:
        - 3.3: calendars block
        - 3.5: default_calendar field
        - 3.6: nodes block with schedule information
    """
    calendars: dict[str, Calendar] = field(default_factory=dict)
    default_calendar: Optional[str] = None
    nodes: dict[str, ScheduleNode] = field(default_factory=dict)
    
    # Runtime fields
    warnings: list[str] = field(default_factory=list)


@dataclass
class ViewFilter:
    """
    Structural filter for node selection in views.
    
    Defines criteria for filtering nodes in a view. All specified
    conditions must be satisfied (AND logic).
    
    Attributes:
        kind: Filter by node.kind (node must have kind in this list)
        status: Filter by node.status (node must have status in this list)
        has_schedule: Filter by scheduling status:
                      True = only nodes in schedule.nodes
                      False = only nodes NOT in schedule.nodes
                      None = no filtering by schedule
        parent: Filter to descendants of specified node_id
    
    Requirements: 4.3 (where filter with kind, status, has_schedule, parent)
    """
    kind: Optional[list[str]] = None
    status: Optional[list[str]] = None
    has_schedule: Optional[bool] = None
    parent: Optional[str] = None


@dataclass
class View:
    """
    View configuration for visualization.
    
    Defines how to display the plan. Views are pure visualization
    and do not affect schedule calculation.
    
    Note: excludes field is NOT allowed in v2 views (moved to Schedule.calendars)
    
    Attributes:
        title: Optional display title for the view
        where: Optional structural filter for node selection
        order_by: Optional field name for sorting nodes
        group_by: Optional field name for grouping nodes
        lanes: Optional lane configuration for Gantt views
               Dictionary of lane_id -> lane config with title and nodes
        
        # Format settings (primarily for Gantt):
        date_format: Date format string for display
        axis_format: Axis format string for Gantt
        tick_interval: Tick interval for Gantt axis
    
    Requirements:
        - 4.2: NO excludes field (moved to Schedule)
        - 4.4: order_by for sorting
        - 4.5: group_by and lanes for grouping
    """
    title: Optional[str] = None
    where: Optional[ViewFilter] = None
    order_by: Optional[str] = None
    group_by: Optional[str] = None
    lanes: Optional[dict[str, Any]] = None
    
    # Format settings (for Gantt)
    date_format: Optional[str] = None
    axis_format: Optional[str] = None
    tick_interval: Optional[str] = None


@dataclass
class MergedPlan:
    """
    Result of merging multiple plan fragments.
    
    Contains all data from merged fragments plus metadata about
    the source of each element for error reporting.
    
    Attributes:
        version: Plan format version (must be 2 for v2)
        meta: Plan metadata (merged from fragments)
        statuses: Dictionary of status_id -> Status definitions
        nodes: Dictionary of node_id -> Node definitions
        schedule: Optional scheduling layer
        views: Dictionary of view_id -> View definitions
        x: Extension data (arbitrary key-value pairs)
        
        # Merge metadata:
        sources: Dictionary mapping element_id to source file path
                 Format: "type:id" -> "file_path"
                 Example: "node:task1" -> "nodes.plan.yaml"
    
    Requirements:
        - 1.9: Merged plan with all data from fragments
        - 1.10: Source tracking for each element
    """
    version: int = 2
    meta: Meta = field(default_factory=Meta)
    statuses: dict[str, Status] = field(default_factory=dict)
    nodes: dict[str, Node] = field(default_factory=dict)
    schedule: Optional[Schedule] = None
    views: dict[str, View] = field(default_factory=dict)
    x: dict[str, Any] = field(default_factory=dict)
    
    # Merge metadata
    sources: dict[str, str] = field(default_factory=dict)
