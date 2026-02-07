"""
Scheduler for opskarta v2 plans.

This module computes dates for scheduled nodes using the "overlay schedule"
concept where only nodes explicitly included in schedule.nodes participate
in date calculation.

Key concepts:
- included: Node is present in schedule.nodes
- computed: Node's dates were successfully calculated
- unschedulable: Node is included but dates cannot be computed (warning)

Algorithm:
1. Identify scheduled nodes (present in schedule.nodes)
2. For each scheduled node, compute start/finish with memoization
3. Dependencies (after) come from nodes, not schedule.nodes
4. Only scheduled dependencies are considered for date calculation
5. If all dependencies are unschedulable, node is also unschedulable

Requirements covered:
- 3.10: Use default_calendar when Schedule_Node doesn't have calendar
- 3.11: Include nodes in schedule.nodes in calculation
- 3.12: Exclude nodes not in schedule.nodes from calculation
- 3.13: Consider only scheduled dependencies for date calculation
- 3.14: Use explicit start or mark as unschedulable when all deps unscheduled
"""

import re
from datetime import date, timedelta
from typing import Optional

from specs.v2.tools.models import Calendar, MergedPlan


# Duration pattern: Nd (days) or Nw (weeks)
DURATION_PATTERN = re.compile(r"^([1-9][0-9]*)([dw])$")

# Date pattern: YYYY-MM-DD
DATE_PATTERN = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")


def parse_date(date_str: str) -> Optional[date]:
    """
    Parse a date string in YYYY-MM-DD format.
    
    Args:
        date_str: Date string in YYYY-MM-DD format
        
    Returns:
        date object or None if parsing fails
    """
    if not date_str:
        return None
    
    match = DATE_PATTERN.match(date_str)
    if not match:
        return None
    
    try:
        year = int(match.group(1))
        month = int(match.group(2))
        day = int(match.group(3))
        return date(year, month, day)
    except ValueError:
        return None


def format_date(d: date) -> str:
    """
    Format a date as YYYY-MM-DD string.
    
    Args:
        d: date object
        
    Returns:
        Date string in YYYY-MM-DD format
    """
    return d.isoformat()


def parse_duration(duration_str: str) -> Optional[int]:
    """
    Parse a duration string (Nd or Nw) to number of days.
    
    Args:
        duration_str: Duration string like "5d" (5 days) or "2w" (2 weeks)
        
    Returns:
        Number of days or None if parsing fails
    """
    if not duration_str:
        return None
    
    match = DURATION_PATTERN.match(duration_str)
    if not match:
        return None
    
    value = int(match.group(1))
    unit = match.group(2)
    
    if unit == "d":
        return value
    elif unit == "w":
        return value * 5  # 1 week = 5 working days (per spec)
    
    return None


def is_excluded_date(d: date, calendar: Calendar) -> bool:
    """
    Check if a date is excluded by the calendar.
    
    Args:
        d: Date to check
        calendar: Calendar with exclusions
        
    Returns:
        True if the date is excluded (non-working day)
    """
    for exclude in calendar.excludes:
        if exclude == "weekends":
            # Saturday = 5, Sunday = 6
            if d.weekday() >= 5:
                return True
        else:
            # Specific date in YYYY-MM-DD format
            excluded_date = parse_date(exclude)
            if excluded_date and d == excluded_date:
                return True
    
    return False


def is_workday(d: date, calendar: Calendar) -> bool:
    """
    Check if a date is a working day according to the calendar.
    
    Args:
        d: Date to check
        calendar: Calendar with exclusions
        
    Returns:
        True if the date is a working day
    """
    return not is_excluded_date(d, calendar)


def next_workday(d: date, calendar: Calendar) -> date:
    """
    Find the next working day after the given date.
    
    Args:
        d: Starting date (exclusive)
        calendar: Calendar with exclusions
        
    Returns:
        The next working day after d
    """
    result = d + timedelta(days=1)
    while not is_workday(result, calendar):
        result += timedelta(days=1)
    return result


