"""
Tests for the scheduler module.

Tests cover:
- 3.10: Use default_calendar when Schedule_Node doesn't have calendar
- 3.11: Include nodes in schedule.nodes in calculation
- 3.12: Exclude nodes not in schedule.nodes from calculation
- 3.13: Consider only scheduled dependencies for date calculation
- 3.14: Use explicit start or mark as unschedulable when all deps unscheduled
"""

import unittest
from datetime import date

from specs.v2.tools.models import (
    Calendar,
    MergedPlan,
    Node,
    Schedule,
    ScheduleNode,
)
from specs.v2.tools.scheduler import (
    add_workdays,
    compute_schedule,
    is_workday,
    next_workday,
    normalize_start,
    parse_date,
    parse_duration,
    sub_workdays,
)


class TestParseDateFunction(unittest.TestCase):
    """Tests for parse_date helper function."""

    def test_valid_date(self):
        """Parse valid YYYY-MM-DD date."""
        result = parse_date("2024-03-15")
        self.assertEqual(result, date(2024, 3, 15))

    def test_invalid_format(self):
        """Invalid format returns None."""
        self.assertIsNone(parse_date("15-03-2024"))
        self.assertIsNone(parse_date("2024/03/15"))
        self.assertIsNone(parse_date("invalid"))

    def test_empty_string(self):
        """Empty string returns None."""
        self.assertIsNone(parse_date(""))

    def test_invalid_date_values(self):
        """Invalid date values return None."""
        self.assertIsNone(parse_date("2024-13-01"))  # Invalid month
        self.assertIsNone(parse_date("2024-02-30"))  # Invalid day


class TestParseDurationFunction(unittest.TestCase):
    """Tests for parse_duration helper function."""

    def test_days(self):
        """Parse duration in days."""
        self.assertEqual(parse_duration("5d"), 5)
        self.assertEqual(parse_duration("1d"), 1)
        self.assertEqual(parse_duration("10d"), 10)
        self.assertEqual(parse_duration("100d"), 100)

    def test_weeks(self):
        """Parse duration in weeks (converted to days)."""
        self.assertEqual(parse_duration("1w"), 7)
        self.assertEqual(parse_duration("2w"), 14)
        self.assertEqual(parse_duration("4w"), 28)

    def test_invalid_format(self):
        """Invalid format returns None."""
        self.assertIsNone(parse_duration("0d"))  # Zero not allowed
        self.assertIsNone(parse_duration("5"))   # Missing unit
        self.assertIsNone(parse_duration("d5"))  # Wrong order
        self.assertIsNone(parse_duration("5m"))  # Invalid unit

    def test_empty_string(self):
        """Empty string returns None."""
        self.assertIsNone(parse_duration(""))


class TestIsWorkdayFunction(unittest.TestCase):
    """Tests for is_workday helper function."""

    def test_weekday_no_exclusions(self):
        """Weekday with no exclusions is a workday."""
        calendar = Calendar(excludes=[])
        # Monday
        self.assertTrue(is_workday(date(2024, 3, 11), calendar))

    def test_weekend_excluded(self):
        """Weekend is not a workday when weekends excluded."""
        calendar = Calendar(excludes=["weekends"])
        # Saturday
        self.assertFalse(is_workday(date(2024, 3, 16), calendar))
        # Sunday
        self.assertFalse(is_workday(date(2024, 3, 17), calendar))

    def test_specific_date_excluded(self):
        """Specific date is not a workday when excluded."""
        calendar = Calendar(excludes=["2024-03-15"])
        self.assertFalse(is_workday(date(2024, 3, 15), calendar))
        self.assertTrue(is_workday(date(2024, 3, 14), calendar))

    def test_combined_exclusions(self):
        """Combined weekends and specific dates."""
        calendar = Calendar(excludes=["weekends", "2024-03-15"])
        # Friday (excluded by specific date)
        self.assertFalse(is_workday(date(2024, 3, 15), calendar))
        # Saturday (excluded by weekends)
        self.assertFalse(is_workday(date(2024, 3, 16), calendar))
        # Thursday (not excluded)
        self.assertTrue(is_workday(date(2024, 3, 14), calendar))


