#!/usr/bin/env python3
"""
Validator for opskarta plan and views files.

Usage:
    python validate.py plan.yaml                    # Validate plan
    python validate.py plan.yaml views.yaml         # Validate plan and views
    python validate.py --schema plan.yaml           # Validate using JSON Schema

Validation levels:
    1. Syntax — YAML correctness
    2. Schema — JSON Schema compliance (optional)
    3. Semantics — referential integrity, business rules

Severity levels:
    - error: critical error, validation fails
    - warn: potential issue, validation succeeds
    - info: informational message

Dependencies: PyYAML (pip install pyyaml)
"""

import argparse
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


# ============================================================================
# Exceptions
# ============================================================================

class ValidationError(Exception):
    """Validation error with field path information."""
    
    def __init__(self, message: str, path: Optional[str] = None, 
                 value: Any = None, expected: Optional[str] = None,
                 available: Optional[List[str]] = None):
        self.message = message
        self.path = path
        self.value = value
        self.expected = expected
        self.available = available
        super().__init__(self._format_message())
    
    def _format_message(self) -> str:
        """Formats error message."""
        lines = []
        
        if self.path:
            lines.append(f"Error: {self.message}")
            lines.append(f"  Path: {self.path}")
        else:
            lines.append(f"Error: {self.message}")
        
        if self.value is not None:
            lines.append(f"  Value: {repr(self.value)}")
        
        if self.expected:
            lines.append(f"  Expected: {self.expected}")
        
        if self.available:
            lines.append(f"  Available: {', '.join(sorted(self.available))}")
        
        return '\n'.join(lines)


# ============================================================================
# File Loading
# ============================================================================

class DuplicateKeyError(Exception):
    """Error when duplicate key is found in YAML."""
    pass


def _make_duplicate_key_checker():
    """
    Creates YAML loader that detects duplicate keys.
    
    Returns:
        Loader class with duplicate checking
    """
    import yaml
    
    class DuplicateKeyLoader(yaml.SafeLoader):
        pass
    
    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        pairs = loader.construct_pairs(node)
        keys = [key for key, _ in pairs]
        duplicates = [key for key in keys if keys.count(key) > 1]
        if duplicates:
            # Find first duplicate
            seen = set()
            for key in keys:
                if key in seen:
                    raise DuplicateKeyError(f"Duplicate key: {key!r}")
                seen.add(key)
        return dict(pairs)
    
    DuplicateKeyLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping
    )
    
    return DuplicateKeyLoader


