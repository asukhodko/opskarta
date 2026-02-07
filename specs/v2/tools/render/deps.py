"""
Dependency graph renderer for opskarta v2 plans.

This module generates Mermaid flowchart representations showing
dependency relationships between nodes. Dependencies are defined
in the node.after field.

Key features:
- Mermaid flowchart LR (left-to-right) format
- Shows "after" relationships as arrows (dependency --> dependent)
- Applies view filtering (where) if view_id is provided

Requirements covered:
- 5.8: render_deps(plan: Merged_Plan, view_id: Optional[string]) -> string
- 5.9: Apply filtering from view if view_id is provided

Example output:
    flowchart LR
        task1["Task 1"]
        task2["Task 2"]
        task3["Task 3"]
        task1 --> task2
        task2 --> task3
"""

from typing import Optional

from specs.v2.tools.models import MergedPlan, View
from specs.v2.tools.render.common import (
    apply_view_filter,
    escape_mermaid_string,
    sanitize_mermaid_text,
)


def _escape_mermaid_label(text: str) -> str:
    """
    Escape and sanitize text for Mermaid labels.
    
    Args:
        text: The label text to escape
        
    Returns:
        Escaped label text safe for Mermaid
    """
    # First sanitize (remove colons etc), then escape special chars
    return escape_mermaid_string(sanitize_mermaid_text(text))


def _sanitize_node_id(node_id: str) -> str:
    """
    Sanitize node ID for use in Mermaid.
    
    Mermaid node IDs should be alphanumeric with underscores.
    Replace any problematic characters.
    
    Args:
        node_id: The original node ID
        
    Returns:
        Sanitized node ID safe for Mermaid
    """
    # Replace dots and hyphens with underscores
    # Keep alphanumeric and underscores
    result = []
    for char in node_id:
        if char.isalnum() or char == "_":
            result.append(char)
        else:
            result.append("_")
    return "".join(result)


def render_deps(plan: MergedPlan, view_id: Optional[str] = None) -> str:
    """
    Generate a Mermaid flowchart showing dependency relationships.
    
    This function creates a Mermaid flowchart diagram showing nodes
    and their dependencies (after relationships). Arrows point from
    the dependency to the dependent node (A --> B means B depends on A).
    
    Args:
        plan: MergedPlan with nodes
        view_id: Optional ID of the view to use for filtering
        
    Returns:
        Mermaid flowchart as a string
        
    Raises:
        ValueError: If view_id is provided but view doesn't exist
        
    Requirements:
        - 5.8: render_deps(plan: Merged_Plan, view_id: Optional[string]) -> string
        - 5.9: Apply filtering from view if view_id is provided
    
    Example output:
        flowchart LR
            task1["Task 1"]
            task2["Task 2"]
            task3["Task 3"]
            task1 --> task2
            task2 --> task3
    """
    lines: list[str] = []
    
    # Get view if specified
    view: Optional[View] = None
    if view_id:
        view = plan.views.get(view_id)
        if view is None:
            raise ValueError(f"View '{view_id}' not found")
    
    # Get all node IDs
    all_node_ids = list(plan.nodes.keys())
    
    # Apply view filter if present
    if view and view.where:
        filtered_ids = set(apply_view_filter(plan, all_node_ids, view.where))
    else:
        filtered_ids = set(all_node_ids)
    
    # If no nodes pass filter, return empty flowchart
    if not filtered_ids:
        return "flowchart LR"
    
    # Start the flowchart
    lines.append("flowchart LR")
    
    # Collect edges (dependency relationships)
    edges: list[tuple[str, str]] = []
    
    # Add node definitions and collect edges
    for node_id in sorted(filtered_ids):
        node = plan.nodes.get(node_id)
        if node is None:
            continue
        
        # Create node definition with label
        safe_id = _sanitize_node_id(node_id)
        safe_label = _escape_mermaid_label(node.title)
        lines.append(f'    {safe_id}["{safe_label}"]')
        
        # Collect edges from after dependencies
        if node.after:
            for dep_id in node.after:
                # Only include edge if both nodes are in filtered set
                if dep_id in filtered_ids:
                    edges.append((dep_id, node_id))
    
    # Add edges (dependency --> dependent)
    for dep_id, node_id in edges:
        safe_dep_id = _sanitize_node_id(dep_id)
        safe_node_id = _sanitize_node_id(node_id)
        lines.append(f"    {safe_dep_id} --> {safe_node_id}")
    
    return "\n".join(lines)
