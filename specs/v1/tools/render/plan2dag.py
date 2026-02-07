#!/usr/bin/env python3
"""
plan2dag: Mermaid flowchart (DAG + parent decomposition) from opskarta v1 plan.yaml.

Features:
- Extended validation per opskarta v1 (types, date/duration/color formats);
- Warnings for after-chains without anchor (no start/finish/end in closure);
- Supports owner as non-core: reads node.x.owner if present, otherwise node.owner (for backward compatibility).
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from datetime import date, datetime
from typing import Any, Dict, Optional, Set, List

import yaml

DATE_FMT = "%Y-%m-%d"
RE_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
RE_DURATION = re.compile(r"^[1-9][0-9]*[dw]$")
RE_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")


# ---------- YAML loader with duplicate key detection ----------

class UniqueKeyLoader(yaml.SafeLoader):
    """YAML loader that raises an exception on duplicate keys."""

    def construct_mapping(self, node, deep: bool = False):  # type: ignore[override]
        mapping = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if key in mapping:
                raise yaml.constructor.ConstructorError(
                    None, None, f"duplicate key: {key}", key_node.start_mark
                )
            value = self.construct_object(value_node, deep=deep)
            mapping[key] = value
        return mapping


def load_yaml(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.load(f, Loader=UniqueKeyLoader)
    if not isinstance(data, dict):
        raise ValueError("plan must be a mapping/object")
    return data


# ---------- Normalization / parsing helpers ----------

def _parse_date(value: Any, path: str) -> None:
    """Validates that the value is a correct date (string YYYY-MM-DD or YAML date/datetime)."""
    if isinstance(value, datetime):
        return
    if isinstance(value, date) and not isinstance(value, datetime):
        return
    if isinstance(value, str):
        s = value.strip()
        if not RE_DATE.match(s):
            raise ValueError(f"{path}: invalid date format {value!r}, expected YYYY-MM-DD")
        try:
            datetime.strptime(s, DATE_FMT)
        except Exception:
            raise ValueError(f"{path}: invalid date value {value!r}")
        return
    raise ValueError(f"{path}: invalid date type {type(value).__name__}")


def _parse_duration(value: Any, path: str) -> None:
    if not isinstance(value, str):
        raise ValueError(f"{path}: duration must be string like '5d' or '2w'")
    s = value.strip()
    if not RE_DURATION.match(s):
        raise ValueError(f"{path}: invalid duration format {value!r}, expected ^[1-9][0-9]*[dw]$")


def escape_mermaid_string(text: str) -> str:
    """
    Escape text for Mermaid flowchart labels inside ["..."].

    Mermaid flowchart does NOT reliably support backslash-escaped quotes (\")
    across renderers. Use Mermaid entity codes instead:
      - "  -> #quot;
      - #  -> #35;  (so it doesn't start an entity by accident)
    """
    return text.replace("#", "#35;").replace('"', "#quot;")


# ---------- Plan validation ----------

def validate_plan(plan: Dict[str, Any]) -> List[str]:
    """
    Returns a list of warnings.
    Errors are raised as exceptions.
    """
    warnings: List[str] = []

    if "version" not in plan:
        raise ValueError("plan missing required field 'version'")
    if not isinstance(plan["version"], int):
        raise ValueError("plan.version must be int")
    if plan["version"] != 1:
        raise ValueError(f"unsupported plan.version {plan['version']}, expected 1")

    nodes = plan.get("nodes")
    if not isinstance(nodes, dict):
        raise ValueError("plan missing required mapping 'nodes'")

    statuses = plan.get("statuses") or {}
    if statuses and not isinstance(statuses, dict):
        raise ValueError("plan.statuses must be mapping/object")

    # validate statuses
    for st_id, st in statuses.items():
        if not isinstance(st_id, str):
            raise ValueError("plan.statuses: keys must be strings")
        if st is None:
            continue
        if not isinstance(st, dict):
            raise ValueError(f"plan.statuses.{st_id} must be mapping/object")
        color = st.get("color")
        if color is not None:
            if not isinstance(color, str) or not RE_COLOR.match(color.strip()):
                raise ValueError(f"plan.statuses.{st_id}.color invalid: {color!r}, expected ^#[0-9a-fA-F]{{6}}$")

    uses_status = False

    # validate nodes
    for node_id, node in nodes.items():
        if not isinstance(node_id, str):
            raise ValueError(f"plan.nodes: node_id keys must be strings (got {type(node_id).__name__}: {node_id!r})")
        if not isinstance(node, dict):
            raise ValueError(f"node '{node_id}' must be a mapping/object")

        if "title" not in node or not isinstance(node.get("title"), str) or not node["title"].strip():
            raise ValueError(f"node '{node_id}' missing required non-empty field 'title'")

        # optional string fields
        for f in ("kind", "status", "parent", "issue"):
            if f in node and node[f] is not None and not isinstance(node[f], str):
                raise ValueError(f"nodes.{node_id}.{f} must be string if present")

        # notes
        if "notes" in node and node["notes"] is not None and not isinstance(node["notes"], str):
            raise ValueError(f"nodes.{node_id}.notes must be string if present")

        # milestone
        if "milestone" in node and node["milestone"] is not None and not isinstance(node["milestone"], bool):
            raise ValueError(f"nodes.{node_id}.milestone must be boolean if present")

        # dates
        for df in ("start", "finish", "end"):
            if df in node and node[df] is not None:
                _parse_date(node[df], f"nodes.{node_id}.{df}")

        # duration
        if "duration" in node and node["duration"] is not None:
            _parse_duration(node["duration"], f"nodes.{node_id}.duration")

        # after
        after = node.get("after") or []
        if "after" in node and node["after"] is not None:
            if not isinstance(after, list):
                raise ValueError(f"nodes.{node_id}.after must be list[string]")
            for i, dep in enumerate(after):
                if not isinstance(dep, str):
                    raise ValueError(f"nodes.{node_id}.after[{i}] must be string node_id")

        st = node.get("status")
        if st:
            uses_status = True
            if not statuses or st not in statuses:
                raise ValueError(f"node '{node_id}' references unknown status '{st}'")

        parent = node.get("parent")
        if parent:
            if parent not in nodes:
                raise ValueError(f"node '{node_id}' has unknown parent '{parent}'")

        for dep in after:
            if dep not in nodes:
                raise ValueError(f"node '{node_id}' has unknown dependency '{dep}' in after")

    if uses_status and not statuses:
        raise ValueError("statuses section is required when nodes specify a status")

    # cycles
    _detect_parent_cycles(nodes)
    _detect_after_cycles(nodes)

    # after-chain anchor warnings
    warnings.extend(_warn_after_chains_without_anchor(nodes))

    return warnings


def _detect_parent_cycles(nodes: Dict[str, Any]) -> None:
    visited: Set[str] = set()
    rec: Set[str] = set()

    def dfs(nid: str) -> None:
        visited.add(nid)
        rec.add(nid)
        parent = nodes[nid].get("parent")
        if parent:
            if parent not in visited:
                dfs(parent)
            elif parent in rec:
                raise ValueError("cycle detected in parent relationships")
        rec.remove(nid)

    for nid in nodes:
        if nid not in visited:
            dfs(nid)


def _detect_after_cycles(nodes: Dict[str, Any]) -> None:
    visited: Set[str] = set()
    rec: Set[str] = set()

    def dfs(nid: str) -> None:
        visited.add(nid)
        rec.add(nid)
        for dep in nodes[nid].get("after") or []:
            if dep not in visited:
                dfs(dep)
            elif dep in rec:
                raise ValueError("cycle detected in after dependencies")
        rec.remove(nid)

    for nid in nodes:
        if nid not in visited:
            dfs(nid)


def _warn_after_chains_without_anchor(nodes: Dict[str, Any]) -> List[str]:
    warnings: List[str] = []
    memo: Dict[str, bool] = {}
    visiting: Set[str] = set()

    def has_anchor(nid: str) -> bool:
        if nid in memo:
            return memo[nid]
        if nid in visiting:
            return True
        visiting.add(nid)
        node = nodes.get(nid, {}) if isinstance(nodes.get(nid), dict) else {}
        if node.get("start") is not None or node.get("finish") is not None or node.get("end") is not None:
            memo[nid] = True
        else:
            anchored = False
            for dep in node.get("after") or []:
                if has_anchor(dep):
                    anchored = True
                    break
            memo[nid] = anchored
        visiting.remove(nid)
        return memo[nid]

    for nid, node in nodes.items():
        if not isinstance(node, dict):
            continue
        if node.get("after") and not has_anchor(nid):
            warnings.append(
                f"nodes.{nid}.after: dependency chain has no anchor (no start/finish/end in closure) -> nodes will be unscheduled in Gantt"
            )

    return warnings


# ---------- Parent / children hierarchy ----------

def build_children_map(plan: Dict[str, Any]) -> Dict[str, list]:
    nodes = plan.get("nodes") or {}
    children: Dict[str, list] = defaultdict(list)
    for node_id, node in nodes.items():
        parent = node.get("parent") if isinstance(node, dict) else None
        if parent:
            children[parent].append(node_id)
    return children


def find_roots(plan: Dict[str, Any]) -> List[str]:
    nodes = plan.get("nodes") or {}
    roots = []
    for node_id, node in nodes.items():
        parent = node.get("parent") if isinstance(node, dict) else None
        if not parent or parent not in nodes:
            roots.append(node_id)
    return roots


# ---------- Status-based colors ----------

def build_status_classes(plan: Dict[str, Any]) -> Dict[str, str]:
    default_map = {
        "not_started": "#9ca3af",
        "in_progress": "#0ea5e9",
        "done": "#22c55e",
        "blocked": "#fecaca",
        "planned": "#aad2e6",
    }
    statuses = plan.get("statuses") or {}
    result: Dict[str, str] = {}
    for status_id, data in statuses.items():
        color = None
        if isinstance(data, dict):
            color = data.get("color")
        if isinstance(color, str) and RE_COLOR.match(color.strip()):
            result[status_id] = color.strip()
        else:
            result[status_id] = default_map.get(status_id, "#e5e7eb")
    return result


# ---------- Text wrapping ----------

def wrap_text(text: str, width: int) -> str:
    if width <= 0:
        return text
    words = text.split()
    if not words:
        return text
    lines = []
    current = words[0]
    for w in words[1:]:
        if len(current) + 1 + len(w) <= width:
            current += " " + w
        else:
            lines.append(current)
            current = w
    lines.append(current)
    return "<br/>".join(lines)


def sanitize_mermaid_text(text: str) -> str:
    """
    На всякий случай чистим двоеточия из человеко-читаемых заголовков/лейблов.
    (Иногда Mermaid flowchart тоже капризничает в subgraph titles.)
    """
    cleaned = text.replace(":", " ").replace("：", " ")
    return " ".join(cleaned.split())


# ---------- Node label ----------

STATUS_EMOJI_PREFIX = {
    "done": "✅",
    "in_progress": "🔄",
    "blocked": "⛔",
}


def get_owner(node: Dict[str, Any]) -> Optional[str]:
    x = node.get("x")
    if isinstance(x, dict) and isinstance(x.get("owner"), str):
        return x.get("owner")
    if isinstance(node.get("owner"), str):  # legacy/non-core
        return node.get("owner")
    return None


def make_node_label(node: Dict[str, Any], node_id: str, wrap_col: Optional[int] = None) -> str:
    title = sanitize_mermaid_text(str(node.get("title", node_id)))
    issue = str(node.get("issue", node_id))
    status = (node.get("status") or "").strip()
    emoji = STATUS_EMOJI_PREFIX.get(status)
    if emoji:
        title = f"{emoji} {title}"
    if wrap_col and wrap_col > 0:
        title = wrap_text(title, wrap_col)

    owner = get_owner(node)
    parts = [title]
    if issue and issue != node_id:
        parts.append(issue)
    if owner:
        owner_text = f"(owner: {owner})"
        if wrap_col and wrap_col > 0:
            owner_text = wrap_text(owner_text, wrap_col)
        parts.append(owner_text)

    label = "<br/>".join(parts)
    label = escape_mermaid_string(label)
    return label


# ---------- DAG generation ----------

def render_dag_mermaid(
    plan: Dict[str, Any],
    direction: str = "LR",
    wrap_col: Optional[int] = None,
    only_tracks: Optional[Set[str]] = None,
) -> str:
    nodes = plan.get("nodes") or {}
    if not nodes:
        raise ValueError("plan.nodes is empty")

    children_map = build_children_map(plan)
    roots = find_roots(plan)
    if not roots:
        raise ValueError("no root nodes found (nodes without parent)")

    status_colors = build_status_classes(plan)

    # which tracks were requested via --track
    requested_tracks: Set[str] = set()
    if only_tracks:
        requested_tracks = {t for t in only_tracks if t in nodes}
        if not requested_tracks:
            raise ValueError(f"none of requested tracks exist in plan: {sorted(only_tracks)}")

    squash_tracks: Set[str] = requested_tracks if len(requested_tracks) == 1 else set()

    # determine visible nodes
    if requested_tracks:
        visible_nodes: Set[str] = set()
        # track + its ancestors
        for tid in requested_tracks:
            cur = tid
            seen: Set[str] = set()
            while True:
                if cur in seen:
                    break
                seen.add(cur)
                visible_nodes.add(cur)
                parent = nodes.get(cur, {}).get("parent")
                if not parent or parent not in nodes:
                    break
                cur = parent
        # plus all descendants
        stack = list(requested_tracks)
        while stack:
            nid = stack.pop()
            for child in children_map.get(nid, []):
                if child not in visible_nodes:
                    visible_nodes.add(child)
                    stack.append(child)
    else:
        visible_nodes = set(nodes.keys())

    lines: List[str] = []
    lines.append(f"flowchart {direction}")
    lines.append("")

    # classDef by status
    for status_id, color in status_colors.items():
        lines.append(f"  classDef {status_id} fill:{color},stroke:#4b5563,color:#000;")
    if status_colors:
        lines.append("")

    declared_nodes: Set[str] = set()

    # root nodes
    for root_id in roots:
        if root_id not in visible_nodes:
            continue
        root_node = nodes.get(root_id, {})
        label = make_node_label(root_node, root_id, wrap_col)
        status = root_node.get("status")
        if status and status in status_colors:
            lines.append(f"  {root_id}[\"{label}\"]:::{status}")
        else:
            lines.append(f"  {root_id}[\"{label}\"]")
        declared_nodes.add(root_id)
    if any(r in visible_nodes for r in roots):
        lines.append("")

    def emit_children(parent_id: str, indent: str) -> None:
        child_ids = [cid for cid in children_map.get(parent_id, []) if cid in visible_nodes]
        child_ids.sort(key=lambda cid: str(nodes[cid].get("title", cid)))
        for cid in child_ids:
            node = nodes[cid]
            grand_children = [gc for gc in children_map.get(cid, []) if gc in visible_nodes]
            has_children = bool(grand_children)
            if has_children:
                sg_id = f"sg_{cid}"
                sg_title = escape_mermaid_string(sanitize_mermaid_text(str(node.get("title", cid))))
                lines.append(f"{indent}subgraph {sg_id}[\"{sg_title}\"]")
                label = make_node_label(node, cid, wrap_col)
                status = node.get("status")
                if status and status in status_colors:
                    lines.append(f"{indent}  {cid}[\"{label}\"]:::{status}")
                else:
                    lines.append(f"{indent}  {cid}[\"{label}\"]")
                declared_nodes.add(cid)
                emit_children(cid, indent + "  ")
                lines.append(f"{indent}end")
            else:
                if cid in declared_nodes:
                    continue
                label = make_node_label(node, cid, wrap_col)
                status = node.get("status")
                if status and status in status_colors:
                    lines.append(f"{indent}{cid}[\"{label}\"]:::{status}")
                else:
                    lines.append(f"{indent}{cid}[\"{label}\"]")
                declared_nodes.add(cid)

    for root_id in roots:
        if root_id not in visible_nodes:
            continue
        track_ids = [tid for tid in children_map.get(root_id, []) if tid in visible_nodes]
        for track_id in track_ids:
            track_node = nodes.get(track_id)
            if track_node is None:
                continue
            if track_id in squash_tracks:
                emit_children(track_id, "  ")
                lines.append("")
            else:
                track_title = escape_mermaid_string(sanitize_mermaid_text(str(track_node.get("title", track_id))))
                lines.append(f"  subgraph {track_id}[\"{track_title}\"]")
                emit_children(track_id, "    ")
                lines.append("  end")
                lines.append("")
            declared_nodes.add(track_id)

    # nodes outside subgraphs
    for nid, node in nodes.items():
        if nid not in visible_nodes:
            continue
        if nid in declared_nodes:
            continue
        if nid in squash_tracks:
            continue
        label = make_node_label(node, nid, wrap_col)
        status = node.get("status")
        if status and status in status_colors:
            lines.append(f"  {nid}[\"{label}\"]:::{status}")
        else:
            lines.append(f"  {nid}[\"{label}\"]")
        declared_nodes.add(nid)

    if any(nid not in declared_nodes for nid in visible_nodes):
        lines.append("")

    incoming_after: Dict[str, list] = defaultdict(list)
    for nid, node in nodes.items():
        for dep_id in node.get("after") or []:
            incoming_after[nid].append(dep_id)

    # parent arrows (dashed) - structure: parent decomposition
    lines.append("  %% Structure: parent (decomposition) - dashed arrows")
    for child_id, node in nodes.items():
        if child_id not in visible_nodes:
            continue
        if child_id in squash_tracks:
            continue
        raw_parent_id = node.get("parent")
        if not raw_parent_id:
            continue
        if raw_parent_id in squash_tracks:
            parent_id = nodes.get(raw_parent_id, {}).get("parent")
        else:
            parent_id = raw_parent_id
        if not parent_id:
            continue
        if parent_id not in nodes and parent_id not in roots:
            continue
        if parent_id not in visible_nodes and parent_id not in roots:
            continue
        if parent_id in roots:
            lines.append(f"  {parent_id} -.-> {child_id}")
            continue

        deps = incoming_after.get(child_id, [])
        has_sibling_dep = False
        for dep_id in deps:
            dep_node = nodes.get(dep_id)
            if dep_node and dep_node.get("parent") == parent_id:
                has_sibling_dep = True
                break
        if has_sibling_dep:
            continue
        lines.append(f"  {parent_id} -.-> {child_id}")
    lines.append("")

    # after arrows (solid) - dependencies
    lines.append("  %% Dependencies: after - solid arrows")
    for node_id, node in nodes.items():
        if node_id not in visible_nodes:
            continue
        if node_id in squash_tracks:
            continue
        for dep_id in node.get("after") or []:
            if dep_id not in nodes or dep_id not in visible_nodes:
                continue
            if dep_id in squash_tracks:
                continue
            lines.append(f"  {dep_id} --> {node_id}")
    lines.append("")

    return "\n".join(lines)


# ---------- CLI ----------

def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Generate Mermaid DAG (flowchart) from opskarta plan.yaml")
    parser.add_argument("--plan", required=True, help="path to *.plan.yaml (project model)")
    parser.add_argument("--direction", choices=["LR", "TB", "BT", "RL"], default="LR", help="graph direction")
    parser.add_argument("--wrap-column", type=int, default=0, help="wrap node labels at this column (0 = no wrap)")
    parser.add_argument("--track", action="append", default=[], help="limit diagram to one or more tracks (node ids)")
    args = parser.parse_args(argv)

    plan = load_yaml(args.plan)

    try:
        warnings = validate_plan(plan)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        raise SystemExit(1)

    for w in warnings:
        print(f"warn: {w}", file=sys.stderr)

    only_tracks = set(args.track) if args.track else None

    try:
        out = render_dag_mermaid(
            plan,
            direction=args.direction,
            wrap_col=args.wrap_column,
            only_tracks=only_tracks,
        )
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        raise SystemExit(1)

    print(out)


if __name__ == "__main__":
    main()