def normalize_yaml_dates(data: Any) -> Any:
    """
    Recursively normalizes YAML dates to YYYY-MM-DD strings.
    
    Args:
        data: Data from YAML parser
        
    Returns:
        Normalized data
    """
    if isinstance(data, datetime):
        return data.date().isoformat()
    elif isinstance(data, date):
        return data.isoformat()
    elif isinstance(data, dict):
        return {k: normalize_yaml_dates(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [normalize_yaml_dates(item) for item in data]
    else:
        return data


def load_yaml(file_path: Path) -> Dict[str, Any]:
    """
    Loads YAML file with duplicate key checking and date normalization.
    
    Raises:
        ValidationError: if file not found, contains invalid YAML,
                        or contains duplicate keys
    """
    try:
        import yaml
    except ImportError:
        print("Error: PyYAML module is not installed", file=sys.stderr)
        print("Install: pip install pyyaml", file=sys.stderr)
        sys.exit(1)
    
    if not file_path.exists():
        raise ValidationError(
            f"File not found: {file_path}",
            expected="existing file"
        )
    
    try:
        content = file_path.read_text(encoding='utf-8')
        
        # Use loader with duplicate key checking
        DuplicateKeyLoader = _make_duplicate_key_checker()
        data = yaml.load(content, Loader=DuplicateKeyLoader)
        
        if data is None:
            return {}
        
        if not isinstance(data, dict):
            raise ValidationError(
                "Root element must be an object",
                path="(root)",
                value=type(data).__name__,
                expected="object (dict)"
            )
        
        # Normalize YAML dates to strings
        data = normalize_yaml_dates(data)
        
        return data
    
    except DuplicateKeyError as e:
        raise ValidationError(
            str(e),
            path=str(file_path),
            expected="unique keys"
        )
        
    except yaml.YAMLError as e:
        raise ValidationError(
            f"YAML parsing error: {e}",
            path=str(file_path)
        )


def load_json_schema(schema_path: Path) -> Dict[str, Any]:
    """Loads JSON Schema file."""
    if not schema_path.exists():
        raise ValidationError(
            f"Schema file not found: {schema_path}",
            expected="existing JSON Schema file"
        )
    
    try:
        content = schema_path.read_text(encoding='utf-8')
        return json.loads(content)
    except json.JSONDecodeError as e:
        raise ValidationError(
            f"JSON Schema parsing error: {e}",
            path=str(schema_path)
        )


# ============================================================================
# Plan Validation
# ============================================================================

def parse_duration_days(duration: str) -> int:
    """
    Parses duration string and returns number of workdays.
    
    Args:
        duration: String in format Nd or Nw
        
    Returns:
        Number of workdays
    """
    if duration.endswith('w'):
        return int(duration[:-1]) * 5
    else:  # 'd'
        return int(duration[:-1])


def compute_finish_date(start_str: str, duration_str: str, excludes_weekends: bool = False) -> str:
    """
    Computes task finish date.
    
    Args:
        start_str: Start date in YYYY-MM-DD format
        duration_str: Duration in Nd or Nw format
        excludes_weekends: Whether to account for weekends
        
    Returns:
        Finish date in YYYY-MM-DD format
    """
    start = datetime.strptime(start_str, '%Y-%m-%d').date()
    duration_days = parse_duration_days(duration_str)
    
    if excludes_weekends:
        # Skip weekends
        days_added = 0
        current = start
        while days_added < duration_days - 1:
            current += __import__('datetime').timedelta(days=1)
            if current.weekday() < 5:  # Mon-Fri
                days_added += 1
        return current.isoformat()
    else:
        # Calendar days
        finish = start + __import__('datetime').timedelta(days=duration_days - 1)
        return finish.isoformat()


def validate_plan(plan: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    """
    Validates plan file.
    
    Checks:
    - Required fields (version, nodes)
    - Referential integrity (parent, after, status)
    - Scheduling field formats (start, duration)
    - Absence of circular dependencies
    - start and after conflicts
    
    Returns:
        Tuple (warnings, infos)
    
    Raises:
        ValidationError: when critical error is found
    """
    warnings: List[str] = []
    infos: List[str] = []
    
    # --- Check version ---
    if 'version' not in plan:
        raise ValidationError(
            "Missing required field 'version'",
            path="version",
            expected="integer (e.g., 1)"
        )
    
    version = plan.get('version')
    if not isinstance(version, int):
        raise ValidationError(
            "Field 'version' must be an integer",
            path="version",
            value=version,
            expected="int"
        )
    
    if version != 1:
        warnings.append(f"Warning: version={version}, validator only supports version=1")
    
    # --- Check nodes ---
    if 'nodes' not in plan:
        raise ValidationError(
            "Missing required field 'nodes'",
            path="nodes",
            expected="object with nodes"
        )
    
    nodes = plan.get('nodes')
    if not isinstance(nodes, dict):
        raise ValidationError(
            "Field 'nodes' must be an object",
            path="nodes",
            value=type(nodes).__name__,
            expected="object (dict)"
        )
    
    # Collect all node_ids for reference checking
    node_ids: Set[str] = set(nodes.keys())
    
    # Collect statuses (if defined)
    statuses: Set[str] = set()
    if 'statuses' in plan:
        statuses_data = plan.get('statuses')
        if isinstance(statuses_data, dict):
            statuses = set(statuses_data.keys())
    
    # --- Validate each node ---
    for node_id, node in nodes.items():
        node_path = f"nodes.{node_id}"
        
        # Check node type
        if not isinstance(node, dict):
            raise ValidationError(
                "Node must be an object",
                path=node_path,
                value=type(node).__name__,
                expected="object (dict)"
            )
        
        # Check required field title
        if 'title' not in node:
            raise ValidationError(
                "Missing required field 'title'",
                path=f"{node_path}.title",
                expected="non-empty string"
            )
        
        title = node.get('title')
        if not isinstance(title, str) or not title.strip():
            raise ValidationError(
                "Field 'title' must be a non-empty string",
                path=f"{node_path}.title",
                value=title,
                expected="non-empty string"
            )
        
        # Check parent (referential integrity)
        if 'parent' in node:
            parent = node.get('parent')
            if parent is not None:
                if not isinstance(parent, str):
                    raise ValidationError(
                        "Field 'parent' must be a string",
                        path=f"{node_path}.parent",
                        value=parent,
                        expected="string (node_id)"
                    )
                if parent not in node_ids:
                    raise ValidationError(
                        "Reference to non-existent node",
                        path=f"{node_path}.parent",
                        value=parent,
                        expected="existing node_id",
                        available=list(node_ids)
                    )
        
        # Check after (referential integrity)
        if 'after' in node:
            after = node.get('after')
            if after is not None:
                if not isinstance(after, list):
                    raise ValidationError(
                        "Field 'after' must be a list",
                        path=f"{node_path}.after",
                        value=type(after).__name__,
                        expected="list of strings"
                    )
                
                for i, dep in enumerate(after):
                    if not isinstance(dep, str):
                        raise ValidationError(
                            "Element of 'after' list must be a string",
                            path=f"{node_path}.after[{i}]",
                            value=dep,
                            expected="string (node_id)"
                        )
                    if dep not in node_ids:
                        raise ValidationError(
                            "Reference to non-existent node in dependencies",
                            path=f"{node_path}.after[{i}]",
                            value=dep,
                            expected="existing node_id",
                            available=list(node_ids)
                        )
        
        # Check status (referential integrity)
        if 'status' in node:
            status = node.get('status')
            if status is not None:
                if not isinstance(status, str):
                    raise ValidationError(
                        "Field 'status' must be a string",
                        path=f"{node_path}.status",
                        value=status,
                        expected="string (status_id)"
                    )
                if statuses and status not in statuses:
                    raise ValidationError(
                        "Reference to non-existent status",
                        path=f"{node_path}.status",
                        value=status,
                        expected="existing status_id",
                        available=list(statuses)
                    )
        
        # Check start format (YYYY-MM-DD)
        if 'start' in node:
            start = node.get('start')
            if start is not None:
                start_str = str(start)
                if not re.match(r'^\d{4}-\d{2}-\d{2}$', start_str):
                    raise ValidationError(
                        "Invalid date format",
                        path=f"{node_path}.start",
                        value=start,
                        expected="format YYYY-MM-DD (e.g., 2024-01-15)"
                    )
                # Check date validity
                try:
                    from datetime import datetime
                    datetime.strptime(start_str, '%Y-%m-%d')
                except ValueError:
                    raise ValidationError(
                        "Invalid date (does not exist in calendar)",
                        path=f"{node_path}.start",
                        value=start,
                        expected="existing date in YYYY-MM-DD format"
                    )
        
        # Check finish format (YYYY-MM-DD)
        if 'finish' in node:
            finish = node.get('finish')
            if finish is not None:
                finish_str = str(finish)
                if not re.match(r'^\d{4}-\d{2}-\d{2}$', finish_str):
                    raise ValidationError(
                        "Invalid date format",
                        path=f"{node_path}.finish",
                        value=finish,
                        expected="format YYYY-MM-DD (e.g., 2024-01-15)"
                    )
                # Check date validity
                try:
                    from datetime import datetime
                    datetime.strptime(finish_str, '%Y-%m-%d')
                except ValueError:
                    raise ValidationError(
                        "Invalid date (does not exist in calendar)",
                        path=f"{node_path}.finish",
                        value=finish,
                        expected="existing date in YYYY-MM-DD format"
                    )
        
        # Check duration format (<number><unit>)
        if 'duration' in node:
            duration = node.get('duration')
            if duration is not None:
                duration_str = str(duration)
                if not re.match(r'^[1-9][0-9]*[dw]$', duration_str):
                    raise ValidationError(
                        "Invalid duration format",
                        path=f"{node_path}.duration",
                        value=duration,
                        expected="format <number><unit>, where number >= 1, unit: d (days) or w (weeks)"
                    )
        
        # Check consistency of start + finish + duration
        start_val = node.get('start')
        finish_val = node.get('finish')
        duration_val = node.get('duration')
        
        if start_val and finish_val and duration_val:
            # All three specified — check consistency
            try:
                computed_finish = compute_finish_date(str(start_val), str(duration_val))
                if computed_finish != str(finish_val):
                    raise ValidationError(
                        "Inconsistent start, finish and duration",
                        path=f"{node_path}",
                        value=f"start={start_val}, finish={finish_val}, duration={duration_val}",
                        expected=f"finish should be {computed_finish} (computed from start+duration)"
                    )
            except (ValueError, KeyError):
                pass  # Skip if format is incorrect (already caught above)
    
    # --- Check circular dependencies ---
    _check_cycles_parent(nodes)
    _check_cycles_after(nodes)
    
    # --- Check after chains without anchor ---
    _check_after_chains_have_anchor(nodes, warnings)
    
    # --- Check start and after conflicts ---
    for node_id, node in nodes.items():
        if not isinstance(node, dict):
            continue
        
        start = node.get('start')
        after = node.get('after')
        
        if start and after and isinstance(after, list):
            # Node has both start and after — check for conflict
            start_str = str(start)
            
            # Compute maximum finish among dependencies
            max_finish = None
            for dep_id in after:
                dep_node = nodes.get(dep_id)
                if not isinstance(dep_node, dict):
                    continue
                
                dep_start = dep_node.get('start')
                dep_duration = dep_node.get('duration', '1d')  # Default 1d
                
                if dep_start:
                    try:
                        dep_finish = compute_finish_date(str(dep_start), str(dep_duration))
                        if max_finish is None or dep_finish > max_finish:
                            max_finish = dep_finish
                    except (ValueError, KeyError):
                        pass  # Skip incorrect data
            
            if max_finish and start_str < max_finish:
                warnings.append(
                    f"Warning: nodes.{node_id}.start ({start_str}) is before "
                    f"dependency finish ({max_finish}). This may be intentional "
                    f"(parallel work) or a planning error."
                )
        
        # Check missing duration for scheduled node (info)
        if start and 'duration' not in node:
            infos.append(
                f"Info: nodes.{node_id} has no duration, using default value 1d"
            )
    
    return warnings, infos


def _check_cycles_parent(nodes: Dict[str, Any]) -> None:
    """
    Checks for absence of circular references via parent.
    
    Raises:
        ValidationError: when cycle is found
    """
    for node_id in nodes:
        visited: Set[str] = set()
        current = node_id
        
        while current:
            if current in visited:
                # Found cycle
                cycle_path = _build_cycle_path(nodes, node_id, 'parent')
                raise ValidationError(
                    "Circular reference detected via parent",
                    path=f"nodes.{node_id}.parent",
                    value=cycle_path,
                    expected="acyclic parent relationship graph"
                )
            
            visited.add(current)
            node = nodes.get(current, {})
            current = node.get('parent') if isinstance(node, dict) else None


def _check_cycles_after(nodes: Dict[str, Any]) -> None:
    """
    Checks for absence of circular dependencies via after.
    
    Uses depth-first search (DFS) algorithm to detect cycles.
    
    Raises:
        ValidationError: when cycle is found
    """
    # States: 0 = not visited, 1 = in progress, 2 = completed
    state: Dict[str, int] = {node_id: 0 for node_id in nodes}
    
    def dfs(node_id: str, path: List[str]) -> None:
        if state[node_id] == 2:
            return
        
        if state[node_id] == 1:
            # Found cycle
            cycle_start = path.index(node_id)
            cycle = path[cycle_start:] + [node_id]
            raise ValidationError(
                "Circular dependency detected via after",
                path=f"nodes.{node_id}.after",
                value=" -> ".join(cycle),
                expected="acyclic dependency graph"
            )
        
        state[node_id] = 1
        path.append(node_id)
        
        node = nodes.get(node_id, {})
        after = node.get('after', []) if isinstance(node, dict) else []
        
        if isinstance(after, list):
            for dep in after:
                if dep in nodes:
                    dfs(dep, path)
        
        path.pop()
        state[node_id] = 2
    
    for node_id in nodes:
        if state[node_id] == 0:
            dfs(node_id, [])


def _build_cycle_path(nodes: Dict[str, Any], start_id: str, field: str) -> str:
    """Builds string representation of cycle for error message."""
    path = [start_id]
    current = start_id
    
    while True:
        node = nodes.get(current, {})
        next_id = node.get(field) if isinstance(node, dict) else None
        
        if next_id is None:
            break
        
        if next_id in path:
            path.append(next_id)
            break
        
        path.append(next_id)
        current = next_id
    
    return " -> ".join(path)


def _check_after_chains_have_anchor(nodes: Dict[str, Any], warnings: List[str]) -> None:
    """
    Checks that after chains have at least one anchor (start or finish).
    
    Nodes with after leading to unscheduled nodes cause validation error.
    
    Args:
        nodes: Nodes dictionary
        warnings: List to add warnings to (not used, error = exception)
        
    Raises:
        ValidationError: if after chain has no anchor
    """
    # Find nodes that can be scheduled (have start, finish, or reachable via after)
    schedulable: Set[str] = set()
    
    # First pass: mark nodes with explicit start or finish
    for node_id, node in nodes.items():
        if not isinstance(node, dict):
            continue
        if node.get('start') or node.get('finish'):
            schedulable.add(node_id)
    
    # Second pass: propagate schedulability via after chains
    changed = True
    while changed:
        changed = False
        for node_id, node in nodes.items():
            if node_id in schedulable:
                continue
            if not isinstance(node, dict):
                continue
            
            after = node.get('after', [])
            if after and isinstance(after, list):
                # If all dependencies are schedulable, node is schedulable too
                if all(dep in schedulable for dep in after if dep in nodes):
                    schedulable.add(node_id)
                    changed = True
    
    # Third pass: check nodes with after that didn't become schedulable
    for node_id, node in nodes.items():
        if not isinstance(node, dict):
            continue
        
        after = node.get('after', [])
        if after and isinstance(after, list) and after:
            if node_id not in schedulable:
                # Find unschedulable dependencies
                unschedulable_deps = [dep for dep in after if dep not in schedulable and dep in nodes]
                if unschedulable_deps:
                    raise ValidationError(
                        "after chain has no anchor (start/finish) — cannot be scheduled",
                        path=f"nodes.{node_id}.after",
                        value=after,
                        expected=f"at least one dependency must be schedulable. Unschedulable: {', '.join(unschedulable_deps)}"
                    )


# ============================================================================
# Views Validation
# ============================================================================

def validate_views(views: Dict[str, Any], plan: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    """
    Validates views file against plan file.
    
    Checks:
    - Required fields (version, project)
    - Match between project and plan's meta.id
    - Node references in views
    
    Returns:
        Tuple (warnings, infos)
    
    Raises:
        ValidationError: when critical error is found
    """
    warnings: List[str] = []
    infos: List[str] = []
    
    # --- Check version ---
    if 'version' not in views:
        raise ValidationError(
            "Missing required field 'version'",
            path="version",
            expected="integer (e.g., 1)"
        )
    
    version = views.get('version')
    if not isinstance(version, int):
        raise ValidationError(
            "Field 'version' must be an integer",
            path="version",
            value=version,
            expected="int"
        )
    
    # --- Check project ---
    if 'project' not in views:
        raise ValidationError(
            "Missing required field 'project'",
            path="project",
            expected="string matching plan's meta.id"
        )
    
    project = views.get('project')
    if not isinstance(project, str):
        raise ValidationError(
            "Field 'project' must be a string",
            path="project",
            value=project,
            expected="string"
        )
    
    # --- Check project matches meta.id ---
    meta = plan.get('meta', {})
    plan_id = meta.get('id') if isinstance(meta, dict) else None
    
    # meta.id is required when using views
    if not plan_id:
        raise ValidationError(
            "Field 'meta.id' is required in plan when using views file",
            path="meta.id",
            expected="non-empty string (project identifier)"
        )
    
    if project != plan_id:
        raise ValidationError(
            "Field 'project' does not match plan's meta.id",
            path="project",
            value=project,
            expected=f"'{plan_id}' (value of meta.id from plan)"
        )
    
    # --- Check node references in gantt_views ---
    node_ids: Set[str] = set(plan.get('nodes', {}).keys())
    
    gantt_views = views.get('gantt_views')
    if gantt_views is not None:
        if not isinstance(gantt_views, dict):
            raise ValidationError(
                "Field 'gantt_views' must be an object",
                path="gantt_views",
                value=type(gantt_views).__name__,
                expected="object (dict)"
            )
        
        for view_id, view in gantt_views.items():
            view_path = f"gantt_views.{view_id}"
            
            if not isinstance(view, dict):
                raise ValidationError(
                    "View must be an object",
                    path=view_path,
                    value=type(view).__name__,
                    expected="object (dict)"
                )
            
            # Check excludes: core vs non-core
            excludes = view.get('excludes')
            if excludes is not None:
                if isinstance(excludes, list):
                    for item in excludes:
                        if isinstance(item, str):
                            # Check if this is a core exclude
                            is_core = (
                                item == "weekends" or
                                re.match(r'^\d{4}-\d{2}-\d{2}$', item)
                            )
                            
                            if is_core:
                                if re.match(r'^\d{4}-\d{2}-\d{2}$', item):
                                    infos.append(
                                        f"Info: {view_path}.excludes contains date '{item}' "
                                        f"(core exclude, affects date calculation)."
                                    )
                            else:
                                warnings.append(
                                    f"Warning: {view_path}.excludes contains non-core value '{item}'. "
                                    f"Non-core excludes are not standardized and will be ignored by portable tools."
                                )
            
            lanes = view.get('lanes')
            if lanes is None:
                raise ValidationError(
                    "Missing required field 'lanes'",
                    path=f"{view_path}.lanes",
                    expected="non-empty object with lanes"
                )
            
            if not isinstance(lanes, dict) or not lanes:
                raise ValidationError(
                    "Field 'lanes' must be a non-empty object",
                    path=f"{view_path}.lanes",
                    value=lanes,
                    expected="non-empty object (dict)"
                )
            
            for lane_id, lane in lanes.items():
                lane_path = f"{view_path}.lanes.{lane_id}"
                
                if not isinstance(lane, dict):
                    raise ValidationError(
                        "Lane must be an object",
                        path=lane_path,
                        value=type(lane).__name__,
                        expected="object (dict)"
                    )
                
                lane_nodes = lane.get('nodes')
                if lane_nodes is None:
                    raise ValidationError(
                        "Missing required field 'nodes'",
                        path=f"{lane_path}.nodes",
                        expected="list of node_ids"
                    )
                
                if not isinstance(lane_nodes, list):
                    raise ValidationError(
                        "Field 'nodes' must be a list",
                        path=f"{lane_path}.nodes",
                        value=type(lane_nodes).__name__,
                        expected="list of strings"
                    )
                
                for i, ref_node_id in enumerate(lane_nodes):
                    if not isinstance(ref_node_id, str):
                        raise ValidationError(
                            "Element of 'nodes' list must be a string",
                            path=f"{lane_path}.nodes[{i}]",
                            value=ref_node_id,
                            expected="string (node_id)"
                        )
                    
                    if ref_node_id not in node_ids:
                        raise ValidationError(
                            "Reference to non-existent node in plan",
                            path=f"{lane_path}.nodes[{i}]",
                            value=ref_node_id,
                            expected="existing node_id from plan",
                            available=list(node_ids)
                        )
    
    return warnings, infos


# ============================================================================
# JSON Schema Validation
# ============================================================================

def validate_with_schema(data: Dict[str, Any], schema: Dict[str, Any], 
                         file_type: str) -> List[str]:
    """
    Validates data using JSON Schema.
    
    Requires: jsonschema library (pip install jsonschema)
    
    Returns:
        List of warnings
    
    Raises:
        ValidationError: when schema validation fails
    """
    try:
        import jsonschema
    except ImportError:
        raise ValidationError(
            "JSON Schema validation requires jsonschema library",
            expected="pip install jsonschema"
        )
    
    try:
        jsonschema.validate(instance=data, schema=schema)
        return []
    except jsonschema.ValidationError as e:
        path = '.'.join(str(p) for p in e.absolute_path) if e.absolute_path else '(root)'
        raise ValidationError(
            f"JSON Schema validation failed: {e.message}",
            path=path,
            value=e.instance if not isinstance(e.instance, dict) else type(e.instance).__name__,
            expected=str(e.schema.get('type', e.schema.get('description', 'see schema')))
        )


# ============================================================================
# CLI Interface
# ============================================================================

def get_script_dir() -> Path:
    """Returns directory where script is located."""
    return Path(__file__).parent.resolve()


def get_schemas_dir() -> Path:
    """Returns path to schemas/ directory relative to script."""
    return get_script_dir().parent / 'schemas'


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description='Validator for opskarta plan and views files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Usage examples:
  python validate.py plan.yaml                    # Validate plan
  python validate.py plan.yaml views.yaml         # Validate plan and views
  python validate.py --schema plan.yaml           # Validate using JSON Schema

Validation levels:
  By default, semantic validation is performed (referential integrity,
  business rules). With --schema flag, JSON Schema compliance is also checked.
        """
    )
    
    parser.add_argument(
        'plan_file',
        type=Path,
        help='Path to plan file (*.plan.yaml)'
    )
    
    parser.add_argument(
        'views_file',
        type=Path,
        nargs='?',
        default=None,
        help='Path to views file (*.views.yaml), optional'
    )
    
    parser.add_argument(
        '--schema',
        action='store_true',
        help='Additionally validate using JSON Schema'
    )
    
    parser.add_argument(
        '--plan-schema',
        type=Path,
        default=None,
        help='Path to JSON Schema for plan (default: schemas/plan.schema.json)'
    )
    
    parser.add_argument(
        '--views-schema',
        type=Path,
        default=None,
        help='Path to JSON Schema for views (default: schemas/views.schema.json)'
    )
    
    args = parser.parse_args()
    
    all_warnings: List[str] = []
    all_infos: List[str] = []
    
    try:
        # --- Load and validate plan ---
        print(f"Validating plan: {args.plan_file}")
        plan = load_yaml(args.plan_file)
        
        # JSON Schema validation (if requested)
        if args.schema:
            schemas_dir = get_schemas_dir()
            plan_schema_path = args.plan_schema or (schemas_dir / 'plan.schema.json')
            
            print(f"  Checking JSON Schema: {plan_schema_path}")
            plan_schema = load_json_schema(plan_schema_path)
            schema_warnings = validate_with_schema(plan, plan_schema, 'plan')
            all_warnings.extend(schema_warnings)
        
        # Semantic validation
        print("  Semantic validation...")
        plan_warnings, plan_infos = validate_plan(plan)
        all_warnings.extend(plan_warnings)
        all_infos.extend(plan_infos)
        
        print(f"  ✓ Plan is valid")
        
        # --- Load and validate views (if specified) ---
        if args.views_file:
            print(f"\nValidating views: {args.views_file}")
            views = load_yaml(args.views_file)
            
            # JSON Schema validation (if requested)
            if args.schema:
                views_schema_path = args.views_schema or (schemas_dir / 'views.schema.json')
                
                print(f"  Checking JSON Schema: {views_schema_path}")
                views_schema = load_json_schema(views_schema_path)
                schema_warnings = validate_with_schema(views, views_schema, 'views')
                all_warnings.extend(schema_warnings)
            
            # Semantic validation
            print("  Semantic validation...")
            views_warnings, views_infos = validate_views(views, plan)
            all_warnings.extend(views_warnings)
            all_infos.extend(views_infos)
            
            print(f"  ✓ Views are valid")
        
        # --- Output warnings ---
        if all_warnings:
            print("\nWarnings:")
            for warning in all_warnings:
                print(f"  ⚠ {warning}")
        
        # --- Output info messages ---
        if all_infos:
            print("\nInfo:")
            for info in all_infos:
                print(f"  ℹ {info}")
        
        print("\n✓ Validation completed successfully")
        sys.exit(0)
        
    except ValidationError as e:
        print(f"\n{e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        sys.exit(130)


if __name__ == '__main__':
    main()
