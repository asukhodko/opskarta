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
import re
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


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


def is_excluded(d: date, excludes: List[str]) -> bool:
    """
    Проверяет, является ли дата исключённым днём (выходной или праздник).
    
    Args:
        d: Дата для проверки
        excludes: Список excludes (weekends, YYYY-MM-DD даты)
        
    Returns:
        True если дата исключена
    """
    # Проверка выходных
    if "weekends" in excludes and d.weekday() >= 5:  # 5=Сб, 6=Вс
        return True
    
    # Проверка конкретных дат (YYYY-MM-DD)
    date_str = d.isoformat()
    if date_str in excludes:
        return True
    
    return False


def is_workday(d: date, excludes: List[str]) -> bool:
    """Проверяет, является ли дата рабочим днём (не исключённым)."""
    return not is_excluded(d, excludes)


def next_workday(d: date, excludes: List[str]) -> date:
    """Возвращает следующий рабочий день после указанной даты."""
    cur = d + timedelta(days=1)
    while is_excluded(cur, excludes):
        cur += timedelta(days=1)
    return cur


def add_workdays(start: date, workdays: int, excludes: List[str]) -> date:
    """
    Добавляет N рабочих дней к начальной дате.
    
    Args:
        start: Начальная дата
        workdays: Количество рабочих дней (может быть 0)
        excludes: Список excludes
        
    Returns:
        Дата после добавления рабочих дней
    """
    cur = start
    step = 1 if workdays >= 0 else -1
    remaining = abs(workdays)
    while remaining > 0:
        cur += timedelta(days=step)
        if is_workday(cur, excludes):
            remaining -= 1
    return cur


def sub_workdays(finish: date, workdays: int, excludes: List[str]) -> date:
    """
    Вычитает N рабочих дней из конечной даты (идёт назад).
    
    Args:
        finish: Конечная дата
        workdays: Количество рабочих дней для вычитания
        excludes: Список excludes
        
    Returns:
        Дата после вычитания рабочих дней
    """
    cur = finish
    subtracted = 0
    while subtracted < workdays:
        cur -= timedelta(days=1)
        if is_workday(cur, excludes):
            subtracted += 1
    return cur


def normalize_start(start: date, excludes: List[str], is_milestone: bool) -> Tuple[date, bool]:
    """
    Нормализует дату начала на следующий рабочий день, если она попала на исключённый день.
    
    Args:
        start: Дата начала
        excludes: Список excludes
        is_milestone: Является ли узел вехой (вехи не нормализуются)
        
    Returns:
        Кортеж (нормализованная_дата, была_ли_нормализация)
    """
    if is_milestone:
        return start, False
    
    if is_excluded(start, excludes):
        # Найти следующий рабочий день
        cur = start
        while is_excluded(cur, excludes):
            cur += timedelta(days=1)
        return cur, True
    
    return start, False


def finish_date(start: date, duration_days: int, excludes: List[str]) -> date:
    """
    Вычисляет дату окончания задачи.
    
    Длительность включает день начала: 1d => finish == start
    
    Args:
        start: Дата начала
        duration_days: Длительность в днях
        excludes: Список excludes
        
    Returns:
        Дата окончания
    """
    if duration_days <= 1:
        return start
    if excludes:  # Если есть excludes, учитываем их
        return add_workdays(start, duration_days - 1, excludes)
    return start + timedelta(days=duration_days - 1)


def get_core_excludes(excludes: List[str]) -> Tuple[List[str], List[str]]:
    """
    Разделяет excludes на core и non-core.
    
    Core excludes: "weekends" и даты YYYY-MM-DD.
    Non-core excludes: всё остальное.
    
    Args:
        excludes: Список excludes
        
    Returns:
        Кортеж (core_excludes, non_core_excludes)
    """
    core = []
    non_core = []
    
    for item in excludes:
        if isinstance(item, str):
            is_core = (
                item == "weekends" or
                re.match(r'^\d{4}-\d{2}-\d{2}$', item)
            )
            if is_core:
                core.append(item)
            else:
                non_core.append(item)
    
    return core, non_core


@dataclass(frozen=True)
class ScheduledNode:
    """Результат планирования узла: даты начала, окончания и длительность."""
    start: date
    finish: date
    duration_days: int