class TestNextWorkdayFunction(unittest.TestCase):
    """Tests for next_workday helper function."""

    def test_next_day_is_workday(self):
        """Next day is a workday."""
        calendar = Calendar(excludes=["weekends"])
        # Monday -> Tuesday
        result = next_workday(date(2024, 3, 11), calendar)
        self.assertEqual(result, date(2024, 3, 12))

    def test_skip_weekend(self):
        """Skip weekend to find next workday."""
        calendar = Calendar(excludes=["weekends"])
        # Friday -> Monday
        result = next_workday(date(2024, 3, 15), calendar)
        self.assertEqual(result, date(2024, 3, 18))

    def test_skip_multiple_excluded_days(self):
        """Skip multiple excluded days."""
        calendar = Calendar(excludes=["weekends", "2024-03-18"])
        # Friday -> Tuesday (skip Sat, Sun, Mon holiday)
        result = next_workday(date(2024, 3, 15), calendar)
        self.assertEqual(result, date(2024, 3, 19))


class TestNormalizeStartFunction(unittest.TestCase):
    """Tests for normalize_start helper function."""

    def test_workday_unchanged(self):
        """Workday start is unchanged."""
        calendar = Calendar(excludes=["weekends"])
        result = normalize_start(date(2024, 3, 11), calendar, False)
        self.assertEqual(result, date(2024, 3, 11))

    def test_weekend_moved_to_monday(self):
        """Weekend start is moved to Monday."""
        calendar = Calendar(excludes=["weekends"])
        # Saturday -> Monday
        result = normalize_start(date(2024, 3, 16), calendar, False)
        self.assertEqual(result, date(2024, 3, 18))

    def test_milestone_on_weekend_unchanged(self):
        """Milestone on weekend is unchanged."""
        calendar = Calendar(excludes=["weekends"])
        # Saturday stays Saturday for milestone
        result = normalize_start(date(2024, 3, 16), calendar, True)
        self.assertEqual(result, date(2024, 3, 16))


class TestAddWorkdaysFunction(unittest.TestCase):
    """Tests for add_workdays helper function."""

    def test_add_zero_days(self):
        """Adding zero days returns same date."""
        calendar = Calendar(excludes=["weekends"])
        result = add_workdays(date(2024, 3, 11), 0, calendar)
        self.assertEqual(result, date(2024, 3, 11))

    def test_add_days_no_weekend(self):
        """Add days without crossing weekend."""
        calendar = Calendar(excludes=["weekends"])
        # Monday + 2 workdays = Wednesday
        result = add_workdays(date(2024, 3, 11), 2, calendar)
        self.assertEqual(result, date(2024, 3, 13))

    def test_add_days_crossing_weekend(self):
        """Add days crossing weekend."""
        calendar = Calendar(excludes=["weekends"])
        # Thursday + 3 workdays = Tuesday (skip Sat, Sun)
        result = add_workdays(date(2024, 3, 14), 3, calendar)
        self.assertEqual(result, date(2024, 3, 19))

    def test_add_days_with_holiday(self):
        """Add days with holiday exclusion."""
        calendar = Calendar(excludes=["weekends", "2024-03-18"])
        # Thursday + 3 workdays = Wednesday (skip Sat, Sun, Mon holiday)
        result = add_workdays(date(2024, 3, 14), 3, calendar)
        self.assertEqual(result, date(2024, 3, 20))


class TestSubWorkdaysFunction(unittest.TestCase):
    """Tests for sub_workdays helper function."""

    def test_sub_zero_days(self):
        """Subtracting zero days returns same date."""
        calendar = Calendar(excludes=["weekends"])
        result = sub_workdays(date(2024, 3, 15), 0, calendar)
        self.assertEqual(result, date(2024, 3, 15))

    def test_sub_days_no_weekend(self):
        """Subtract days without crossing weekend."""
        calendar = Calendar(excludes=["weekends"])
        # Wednesday - 2 workdays = Monday
        result = sub_workdays(date(2024, 3, 13), 2, calendar)
        self.assertEqual(result, date(2024, 3, 11))

    def test_sub_days_crossing_weekend(self):
        """Subtract days crossing weekend."""
        calendar = Calendar(excludes=["weekends"])
        # Tuesday - 3 workdays = Thursday (skip Sat, Sun)
        result = sub_workdays(date(2024, 3, 19), 3, calendar)
        self.assertEqual(result, date(2024, 3, 14))


