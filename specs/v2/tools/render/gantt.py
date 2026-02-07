"""
Gantt renderer for opskarta v2 plans.

This module generates Mermaid Gantt diagrams from MergedPlan objects.
It uses computed dates from the scheduler and applies view filtering
when a view_id is provided.

Key features:
- Generates Mermaid Gantt syntax
- Uses calendar from schedule for date calculations
- Applies view filtering (where) if view_id is provided
- Supports view format settings (date_format, axis_format, tick_interval)

Requirements covered:
- 5.4: render_gantt(plan: Merged_Plan, view_id: string) -> string
- 5.5: Use calendar from schedule for Gantt dates
"""

from typing import Optional

from specs.v2.tools.models import MergedPlan, View, ViewFilter
from specs.v2.tools.render.common import (
    apply_view_filter,
    get_descendants,
    escape_mermaid_string,
    sanitize_mermaid_text,
)


# Re-export for backward compatibility with existing test imports
def _get_descendants(plan: MergedPlan, parent_id: str) -> set[str]:
    """
    Get all descendants of a node (children, grandchildren, etc.).
    
    This is a wrapper for backward compatibility. Use get_descendants from common.py.
    
    Args:
        plan: MergedPlan containing nodes
        parent_id: ID of the parent node
        
    Returns:
        Set of descendant node IDs (not including parent itself)
    """
    return get_descendants(plan, parent_id)


def _escape_mermaid_title(title: str) -> str:
    """
    Escape and sanitize title for Mermaid syntax.
    
    Args:
        title: Original title string
        
    Returns:
        Escaped title safe for Mermaid
    """
    # First sanitize (remove colons etc), then escape special chars
    return escape_mermaid_string(sanitize_mermaid_text(title))


def _sanitize_task_id(node_id: str) -> str:
    """
    Sanitize node ID for use as Mermaid task ID.
    
    Mermaid task IDs should be simple identifiers.
    
    Args:
        node_id: Original node ID
        
    Returns:
        Sanitized task ID
    """
    # Replace dots and dashes with underscores for safer IDs
    result = node_id.replace(".", "_").replace("-", "_")
    return result


def render_gantt(plan: MergedPlan, view_id: str) -> str:
    """
    Generate a Mermaid Gantt diagram from a MergedPlan.
    
    This function creates a Mermaid Gantt diagram showing scheduled nodes
    with their computed dates. If a view_id is provided, the view's filter
    and format settings are applied.
    
    The function uses dates computed by the scheduler (computed_start,
    computed_finish) which are calculated using the calendar from schedule.
    
    Args:
        plan: MergedPlan with schedule and computed dates
        view_id: ID of the view to use for filtering and formatting
        
    Returns:
        Mermaid Gantt diagram as a string
        
    Raises:
        ValueError: If view_id is provided but view doesn't exist
        
    Requirements:
        - 5.4: render_gantt(plan: Merged_Plan, view_id: string) -> string
        - 5.5: Use calendar from schedule for Gantt dates
    
    Example output:
        ```mermaid
        gantt
            title Project Timeline
            dateFormat YYYY-MM-DD
            
            section Phase 1
            Task 1 :task1, 2024-03-01, 2024-03-05
            Task 2 :task2, 2024-03-06, 2024-03-10
        ```
    """
    lines: list[str] = []
    
    # Get view if specified
    view: Optional[View] = None
    if view_id:
        view = plan.views.get(view_id)
        if view is None:
            raise ValueError(f"View '{view_id}' not found")
    
    # Start Gantt diagram
    lines.append("gantt")
    
    # Add title from view or meta
    title = None
    if view and view.title:
        title = view.title
    elif plan.meta and plan.meta.title:
        title = plan.meta.title
    
    if title:
        lines.append(f"    title {_escape_mermaid_title(title)}")
    
    # Add date format (from view or default)
    date_format = "YYYY-MM-DD"
    if view and view.date_format:
        date_format = view.date_format
    lines.append(f"    dateFormat {date_format}")
    
    # Add axis format if specified in view
    if view and view.axis_format:
        lines.append(f"    axisFormat {view.axis_format}")
    
    # Add tick interval if specified in view
    if view and view.tick_interval:
        lines.append(f"    tickInterval {view.tick_interval}")
    
    lines.append("")
    
    # Get scheduled nodes with computed dates
    if plan.schedule is None:
        # No schedule, return empty Gantt
        return "\n".join(lines)
    
    # Get list of scheduled node IDs
    scheduled_node_ids = list(plan.schedule.nodes.keys())
    
    # Apply view filter if present
    if view and view.where:
        scheduled_node_ids = apply_view_filter(plan, scheduled_node_ids, view.where)
    
    # Filter to only nodes with computed dates
    nodes_with_dates = []
    for node_id in scheduled_node_ids:
        sn = plan.schedule.nodes.get(node_id)
        if sn and sn.computed_start and sn.computed_finish:
            nodes_with_dates.append(node_id)
    
    if not nodes_with_dates:
        # No nodes with dates to render
        return "\n".join(lines)
    
    # Group nodes by parent (section) or render flat
    if view and view.group_by == "parent":
        _render_grouped_by_parent(plan, nodes_with_dates, lines)
    elif view and view.lanes:
        _render_with_lanes(plan, nodes_with_dates, view.lanes, lines)
    else:
        _render_flat(plan, nodes_with_dates, lines)
    
    return "\n".join(lines)


