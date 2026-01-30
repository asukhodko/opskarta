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
from render.mermaid_gantt import (
    parse_duration,
    parse_date,
    finish_date,
    compute_schedule,
    SchedulingError,
)


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
        self.assertEqual(finish_date(start, 1, exclude_weekends=False), date(2024, 3, 1))
    
    def test_finish_calendar_days(self):
        """Вычисление без исключения выходных."""
        start = date(2024, 3, 1)  # Friday
        # 5 календарных дней: 1, 2, 3, 4, 5
        self.assertEqual(finish_date(start, 5, exclude_weekends=False), date(2024, 3, 5))
    
    def test_finish_workdays(self):
        """Вычисление с исключением выходных."""
        start = date(2024, 3, 1)  # Friday
        # 5 рабочих дней: Fri(1), Mon(4), Tue(5), Wed(6), Thu(7)
        self.assertEqual(finish_date(start, 5, exclude_weekends=True), date(2024, 3, 7))
    
    def test_weeks_workdays(self):
        """1w = 5 рабочих дней."""
        start = date(2024, 3, 4)  # Monday
        # 1w = 5 рабочих дней: Mon, Tue, Wed, Thu, Fri
        duration = parse_duration("1w")  # = 5
        self.assertEqual(finish_date(start, duration, exclude_weekends=True), date(2024, 3, 8))


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
        schedule = compute_schedule(nodes, exclude_weekends=False)
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
        schedule = compute_schedule(nodes, exclude_weekends=False)
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
        schedule = compute_schedule(nodes, exclude_weekends=False)
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
        schedule = compute_schedule(nodes, exclude_weekends=False)
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
        schedule = compute_schedule(nodes, exclude_weekends=False)
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
        warnings = validate_plan(plan)  # Should not raise
        self.assertIsInstance(warnings, list)
    
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
            warnings = validate_plan(plan)
            self.assertIsInstance(warnings, list)
    
    def test_weeks_duration_fixture(self):
        """Файл с неделями должен проходить валидацию."""
        plan_path = self.fixtures_dir / "weeks_duration.plan.yaml"
        if plan_path.exists():
            plan = load_yaml(plan_path)
            warnings = validate_plan(plan)
            self.assertIsInstance(warnings, list)


if __name__ == "__main__":
    unittest.main(verbosity=2)