class TestComputeScheduleEmpty(unittest.TestCase):
    """Tests for compute_schedule with empty/no schedule."""

    def test_no_schedule_block(self):
        """Plan without schedule block should not raise errors."""
        plan = MergedPlan(
            nodes={"task1": Node(title="Task 1")}
        )
        
        compute_schedule(plan)
        
        # No schedule, nothing to compute
        self.assertIsNone(plan.schedule)

    def test_empty_schedule_nodes(self):
        """Schedule with no nodes should not raise errors."""
        plan = MergedPlan(
            nodes={"task1": Node(title="Task 1")},
            schedule=Schedule(nodes={})
        )
        
        compute_schedule(plan)
        
        self.assertEqual(len(plan.schedule.nodes), 0)


class TestComputeScheduleExplicitStart(unittest.TestCase):
    """Tests for compute_schedule with explicit start dates."""

    def test_explicit_start_and_duration(self):
        """Node with explicit start and duration."""
        plan = MergedPlan(
            nodes={"task1": Node(title="Task 1")},
            schedule=Schedule(
                calendars={"default": Calendar(excludes=["weekends"])},
                default_calendar="default",
                nodes={
                    "task1": ScheduleNode(start="2024-03-11", duration="5d")
                }
            )
        )
        
        compute_schedule(plan)
        
        sn = plan.schedule.nodes["task1"]
        self.assertEqual(sn.computed_start, "2024-03-11")
        # Monday + 4 workdays = Friday
        self.assertEqual(sn.computed_finish, "2024-03-15")

    def test_explicit_start_no_duration(self):
        """Node with explicit start, no duration (default 1 day)."""
        plan = MergedPlan(
            nodes={"task1": Node(title="Task 1")},
            schedule=Schedule(
                calendars={"default": Calendar(excludes=["weekends"])},
                default_calendar="default",
                nodes={
                    "task1": ScheduleNode(start="2024-03-11")
                }
            )
        )
        
        compute_schedule(plan)
        
        sn = plan.schedule.nodes["task1"]
        self.assertEqual(sn.computed_start, "2024-03-11")
        self.assertEqual(sn.computed_finish, "2024-03-11")

    def test_explicit_start_and_finish(self):
        """Node with explicit start and finish."""
        plan = MergedPlan(
            nodes={"task1": Node(title="Task 1")},
            schedule=Schedule(
                calendars={"default": Calendar(excludes=["weekends"])},
                default_calendar="default",
                nodes={
                    "task1": ScheduleNode(start="2024-03-11", finish="2024-03-15")
                }
            )
        )
        
        compute_schedule(plan)
        
        sn = plan.schedule.nodes["task1"]
        self.assertEqual(sn.computed_start, "2024-03-11")
        self.assertEqual(sn.computed_finish, "2024-03-15")


class TestComputeScheduleDefaultCalendar(unittest.TestCase):
    """Tests for default_calendar usage (Requirement 3.10)."""

    def test_uses_default_calendar(self):
        """Node without calendar uses default_calendar (Requirement 3.10)."""
        plan = MergedPlan(
            nodes={"task1": Node(title="Task 1")},
            schedule=Schedule(
                calendars={"work": Calendar(excludes=["weekends"])},
                default_calendar="work",
                nodes={
                    "task1": ScheduleNode(start="2024-03-15", duration="3d")
                }
            )
        )
        
        compute_schedule(plan)
        
        sn = plan.schedule.nodes["task1"]
        # Friday + 2 workdays = Tuesday (skip weekend)
        self.assertEqual(sn.computed_start, "2024-03-15")
        self.assertEqual(sn.computed_finish, "2024-03-19")

    def test_explicit_calendar_overrides_default(self):
        """Node with explicit calendar ignores default_calendar."""
        plan = MergedPlan(
            nodes={"task1": Node(title="Task 1")},
            schedule=Schedule(
                calendars={
                    "work": Calendar(excludes=["weekends"]),
                    "no_exclusions": Calendar(excludes=[])
                },
                default_calendar="work",
                nodes={
                    "task1": ScheduleNode(
                        start="2024-03-15",
                        duration="3d",
                        calendar="no_exclusions"
                    )
                }
            )
        )
        
        compute_schedule(plan)
        
        sn = plan.schedule.nodes["task1"]
        # Friday + 2 days = Sunday (no weekend exclusion)
        self.assertEqual(sn.computed_start, "2024-03-15")
        self.assertEqual(sn.computed_finish, "2024-03-17")

    def test_no_calendar_no_default(self):
        """Node without calendar and no default uses empty calendar."""
        plan = MergedPlan(
            nodes={"task1": Node(title="Task 1")},
            schedule=Schedule(
                calendars={},
                nodes={
                    "task1": ScheduleNode(start="2024-03-16", duration="3d")
                }
            )
        )
        
        compute_schedule(plan)
        
        sn = plan.schedule.nodes["task1"]
        # Saturday + 2 days = Monday (no exclusions)
        self.assertEqual(sn.computed_start, "2024-03-16")
        self.assertEqual(sn.computed_finish, "2024-03-18")