def compute_schedule(nodes: Dict[str, Dict[str, Any]], excludes: List[str]) -> Dict[str, ScheduledNode]:
    """
    Вычисляет расписание для узлов на основе явных дат начала/окончания и зависимостей `after`.
    
    Core-поведение: узлы без явного start, finish или after являются непланируемыми (unscheduled).
    
    Приоритет вычисления start:
    1. Явный start (если указан) — после нормализации на excluded day
    2. Явный finish + duration (если start отсутствует) — backward scheduling
    3. Зависимости after (если start и finish отсутствуют) — next workday после max finish
    4. Опциональное расширение anchor_to_parent_start
    
    Args:
        nodes: Словарь узлов из плана
        excludes: Список excludes (weekends, YYYY-MM-DD даты)
        
    Returns:
        Словарь {node_id: ScheduledNode} с вычисленным расписанием
        
    Raises:
        SchedulingError: при обнаружении циклов или отсутствующих данных
    """
    # Проверяем и предупреждаем о non-core excludes
    core_excludes, non_core_excludes = get_core_excludes(excludes)
    for nc in non_core_excludes:
        print(
            f"Предупреждение: non-core exclude значение '{nc}' будет игнорироваться в расчётах. "
            f"Core excludes: 'weekends' и даты YYYY-MM-DD.",
            file=sys.stderr
        )
    
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
        is_milestone = node.get("milestone", False)
        
        # Парсинг start
        start_value = node.get("start")
        start: Optional[date] = None
        if isinstance(start_value, datetime):
            start = start_value.date()
        elif isinstance(start_value, date):
            start = start_value
        elif isinstance(start_value, str) and start_value.strip():
            start = parse_date(start_value.strip())
        
        # Парсинг finish
        finish_value = node.get("finish")
        finish: Optional[date] = None
        if isinstance(finish_value, datetime):
            finish = finish_value.date()
        elif isinstance(finish_value, date):
            finish = finish_value
        elif isinstance(finish_value, str) and finish_value.strip():
            finish = parse_date(finish_value.strip())
        
        # Приоритет 1: Явный start
        if start is not None:
            # Нормализация start, если попал на excluded day
            normalized_start, was_normalized = normalize_start(start, core_excludes, is_milestone)
            if was_normalized:
                print(
                    f"Предупреждение: nodes.{node_id}.start ({start.isoformat()}) попал на исключённый день, "
                    f"нормализован на {normalized_start.isoformat()}",
                    file=sys.stderr
                )
            start = normalized_start
        
        # Приоритет 2: Явный finish + duration (backward scheduling)
        elif finish is not None and start is None:
            # Вычисляем start назад от finish
            if duration_days > 1:
                start = sub_workdays(finish, duration_days - 1, core_excludes)
            else:
                start = finish
        
        # Приоритет 3: Зависимости after
        elif start is None and finish is None:
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
                    start = next_workday(latest, core_excludes)
            
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
                            start = parent_sched.start

        visiting.remove(node_id)
        
        # Если не удалось определить дату начала, возвращаем None (unscheduled)
        if start is None:
            skipped_nodes.append(node_id)
            return None

        # Вычисляем finish из start + duration
        computed_finish = finish_date(start, duration_days, core_excludes)
        
        # Если finish был явно указан, проверяем согласованность
        if finish is not None and computed_finish != finish:
            print(
                f"Предупреждение: nodes.{node_id} имеет несогласованные start+duration и finish. "
                f"Вычисленный finish: {computed_finish.isoformat()}, указанный finish: {finish.isoformat()}",
                file=sys.stderr
            )
        
        sched = ScheduledNode(start=start, finish=computed_finish, duration_days=duration_days)
        cache[node_id] = sched
        return sched

    for node_id in nodes.keys():
        resolve(node_id)

    # Выводим предупреждение о пропущенных узлах
    if skipped_nodes:
        print(f"Информация: следующие узлы не имеют вычислимой даты начала и будут пропущены: {', '.join(skipped_nodes)}", file=sys.stderr)

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
    
    # Разделяем excludes на core и non-core
    core_excludes, non_core_excludes = get_core_excludes(excludes)
    exclude_weekends = "weekends" in core_excludes
    date_excludes = [ex for ex in core_excludes if ex != "weekends"]

    nodes: Dict[str, Dict[str, Any]] = plan.get("nodes") or {}
    statuses: Dict[str, Any] = plan.get("statuses") or {}

    # Передаём полный список excludes в compute_schedule
    schedule = compute_schedule(nodes, excludes=excludes)

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
    
    # Выводим только core excludes в Mermaid
    if exclude_weekends:
        lines.append("    excludes weekends")
    for date_ex in date_excludes:
        lines.append(f"    excludes {date_ex}")
    
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
