#!/usr/bin/env python3
"""
Тесты для opskarta v1.

Использование:
    python test_scheduling.py                    # Запуск всех тестов
    python test_scheduling.py -v                 # Подробный вывод
    python test_scheduling.py TestDuration       # Запуск одной группы тестов

Можно также запускать через pytest:
    pytest test_scheduling.py -v
"""

import sys
import unittest
from datetime import date
from pathlib import Path

# Добавляем путь к tools для импорта
TOOLS_DIR = Path(__file__).parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

from validate import validate_plan, validate_views, load_yaml, ValidationError
from render.plan2gantt import (
    parse_duration_days,
    parse_date_field,
    add_workdays,
    sub_workdays,
    is_workday as _is_workday,
    normalize_start as _normalize_start,
    compute_node_schedule,
    ValidationFailed,
    Reporter,
    Calendar,
)


# ----------------------------
# Compatibility wrappers
# ----------------------------

class SchedulingError(Exception):
    """Compatibility exception for tests."""
    pass


class _SilentReporter(Reporter):
    """Reporter that doesn't print anything."""
    def error(self, msg: str) -> None:
        self.errors += 1
    def warn(self, msg: str) -> None:
        self.warnings += 1
    def info(self, msg: str) -> None:
        self.infos += 1


def _make_calendar(excludes: list) -> Calendar:
    """Convert excludes list to Calendar object."""
    weekends = "weekends" in excludes
    exclude_dates = set()
    for item in excludes:
        if item != "weekends" and isinstance(item, str):
            from datetime import datetime
            try:
                exclude_dates.add(datetime.strptime(item, "%Y-%m-%d").date())
            except ValueError:
                pass
    return Calendar(weekends=weekends, exclude_dates=exclude_dates)


def parse_duration(value) -> int:
    """Compatibility wrapper for parse_duration_days."""
    rep = _SilentReporter()
    if value is None:
        return 1
    if isinstance(value, int):
        if value <= 0:
            raise SchedulingError(f"Invalid duration: {value}")
        return value
    if isinstance(value, str):
        s = value.strip()
        # Handle string without suffix
        if s.isdigit():
            n = int(s)
            if n <= 0:
                raise SchedulingError(f"Invalid duration: {value}")
            return n
        # Handle weeks
        if s.endswith('w'):
            try:
                n = int(s[:-1])
                if n <= 0:
                    raise SchedulingError(f"Invalid duration: {value}")
                return n * 5
            except ValueError:
                raise SchedulingError(f"Invalid duration format: {value}")
        # Handle days
        if s.endswith('d'):
            try:
                n = int(s[:-1])
                if n <= 0:
                    raise SchedulingError(f"Invalid duration: {value}")
                return n
            except ValueError:
                raise SchedulingError(f"Invalid duration format: {value}")
        raise SchedulingError(f"Invalid duration format: {value}")
    raise SchedulingError(f"Invalid duration type: {type(value)}")


def parse_date(value) -> date:
    """Compatibility wrapper for parse_date_field."""
    rep = _SilentReporter()
    try:
        return parse_date_field(value, "test", rep)
    except ValidationFailed:
        raise SchedulingError(f"Invalid date: {value}")


def finish_date(start: date, duration: int, excludes: list) -> date:
    """Calculate finish date from start and duration."""
    cal = _make_calendar(excludes)
    return add_workdays(start, duration - 1, cal)


def is_excluded(d: date, excludes: list) -> bool:
    """Check if date is excluded."""
    cal = _make_calendar(excludes)
    return not _is_workday(d, cal)


def is_workday(d: date, excludes: list) -> bool:
    """Check if date is a workday."""
    cal = _make_calendar(excludes)
    return _is_workday(d, cal)


def normalize_start(d: date, excludes: list, is_milestone: bool = False):
    """Normalize start date to next workday if excluded."""
    cal = _make_calendar(excludes)
    rep = _SilentReporter()
    normalized = _normalize_start(d, cal, is_milestone, rep, "test")
    was_normalized = normalized != d
    return normalized, was_normalized