class TestComputeScheduleIncludedExcluded(unittest.TestCase):
    """Tests for included/excluded nodes (Requirements 3.11, 3.12)."""

    def test_only_scheduled_nodes_computed(self):
        """Only nodes in schedule.nodes get computed dates (Req 3.11, 3.12)."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1"),
                "task2": Node(title="Task 2"),
                "task3": Node(title="Task 3"),
            },
            schedule=Schedule(
                calendars={"default": Calendar(excludes=["weekends"])},
                default_calendar="default",
                nodes={
                    "task1": ScheduleNode(start="2024-03-11", duration="3d"),
                    # task2 not in schedule.nodes
                    "task3": ScheduleNode(start="2024-03-14", duration="2d"),
                }
            )
        )
        
        compute_schedule(plan)
        
        # task1 and task3 have computed dates
        self.assertEqual(plan.schedule.nodes["task1"].computed_start, "2024-03-11")
        self.assertEqual(plan.schedule.nodes["task3"].computed_start, "2024-03-14")
        
        # task2 is not in schedule.nodes, so no computed dates
        self.assertNotIn("task2", plan.schedule.nodes)


class TestComputeScheduleDependencies(unittest.TestCase):
    """Tests for dependency handling (Requirements 3.13, 3.14)."""

    def test_after_scheduled_dependency(self):
        """Node starts after scheduled dependency finishes (Req 3.13)."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1"),
                "task2": Node(title="Task 2", after=["task1"]),
            },
            schedule=Schedule(
                calendars={"default": Calendar(excludes=["weekends"])},
                default_calendar="default",
                nodes={
                    "task1": ScheduleNode(start="2024-03-11", duration="3d"),
                    "task2": ScheduleNode(duration="2d"),
                }
            )
        )
        
        compute_schedule(plan)
        
        # task1: Mon-Wed
        self.assertEqual(plan.schedule.nodes["task1"].computed_start, "2024-03-11")
        self.assertEqual(plan.schedule.nodes["task1"].computed_finish, "2024-03-13")
        
        # task2: starts Thu (next workday after Wed)
        self.assertEqual(plan.schedule.nodes["task2"].computed_start, "2024-03-14")
        self.assertEqual(plan.schedule.nodes["task2"].computed_finish, "2024-03-15")

    def test_after_unscheduled_dependency_ignored(self):
        """Unscheduled dependencies are ignored (Req 3.13)."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1"),  # Not scheduled
                "task2": Node(title="Task 2", after=["task1"]),
            },
            schedule=Schedule(
                calendars={"default": Calendar(excludes=["weekends"])},
                default_calendar="default",
                nodes={
                    # task1 not in schedule.nodes
                    "task2": ScheduleNode(duration="2d"),
                }
            )
        )
        
        compute_schedule(plan)
        
        # task2 has no scheduled dependencies, so it's unschedulable
        self.assertIsNone(plan.schedule.nodes["task2"].computed_start)
        self.assertIsNone(plan.schedule.nodes["task2"].computed_finish)
        self.assertTrue(len(plan.schedule.warnings) > 0)

    def test_mixed_scheduled_unscheduled_dependencies(self):
        """Only scheduled dependencies are considered (Req 3.13)."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1"),  # Not scheduled
                "task2": Node(title="Task 2"),  # Scheduled
                "task3": Node(title="Task 3", after=["task1", "task2"]),
            },
            schedule=Schedule(
                calendars={"default": Calendar(excludes=["weekends"])},
                default_calendar="default",
                nodes={
                    # task1 not in schedule.nodes
                    "task2": ScheduleNode(start="2024-03-11", duration="3d"),
                    "task3": ScheduleNode(duration="2d"),
                }
            )
        )
        
        compute_schedule(plan)
        
        # task3 only considers task2 (scheduled), ignores task1 (unscheduled)
        self.assertEqual(plan.schedule.nodes["task3"].computed_start, "2024-03-14")
        self.assertEqual(plan.schedule.nodes["task3"].computed_finish, "2024-03-15")

    def test_multiple_scheduled_dependencies(self):
        """Node starts after latest dependency finishes."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1"),
                "task2": Node(title="Task 2"),
                "task3": Node(title="Task 3", after=["task1", "task2"]),
            },
            schedule=Schedule(
                calendars={"default": Calendar(excludes=["weekends"])},
                default_calendar="default",
                nodes={
                    "task1": ScheduleNode(start="2024-03-11", duration="2d"),
                    "task2": ScheduleNode(start="2024-03-11", duration="5d"),
                    "task3": ScheduleNode(duration="2d"),
                }
            )
        )
        
        compute_schedule(plan)
        
        # task1 finishes Tue, task2 finishes Mon (next week)
        # task3 starts after the latest (task2)
        self.assertEqual(plan.schedule.nodes["task1"].computed_finish, "2024-03-12")
        self.assertEqual(plan.schedule.nodes["task2"].computed_finish, "2024-03-15")
        self.assertEqual(plan.schedule.nodes["task3"].computed_start, "2024-03-18")

    def test_all_dependencies_unschedulable(self):
        """Node is unschedulable when all deps are unschedulable (Req 3.14)."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1"),  # Not scheduled
                "task2": Node(title="Task 2", after=["task1"]),
            },
            schedule=Schedule(
                calendars={"default": Calendar(excludes=["weekends"])},
                default_calendar="default",
                nodes={
                    "task2": ScheduleNode(duration="2d"),
                }
            )
        )
        
        compute_schedule(plan)
        
        # task2 is unschedulable (no scheduled deps, no explicit start)
        self.assertIsNone(plan.schedule.nodes["task2"].computed_start)
        self.assertTrue(any("task2" in w for w in plan.schedule.warnings))