def _render_flat(
    plan: MergedPlan,
    node_ids: list[str],
    lines: list[str]
) -> None:
    """
    Render nodes as a flat list without sections.
    
    Args:
        plan: MergedPlan with nodes and schedule
        node_ids: List of node IDs to render
        lines: Output lines list to append to
    """
    for node_id in node_ids:
        node = plan.nodes.get(node_id)
        sn = plan.schedule.nodes.get(node_id)
        
        if node is None or sn is None:
            continue
        
        title = _escape_mermaid_title(node.title)
        task_id = _sanitize_task_id(node_id)
        start = sn.computed_start
        finish = sn.computed_finish
        
        if node.milestone:
            # Milestones use milestone syntax
            lines.append(f"    {title} :{task_id}, milestone, {start}, 0d")
        else:
            # Regular tasks
            lines.append(f"    {title} :{task_id}, {start}, {finish}")


def _render_grouped_by_parent(
    plan: MergedPlan,
    node_ids: list[str],
    lines: list[str]
) -> None:
    """
    Render nodes grouped by parent as sections.
    
    Args:
        plan: MergedPlan with nodes and schedule
        node_ids: List of node IDs to render
        lines: Output lines list to append to
    """
    # Build parent -> children mapping for scheduled nodes
    parent_groups: dict[Optional[str], list[str]] = {}
    
    for node_id in node_ids:
        node = plan.nodes.get(node_id)
        if node is None:
            continue
        
        parent = node.parent
        if parent not in parent_groups:
            parent_groups[parent] = []
        parent_groups[parent].append(node_id)
    
    # Render each group as a section
    for parent_id, children in parent_groups.items():
        # Get section title
        if parent_id:
            parent_node = plan.nodes.get(parent_id)
            section_title = parent_node.title if parent_node else parent_id
        else:
            section_title = "Tasks"
        
        lines.append(f"    section {_escape_mermaid_title(section_title)}")
        
        for node_id in children:
            node = plan.nodes.get(node_id)
            sn = plan.schedule.nodes.get(node_id)
            
            if node is None or sn is None:
                continue
            
            title = _escape_mermaid_title(node.title)
            task_id = _sanitize_task_id(node_id)
            start = sn.computed_start
            finish = sn.computed_finish
            
            if node.milestone:
                lines.append(f"    {title} :{task_id}, milestone, {start}, 0d")
            else:
                lines.append(f"    {title} :{task_id}, {start}, {finish}")


def _render_with_lanes(
    plan: MergedPlan,
    node_ids: list[str],
    lanes: dict,
    lines: list[str]
) -> None:
    """
    Render nodes using lane configuration.
    
    Lanes define custom sections with specific nodes.
    
    Args:
        plan: MergedPlan with nodes and schedule
        node_ids: List of node IDs to render
        lanes: Lane configuration from view
        lines: Output lines list to append to
    """
    node_ids_set = set(node_ids)
    rendered_nodes = set()
    
    for lane_id, lane_config in lanes.items():
        lane_title = lane_config.get("title", lane_id)
        lane_nodes = lane_config.get("nodes", [])
        
        # Filter to only scheduled nodes in this lane
        lane_scheduled = [n for n in lane_nodes if n in node_ids_set]
        
        if not lane_scheduled:
            continue
        
        lines.append(f"    section {_escape_mermaid_title(lane_title)}")
        
        for node_id in lane_scheduled:
            node = plan.nodes.get(node_id)
            sn = plan.schedule.nodes.get(node_id)
            
            if node is None or sn is None:
                continue
            
            title = _escape_mermaid_title(node.title)
            task_id = _sanitize_task_id(node_id)
            start = sn.computed_start
            finish = sn.computed_finish
            
            if node.milestone:
                lines.append(f"    {title} :{task_id}, milestone, {start}, 0d")
            else:
                lines.append(f"    {title} :{task_id}, {start}, {finish}")
            
            rendered_nodes.add(node_id)
    
    # Render remaining nodes not in any lane
    remaining = [n for n in node_ids if n not in rendered_nodes]
    if remaining:
        lines.append("    section Other")
        for node_id in remaining:
            node = plan.nodes.get(node_id)
            sn = plan.schedule.nodes.get(node_id)
            
            if node is None or sn is None:
                continue
            
            title = _escape_mermaid_title(node.title)
            task_id = _sanitize_task_id(node_id)
            start = sn.computed_start
            finish = sn.computed_finish
            
            if node.milestone:
                lines.append(f"    {title} :{task_id}, milestone, {start}, 0d")
            else:
                lines.append(f"    {title} :{task_id}, {start}, {finish}")