def compute_schedule(nodes: dict, excludes: list) -> dict:
    """Compute schedule for all nodes."""
    cal = _make_calendar(excludes)
    rep = _SilentReporter()
    
    # Build a minimal plan structure
    plan = {
        "version": 1,
        "meta": {"id": "test", "title": "Test"},
        "nodes": nodes,
    }
    
    cache = {}
    result = {}
    
    for node_id in nodes:
        try:
            visiting = set()
            sched = compute_node_schedule(node_id, plan, cal, rep, cache, visiting)
            if sched.start is not None:
                result[node_id] = sched
        except ValidationFailed:
            pass
    
    return result


# ----------------------------
# Tests
# ----------------------------

class TestDuration(unittest.TestCase):
    """Тесты парсинга длительности."""
    
    def test_days_with_suffix(self):
        """Длительность в днях с суффиксом d."""
        self.assertEqual(parse_duration("5d"), 5)
        self.assertEqual(parse_duration("1d"), 1)
        self.assertEqual(parse_duration("10d"), 10)
        self.assertEqual(parse_duration("100d"), 100)
    
    def test_weeks_with_suffix(self):
        """Длительность в неделях (1w = 5 рабочих дней)."""
        self.assertEqual(parse_duration("1w"), 5)
        self.assertEqual(parse_duration("2w"), 10)
        self.assertEqual(parse_duration("3w"), 15)
    
    def test_integer(self):
        """Длительность как целое число."""
        self.assertEqual(parse_duration(5), 5)
        self.assertEqual(parse_duration(1), 1)
    
    def test_string_without_suffix(self):
        """Строка без суффикса интерпретируется как дни."""
        self.assertEqual(parse_duration("5"), 5)
        self.assertEqual(parse_duration("10"), 10)
    
    def test_none_default(self):
        """None возвращает умолчание 1 день."""
        self.assertEqual(parse_duration(None), 1)
    
    def test_invalid_zero(self):
        """Ноль недопустим."""
        with self.assertRaises(SchedulingError):
            parse_duration("0d")
        with self.assertRaises(SchedulingError):
            parse_duration(0)
    
    def test_invalid_negative(self):
        """Отрицательные значения недопустимы."""
        with self.assertRaises(SchedulingError):
            parse_duration(-1)
    
    def test_invalid_format(self):
        """Неверный формат."""
        with self.assertRaises(SchedulingError):
            parse_duration("5m")
        with self.assertRaises(SchedulingError):
            parse_duration("abc")


class TestDateCalculation(unittest.TestCase):
    """Тесты вычисления дат."""
    
    def test_finish_same_day(self):
        """1d = начало и конец в один день."""
        start = date(2024, 3, 1)
        self.assertEqual(finish_date(start, 1, []), date(2024, 3, 1))
    
    def test_finish_calendar_days(self):
        """Вычисление без исключения выходных."""
        start = date(2024, 3, 1)  # Friday
        # 5 календарных дней: 1, 2, 3, 4, 5
        self.assertEqual(finish_date(start, 5, []), date(2024, 3, 5))
    
    def test_finish_workdays(self):
        """Вычисление с исключением выходных."""
        start = date(2024, 3, 1)  # Friday
        # 5 рабочих дней: Fri(1), Mon(4), Tue(5), Wed(6), Thu(7)
        self.assertEqual(finish_date(start, 5, ["weekends"]), date(2024, 3, 7))
    
    def test_weeks_workdays(self):
        """1w = 5 рабочих дней."""
        start = date(2024, 3, 4)  # Monday
        # 1w = 5 рабочих дней: Mon, Tue, Wed, Thu, Fri
        duration = parse_duration("1w")  # = 5
        self.assertEqual(finish_date(start, duration, ["weekends"]), date(2024, 3, 8))


