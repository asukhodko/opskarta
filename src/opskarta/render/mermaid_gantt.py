from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional

from ..errors import SchedulingError
from ..scheduling import ScheduledNode, compute_schedule

STATUS_TO_MERMAID_TAG = {
    "done": "done",
    "in_progress": "active",
    "blocked": "crit",
    "not_started": None,
}

STATUS_TO_EMOJI = {
    "done": "✅ ",
    "in_progress": "🔄 ",
    "blocked": "⛔ ",
    "not_started": "",
}


def _theme_vars_from_statuses(statuses: Dict[str, Any]) -> Dict[str, str]:
    # Fallback colors
    not_started = (statuses.get("not_started") or {}).get("color") or "#9ca3af"
    in_progress = (statuses.get("in_progress") or {}).get("color") or "#0ea5e9"
    done = (statuses.get("done") or {}).get("color") or "#22c55e"
    blocked = (statuses.get("blocked") or {}).get("color") or "#fecaca"

    return {
        "taskBkgColor": not_started,
        "taskBorderColor": "#4b5563",
        "taskTextColor": "#000000",
        "taskTextDarkColor": "#000000",
        "taskTextLightColor": "#000000",
        "activeTaskBkgColor": in_progress,
        "activeTaskBorderColor": in_progress,
        "doneTaskBkgColor": done,
        "doneTaskBorderColor": "#16a34a",
        "critBkgColor": blocked,
        "critBorderColor": blocked,
        "todayLineColor": "#ef4444",
    }


def render_mermaid_gantt(
    *,
    plan: Dict[str, Any],
    view: Dict[str, Any],
) -> str:
    title = view.get("title") or plan.get("meta", {}).get("title") or "opskarta gantt"
    date_format = view.get("date_format") or "YYYY-MM-DD"
    axis_format = view.get("axis_format")
    excludes = view.get("excludes") or []
    exclude_weekends = "weekends" in excludes

    nodes: Dict[str, Dict[str, Any]] = plan.get("nodes") or {}
    statuses: Dict[str, Any] = plan.get("statuses") or {}

    schedule = compute_schedule(nodes, exclude_weekends=exclude_weekends)

    theme_vars = _theme_vars_from_statuses(statuses)
    theme_init = {
        "theme": "base",
        "themeVariables": theme_vars,
    }

    lines: List[str] = []
    lines.append("```mermaid")
    lines.append(f"%%{{init: {theme_init} }}%%")
    lines.append("")
    lines.append("gantt")
    lines.append(f"    title {title}")
    lines.append(f"    dateFormat  {date_format}")
    if axis_format:
        lines.append(f"    axisFormat  {axis_format}")
    if exclude_weekends:
        lines.append("    excludes weekends")
    lines.append("")

    lanes = view.get("lanes") or {}
    for lane_id, lane in lanes.items():
        lane_title = lane.get("title") or lane_id
        lines.append(f"    section {lane_title}")

        lane_nodes: List[str] = lane.get("nodes") or []
        for node_id in lane_nodes:
            if node_id not in nodes:
                raise SchedulingError(f"View references unknown node: {node_id}")

            node = nodes[node_id]
            node_title = node.get("title") or node_id
            status = node.get("status")
            emoji = STATUS_TO_EMOJI.get(status, "")
            mermaid_tag = STATUS_TO_MERMAID_TAG.get(status)

            # schedule might be missing if node has no scheduling info (container). Try best effort.
            sched: Optional[ScheduledNode] = schedule.get(node_id)
            if sched is None:
                # No explicit start; try to skip silently.
                continue

            start_str = sched.start.isoformat()
            duration = f"{sched.duration_days}d"

            if mermaid_tag:
                lines.append(f"    {emoji}{node_title}  :{mermaid_tag}, {node_id}, {start_str}, {duration}")
            else:
                lines.append(f"    {emoji}{node_title}  :{node_id}, {start_str}, {duration}")

        lines.append("")

    lines.append("```")
    lines.append("")
    return "\n".join(lines)