class TestComputeScheduleMilestones(unittest.TestCase):
    """Tests for milestone handling."""

    def test_milestone_zero_duration(self):
        """Milestone has zero duration (finish = start)."""
        plan = MergedPlan(
            nodes={"m1": Node(title="Milestone 1", milestone=True)},
            schedule=Schedule(
                calendars={"default": Calendar(excludes=["weekends"])},
                default_calendar="default",
                nodes={
                    "m1": ScheduleNode(start="2024-03-15")
                }
            )
        )
        
        compute_schedule(plan)
        
        sn = plan.schedule.nodes["m1"]
        self.assertEqual(sn.computed_start, "2024-03-15")
        self.assertEqual(sn.computed_finish, "2024-03-15")

    def test_milestone_after_dependency(self):
        """Milestone starts on same day as dependency finish."""
        plan = MergedPlan(
            nodes={
                "task1": Node(title="Task 1"),
                "m1": Node(title="Milestone 1", milestone=True, after=["task1"]),
            },
            schedule=Schedule(
                calendars={"default": Calendar(excludes=["weekends"])},
                default_calendar="default",
                nodes={
                    "task1": ScheduleNode(start="2024-03-11", duration="3d"),
                    "m1": ScheduleNode(),
                }
            )
        )
        
        compute_schedule(plan)
        
        # task1 finishes Wed
        self.assertEqual(plan.schedule.nodes["task1"].computed_finish, "2024-03-13")
        # Milestone is on same day as task1 finish
        self.assertEqual(plan.schedule.nodes["m1"].computed_start, "2024-03-13")
        self.assertEqual(plan.schedule.nodes["m1"].computed_finish, "2024-03-13")

    def test_milestone_on_weekend_allowed(self):
        """Milestone can be on weekend (not normalized)."""
        plan = MergedPlan(
            nodes={"m1": Node(title="Milestone 1", milestone=True)},
            schedule=Schedule(
                calendars={"default": Calendar(excludes=["weekends"])},
                default_calendar="default",
                nodes={
                    "m1": ScheduleNode(start="2024-03-16")  # Saturday
                }
            )
        )
        
        compute_schedule(plan)
        
        sn = plan.schedule.nodes["m1"]
        self.assertEqual(sn.computed_start, "2024-03-16")


