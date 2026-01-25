from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

from .errors import SchedulingError


def parse_date(value: str) -> date:
    try:
        y, m, d = value.split("-")
        return date(int(y), int(m), int(d))
    except Exception as e:  # noqa: BLE001
        raise SchedulingError(f"Invalid date: {value!r}. Expected YYYY-MM-DD") from e


def parse_duration(value: Any) -> int:
    """Return duration in days (integer). Accepts '10d' or int."""
    if value is None:
        return 1
    if isinstance(value, int):
        if value <= 0:
            raise SchedulingError(f"Duration must be positive, got {value}")
        return value
    if isinstance(value, str):
        s = value.strip()
        if s.isdigit():
            n = int(s)
            if n <= 0:
                raise SchedulingError(f"Duration must be positive, got {value!r}")
            return n
        if s.endswith("d") and s[:-1].isdigit():
            n = int(s[:-1])
            if n <= 0:
                raise SchedulingError(f"Duration must be positive, got {value!r}")
            return n
    raise SchedulingError(f"Unsupported duration format: {value!r} (expected int or 'Nd')")


def is_weekend(d: date) -> bool:
    return d.weekday() >= 5  # 5=Sat, 6=Sun


def next_workday(d: date) -> date:
    cur = d + timedelta(days=1)
    while is_weekend(cur):
        cur += timedelta(days=1)
    return cur


def add_workdays(start: date, workdays: int) -> date:
    """Add N workdays to start (N may be 0)."""
    cur = start
    step = 1 if workdays >= 0 else -1
    remaining = abs(workdays)
    while remaining > 0:
        cur += timedelta(days=step)
        if not is_weekend(cur):
            remaining -= 1
    return cur


def finish_date(start: date, duration_days: int, exclude_weekends: bool) -> date:
    # duration is inclusive of the start day: 1d => finish == start
    if duration_days <= 1:
        return start
    if exclude_weekends:
        return add_workdays(start, duration_days - 1)
    return start + timedelta(days=duration_days - 1)


@dataclass(frozen=True)
class ScheduledNode:
    start: date
    finish: date
    duration_days: int


def compute_schedule(nodes: Dict[str, Dict[str, Any]], exclude_weekends: bool) -> Dict[str, ScheduledNode]:
    """Compute start/finish for nodes based on explicit start and `after` dependencies."""
    cache: Dict[str, ScheduledNode] = {}
    visiting: Set[str] = set()

    def resolve(node_id: str) -> ScheduledNode:
        if node_id in cache:
            return cache[node_id]
        if node_id in visiting:
            raise SchedulingError(f"Cycle detected while scheduling: {node_id}")
        if node_id not in nodes:
            raise SchedulingError(f"Unknown node referenced: {node_id}")

        visiting.add(node_id)
        node = nodes[node_id]

        duration_days = parse_duration(node.get("duration"))
        start_value = node.get("start")

        if isinstance(start_value, datetime):
            start = start_value.date()
        elif isinstance(start_value, date):
            start = start_value
        elif isinstance(start_value, str) and start_value.strip():
            start = parse_date(start_value.strip())
        else:
            after: List[str] = node.get("after") or []
            if not after:
                raise SchedulingError(
                    f"Node {node_id!r} has no 'start' and no 'after' dependencies. "
                    "Provide start date or dependencies."
                )

            # Start after the latest dependency finishes
            dep_finishes: List[date] = []
            for dep_id in after:
                dep_sched = resolve(dep_id)
                dep_finishes.append(dep_sched.finish)

            latest = max(dep_finishes)
            start = next_workday(latest) if exclude_weekends else latest + timedelta(days=1)

        finish = finish_date(start, duration_days, exclude_weekends)
        sched = ScheduledNode(start=start, finish=finish, duration_days=duration_days)
        cache[node_id] = sched
        visiting.remove(node_id)
        return sched

    for node_id in nodes.keys():
        # We only schedule nodes that have either start or after or duration usage in views.
        # For simplicity: try to resolve everything, but skip nodes without any scheduling info.
        node = nodes[node_id]
        if node.get("start") is None and not node.get("after"):
            # Skip unscheduled nodes quietly (they might be pure containers).
            continue
        resolve(node_id)

    return cache
