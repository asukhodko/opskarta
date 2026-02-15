#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migrate opskarta plan/view files from v1 to v2.

Scope:
- Converts plan file:
  - version: 1 -> 2
  - move start/finish/duration from nodes.* to schedule.nodes.*
  - convert after: [A, B] → deps: [{id: A}, {id: B}]
  - create schedule.nodes entry for any node that had at least one of:
    start|finish|duration|after(now deps)
  - fail-fast on deprecated/ambiguous node field "end"
- Converts views file:
  - version: 1 -> 2
  - gantt_views -> views
  - drop top-level project
  - move excludes to plan.schedule.calendars.default.excludes
  - add where.has_schedule: true to every migrated view

Usage:
  python3 migrate_opskarta_v1_to_v2.py \
    --plan-in old.plan.yaml \
    --views-in old.views.yaml \
    --plan-out new.plan.yaml \
    --views-out new.views.yaml

  python3 migrate_opskarta_v1_to_v2.py \
    --plan-in plan.yaml \
    --views-in views.yaml \
    --in-place --backup
"""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple

RUAMEL_AVAILABLE = False
try:
    from ruamel.yaml import YAML
    from ruamel.yaml.comments import CommentedMap

    RUAMEL_AVAILABLE = True
except Exception:  # pragma: no cover
    YAML = None  # type: ignore[assignment]
    CommentedMap = dict  # type: ignore[misc,assignment]
    import yaml as pyyaml  # type: ignore[import-not-found]


class MigrationError(RuntimeError):
    pass


def _new_map() -> MutableMapping[str, Any]:
    if RUAMEL_AVAILABLE:
        return CommentedMap()  # type: ignore[call-arg]
    return {}


def _load_yaml(path: Path) -> Tuple[Any, Any]:
    if RUAMEL_AVAILABLE:
        yaml = YAML(typ="rt")
        yaml.preserve_quotes = True
        yaml.width = 4096
        yaml.indent(mapping=2, sequence=4, offset=2)
        with path.open("r", encoding="utf-8") as f:
            return yaml.load(f), yaml

    with path.open("r", encoding="utf-8") as f:
        return pyyaml.safe_load(f), pyyaml  # type: ignore[name-defined]


def _dump_yaml(data: Any, path: Path, yaml_backend: Any) -> None:
    if RUAMEL_AVAILABLE:
        with path.open("w", encoding="utf-8") as f:
            yaml_backend.dump(data, f)
        return

    with path.open("w", encoding="utf-8") as f:
        pyyaml.safe_dump(  # type: ignore[name-defined]
            data,
            f,
            allow_unicode=True,
            sort_keys=False,
            width=4096,
        )


def _require_mapping(name: str, value: Any) -> MutableMapping[str, Any]:
    if not isinstance(value, MutableMapping):
        raise MigrationError(f"{name} must be a mapping, got: {type(value).__name__}")
    return value


def _require_version(doc_name: str, doc: Mapping[str, Any], expected: int) -> None:
    version = doc.get("version")
    if version != expected:
        raise MigrationError(f"{doc_name} must have version: {expected}, got: {version!r}")


def _normalize_excludes(raw: Any) -> List[str]:
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise MigrationError(f"view.excludes must be a list, got: {type(raw).__name__}")
    result: List[str] = []
    for i, item in enumerate(raw):
        if not isinstance(item, str):
            raise MigrationError(f"view.excludes[{i}] must be string, got: {type(item).__name__}")
        result.append(item)
    return result


def _compare_excludes(values: Sequence[List[str]]) -> Optional[List[str]]:
    if not values:
        return None
    base = set(values[0])
    for idx, excludes in enumerate(values[1:], start=2):
        if set(excludes) != base:
            raise MigrationError(
                "Views have different excludes sets. "
                f"View #1: {sorted(base)}; view #{idx}: {sorted(set(excludes))}. "
                "Resolve manually before migration."
            )
    return values[0]


def _collect_uniform_excludes(v1_views: Mapping[str, Any]) -> List[str]:
    excludes_per_view: List[List[str]] = []
    for view_id, view in v1_views.items():
        if not isinstance(view, Mapping):
            raise MigrationError(f"gantt_views.{view_id} must be a mapping")
        excludes_per_view.append(_normalize_excludes(view.get("excludes")))

    unified = _compare_excludes(excludes_per_view)
    if unified is None:
        return []
    return unified


def migrate_views_v1_to_v2(views_doc: MutableMapping[str, Any]) -> Tuple[MutableMapping[str, Any], List[str]]:
    _require_version("views file", views_doc, 1)
    v1_gantt_views = _require_mapping("gantt_views", views_doc.get("gantt_views"))

    unified_excludes = _collect_uniform_excludes(v1_gantt_views)

    v2_doc = _new_map()
    v2_doc["version"] = 2

    v2_views = _new_map()
    for view_id, view in v1_gantt_views.items():
        if not isinstance(view, Mapping):
            raise MigrationError(f"gantt_views.{view_id} must be a mapping")

        new_view = _new_map()
        for key, value in view.items():
            if key == "excludes":
                continue
            new_view[key] = copy.deepcopy(value)

        where = new_view.get("where")
        if where is None:
            where = _new_map()
            new_view["where"] = where
        if not isinstance(where, MutableMapping):
            raise MigrationError(f"gantt_views.{view_id}.where must be mapping if present")
        where["has_schedule"] = True

        v2_views[str(view_id)] = new_view

    v2_doc["views"] = v2_views
    return v2_doc, unified_excludes


def migrate_plan_v1_to_v2(
    plan_doc: MutableMapping[str, Any],
    *,
    excludes: List[str],
) -> MutableMapping[str, Any]:
    _require_version("plan file", plan_doc, 1)
    nodes = _require_mapping("nodes", plan_doc.get("nodes"))

    for key in ("schedule", "views"):
        if key in plan_doc:
            raise MigrationError(f"plan file already contains '{key}'. Refusing implicit merge.")

    schedule_nodes = _new_map()
    moved_fields = 0

    for node_id, node in nodes.items():
        if not isinstance(node, MutableMapping):
            raise MigrationError(f"nodes.{node_id} must be a mapping")

        if "end" in node:
            raise MigrationError(
                f"nodes.{node_id} contains unsupported field 'end'. "
                "Migration is intentionally fail-fast because v2 uses 'finish'."
            )

        should_include = any(field in node for field in ("start", "finish", "duration", "after"))
        schedule_node = _new_map()

        for field in ("start", "finish", "duration"):
            if field in node:
                schedule_node[field] = node.pop(field)
                moved_fields += 1

        # Convert after: [A, B] → deps: [{id: A}, {id: B}]
        if "after" in node:
            after_list = node.pop("after")
            if after_list is not None:
                if not isinstance(after_list, list):
                    raise MigrationError(
                        f"nodes.{node_id}.after must be a list, got: {type(after_list).__name__}"
                    )
                deps = []
                for dep_id in after_list:
                    if not isinstance(dep_id, str):
                        raise MigrationError(
                            f"nodes.{node_id}.after[] items must be strings, got: {type(dep_id).__name__}"
                        )
                    dep_edge = _new_map()
                    dep_edge["id"] = dep_id
                    deps.append(dep_edge)
                if deps:
                    node["deps"] = deps

        if should_include:
            schedule_nodes[str(node_id)] = schedule_node

    plan_doc["version"] = 2

    schedule = _new_map()
    schedule["nodes"] = schedule_nodes

    if excludes:
        calendars = _new_map()
        default_calendar = _new_map()
        default_calendar["excludes"] = excludes
        calendars["default"] = default_calendar
        schedule["calendars"] = calendars
        schedule["default_calendar"] = "default"

    plan_doc["schedule"] = schedule

    return {
        "plan": plan_doc,
        "schedule_nodes_count": len(schedule_nodes),
        "moved_fields_count": moved_fields,
    }


def validate_migrated_view_lanes(
    plan_doc: MutableMapping[str, Any],
    views_doc: MutableMapping[str, Any],
) -> None:
    """
    Fail-fast validation for migrated views.lanes node references.

    This catches stale lane node IDs early, before writing output files.
    """
    nodes = _require_mapping("nodes", plan_doc.get("nodes"))
    views = _require_mapping("views", views_doc.get("views"))

    for view_id, view in views.items():
        if not isinstance(view, MutableMapping):
            raise MigrationError(f"views.{view_id} must be a mapping")

        lanes = view.get("lanes")
        if lanes is None:
            continue
        if not isinstance(lanes, MutableMapping):
            raise MigrationError(f"views.{view_id}.lanes must be a mapping")

        for lane_id, lane in lanes.items():
            lane_path = f"views.{view_id}.lanes.{lane_id}"
            if not isinstance(lane, MutableMapping):
                raise MigrationError(f"{lane_path} must be a mapping")

            lane_nodes = lane.get("nodes")
            if lane_nodes is None:
                raise MigrationError(f"{lane_path}.nodes is required")
            if not isinstance(lane_nodes, list):
                raise MigrationError(f"{lane_path}.nodes must be a list[string]")

            for i, node_id in enumerate(lane_nodes):
                if not isinstance(node_id, str):
                    raise MigrationError(
                        f"{lane_path}.nodes[{i}] must be string node_id, got {type(node_id).__name__}"
                    )
                if node_id not in nodes:
                    raise MigrationError(
                        f"{lane_path}.nodes[{i}] references unknown node_id {node_id!r}"
                    )


def _backup_path(path: Path) -> Path:
    ts = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    return path.with_name(f"{path.name}.bak.{ts}")


def _parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Migrate opskarta plan/views from v1 to v2.")
    parser.add_argument("--plan-in", required=True, help="Input plan YAML (v1)")
    parser.add_argument("--views-in", required=True, help="Input views YAML (v1)")
    parser.add_argument("--plan-out", help="Output plan YAML (v2)")
    parser.add_argument("--views-out", help="Output views YAML (v2)")
    parser.add_argument("--in-place", action="store_true", help="Rewrite --plan-in and --views-in")
    parser.add_argument("--backup", action="store_true", help="Create .bak.TIMESTAMP files (only with --in-place)")
    args = parser.parse_args(argv)

    if args.in_place:
        if args.plan_out or args.views_out:
            parser.error("--plan-out/--views-out cannot be used with --in-place")
    else:
        if not args.plan_out or not args.views_out:
            parser.error("--plan-out and --views-out are required unless --in-place is used")

    if args.backup and not args.in_place:
        parser.error("--backup can only be used with --in-place")

    return args


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parse_args(argv)

    plan_in = Path(args.plan_in)
    views_in = Path(args.views_in)

    if args.in_place:
        plan_out = plan_in
        views_out = views_in
    else:
        plan_out = Path(args.plan_out)
        views_out = Path(args.views_out)

    plan_doc, plan_yaml_backend = _load_yaml(plan_in)
    views_doc, views_yaml_backend = _load_yaml(views_in)

    plan_doc = _require_mapping("plan root", plan_doc)
    views_doc = _require_mapping("views root", views_doc)

    v2_views_doc, excludes = migrate_views_v1_to_v2(views_doc)
    plan_result = migrate_plan_v1_to_v2(plan_doc, excludes=excludes)
    v2_plan_doc = plan_result["plan"]
    validate_migrated_view_lanes(v2_plan_doc, v2_views_doc)

    if args.in_place and args.backup:
        plan_bak = _backup_path(plan_in)
        views_bak = _backup_path(views_in)
        shutil.copy2(plan_in, plan_bak)
        shutil.copy2(views_in, views_bak)
        print(f"Backup created: {plan_bak}")
        print(f"Backup created: {views_bak}")

    _dump_yaml(v2_plan_doc, plan_out, plan_yaml_backend)
    _dump_yaml(v2_views_doc, views_out, views_yaml_backend)

    print("Migration completed.")
    print(f"Plan: {plan_in} -> {plan_out}")
    print(f"Views: {views_in} -> {views_out}")
    print(f"Nodes in plan: {len(v2_plan_doc.get('nodes', {}))}")
    print(f"schedule.nodes: {plan_result['schedule_nodes_count']}")
    print(f"Moved fields (start/finish/duration): {plan_result['moved_fields_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