def normalize_start(d: date, calendar: Calendar, is_milestone: bool) -> date:
    """
    Normalize a start date to a working day.
    
    For milestones, the date is returned as-is (milestones can be on any day).
    For regular nodes, if the date falls on a non-working day, it's moved
    to the next working day.
    
    Args:
        d: Start date to normalize
        calendar: Calendar with exclusions
        is_milestone: Whether the node is a milestone
        
    Returns:
        Normalized start date
    """
    if is_milestone:
        return d
    
    if is_workday(d, calendar):
        return d
    
    return next_workday(d - timedelta(days=1), calendar)


def add_workdays(start: date, days: int, calendar: Calendar) -> date:
    """
    Add working days to a start date.
    
    Args:
        start: Starting date (inclusive)
        days: Number of working days to add (0 means same day)
        calendar: Calendar with exclusions
        
    Returns:
        The resulting date after adding working days
    """
    if days <= 0:
        return start
    
    result = start
    remaining = days
    
    while remaining > 0:
        result += timedelta(days=1)
        if is_workday(result, calendar):
            remaining -= 1
    
    return result


def sub_workdays(end: date, days: int, calendar: Calendar) -> date:
    """
    Subtract working days from an end date.
    
    Args:
        end: Ending date (inclusive)
        days: Number of working days to subtract (0 means same day)
        calendar: Calendar with exclusions
        
    Returns:
        The resulting date after subtracting working days
    """
    if days <= 0:
        return end
    
    result = end
    remaining = days
    
    while remaining > 0:
        result -= timedelta(days=1)
        if is_workday(result, calendar):
            remaining -= 1
    
    return result