class TestScheduleComputation(unittest.TestCase):
    """Тесты вычисления расписания."""
    
    def test_explicit_start(self):
        """Узел с явным start."""
        nodes = {
            "task1": {
                "title": "Task 1",
                "start": "2024-03-01",
                "duration": "5d"
            }
        }
        schedule = compute_schedule(nodes, excludes=[])
        self.assertIn("task1", schedule)
        self.assertEqual(schedule["task1"].start, date(2024, 3, 1))
        self.assertEqual(schedule["task1"].finish, date(2024, 3, 5))
    
    def test_after_dependency(self):
        """Узел с зависимостью after."""
        nodes = {
            "task1": {
                "title": "Task 1",
                "start": "2024-03-01",
                "duration": "3d"
            },
            "task2": {
                "title": "Task 2",
                "after": ["task1"],
                "duration": "2d"
            }
        }
        schedule = compute_schedule(nodes, excludes=[])
        # task1: 01-03, task2 starts 04
        self.assertEqual(schedule["task2"].start, date(2024, 3, 4))
        self.assertEqual(schedule["task2"].finish, date(2024, 3, 5))
    
    def test_start_takes_precedence(self):
        """start имеет приоритет над after."""
        nodes = {
            "dep": {
                "title": "Dependency",
                "start": "2024-03-01",
                "duration": "5d"
                # finish = 03-05
            },
            "task": {
                "title": "Task",
                "start": "2024-03-04",  # Explicit, before dep finishes
                "after": ["dep"],
                "duration": "3d"
            }
        }
        schedule = compute_schedule(nodes, excludes=[])
        # start should be 03-04 (explicit), not 03-06 (after dep)
        self.assertEqual(schedule["task"].start, date(2024, 3, 4))
    
    def test_unscheduled_node(self):
        """Узел без start и after — непланируемый."""
        nodes = {
            "unscheduled": {
                "title": "Unscheduled task",
                "duration": "5d"
            }
        }
        schedule = compute_schedule(nodes, excludes=[])
        # Node should not be in schedule
        self.assertNotIn("unscheduled", schedule)
    
    def test_parent_inheritance_opt_in(self):
        """Наследование от родителя только с x.scheduling.anchor_to_parent_start."""
        nodes = {
            "parent": {
                "title": "Parent",
                "start": "2024-03-01",
                "duration": "10d"
            },
            "child_no_anchor": {
                "title": "Child without anchor",
                "parent": "parent",
                "duration": "3d"
            },
            "child_with_anchor": {
                "title": "Child with anchor",
                "parent": "parent",
                "duration": "3d",
                "x": {
                    "scheduling": {
                        "anchor_to_parent_start": True
                    }
                }
            }
        }
        schedule = compute_schedule(nodes, excludes=[])
        # Child without anchor should be unscheduled
        self.assertNotIn("child_no_anchor", schedule)
        # Child with anchor should inherit parent's start
        self.assertIn("child_with_anchor", schedule)
        self.assertEqual(schedule["child_with_anchor"].start, date(2024, 3, 1))


class TestValidation(unittest.TestCase):
    """Тесты валидации."""
    
    def test_valid_duration_format(self):
        """Валидный формат duration."""
        plan = {
            "version": 1,
            "meta": {"id": "test", "title": "Test"},
            "nodes": {
                "task1": {"title": "Task", "duration": "5d"},
                "task2": {"title": "Task", "duration": "2w"},
            }
        }
        warnings, infos = validate_plan(plan)  # Should not raise
        self.assertIsInstance(warnings, list)
        self.assertIsInstance(infos, list)
    
    def test_invalid_duration_zero(self):
        """Ноль в duration недопустим."""
        plan = {
            "version": 1,
            "meta": {"id": "test", "title": "Test"},
            "nodes": {
                "task1": {"title": "Task", "duration": "0d"}
            }
        }
        with self.assertRaises(ValidationError):
            validate_plan(plan)
    
    def test_invalid_date_format(self):
        """Неверный формат даты."""
        plan = {
            "version": 1,
            "meta": {"id": "test", "title": "Test"},
            "nodes": {
                "task1": {"title": "Task", "start": "2024-13-45"}
            }
        }
        with self.assertRaises(ValidationError):
            validate_plan(plan)
    
    def test_meta_id_required_with_views(self):
        """meta.id обязателен при использовании views."""
        plan = {
            "version": 1,
            "nodes": {
                "task1": {"title": "Task"}
            }
        }
        views = {
            "version": 1,
            "project": "test",
            "gantt_views": {
                "main": {
                    "title": "Main",
                    "lanes": {
                        "lane1": {
                            "title": "Lane",
                            "nodes": ["task1"]
                        }
                    }
                }
            }
        }
        with self.assertRaises(ValidationError) as ctx:
            validate_views(views, plan)
        self.assertIn("meta.id", str(ctx.exception))


