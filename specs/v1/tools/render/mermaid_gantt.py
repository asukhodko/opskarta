#!/usr/bin/env python3
"""
Рендерер Mermaid Gantt диаграмм для opskarta.

Использование:
    python -m render.mermaid_gantt --plan plan.yaml --views views.yaml --view overview
    python -m render.mermaid_gantt --plan plan.yaml --views views.yaml --view overview --output gantt.md

Описание:
    Генерирует диаграмму Gantt в формате Mermaid на основе файла плана
    и выбранного представления из файла views.

Зависимости: PyYAML (pip install pyyaml)
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


# ============================================================================
# Исключения
# ============================================================================

class RenderError(Exception):
    """Базовое исключение для ошибок рендеринга."""
    pass


class SchedulingError(RenderError):
    """Ошибка при вычислении расписания (отсутствующие даты, циклы и т.д.)."""
    pass


class FileError(RenderError):
    """Ошибка при работе с файлами."""
    pass


# ============================================================================
# Загрузка файлов
# ============================================================================

def load_yaml(path: str | Path) -> Dict[str, Any]:
    """
    Загружает YAML файл.
    
    Args:
        path: Путь к YAML файлу
        
    Returns:
        Словарь с данными из файла
        
    Raises:
        FileError: если файл не найден или содержит невалидный YAML
    """
    try:
        import yaml
    except ImportError:
        print("Ошибка: модуль PyYAML не установлен", file=sys.stderr)
        print("Установите: pip install pyyaml", file=sys.stderr)
        sys.exit(1)
    
    p = Path(path)
    
    if not p.exists():
        raise FileError(f"Файл не найден: {p}")
    
    try:
        data = yaml.safe_load(p.read_text(encoding="utf-8"))
    except Exception as e:
        raise FileError(f"Ошибка парсинга YAML: {p}: {e}") from e

    if data is None:
        return {}
    
    if not isinstance(data, dict):
        raise FileError(f"Корневой элемент YAML должен быть объектом: {p}")

    return data


# ============================================================================
# Планирование (scheduling)
# ============================================================================

def parse_date(value: str) -> date:
    """
    Парсит дату из строки формата YYYY-MM-DD.
    
    Args:
        value: Строка с датой
        
    Returns:
        Объект date
        
    Raises:
        SchedulingError: если формат даты неверный
    """
    try:
        y, m, d = value.split("-")
        return date(int(y), int(m), int(d))
    except Exception as e:
        raise SchedulingError(f"Неверный формат даты: {value!r}. Ожидается YYYY-MM-DD") from e


def parse_duration(value: Any) -> int:
    """
    Парсит длительность в рабочих днях.
    
    Принимает:
    - int: количество дней
    - str: '10d' (дни) или '2w' (недели, 1w = 5 рабочих дней) или '10' (дни)
    - None: по умолчанию 1 день
    
    Args:
        value: Значение длительности
        
    Returns:
        Количество рабочих дней (целое число)
        
    Raises:
        SchedulingError: если формат длительности неверный
    """
    if value is None:
        return 1
    
    if isinstance(value, int):
        if value <= 0:
            raise SchedulingError(f"Длительность должна быть положительной, получено {value}")
        return value
    
    if isinstance(value, str):
        s = value.strip()
        if s.isdigit():
            n = int(s)
            if n <= 0:
                raise SchedulingError(f"Длительность должна быть положительной, получено {value!r}")
            return n
        if s.endswith("d") and s[:-1].isdigit():
            n = int(s[:-1])
            if n <= 0:
                raise SchedulingError(f"Длительность должна быть положительной, получено {value!r}")
            return n
        if s.endswith("w") and s[:-1].isdigit():
            # 1w = 5 рабочих дней
            n = int(s[:-1])
            if n <= 0:
                raise SchedulingError(f"Длительность должна быть положительной, получено {value!r}")
            return n * 5
    
    raise SchedulingError(f"Неподдерживаемый формат длительности: {value!r} (ожидается int, 'Nd' или 'Nw')")


def is_weekend(d: date) -> bool:
    """Проверяет, является ли дата выходным днём (суббота или воскресенье)."""
    return d.weekday() >= 5  # 5=Сб, 6=Вс


def next_workday(d: date) -> date:
    """Возвращает следующий рабочий день после указанной даты."""
    cur = d + timedelta(days=1)
    while is_weekend(cur):
        cur += timedelta(days=1)
    return cur


def add_workdays(start: date, workdays: int) -> date:
    """
    Добавляет N рабочих дней к начальной дате.
    
    Args:
        start: Начальная дата
        workdays: Количество рабочих дней (может быть 0)
        
    Returns:
        Дата после добавления рабочих дней
    """
    cur = start
    step = 1 if workdays >= 0 else -1
    remaining = abs(workdays)
    while remaining > 0:
        cur += timedelta(days=step)
        if not is_weekend(cur):
            remaining -= 1
    return cur


def finish_date(start: date, duration_days: int, exclude_weekends: bool) -> date:
    """
    Вычисляет дату окончания задачи.
    
    Длительность включает день начала: 1d => finish == start
    
    Args:
        start: Дата начала
        duration_days: Длительность в днях
        exclude_weekends: Исключать ли выходные
        
    Returns:
        Дата окончания
    """
    if duration_days <= 1:
        return start
    if exclude_weekends:
        return add_workdays(start, duration_days - 1)
    return start + timedelta(days=duration_days - 1)


@dataclass(frozen=True)
class ScheduledNode:
    """Результат планирования узла: даты начала, окончания и длительность."""
    start: date
    finish: date
    duration_days: int


def compute_schedule(nodes: Dict[str, Dict[str, Any]], exclude_weekends: bool) -> Dict[str, ScheduledNode]:
    """
    Вычисляет расписание для узлов на основе явных дат начала и зависимостей `after`.
    
    Core-поведение: узлы без явного start или after являются непланируемыми (unscheduled).
    
    Опциональное расширение: если узел имеет `x.scheduling.anchor_to_parent_start: true`,
    он может унаследовать дату начала от родителя.
    
    Args:
        nodes: Словарь узлов из плана
        exclude_weekends: Исключать ли выходные при расчёте
        
    Returns:
        Словарь {node_id: ScheduledNode} с вычисленным расписанием
        
    Raises:
        SchedulingError: при обнаружении циклов или отсутствующих данных
    """
    cache: Dict[str, ScheduledNode] = {}
    visiting: Set[str] = set()
    skipped_nodes: List[str] = []

    def resolve(node_id: str) -> Optional[ScheduledNode]:
        if node_id in cache:
            return cache[node_id]
        if node_id in visiting:
            raise SchedulingError(f"Обнаружен цикл при планировании: {node_id}")
        if node_id not in nodes:
            raise SchedulingError(f"Ссылка на несуществующий узел: {node_id}")

        visiting.add(node_id)
        node = nodes[node_id]

        duration_days = parse_duration(node.get("duration"))
        start_value = node.get("start")
        start: Optional[date] = None

        if isinstance(start_value, datetime):
            start = start_value.date()
        elif isinstance(start_value, date):
            start = start_value
        elif isinstance(start_value, str) and start_value.strip():
            start = parse_date(start_value.strip())
        else:
            after: List[str] = node.get("after") or []
            if after:
                # Начинаем после завершения последней зависимости
                dep_finishes: List[date] = []
                for dep_id in after:
                    dep_sched = resolve(dep_id)
                    if dep_sched:
                        dep_finishes.append(dep_sched.finish)

                if dep_finishes:
                    latest = max(dep_finishes)
                    start = next_workday(latest) if exclude_weekends else latest + timedelta(days=1)
            
            # Опциональное расширение: наследование даты от родителя
            # Активируется только через x.scheduling.anchor_to_parent_start: true
            if start is None:
                x_data = node.get("x") or {}
                scheduling_ext = x_data.get("scheduling") or {} if isinstance(x_data, dict) else {}
                anchor_to_parent = scheduling_ext.get("anchor_to_parent_start", False) if isinstance(scheduling_ext, dict) else False
                
                if anchor_to_parent:
                    parent_id = node.get("parent")
                    if parent_id and parent_id in nodes:
                        parent_sched = resolve(parent_id)
                        if parent_sched:
                            # Если есть after, берём максимум
                            if after and start is None:
                                # after был обработан выше, но не дал результата
                                start = parent_sched.start
                            else:
                                start = parent_sched.start

        visiting.remove(node_id)
        
        # Если не удалось определить дату начала, возвращаем None (unscheduled)
        if start is None:
            skipped_nodes.append(node_id)
            return None

        finish = finish_date(start, duration_days, exclude_weekends)
        sched = ScheduledNode(start=start, finish=finish, duration_days=duration_days)
        cache[node_id] = sched
        return sched

    for node_id in nodes.keys():
        resolve(node_id)

    # Выводим предупреждение о пропущенных узлах
    if skipped_nodes:
        import sys
        print(f"Предупреждение: следующие узлы не имеют вычислимой даты начала и будут пропущены: {', '.join(skipped_nodes)}", file=sys.stderr)

    return cache


# ============================================================================
# Рендеринг Mermaid Gantt
# ============================================================================

# Соответствие статусов opskarta тегам Mermaid
STATUS_TO_MERMAID_TAG = {
    "done": "done",
    "in_progress": "active",
    "blocked": "crit",
    "not_started": None,
}

# Эмодзи для статусов (для наглядности в диаграмме)
STATUS_TO_EMOJI = {
    "done": "✅ ",
    "in_progress": "🔄 ",
    "blocked": "⛔ ",
    "not_started": "",
}


def _theme_vars_from_statuses(statuses: Dict[str, Any]) -> Dict[str, str]:
    """
    Генерирует переменные темы Mermaid на основе цветов статусов.
    
    Args:
        statuses: Словарь статусов из плана
        
    Returns:
        Словарь переменных темы для Mermaid
    """
    # Цвета по умолчанию
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
    """
    Генерирует диаграмму Gantt в формате Mermaid.
    
    Args:
        plan: Данные плана (словарь из plan.yaml)
        view: Данные представления (один элемент из gantt_views)
        
    Returns:
        Строка с Mermaid-разметкой диаграммы Gantt
        
    Raises:
        SchedulingError: при ошибках планирования
        RenderError: при ошибках рендеринга
    """
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
                raise SchedulingError(f"Представление ссылается на несуществующий узел: {node_id}")

            node = nodes[node_id]
            node_title = node.get("title") or node_id
            status = node.get("status")
            emoji = STATUS_TO_EMOJI.get(status, "")
            mermaid_tag = STATUS_TO_MERMAID_TAG.get(status)

            # Расписание может отсутствовать для контейнерных узлов
            sched: Optional[ScheduledNode] = schedule.get(node_id)
            if sched is None:
                # Нет явной даты начала — пропускаем
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


# ============================================================================
# CLI интерфейс
# ============================================================================

def main():
    """Главная функция CLI."""
    parser = argparse.ArgumentParser(
        description='Рендерер Mermaid Gantt диаграмм для opskarta',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python -m render.mermaid_gantt --plan plan.yaml --views views.yaml --view overview
  python -m render.mermaid_gantt --plan plan.yaml --views views.yaml --view overview --output gantt.md

Описание:
  Генерирует диаграмму Gantt в формате Mermaid на основе файла плана
  и выбранного представления из файла views.
        """
    )
    
    parser.add_argument(
        '--plan',
        type=Path,
        required=True,
        help='Путь к файлу плана (*.plan.yaml)'
    )
    
    parser.add_argument(
        '--views',
        type=Path,
        required=True,
        help='Путь к файлу представлений (*.views.yaml)'
    )
    
    parser.add_argument(
        '--view',
        type=str,
        default=None,
        help='Имя представления из gantt_views (обязательно, если не указан --list-views)'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=Path,
        default=None,
        help='Путь для сохранения результата (по умолчанию: stdout)'
    )
    
    parser.add_argument(
        '--list-views',
        action='store_true',
        help='Показать список доступных представлений и выйти'
    )
    
    args = parser.parse_args()
    
    try:
        # Загрузка файлов
        plan = load_yaml(args.plan)
        views = load_yaml(args.views)
        
        gantt_views = views.get('gantt_views', {})
        
        # Режим списка представлений
        if args.list_views:
            if not gantt_views:
                print("Представления не найдены в файле views", file=sys.stderr)
                sys.exit(1)
            
            print("Доступные представления:")
            for view_id, view_data in gantt_views.items():
                title = view_data.get('title', view_id) if isinstance(view_data, dict) else view_id
                print(f"  - {view_id}: {title}")
            sys.exit(0)
        
        # Проверка наличия аргумента --view
        if not args.view:
            print("Ошибка: требуется указать --view или --list-views", file=sys.stderr)
            sys.exit(1)
        
        # Проверка наличия представления
        if args.view not in gantt_views:
            available = list(gantt_views.keys())
            print(f"Ошибка: представление '{args.view}' не найдено", file=sys.stderr)
            if available:
                print(f"Доступные представления: {', '.join(available)}", file=sys.stderr)
            else:
                print("В файле views нет определённых представлений", file=sys.stderr)
            sys.exit(1)
        
        view = gantt_views[args.view]
        
        # Рендеринг
        result = render_mermaid_gantt(plan=plan, view=view)
        
        # Вывод результата
        if args.output:
            args.output.write_text(result, encoding='utf-8')
            print(f"Диаграмма сохранена в: {args.output}")
        else:
            print(result)
        
        sys.exit(0)
        
    except (RenderError, SchedulingError, FileError) as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nПрервано пользователем", file=sys.stderr)
        sys.exit(130)


if __name__ == '__main__':
    main()