def compute_schedule(plan: MergedPlan) -> None:
    """
    Compute dates for scheduled nodes.
    
    This function calculates computed_start and computed_finish for all
    nodes present in schedule.nodes. It uses memoization to avoid
    redundant calculations.
    
    Key principles:
    - Only nodes in schedule.nodes participate in calculation
    - Dependencies (after) come from nodes, not schedule.nodes
    - Only scheduled dependencies are considered
    - Uses memoization to avoid repeated calculations
    
    Node states:
    - included: present in schedule.nodes
    - computed: dates successfully calculated
    - unschedulable: included but dates cannot be computed (warning)
    
    Args:
        plan: MergedPlan with schedule to process. Schedule nodes are
              modified in-place with computed_start and computed_finish.
              Warnings are added to plan.schedule.warnings.
    
    Requirements:
        - 3.10: Use default_calendar when calendar not specified
        - 3.11: Include nodes in schedule.nodes in calculation
        - 3.12: Exclude nodes not in schedule.nodes from calculation
        - 3.13: Consider only scheduled dependencies for date calculation
        - 3.14: Use explicit start or mark as unschedulable
    """
    # Skip if no schedule block (Requirement 3.1, 3.2 - schedule is optional)
    if plan.schedule is None:
        return
    
    # Set of scheduled node IDs (Requirement 3.11, 3.12)
    scheduled_ids = set(plan.schedule.nodes.keys())
    
    if not scheduled_ids:
        return
    
    # Memoization cache: node_id -> (start, finish) or None if unschedulable
    cache: dict[str, tuple[Optional[date], Optional[date]]] = {}
    
    # Warnings collection
    warnings: list[str] = []
    
    def get_calendar(node_id: str) -> Calendar:
        """
        Get the calendar for a scheduled node.
        
        Uses the node's explicit calendar if set, otherwise falls back
        to default_calendar. If neither is available, returns an empty
        calendar (no exclusions).
        
        Requirement: 3.10
        """
        sn = plan.schedule.nodes[node_id]
        cal_id = sn.calendar or plan.schedule.default_calendar
        
        if cal_id and cal_id in plan.schedule.calendars:
            return plan.schedule.calendars[cal_id]
        
        # Return empty calendar if no calendar found
        return Calendar(excludes=[])
    
    def compute_dates(node_id: str) -> tuple[Optional[date], Optional[date]]:
        """
        Compute start and finish dates for a scheduled node with memoization.
        
        Returns (start, finish) tuple. If dates cannot be computed,
        returns (None, None) and adds a warning.
        """
        # Check memoization cache
        if node_id in cache:
            return cache[node_id]
        
        sn = plan.schedule.nodes[node_id]
        node = plan.nodes.get(node_id)
        
        if node is None:
            # Node doesn't exist in nodes (should be caught by validator)
            cache[node_id] = (None, None)
            return (None, None)
        
        calendar = get_calendar(node_id)
        is_milestone = node.milestone
        
        start: Optional[date] = None
        finish: Optional[date] = None
        
        # Priority 1: Explicit start date
        if sn.start:
            parsed_start = parse_date(sn.start)
            if parsed_start:
                start = normalize_start(parsed_start, calendar, is_milestone)
        
        # Priority 2: finish + duration (backward scheduling)
        elif sn.finish and sn.duration:
            parsed_finish = parse_date(sn.finish)
            duration_days = parse_duration(sn.duration)
            
            if parsed_finish and duration_days:
                # Subtract duration from finish to get start
                # duration is in working days, so we need to subtract (duration - 1)
                # because both start and finish are inclusive
                start = sub_workdays(parsed_finish, duration_days - 1, calendar)
        
        # Priority 3: Dependencies (after) - only scheduled ones (Requirement 3.13)
        elif node.after:
            scheduled_deps = [dep_id for dep_id in node.after if dep_id in scheduled_ids]
            
            if scheduled_deps:
                # Compute finish dates for all scheduled dependencies
                dep_finishes: list[date] = []
                
                for dep_id in scheduled_deps:
                    _, dep_finish = compute_dates(dep_id)
                    if dep_finish is not None:
                        dep_finishes.append(dep_finish)
                
                if dep_finishes:
                    # Start after the latest dependency finishes
                    max_finish = max(dep_finishes)
                    
                    if is_milestone:
                        # Milestones can start on the same day as dependency finish
                        start = max_finish
                    else:
                        # Regular nodes start on the next working day
                        start = next_workday(max_finish, calendar)
                else:
                    # All scheduled dependencies are unschedulable (Requirement 3.14)
                    warnings.append(
                        f"Node '{node_id}': all scheduled dependencies are unschedulable"
                    )
            # else: no scheduled dependencies, fall through to unschedulable
        
        # Compute finish date if we have a start
        if start is not None:
            if sn.finish:
                # Explicit finish date
                parsed_finish = parse_date(sn.finish)
                if parsed_finish:
                    finish = parsed_finish
                else:
                    # Invalid finish date, compute from duration
                    duration_days = parse_duration(sn.duration) if sn.duration else 1
                    finish = add_workdays(start, duration_days - 1, calendar)
            else:
                # Compute finish from duration (default: 1 day for milestones)
                duration_days = parse_duration(sn.duration) if sn.duration else 1
                
                if is_milestone:
                    # Milestones have zero duration (finish = start)
                    finish = start
                else:
                    # Regular nodes: add (duration - 1) working days
                    finish = add_workdays(start, duration_days - 1, calendar)
        else:
            # Node is unschedulable (Requirement 3.14)
            if node_id not in [w.split("'")[1] for w in warnings if "'" in w]:
                warnings.append(f"Node '{node_id}': cannot compute start date")
        
        # Store in cache
        cache[node_id] = (start, finish)
        return (start, finish)
    
    # Compute dates for all scheduled nodes
    for node_id in scheduled_ids:
        sn = plan.schedule.nodes[node_id]
        start, finish = compute_dates(node_id)
        
        # Store computed dates as strings
        sn.computed_start = format_date(start) if start else None
        sn.computed_finish = format_date(finish) if finish else None
    
    # Store warnings in schedule
    plan.schedule.warnings = warnings