class TestFixtures(unittest.TestCase):
    """Тесты на файлах-фикстурах."""
    
    @classmethod
    def setUpClass(cls):
        cls.fixtures_dir = Path(__file__).parent / "fixtures"
    
    def test_extensions_fixture(self):
        """Файл с расширениями должен проходить валидацию."""
        plan_path = self.fixtures_dir / "extensions.plan.yaml"
        if plan_path.exists():
            plan = load_yaml(plan_path)
            warnings, infos = validate_plan(plan)
            self.assertIsInstance(warnings, list)
    
    def test_weeks_duration_fixture(self):
        """Файл с неделями должен проходить валидацию."""
        plan_path = self.fixtures_dir / "weeks_duration.plan.yaml"
        if plan_path.exists():
            plan = load_yaml(plan_path)
            warnings, infos = validate_plan(plan)
            self.assertIsInstance(warnings, list)
    
    def test_finish_field_fixture(self):
        """Файл с полем finish должен проходить валидацию."""
        plan_path = self.fixtures_dir / "finish_field.plan.yaml"
        if plan_path.exists():
            plan = load_yaml(plan_path)
            warnings, infos = validate_plan(plan)
            self.assertIsInstance(warnings, list)
    
    def test_date_excludes_fixture(self):
        """Файл с датами в excludes должен проходить валидацию."""
        plan_path = self.fixtures_dir / "date_excludes.plan.yaml"
        if plan_path.exists():
            plan = load_yaml(plan_path)
            warnings, infos = validate_plan(plan)
            self.assertIsInstance(warnings, list)


class TestFinishField(unittest.TestCase):
    """Тесты для поля finish (backward scheduling)."""
    
    def test_backward_scheduling(self):
        """finish + duration вычисляет start назад."""
        finish = date(2024, 3, 15)  # Friday
        # 5 рабочих дней назад: Fri(15), Thu(14), Wed(13), Tue(12), Mon(11)
        cal = _make_calendar(["weekends"])
        start = sub_workdays(finish, 4, cal)  # -4 workdays from finish
        self.assertEqual(start, date(2024, 3, 11))
    
    def test_finish_field_in_schedule(self):
        """Узел с finish + duration вычисляет start."""
        nodes = {
            "task1": {
                "title": "Task 1",
                "finish": "2024-03-15",
                "duration": "5d"
            }
        }
        schedule = compute_schedule(nodes, excludes=[])
        self.assertIn("task1", schedule)
        # Without excludes, 5 days back from Mar 15: Mar 11
        self.assertEqual(schedule["task1"].start, date(2024, 3, 11))
        self.assertEqual(schedule["task1"].finish, date(2024, 3, 15))


class TestDateExcludes(unittest.TestCase):
    """Тесты для исключения конкретных дат."""
    
    def test_date_excludes_in_calendar(self):
        """Конкретные даты исключаются из расчётов."""
        excludes = ["weekends", "2024-03-08"]
        
        # Friday Mar 8 is a holiday
        self.assertTrue(is_excluded(date(2024, 3, 8), excludes))
        self.assertFalse(is_workday(date(2024, 3, 8), excludes))
        
        # Thursday Mar 7 is a workday
        self.assertFalse(is_excluded(date(2024, 3, 7), excludes))
        self.assertTrue(is_workday(date(2024, 3, 7), excludes))
    
    def test_add_workdays_with_holiday(self):
        """add_workdays пропускает праздники."""
        excludes = ["weekends", "2024-03-08"]
        cal = _make_calendar(excludes)
        
        # Start Thu Mar 7, add 2 workdays
        # Fri(8) is holiday, skip to Mon(11), Tue(12)
        start = date(2024, 3, 7)
        result = add_workdays(start, 2, cal)
        self.assertEqual(result, date(2024, 3, 12))


class TestStartNormalization(unittest.TestCase):
    """Тесты нормализации start на исключённый день."""
    
    def test_normalize_start_on_weekend(self):
        """start на выходной нормализуется на понедельник."""
        excludes = ["weekends"]
        
        # Saturday Mar 2
        start = date(2024, 3, 2)
        normalized, was_normalized = normalize_start(start, excludes, is_milestone=False)
        self.assertTrue(was_normalized)
        self.assertEqual(normalized, date(2024, 3, 4))  # Monday
    
    def test_milestone_not_normalized(self):
        """Вехи НЕ нормализуются."""
        excludes = ["weekends"]
        
        # Saturday Mar 2
        start = date(2024, 3, 2)
        normalized, was_normalized = normalize_start(start, excludes, is_milestone=True)
        self.assertFalse(was_normalized)
        self.assertEqual(normalized, date(2024, 3, 2))  # Unchanged


if __name__ == "__main__":
    unittest.main(verbosity=2)
