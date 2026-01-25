from __future__ import annotations

from typing import Any, Dict

from .errors import ValidationError


def validate_plan(plan: Dict[str, Any]) -> None:
    if plan.get("version") != 1:
        raise ValidationError("plan.version must be 1 (for now)")

    meta = plan.get("meta")
    if not isinstance(meta, dict):
        raise ValidationError("plan.meta must be an object")

    if not meta.get("id") or not isinstance(meta.get("id"), str):
        raise ValidationError("plan.meta.id must be a non-empty string")

    if not meta.get("title") or not isinstance(meta.get("title"), str):
        raise ValidationError("plan.meta.title must be a non-empty string")

    nodes = plan.get("nodes")
    if not isinstance(nodes, dict) or not nodes:
        raise ValidationError("plan.nodes must be a non-empty object mapping node_id -> node")

    for node_id, node in nodes.items():
        if not isinstance(node_id, str) or not node_id:
            raise ValidationError("node_id keys must be non-empty strings")

        if not isinstance(node, dict):
            raise ValidationError(f"nodes.{node_id} must be an object")

        if not node.get("title") or not isinstance(node.get("title"), str):
            raise ValidationError(f"nodes.{node_id}.title must be a non-empty string")

        parent = node.get("parent")
        if parent is not None and not isinstance(parent, str):
            raise ValidationError(f"nodes.{node_id}.parent must be a string if present")

        after = node.get("after")
        if after is not None:
            if not isinstance(after, list) or not all(isinstance(x, str) for x in after):
                raise ValidationError(f"nodes.{node_id}.after must be a list of strings if present")


def validate_views(views: Dict[str, Any], project_id: str) -> None:
    if views.get("version") != 1:
        raise ValidationError("views.version must be 1 (for now)")

    if views.get("project") != project_id:
        raise ValidationError(f"views.project must equal plan.meta.id ({project_id})")

    gantt_views = views.get("gantt_views")
    if gantt_views is None:
        return
    if not isinstance(gantt_views, dict):
        raise ValidationError("views.gantt_views must be an object if present")

    for view_id, view in gantt_views.items():
        if not isinstance(view, dict):
            raise ValidationError(f"gantt_views.{view_id} must be an object")

        lanes = view.get("lanes")
        if lanes is None or not isinstance(lanes, dict) or not lanes:
            raise ValidationError(f"gantt_views.{view_id}.lanes must be a non-empty object")

        for lane_id, lane in lanes.items():
            if not isinstance(lane, dict):
                raise ValidationError(f"gantt_views.{view_id}.lanes.{lane_id} must be an object")
            nodes = lane.get("nodes")
            if nodes is None or not isinstance(nodes, list) or not all(isinstance(x, str) for x in nodes):
                raise ValidationError(
                    f"gantt_views.{view_id}.lanes.{lane_id}.nodes must be a list of node ids"
                )
