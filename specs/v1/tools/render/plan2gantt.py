#!/usr/bin/env python3
"""
plan2gantt: opskarta v1 (core) -> Mermaid Gantt renderer.

Core features implemented:
- Strict YAML loading with duplicate key detection;
- Plan and views validation per opskarta v1 (schema + referential integrity + formats);
- Canonical scheduling algorithm (per-view calendar):
  1) explicit start (normalized to next workday if falls on exclude and not milestone)
  2) finish + duration (backward planning)
  3) after (start = next_workday(max_finish_deps), milestone = max_finish_deps)
  4) x-extension: anchor_to_parent_start (non-core, opt-in)
  5) otherwise node is unscheduled (not rendered on Gantt)
- Core excludes: "weekends" + dates YYYY-MM-DD (others warn and ignore);
- Default duration: 1d only for nodes where start is computable/set and no duration/finish;
- Warnings (warn/info) for expected edge cases.

Mermaid profile features:
- init block with theme + status colors;
- date_format -> dateFormat, axis_format -> axisFormat, tick_interval -> tickInterval;
- milestone: true -> Mermaid tag "milestone" (can combine with status).

Example:
  python3 -m render.plan2gantt \\
    --plan gitlab-upgrade-15-7-to-18.plan.yaml \\
    --views gitlab-upgrade-15-7-to-18.views.yaml \\
    --view all-teams
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import yaml

DATE_FMT = "%Y-%m-%d"
RE_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
RE_DURATION = re.compile(r"^[1-9][0-9]*[dw]$")
RE_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")


# ----------------------------
# Reporting (warn/info/errors)
# ----------------------------

class ValidationFailed(Exception):
    pass


@dataclass
class Reporter:
    errors: int = 0
    warnings: int = 0
    infos: int = 0

    def error(self, msg: str) -> None:
        self.errors += 1
        print(f"ERROR: {msg}", file=sys.stderr)

    def warn(self, msg: str) -> None:
        self.warnings += 1
        print(f"warn: {msg}", file=sys.stderr)

    def info(self, msg: str) -> None:
        self.infos += 1
        print(f"info: {msg}", file=sys.stderr)

    def raise_if_errors(self) -> None:
        if self.errors:
            raise ValidationFailed(f"validation failed with {self.errors} error(s)")


# ----------------------------
# YAML loader with duplicate keys detection
# ----------------------------

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


def load_yaml_unique(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.load(f, Loader=UniqueKeyLoader)
    if not isinstance(data, dict):
        raise ValidationFailed(f"{path}: root must be a mapping/object")
    return data


# ----------------------------
# Normalization helpers
# ----------------------------

def parse_date_field(value: Any, field_path: str, rep: Reporter) -> date:
    """
    Normalizes YAML date/string to datetime.date.
    Spec allows YAML date/datetime, but canonical form is string YYYY-MM-DD.
    """
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, str):
        s = value.strip()
        if not RE_DATE.match(s):
            rep.error(f"{field_path}: invalid date format {value!r}, expected YYYY-MM-DD")
            raise ValidationFailed
        try:
            return datetime.strptime(s, DATE_FMT).date()
        except Exception:
            rep.error(f"{field_path}: invalid date value {value!r}")
            raise ValidationFailed
    rep.error(f"{field_path}: invalid date type {type(value).__name__}, expected string or YAML date")
    raise ValidationFailed


def parse_duration_days(value: Any, field_path: str, rep: Reporter) -> int:
    """
    duration: <N><unit>, unit in {d,w}. w = 5 workdays.
    """
    if not isinstance(value, str):
        rep.error(f"{field_path}: duration must be string like '5d' or '2w'")
        raise ValidationFailed
    s = value.strip()
    if not RE_DURATION.match(s):
        rep.error(f"{field_path}: invalid duration format {value!r}, expected ^[1-9][0-9]*[dw]$")
        raise ValidationFailed
    n = int(s[:-1])
    unit = s[-1]
    return n if unit == "d" else n * 5


# ----------------------------
# Calendar (per-view)
# ----------------------------

@dataclass(frozen=True)
class Calendar:
    weekends: bool
    exclude_dates: Set[date]


def build_calendar(excludes: Any, rep: Reporter, view_path: str) -> Calendar:
    weekends = False
    dates: Set[date] = set()

    if excludes is None:
        excludes = []
    if not isinstance(excludes, list):
        rep.error(f"{view_path}.excludes: must be a list")
        raise ValidationFailed

    for i, item in enumerate(excludes):
        item_path = f"{view_path}.excludes[{i}]"
        if isinstance(item, (date, datetime)):
            d = item.date() if isinstance(item, datetime) else item
            dates.add(d)
            continue
        if not isinstance(item, str):
            rep.warn(f"{item_path}: non-string exclude {type(item).__name__} treated as str and ignored")
            continue
        s = item.strip()
        if s == "weekends":
            weekends = True
            continue
        if RE_DATE.match(s):
            try:
                d = datetime.strptime(s, DATE_FMT).date()
            except Exception:
                rep.error(f"{item_path}: invalid date value {item!r}")
                raise ValidationFailed
            dates.add(d)
            continue
        # non-core exclude
        rep.warn(f"{item_path}: unknown exclude {item!r} is non-core and will be ignored")

    return Calendar(weekends=weekends, exclude_dates=dates)


def is_workday(d: date, cal: Calendar) -> bool:
    if cal.weekends and d.weekday() >= 5:
        return False
    if d in cal.exclude_dates:
        return False
    return True


def next_workday(d: date, cal: Calendar) -> date:
    cur = d + timedelta(days=1)
    while not is_workday(cur, cal):
        cur += timedelta(days=1)
    return cur


def prev_workday(d: date, cal: Calendar) -> date:
    cur = d - timedelta(days=1)
    while not is_workday(cur, cal):
        cur -= timedelta(days=1)
    return cur


def add_workdays(start: date, n: int, cal: Calendar) -> date:
    """
    Canonical add_workdays from spec:
    adds n workdays AFTER start (start is included in duration via duration-1).
    n=0 => returns start.
    """
    cur = start
    added = 0
    while added < n:
        cur += timedelta(days=1)
        if is_workday(cur, cal):
            added += 1
    return cur


def sub_workdays(finish: date, n: int, cal: Calendar) -> date:
    """
    Canonical sub_workdays from spec:
    subtracts n workdays BEFORE finish (finish is included via duration-1).
    n=0 => returns finish.
    """
    cur = finish
    subtracted = 0
    while subtracted < n:
        cur -= timedelta(days=1)
        if is_workday(cur, cal):
            subtracted += 1
    return cur


def count_workdays_between(start: date, finish: date, cal: Calendar) -> int:
    if finish < start:
        return 0
    cur = start
    count = 0
    while cur <= finish:
        if is_workday(cur, cal):
            count += 1
        cur += timedelta(days=1)
    return count


def normalize_start(d: date, cal: Calendar, milestone: bool, rep: Reporter, node_path: str) -> date:
    if milestone:
        return d
    if is_workday(d, cal):
        return d
    cur = d
    while not is_workday(cur, cal):
        cur += timedelta(days=1)
    rep.warn(f"{node_path}.start: {d.isoformat()} is excluded, normalized to {cur.isoformat()}")
    return cur


# ----------------------------
# Validation: plan + views
# ----------------------------

def validate_plan(plan: Dict[str, Any], rep: Reporter) -> None:
    if "version" not in plan:
        rep.error("plan.version: missing required field")
        raise ValidationFailed
    if not isinstance(plan["version"], int):
        rep.error(f"plan.version: must be int, got {type(plan['version']).__name__}")
        raise ValidationFailed
    if plan["version"] != 1:
        rep.error(f"plan.version: unsupported version {plan['version']}, expected 1")
        raise ValidationFailed

    nodes = plan.get("nodes")
    if not isinstance(nodes, dict):
        rep.error("plan.nodes: missing required mapping")
        raise ValidationFailed

    meta = plan.get("meta") or {}
    if meta and not isinstance(meta, dict):
        rep.error("plan.meta: must be mapping/object")
        raise ValidationFailed

    statuses = plan.get("statuses") or {}
    if statuses and not isinstance(statuses, dict):
        rep.error("plan.statuses: must be mapping/object")
        raise ValidationFailed

    # status usage requires statuses section
    uses_status = False

    # validate statuses
    for st_id, st in statuses.items():
        if not isinstance(st_id, str):
            rep.error(f"plan.statuses: status key must be string, got {type(st_id).__name__}")
            raise ValidationFailed
        if st is None:
            continue
        if not isinstance(st, dict):
            rep.error(f"plan.statuses.{st_id}: must be mapping/object")
            raise ValidationFailed
        color = st.get("color")
        if color is not None:
            if not isinstance(color, str) or not RE_COLOR.match(color.strip()):
                rep.error(f"plan.statuses.{st_id}.color: invalid color {color!r}, expected ^#[0-9a-fA-F]{{6}}$")
                raise ValidationFailed
        label = st.get("label")
        if label is not None and not isinstance(label, str):
            rep.error(f"plan.statuses.{st_id}.label: must be string")
            raise ValidationFailed

    # validate nodes
    for node_id, node in nodes.items():
        if not isinstance(node_id, str):
            rep.error(f"plan.nodes: node_id keys must be strings, got {type(node_id).__name__} ({node_id!r})")
            raise ValidationFailed
        node_path = f"plan.nodes.{node_id}"
        if not isinstance(node, dict):
            rep.error(f"{node_path}: node must be mapping/object")
            raise ValidationFailed
        title = node.get("title")
        if not isinstance(title, str) or not title.strip():
            rep.error(f"{node_path}.title: required non-empty string")
            raise ValidationFailed

        # optional string fields
        for f in ("kind", "status", "parent", "issue"):
            if f in node and node[f] is not None and not isinstance(node[f], str):
                rep.error(f"{node_path}.{f}: must be string if present")
                raise ValidationFailed

        # after
        if "after" in node and node["after"] is not None:
            if not isinstance(node["after"], list):
                rep.error(f"{node_path}.after: must be list[string]")
                raise ValidationFailed
            for i, dep in enumerate(node["after"]):
                if not isinstance(dep, str):
                    rep.error(f"{node_path}.after[{i}]: must be string node_id")
                    raise ValidationFailed

        # milestone
        if "milestone" in node and node["milestone"] is not None and not isinstance(node["milestone"], bool):
            rep.error(f"{node_path}.milestone: must be boolean")
            raise ValidationFailed

        # date fields format check (types and parseability)
        for df in ("start", "finish", "end"):
            if df in node and node[df] is not None:
                _ = parse_date_field(node[df], f"{node_path}.{df}", rep)

        # duration
        if "duration" in node and node["duration"] is not None:
            _ = parse_duration_days(node["duration"], f"{node_path}.duration", rep)

        # notes
        if "notes" in node and node["notes"] is not None and not isinstance(node["notes"], str):
            rep.error(f"{node_path}.notes: must be string/multiline if present")
            raise ValidationFailed

        # status integrity
        st = node.get("status")
        if st:
            uses_status = True
            if not statuses or st not in statuses:
                rep.error(f"{node_path}.status: unknown status {st!r} (not in plan.statuses)")
                raise ValidationFailed

        # parent integrity
        parent = node.get("parent")
        if parent and parent not in nodes:
            rep.error(f"{node_path}.parent: unknown parent {parent!r}")
            raise ValidationFailed

        # after integrity
        for dep in node.get("after") or []:
            if dep not in nodes:
                rep.error(f"{node_path}.after: unknown dependency {dep!r}")
                raise ValidationFailed

    if uses_status and not statuses:
        rep.error("plan.statuses: required because at least one node specifies status")
        raise ValidationFailed

    # cycles: parent + after
    detect_cycles_parent(nodes, rep)
    detect_cycles_after(nodes, rep)


def detect_cycles_parent(nodes: Dict[str, Any], rep: Reporter) -> None:
    visited: Set[str] = set()
    in_stack: Set[str] = set()

    def dfs(nid: str) -> None:
        visited.add(nid)
        in_stack.add(nid)
        parent = nodes[nid].get("parent")
        if parent:
            if parent not in visited:
                dfs(parent)
            elif parent in in_stack:
                rep.error("cycle detected in parent relationships")
                raise ValidationFailed
        in_stack.remove(nid)

    for nid in nodes.keys():
        if nid not in visited:
            dfs(nid)


def detect_cycles_after(nodes: Dict[str, Any], rep: Reporter) -> None:
    visited: Set[str] = set()
    in_stack: Set[str] = set()

    def dfs(nid: str) -> None:
        visited.add(nid)
        in_stack.add(nid)
        for dep in nodes[nid].get("after") or []:
            if dep not in visited:
                dfs(dep)
            elif dep in in_stack:
                rep.error("cycle detected in after dependencies")
                raise ValidationFailed
        in_stack.remove(nid)

    for nid in nodes.keys():
        if nid not in visited:
            dfs(nid)


def validate_views(views: Dict[str, Any], plan: Dict[str, Any], rep: Reporter) -> None:
    if "version" not in views:
        rep.error("views.version: missing required field")
        raise ValidationFailed
    if not isinstance(views["version"], int):
        rep.error(f"views.version: must be int, got {type(views['version']).__name__}")
        raise ValidationFailed
    if views["version"] != 1:
        rep.error(f"views.version: unsupported version {views['version']}, expected 1")
        raise ValidationFailed

    project = views.get("project")
    if not isinstance(project, str) or not project.strip():
        rep.error("views.project: missing required string")
        raise ValidationFailed

    meta = plan.get("meta") or {}
    meta_id = meta.get("id") if isinstance(meta, dict) else None
    if not isinstance(meta_id, str) or not meta_id.strip():
        rep.error("plan.meta.id: required when using views.yaml")
        raise ValidationFailed

    if project != meta_id:
        rep.error(f"views.project ({project}) != plan.meta.id ({meta_id})")
        raise ValidationFailed

    gantt_views = views.get("gantt_views") or {}
    if gantt_views and not isinstance(gantt_views, dict):
        rep.error("views.gantt_views: must be mapping/object")
        raise ValidationFailed

    nodes = plan.get("nodes") or {}
    for view_id, view in gantt_views.items():
        if not isinstance(view_id, str):
            rep.error("views.gantt_views: keys must be strings")
            raise ValidationFailed
        view_path = f"views.gantt_views.{view_id}"
        if not isinstance(view, dict):
            rep.error(f"{view_path}: view must be mapping/object")
            raise ValidationFailed
        title = view.get("title")
        if title is not None and not isinstance(title, str):
            rep.error(f"{view_path}.title: must be string")
            raise ValidationFailed

        excludes = view.get("excludes")
        if excludes is not None and not isinstance(excludes, list):
            rep.error(f"{view_path}.excludes: must be list")
            raise ValidationFailed

        lanes = view.get("lanes")
        if lanes is None:
            rep.error(f"{view_path}.lanes: missing required mapping")
            raise ValidationFailed
        if not isinstance(lanes, dict):
            rep.error(f"{view_path}.lanes: must be mapping/object")
            raise ValidationFailed

        for lane_id, lane in lanes.items():
            if not isinstance(lane_id, str):
                rep.error(f"{view_path}.lanes: lane keys must be strings")
                raise ValidationFailed
            lane_path = f"{view_path}.lanes.{lane_id}"
            if not isinstance(lane, dict):
                rep.error(f"{lane_path}: must be mapping/object")
                raise ValidationFailed
            if "title" in lane and lane["title"] is not None and not isinstance(lane["title"], str):
                rep.error(f"{lane_path}.title: must be string")
                raise ValidationFailed
            node_list = lane.get("nodes")
            if node_list is None:
                rep.error(f"{lane_path}.nodes: missing required list")
                raise ValidationFailed
            if not isinstance(node_list, list):
                rep.error(f"{lane_path}.nodes: must be list[string]")
                raise ValidationFailed
            for i, nid in enumerate(node_list):
                if not isinstance(nid, str):
                    rep.error(f"{lane_path}.nodes[{i}]: must be string node_id")
                    raise ValidationFailed
                if nid not in nodes:
                    rep.error(f"{lane_path}.nodes[{i}]: unknown node_id {nid!r} (not in plan.nodes)")
                    raise ValidationFailed


# ----------------------------
# After-chain anchor warnings (no calendar needed)
# ----------------------------

def warn_after_chains_without_anchor(plan: Dict[str, Any], rep: Reporter) -> None:
    nodes: Dict[str, Any] = plan.get("nodes") or {}
    memo: Dict[str, bool] = {}
    visiting: Set[str] = set()

    def has_anchor(nid: str) -> bool:
        if nid in memo:
            return memo[nid]
        if nid in visiting:
            # cycles are already validated separately as ERROR, should not reach here
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
            rep.warn(
                f"plan.nodes.{nid}.after: dependency chain has no anchor (no start/finish/end in closure) -> node will be unscheduled"
            )


# ----------------------------
# Extension: x.scheduling.anchor_to_parent_start
# ----------------------------

def x_anchor_to_parent_start(node: Dict[str, Any], rep: Reporter, node_path: str) -> bool:
    """
    Reads node.x.scheduling.anchor_to_parent_start extension.
    Returns True if enabled, False otherwise.
    """
    x = node.get("x")
    if x is None:
        return False
    if not isinstance(x, dict):
        rep.warn(f"{node_path}.x: must be mapping/object to use extensions; ignored")
        return False
    scheduling = x.get("scheduling")
    if scheduling is None:
        return False
    if not isinstance(scheduling, dict):
        rep.warn(f"{node_path}.x.scheduling: must be mapping/object; ignored")
        return False
    v = scheduling.get("anchor_to_parent_start", False)
    if not isinstance(v, bool):
        rep.warn(f"{node_path}.x.scheduling.anchor_to_parent_start: must be boolean; treated as false")
        return False
    return v


# ----------------------------
# Scheduling
# ----------------------------

@dataclass(frozen=True)
class NodeSchedule:
    start: Optional[date]
    finish: Optional[date]
    duration_days: Optional[int]  # effective workdays duration for rendering; may be None if start is None


def compute_node_schedule(
    node_id: str,
    plan: Dict[str, Any],
    cal: Calendar,
    rep: Reporter,
    cache: Dict[str, NodeSchedule],
    visiting: Set[str],
) -> NodeSchedule:
    if node_id in cache:
        return cache[node_id]

    # Cycle detection during scheduling (for parent-anchor extension)
    if node_id in visiting:
        rep.error(f"scheduling cycle detected while resolving {node_id!r} (after/parent/x)")
        raise ValidationFailed
    visiting.add(node_id)

    try:
        nodes: Dict[str, Any] = plan.get("nodes") or {}
        node = nodes.get(node_id)
        if node is None:
            rep.error(f"internal: missing node {node_id!r}")
            raise ValidationFailed
        if not isinstance(node, dict):
            rep.error(f"plan.nodes.{node_id}: must be mapping/object")
            raise ValidationFailed

        node_path = f"plan.nodes.{node_id}"
        milestone = bool(node.get("milestone"))
        after: List[str] = list(node.get("after") or [])

        raw_start = node.get("start")
        raw_finish = node.get("finish")
        raw_end = node.get("end")
        raw_duration = node.get("duration")

        if raw_finish is not None and raw_end is not None:
            rep.error(f"{node_path}: both 'finish' and legacy 'end' specified; use only 'finish'")
            raise ValidationFailed

        start_explicit = parse_date_field(raw_start, f"{node_path}.start", rep) if raw_start is not None else None
        finish_explicit = parse_date_field(raw_finish, f"{node_path}.finish", rep) if raw_finish is not None else None

        # legacy end (exclusive) -> finish (inclusive) per-view calendar
        if raw_end is not None and finish_explicit is None:
            end_excl = parse_date_field(raw_end, f"{node_path}.end", rep)
            finish_explicit = prev_workday(end_excl, cal)
            rep.warn(f"{node_path}.end: legacy exclusive end detected; converted to finish={finish_explicit.isoformat()} (view calendar)")

        duration_days: Optional[int] = None
        if raw_duration is not None:
            duration_days = parse_duration_days(raw_duration, f"{node_path}.duration", rep)

        # finish on excluded day warning (only if explicitly set or via end-conversion)
        if finish_explicit is not None and (not milestone) and (not is_workday(finish_explicit, cal)):
            rep.warn(f"{node_path}.finish: {finish_explicit.isoformat()} falls on excluded day (deadline is allowed, but check consistency)")

        # resolve dependency finishes (needed for 'after' and for start-vs-after warning)
        dep_finishes: List[date] = []
        deps_have_finishes = True
        for dep_id in after:
            dep_sched = compute_node_schedule(dep_id, plan, cal, rep, cache, visiting)
            if dep_sched.finish is None:
                deps_have_finishes = False
            else:
                dep_finishes.append(dep_sched.finish)

        # 1) explicit start
        start: Optional[date] = None
        start_source: Optional[str] = None

        if start_explicit is not None:
            start = normalize_start(start_explicit, cal, milestone, rep, node_path)
            start_source = "start"
        # 2) finish + duration (requires duration)
        elif finish_explicit is not None and duration_days is not None:
            eff_dur = 1 if milestone else duration_days
            start_candidate = sub_workdays(finish_explicit, eff_dur - 1, cal)
            start = normalize_start(start_candidate, cal, milestone, rep, node_path)
            start_source = "finish+duration"
        # 3) after
        elif after:
            if deps_have_finishes and dep_finishes:
                max_finish = max(dep_finishes)
                start_candidate = max_finish if milestone else next_workday(max_finish, cal)
                start = normalize_start(start_candidate, cal, milestone, rep, node_path)
                start_source = "after"
            else:
                # cannot compute start from after (deps have no finish)
                start = None
                start_source = None

        # 4) x-extension: anchor_to_parent_start (non-core)
        if start is None and x_anchor_to_parent_start(node, rep, node_path):
            parent_id = node.get("parent")
            if isinstance(parent_id, str) and parent_id.strip():
                parent_sched = compute_node_schedule(parent_id, plan, cal, rep, cache, visiting)
                if parent_sched.start is not None:
                    start = normalize_start(parent_sched.start, cal, milestone, rep, node_path)
                    start_source = "x.anchor_to_parent_start"
                    if after:
                        rep.warn(
                            f"{node_path}: after could not schedule (deps missing finish); "
                            f"anchored to parent start via x.scheduling.anchor_to_parent_start"
                        )
                    else:
                        rep.info(
                            f"{node_path}: anchored to parent {parent_id}.start={start.isoformat()} via x.scheduling.anchor_to_parent_start"
                        )
                else:
                    rep.warn(f"{node_path}: anchor_to_parent_start=true but parent {parent_id!r} is unscheduled; node remains unscheduled")
            else:
                rep.warn(f"{node_path}: anchor_to_parent_start=true but node has no valid parent; ignored")

        # If start is still None, node is unscheduled for Gantt (but may still have finish as deadline)
        if start is None:
            sched = NodeSchedule(start=None, finish=finish_explicit, duration_days=None)
            cache[node_id] = sched
            return sched

        # Warn if node has both explicit/computed start (not from after) and after constraints that would start later
        if after and start_source in ("start", "finish+duration") and deps_have_finishes and dep_finishes:
            max_finish = max(dep_finishes)
            recommended = max_finish if milestone else next_workday(max_finish, cal)
            if start < recommended:
                rep.warn(
                    f"{node_path}: start={start.isoformat()} is earlier than start_from_after={recommended.isoformat()} "
                    f"(after is treated as logical dependency per spec, but this may be a planning bug)"
                )

        # Determine effective duration + finish
        eff_duration: Optional[int] = None
        finish: Optional[date] = None

        if milestone:
            # Milestone is a point: finish == start, duration for rendering is 1d
            if duration_days is not None and duration_days != 1:
                rep.warn(f"{node_path}.duration: milestone ignores duration; rendered as 1d")
            eff_duration = 1
            finish = start
            if finish_explicit is not None and finish_explicit != finish:
                rep.error(
                    f"{node_path}: milestone has start={start.isoformat()} but finish={finish_explicit.isoformat()} "
                    f"(milestone must be a single date)"
                )
                raise ValidationFailed
        else:
            if finish_explicit is not None and duration_days is not None:
                # all three: must be consistent
                computed_finish = add_workdays(start, duration_days - 1, cal)
                if computed_finish != finish_explicit:
                    rep.error(
                        f"{node_path}: inconsistent start/finish/duration under this view calendar "
                        f"(start={start.isoformat()}, duration={duration_days} workdays => finish={computed_finish.isoformat()}, "
                        f"but plan says finish={finish_explicit.isoformat()})"
                    )
                    raise ValidationFailed
                eff_duration = duration_days
                finish = finish_explicit
            elif finish_explicit is not None and duration_days is None:
                # start + finish -> derive duration
                derived = count_workdays_between(start, finish_explicit, cal)
                if derived <= 0:
                    rep.error(
                        f"{node_path}: finish={finish_explicit.isoformat()} is before start={start.isoformat()} (or yields 0 workdays)"
                    )
                    raise ValidationFailed
                eff_duration = derived
                finish = finish_explicit
            elif duration_days is not None:
                eff_duration = duration_days
                finish = add_workdays(start, duration_days - 1, cal)
            else:
                # scheduled but duration missing and finish missing => default 1d
                rep.info(f"{node_path}.duration: missing for scheduled node; defaulted to 1d")
                eff_duration = 1
                finish = start

        sched = NodeSchedule(start=start, finish=finish, duration_days=eff_duration)
        cache[node_id] = sched
        return sched
    finally:
        visiting.remove(node_id)


# ----------------------------
# Mermaid rendering
# ----------------------------

def wrap_mermaid_markdown(src: str) -> str:
    """Wraps Mermaid source in markdown code fence."""
    return "```mermaid\n" + src.rstrip() + "\n```\n"


def sanitize_mermaid_text(text: str) -> str:
    """
    Mermaid Gantt использует ':' как разделитель (Task name :meta,...).
    Чтобы названия задач/секций не ломали парсер — вырезаем двоеточия.
    """
    # На всякий: ASCII ':' и fullwidth '：'
    cleaned = text.replace(":", " ").replace("：", " ")
    # Уберём лишние пробелы, чтобы "foo:bar" не превращался в "foobar"
    return " ".join(cleaned.split())


def get_status_color(plan: Dict[str, Any], status_key: str) -> Optional[str]:
    statuses = plan.get("statuses") or {}
    st = statuses.get(status_key) or {}
    color = st.get("color") if isinstance(st, dict) else None
    if isinstance(color, str) and RE_COLOR.match(color.strip()):
        return color.strip()
    defaults = {
        "not_started": "#9ca3af",
        "in_progress": "#0ea5e9",
        "done": "#22c55e",
        "blocked": "#fecaca",
        "planned": "#aad2e6",
    }
    return defaults.get(status_key)


def build_gantt_init_block(plan: Dict[str, Any]) -> str:
    theme_vars = {
        "taskBkgColor": get_status_color(plan, "not_started") or "#9ca3af",
        "taskBorderColor": "#4b5563",
        "taskTextColor": "#000000",
        "taskTextDarkColor": "#000000",
        "taskTextLightColor": "#000000",
        "activeTaskBkgColor": get_status_color(plan, "in_progress") or "#0ea5e9",
        "activeTaskBorderColor": get_status_color(plan, "in_progress") or "#0ea5e9",
        "doneTaskBkgColor": get_status_color(plan, "done") or "#22c55e",
        "doneTaskBorderColor": "#16a34a",
        "critBkgColor": get_status_color(plan, "blocked") or "#fecaca",
        "critBorderColor": get_status_color(plan, "blocked") or "#fecaca",
        "todayLineColor": "#ef4444",
    }
    cfg = {"theme": "base", "themeVariables": theme_vars}
    return f"%%{{init: {json.dumps(cfg, ensure_ascii=False)} }}%%"


def canonical_mermaid_excludes_tokens(view: Dict[str, Any], cal: Calendar) -> List[str]:
    tokens: List[str] = []
    if cal.weekends:
        tokens.append("weekends")
    # sort dates for stable output
    for d in sorted(cal.exclude_dates):
        tokens.append(d.isoformat())
    return tokens


def render_gantt_mermaid(plan: Dict[str, Any], view: Dict[str, Any], view_id: str, rep: Reporter) -> str:
    view_path = f"views.gantt_views.{view_id}"
    cal = build_calendar(view.get("excludes"), rep, view_path)

    schedule_cache: Dict[str, NodeSchedule] = {}
    visiting: Set[str] = set()

    lanes = view.get("lanes") or {}
    nodes_map = plan.get("nodes") or {}

    # compute schedules for all nodes mentioned in lanes (deps resolved recursively)
    for lane in lanes.values():
        for node_id in lane.get("nodes", []):
            compute_node_schedule(node_id, plan, cal, rep, schedule_cache, visiting)

    lines: List[str] = []
    lines.append(build_gantt_init_block(plan))
    lines.append("")
    lines.append("gantt")

    # Title fallback: view.title -> plan.meta.title -> "opskarta gantt"
    meta = plan.get("meta") or {}
    meta_title = meta.get("title") if isinstance(meta, dict) else None

    title = view.get("title")
    if not (isinstance(title, str) and title.strip()):
        title = meta_title

    if not (isinstance(title, str) and title.strip()):
        title = "opskarta gantt"

    title = sanitize_mermaid_text(title.strip())
    lines.append(f"    title {title}")

    date_format = view.get("date_format") or "YYYY-MM-DD"
    if not isinstance(date_format, str):
        rep.error(f"{view_path}.date_format: must be string if present")
        raise ValidationFailed
    lines.append(f"    dateFormat  {date_format}")

    axis_format = view.get("axis_format")
    if axis_format is not None:
        if not isinstance(axis_format, str):
            rep.error(f"{view_path}.axis_format: must be string if present")
            raise ValidationFailed
        lines.append(f"    axisFormat  {axis_format}")

    tick_interval = view.get("tick_interval")
    if tick_interval is not None:
        if not isinstance(tick_interval, str):
            rep.error(f"{view_path}.tick_interval: must be string if present")
            raise ValidationFailed
        lines.append(f"    tickInterval  {tick_interval}")

    tokens = canonical_mermaid_excludes_tokens(view, cal)
    if tokens:
        lines.append(f"    excludes {' '.join(tokens)}")

    lines.append("")

    for lane_id, lane in lanes.items():
        lane_title = sanitize_mermaid_text(str(lane.get("title", lane_id)))
        lines.append(f"    section {lane_title}")
        for node_id in lane.get("nodes", []):
            node = nodes_map.get(node_id)
            if not isinstance(node, dict):
                rep.error(f"{view_path}.lanes.{lane_id}.nodes: node {node_id!r} is not a mapping in plan")
                raise ValidationFailed

            sched = schedule_cache.get(node_id)
            if sched is None or sched.start is None:
                # core: unscheduled nodes are not shown on Gantt
                continue

            start_str = sched.start.isoformat()
            dur_days = sched.duration_days or 1
            dur_str = f"{dur_days}d"

            status = (node.get("status") or "").strip()
            title_str = str(node.get("title", node_id))

            emoji = {
                "done": "✅",
                "in_progress": "🔄",
                "blocked": "⛔",
            }.get(status)
            if emoji:
                title_str = f"{emoji} {title_str}"

            title_str = sanitize_mermaid_text(title_str)

            tags: List[str] = []
            if bool(node.get("milestone")):
                tags.append("milestone")
            if status == "in_progress":
                tags.append("active")
            elif status == "done":
                tags.append("done")
            elif status == "blocked":
                tags.append("crit")

            meta = ", ".join(tags + [node_id]) if tags else node_id
            lines.append(f"    {title_str}  :{meta},    {start_str}, {dur_str}")

        lines.append("")

    return "\n".join(lines)


# ----------------------------
# CLI
# ----------------------------

def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Generate Mermaid Gantt from opskarta plan and views YAML files")
    parser.add_argument("--plan", required=True, help="path to *.plan.yaml (project model)")
    parser.add_argument("--views", required=True, help="path to *.views.yaml (view definitions)")
    parser.add_argument("--view", required=False, help="name of gantt view to render (key in gantt_views)")
    parser.add_argument("--list-views", action="store_true", help="list available gantt views and exit")
    parser.add_argument("-o", "--output", type=Path, default=None, help="write output to file (default: stdout)")
    parser.add_argument("--markdown", action="store_true", help="wrap output in ```mermaid``` fence")
    args = parser.parse_args(argv)

    rep = Reporter()

    try:
        plan = load_yaml_unique(args.plan)
        views = load_yaml_unique(args.views)

        validate_plan(plan, rep)
        validate_views(views, plan, rep)
        warn_after_chains_without_anchor(plan, rep)

        gantt_views = (views.get("gantt_views") or {})

        # --list-views: show available views and exit
        if args.list_views:
            if not gantt_views:
                print("No gantt_views found in views file", file=sys.stderr)
                raise SystemExit(1)
            print("Available gantt views:")
            for view_id, view in gantt_views.items():
                title = view.get("title", "") if isinstance(view, dict) else ""
                title = title.strip() if isinstance(title, str) else ""
                print(f"  - {view_id}: {title}" if title else f"  - {view_id}")
            raise SystemExit(0)

        # --view is required unless --list-views
        if not args.view:
            parser.error("--view is required unless --list-views is set")

        view = gantt_views.get(args.view)
        if view is None:
            rep.error(f"views.gantt_views: unknown view {args.view!r}")
            rep.raise_if_errors()
            raise SystemExit(1)
        if not isinstance(view, dict):
            rep.error(f"views.gantt_views.{args.view}: must be mapping/object")
            rep.raise_if_errors()
            raise SystemExit(1)

        out = render_gantt_mermaid(plan, view, args.view, rep)
        rep.raise_if_errors()

        # Apply markdown wrapper if requested
        if args.markdown:
            out = wrap_mermaid_markdown(out)

        # Output to file or stdout
        if args.output:
            args.output.write_text(out, encoding="utf-8")
            print(f"Output written to {args.output}", file=sys.stderr)
        else:
            print(out)

    except ValidationFailed:
        # errors already printed via Reporter
        raise SystemExit(1)


if __name__ == "__main__":
    main()