class TestComputeScheduleBackwardScheduling(unittest.TestCase):
    """Tests for backward scheduling (finish + duration)."""

    def test_finish_and_duration(self):
        """Compute start from finish and duration."""
        plan = MergedPlan(
            nodes={"task1": Node(title="Task 1")},
            schedule=Schedule(
                calendars={"default": Calendar(excludes=["weekends"])},
                default_calendar="default",
                nodes={
                    "task1": ScheduleNode(finish="2024-03-15", duration="5d")
                }
            )
        )
        
        compute_schedule(plan)
        
        sn = plan.schedule.nodes["task1"]
        # Friday - 4 workdays = Monday
        self.assertEqual(sn.computed_start, "2024-03-11")
        self.assertEqual(sn.computed_finish, "2024-03-15")


class TestComputeScheduleMemoization(unittest.TestCase):
    """Tests for memoization behavior."""

    def test_diamond_dependency(self):
        """Diamond dependency pattern uses memoization correctly."""
        plan = MergedPlan(
            nodes={
                "start": Node(title="Start"),
                "branch1": Node(title="Branch 1", after=["start"]),
                "branch2": Node(title="Branch 2", after=["start"]),
                "end": Node(title="End", after=["branch1", "branch2"]),
            },
            schedule=Schedule(
                calendars={"default": Calendar(excludes=["weekends"])},
                default_calendar="default",
                nodes={
                    "start": ScheduleNode(start="2024-03-11", duration="2d"),
                    "branch1": ScheduleNode(duration="3d"),
                    "branch2": ScheduleNode(duration="5d"),
                    "end": ScheduleNode(duration="1d"),
                }
            )
        )
        
        compute_schedule(plan)
        
        # start: Mon-Tue
        self.assertEqual(plan.schedule.nodes["start"].computed_finish, "2024-03-12")
        # branch1: Wed-Fri
        self.assertEqual(plan.schedule.nodes["branch1"].computed_start, "2024-03-13")
        self.assertEqual(plan.schedule.nodes["branch1"].computed_finish, "2024-03-15")
        # branch2: Wed-Tue (next week)
        self.assertEqual(plan.schedule.nodes["branch2"].computed_start, "2024-03-13")
        self.assertEqual(plan.schedule.nodes["branch2"].computed_finish, "2024-03-19")
        # end: starts after branch2 (the later one)
        self.assertEqual(plan.schedule.nodes["end"].computed_start, "2024-03-20")


class TestComputeScheduleDesignExamples(unittest.TestCase):
    """Tests based on examples from design.md."""

    def test_design_example_partial_schedule(self):
        """
        Example from design.md: partial schedule.
        
        task1, task2, milestone1 are scheduled
        task3 is not scheduled
        """
        plan = MergedPlan(
            nodes={
                "milestone1": Node(title="MVP", milestone=True, after=["task2"]),
                "task1": Node(title="Backend API"),
                "task2": Node(title="Frontend", after=["task1"]),
                "task3": Node(title="Documentation"),  # Not scheduled
            },
            schedule=Schedule(
                calendars={"work": Calendar(excludes=["weekends"])},
                default_calendar="work",
                nodes={
                    "task1": ScheduleNode(start="2024-03-01", duration="3d"),
                    "task2": ScheduleNode(duration="5d"),
                    "milestone1": ScheduleNode(),
                }
            )
        )
        
        compute_schedule(plan)
        
        # task1: Fri-Tue (Mar 1 is Friday)
        self.assertEqual(plan.schedule.nodes["task1"].computed_start, "2024-03-01")
        self.assertEqual(plan.schedule.nodes["task1"].computed_finish, "2024-03-05")
        
        # task2: starts Wed (after task1)
        self.assertEqual(plan.schedule.nodes["task2"].computed_start, "2024-03-06")
        self.assertEqual(plan.schedule.nodes["task2"].computed_finish, "2024-03-12")
        
        # milestone1: same day as task2 finish
        self.assertEqual(plan.schedule.nodes["milestone1"].computed_start, "2024-03-12")
        
        # task3 is not in schedule.nodes
        self.assertNotIn("task3", plan.schedule.nodes)


if __name__ == "__main__":
    unittest.main()
