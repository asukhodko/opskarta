#!/usr/bin/env python3
"""
Валидатор файлов плана и представлений opskarta.

Использование:
    python validate.py plan.yaml                    # Валидация плана
    python validate.py plan.yaml views.yaml         # Валидация плана и views
    python validate.py --schema plan.yaml           # Валидация через JSON Schema

Уровни валидации:
    1. Синтаксис — корректность YAML
    2. Схема — соответствие JSON Schema (опционально)
    3. Семантика — ссылочная целостность, бизнес-правила

Зависимости: PyYAML (pip install pyyaml)
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


# ============================================================================
# Исключения
# ============================================================================

class ValidationError(Exception):
    """Ошибка валидации с информацией о пути к полю."""
    
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
        """Форматирует сообщение об ошибке."""
        lines = []
        
        if self.path:
            lines.append(f"Ошибка: {self.message}")
            lines.append(f"  Путь: {self.path}")
        else:
            lines.append(f"Ошибка: {self.message}")
        
        if self.value is not None:
            lines.append(f"  Значение: {repr(self.value)}")
        
        if self.expected:
            lines.append(f"  Ожидается: {self.expected}")
        
        if self.available:
            lines.append(f"  Доступные: {', '.join(sorted(self.available))}")
        
        return '\n'.join(lines)


# ============================================================================
# Загрузка файлов
# ============================================================================

def load_yaml(file_path: Path) -> Dict[str, Any]:
    """
    Загружает YAML файл.
    
    Raises:
        ValidationError: если файл не найден или содержит невалидный YAML
    """
    try:
        import yaml
    except ImportError:
        print("Ошибка: модуль PyYAML не установлен", file=sys.stderr)
        print("Установите: pip install pyyaml", file=sys.stderr)
        sys.exit(1)
    
    if not file_path.exists():
        raise ValidationError(
            f"Файл не найден: {file_path}",
            expected="существующий файл"
        )
    
    try:
        content = file_path.read_text(encoding='utf-8')
        data = yaml.safe_load(content)
        
        if data is None:
            return {}
        
        if not isinstance(data, dict):
            raise ValidationError(
                "Корневой элемент должен быть объектом",
                path="(корень)",
                value=type(data).__name__,
                expected="object (dict)"
            )
        
        return data
        
    except yaml.YAMLError as e:
        raise ValidationError(
            f"Ошибка парсинга YAML: {e}",
            path=str(file_path)
        )


def load_json_schema(schema_path: Path) -> Dict[str, Any]:
    """Загружает JSON Schema файл."""
    if not schema_path.exists():
        raise ValidationError(
            f"Файл схемы не найден: {schema_path}",
            expected="существующий файл JSON Schema"
        )
    
    try:
        content = schema_path.read_text(encoding='utf-8')
        return json.loads(content)
    except json.JSONDecodeError as e:
        raise ValidationError(
            f"Ошибка парсинга JSON Schema: {e}",
            path=str(schema_path)
        )


# ============================================================================
# Валидация плана
# ============================================================================

def validate_plan(plan: Dict[str, Any]) -> List[str]:
    """
    Валидирует файл плана.
    
    Проверяет:
    - Обязательные поля (version, nodes)
    - Ссылочную целостность (parent, after, status)
    - Формат полей планирования (start, duration)
    - Отсутствие циклических зависимостей
    
    Returns:
        Список предупреждений (не критичных проблем)
    
    Raises:
        ValidationError: при обнаружении критической ошибки
    """
    warnings: List[str] = []
    
    # --- Проверка version ---
    if 'version' not in plan:
        raise ValidationError(
            "Отсутствует обязательное поле 'version'",
            path="version",
            expected="целое число (например, 1)"
        )
    
    version = plan.get('version')
    if not isinstance(version, int):
        raise ValidationError(
            "Поле 'version' должно быть целым числом",
            path="version",
            value=version,
            expected="int"
        )
    
    if version != 1:
        warnings.append(f"Предупреждение: version={version}, валидатор поддерживает только version=1")
    
    # --- Проверка nodes ---
    if 'nodes' not in plan:
        raise ValidationError(
            "Отсутствует обязательное поле 'nodes'",
            path="nodes",
            expected="объект с узлами"
        )
    
    nodes = plan.get('nodes')
    if not isinstance(nodes, dict):
        raise ValidationError(
            "Поле 'nodes' должно быть объектом",
            path="nodes",
            value=type(nodes).__name__,
            expected="object (dict)"
        )
    
    # Собираем множество всех node_id для проверки ссылок
    node_ids: Set[str] = set(nodes.keys())
    
    # Собираем множество статусов (если определены)
    statuses: Set[str] = set()
    if 'statuses' in plan:
        statuses_data = plan.get('statuses')
        if isinstance(statuses_data, dict):
            statuses = set(statuses_data.keys())
    
    # --- Валидация каждого узла ---
    for node_id, node in nodes.items():
        node_path = f"nodes.{node_id}"
        
        # Проверка типа узла
        if not isinstance(node, dict):
            raise ValidationError(
                "Узел должен быть объектом",
                path=node_path,
                value=type(node).__name__,
                expected="object (dict)"
            )
        
        # Проверка обязательного поля title
        if 'title' not in node:
            raise ValidationError(
                "Отсутствует обязательное поле 'title'",
                path=f"{node_path}.title",
                expected="непустая строка"
            )
        
        title = node.get('title')
        if not isinstance(title, str) or not title.strip():
            raise ValidationError(
                "Поле 'title' должно быть непустой строкой",
                path=f"{node_path}.title",
                value=title,
                expected="непустая строка"
            )
        
        # Проверка parent (ссылочная целостность)
        if 'parent' in node:
            parent = node.get('parent')
            if parent is not None:
                if not isinstance(parent, str):
                    raise ValidationError(
                        "Поле 'parent' должно быть строкой",
                        path=f"{node_path}.parent",
                        value=parent,
                        expected="string (node_id)"
                    )
                if parent not in node_ids:
                    raise ValidationError(
                        "Ссылка на несуществующий узел",
                        path=f"{node_path}.parent",
                        value=parent,
                        expected="существующий node_id",
                        available=list(node_ids)
                    )
        
        # Проверка after (ссылочная целостность)
        if 'after' in node:
            after = node.get('after')
            if after is not None:
                if not isinstance(after, list):
                    raise ValidationError(
                        "Поле 'after' должно быть списком",
                        path=f"{node_path}.after",
                        value=type(after).__name__,
                        expected="list of strings"
                    )
                
                for i, dep in enumerate(after):
                    if not isinstance(dep, str):
                        raise ValidationError(
                            "Элемент списка 'after' должен быть строкой",
                            path=f"{node_path}.after[{i}]",
                            value=dep,
                            expected="string (node_id)"
                        )
                    if dep not in node_ids:
                        raise ValidationError(
                            "Ссылка на несуществующий узел в зависимостях",
                            path=f"{node_path}.after[{i}]",
                            value=dep,
                            expected="существующий node_id",
                            available=list(node_ids)
                        )
        
        # Проверка status (ссылочная целостность)
        if 'status' in node:
            status = node.get('status')
            if status is not None:
                if not isinstance(status, str):
                    raise ValidationError(
                        "Поле 'status' должно быть строкой",
                        path=f"{node_path}.status",
                        value=status,
                        expected="string (status_id)"
                    )
                if statuses and status not in statuses:
                    raise ValidationError(
                        "Ссылка на несуществующий статус",
                        path=f"{node_path}.status",
                        value=status,
                        expected="существующий status_id",
                        available=list(statuses)
                    )
        
        # Проверка формата start (YYYY-MM-DD)
        if 'start' in node:
            start = node.get('start')
            if start is not None:
                start_str = str(start)
                if not re.match(r'^\d{4}-\d{2}-\d{2}$', start_str):
                    raise ValidationError(
                        "Неверный формат даты",
                        path=f"{node_path}.start",
                        value=start,
                        expected="формат YYYY-MM-DD (например, 2024-01-15)"
                    )
                # Проверка корректности даты
                try:
                    from datetime import datetime
                    datetime.strptime(start_str, '%Y-%m-%d')
                except ValueError:
                    raise ValidationError(
                        "Некорректная дата (не существует в календаре)",
                        path=f"{node_path}.start",
                        value=start,
                        expected="существующая дата в формате YYYY-MM-DD"
                    )
        
        # Проверка формата duration (<число><единица>)
        if 'duration' in node:
            duration = node.get('duration')
            if duration is not None:
                duration_str = str(duration)
                if not re.match(r'^[1-9][0-9]*[dw]$', duration_str):
                    raise ValidationError(
                        "Неверный формат длительности",
                        path=f"{node_path}.duration",
                        value=duration,
                        expected="формат <число><единица>, где число >= 1, единица: d (дни) или w (недели)"
                    )
    
    # --- Проверка циклических зависимостей ---
    _check_cycles_parent(nodes)
    _check_cycles_after(nodes)
    
    return warnings


def _check_cycles_parent(nodes: Dict[str, Any]) -> None:
    """
    Проверяет отсутствие циклических ссылок через parent.
    
    Raises:
        ValidationError: при обнаружении цикла
    """
    for node_id in nodes:
        visited: Set[str] = set()
        current = node_id
        
        while current:
            if current in visited:
                # Нашли цикл
                cycle_path = _build_cycle_path(nodes, node_id, 'parent')
                raise ValidationError(
                    "Обнаружена циклическая ссылка через parent",
                    path=f"nodes.{node_id}.parent",
                    value=cycle_path,
                    expected="ациклический граф родительских связей"
                )
            
            visited.add(current)
            node = nodes.get(current, {})
            current = node.get('parent') if isinstance(node, dict) else None


def _check_cycles_after(nodes: Dict[str, Any]) -> None:
    """
    Проверяет отсутствие циклических зависимостей через after.
    
    Использует алгоритм поиска в глубину (DFS) для обнаружения циклов.
    
    Raises:
        ValidationError: при обнаружении цикла
    """
    # Состояния: 0 = не посещён, 1 = в процессе, 2 = завершён
    state: Dict[str, int] = {node_id: 0 for node_id in nodes}
    
    def dfs(node_id: str, path: List[str]) -> None:
        if state[node_id] == 2:
            return
        
        if state[node_id] == 1:
            # Нашли цикл
            cycle_start = path.index(node_id)
            cycle = path[cycle_start:] + [node_id]
            raise ValidationError(
                "Обнаружена циклическая зависимость через after",
                path=f"nodes.{node_id}.after",
                value=" -> ".join(cycle),
                expected="ациклический граф зависимостей"
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
    """Строит строковое представление цикла для сообщения об ошибке."""
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


# ============================================================================
# Валидация views
# ============================================================================

def validate_views(views: Dict[str, Any], plan: Dict[str, Any]) -> List[str]:
    """
    Валидирует файл представлений относительно файла плана.
    
    Проверяет:
    - Обязательные поля (version, project)
    - Соответствие project и meta.id плана
    - Ссылки на узлы в представлениях
    
    Returns:
        Список предупреждений
    
    Raises:
        ValidationError: при обнаружении критической ошибки
    """
    warnings: List[str] = []
    
    # --- Проверка version ---
    if 'version' not in views:
        raise ValidationError(
            "Отсутствует обязательное поле 'version'",
            path="version",
            expected="целое число (например, 1)"
        )
    
    version = views.get('version')
    if not isinstance(version, int):
        raise ValidationError(
            "Поле 'version' должно быть целым числом",
            path="version",
            value=version,
            expected="int"
        )
    
    # --- Проверка project ---
    if 'project' not in views:
        raise ValidationError(
            "Отсутствует обязательное поле 'project'",
            path="project",
            expected="строка, совпадающая с meta.id плана"
        )
    
    project = views.get('project')
    if not isinstance(project, str):
        raise ValidationError(
            "Поле 'project' должно быть строкой",
            path="project",
            value=project,
            expected="string"
        )
    
    # --- Проверка соответствия project и meta.id ---
    meta = plan.get('meta', {})
    plan_id = meta.get('id') if isinstance(meta, dict) else None
    
    # meta.id обязателен при использовании views
    if not plan_id:
        raise ValidationError(
            "Поле 'meta.id' обязательно в плане при использовании файла представлений",
            path="meta.id",
            expected="непустая строка (идентификатор проекта)"
        )
    
    if project != plan_id:
        raise ValidationError(
            "Поле 'project' не совпадает с meta.id плана",
            path="project",
            value=project,
            expected=f"'{plan_id}' (значение meta.id из плана)"
        )
    
    # --- Проверка ссылок на узлы в gantt_views ---
    node_ids: Set[str] = set(plan.get('nodes', {}).keys())
    
    gantt_views = views.get('gantt_views')
    if gantt_views is not None:
        if not isinstance(gantt_views, dict):
            raise ValidationError(
                "Поле 'gantt_views' должно быть объектом",
                path="gantt_views",
                value=type(gantt_views).__name__,
                expected="object (dict)"
            )
        
        for view_id, view in gantt_views.items():
            view_path = f"gantt_views.{view_id}"
            
            if not isinstance(view, dict):
                raise ValidationError(
                    "Представление должно быть объектом",
                    path=view_path,
                    value=type(view).__name__,
                    expected="object (dict)"
                )
            
            # Проверка excludes и предупреждение о конкретных датах
            excludes = view.get('excludes')
            if excludes is not None:
                if isinstance(excludes, list):
                    for item in excludes:
                        if isinstance(item, str) and re.match(r'^\d{4}-\d{2}-\d{2}$', item):
                            warnings.append(
                                f"Предупреждение: {view_path}.excludes содержит конкретную дату '{item}'. "
                                f"Конкретные даты являются подсказками для рендерера и не влияют на core-алгоритм вычисления дат."
                            )
            
            lanes = view.get('lanes')
            if lanes is None:
                raise ValidationError(
                    "Отсутствует обязательное поле 'lanes'",
                    path=f"{view_path}.lanes",
                    expected="непустой объект с дорожками"
                )
            
            if not isinstance(lanes, dict) or not lanes:
                raise ValidationError(
                    "Поле 'lanes' должно быть непустым объектом",
                    path=f"{view_path}.lanes",
                    value=lanes,
                    expected="непустой object (dict)"
                )
            
            for lane_id, lane in lanes.items():
                lane_path = f"{view_path}.lanes.{lane_id}"
                
                if not isinstance(lane, dict):
                    raise ValidationError(
                        "Дорожка должна быть объектом",
                        path=lane_path,
                        value=type(lane).__name__,
                        expected="object (dict)"
                    )
                
                lane_nodes = lane.get('nodes')
                if lane_nodes is None:
                    raise ValidationError(
                        "Отсутствует обязательное поле 'nodes'",
                        path=f"{lane_path}.nodes",
                        expected="список node_id"
                    )
                
                if not isinstance(lane_nodes, list):
                    raise ValidationError(
                        "Поле 'nodes' должно быть списком",
                        path=f"{lane_path}.nodes",
                        value=type(lane_nodes).__name__,
                        expected="list of strings"
                    )
                
                for i, ref_node_id in enumerate(lane_nodes):
                    if not isinstance(ref_node_id, str):
                        raise ValidationError(
                            "Элемент списка 'nodes' должен быть строкой",
                            path=f"{lane_path}.nodes[{i}]",
                            value=ref_node_id,
                            expected="string (node_id)"
                        )
                    
                    if ref_node_id not in node_ids:
                        raise ValidationError(
                            "Ссылка на несуществующий узел в плане",
                            path=f"{lane_path}.nodes[{i}]",
                            value=ref_node_id,
                            expected="существующий node_id из плана",
                            available=list(node_ids)
                        )
    
    return warnings


# ============================================================================
# Валидация через JSON Schema
# ============================================================================

def validate_with_schema(data: Dict[str, Any], schema: Dict[str, Any], 
                         file_type: str) -> List[str]:
    """
    Валидирует данные через JSON Schema.
    
    Requires: jsonschema library (pip install jsonschema)
    
    Returns:
        Список предупреждений
    
    Raises:
        ValidationError: при несоответствии схеме
    """
    try:
        import jsonschema
    except ImportError:
        raise ValidationError(
            "Для валидации через JSON Schema требуется библиотека jsonschema",
            expected="pip install jsonschema"
        )
    
    try:
        jsonschema.validate(instance=data, schema=schema)
        return []
    except jsonschema.ValidationError as e:
        path = '.'.join(str(p) for p in e.absolute_path) if e.absolute_path else '(корень)'
        raise ValidationError(
            f"Несоответствие JSON Schema: {e.message}",
            path=path,
            value=e.instance if not isinstance(e.instance, dict) else type(e.instance).__name__,
            expected=str(e.schema.get('type', e.schema.get('description', 'см. схему')))
        )


# ============================================================================
# CLI интерфейс
# ============================================================================

def get_script_dir() -> Path:
    """Возвращает директорию, в которой находится скрипт."""
    return Path(__file__).parent.resolve()


def get_schemas_dir() -> Path:
    """Возвращает путь к директории schemas/ относительно скрипта."""
    return get_script_dir().parent / 'schemas'


def main():
    """Главная функция CLI."""
    parser = argparse.ArgumentParser(
        description='Валидатор файлов плана и представлений opskarta',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python validate.py plan.yaml                    # Валидация плана
  python validate.py plan.yaml views.yaml         # Валидация плана и views
  python validate.py --schema plan.yaml           # Валидация через JSON Schema

Уровни валидации:
  По умолчанию выполняется семантическая валидация (ссылочная целостность,
  бизнес-правила). С флагом --schema дополнительно проверяется соответствие
  JSON Schema.
        """
    )
    
    parser.add_argument(
        'plan_file',
        type=Path,
        help='Путь к файлу плана (*.plan.yaml)'
    )
    
    parser.add_argument(
        'views_file',
        type=Path,
        nargs='?',
        default=None,
        help='Путь к файлу представлений (*.views.yaml), опционально'
    )
    
    parser.add_argument(
        '--schema',
        action='store_true',
        help='Дополнительно валидировать через JSON Schema'
    )
    
    parser.add_argument(
        '--plan-schema',
        type=Path,
        default=None,
        help='Путь к JSON Schema для плана (по умолчанию: schemas/plan.schema.json)'
    )
    
    parser.add_argument(
        '--views-schema',
        type=Path,
        default=None,
        help='Путь к JSON Schema для views (по умолчанию: schemas/views.schema.json)'
    )
    
    args = parser.parse_args()
    
    all_warnings: List[str] = []
    
    try:
        # --- Загрузка и валидация плана ---
        print(f"Валидация плана: {args.plan_file}")
        plan = load_yaml(args.plan_file)
        
        # Валидация через JSON Schema (если запрошено)
        if args.schema:
            schemas_dir = get_schemas_dir()
            plan_schema_path = args.plan_schema or (schemas_dir / 'plan.schema.json')
            
            print(f"  Проверка JSON Schema: {plan_schema_path}")
            plan_schema = load_json_schema(plan_schema_path)
            schema_warnings = validate_with_schema(plan, plan_schema, 'plan')
            all_warnings.extend(schema_warnings)
        
        # Семантическая валидация
        print("  Семантическая валидация...")
        plan_warnings = validate_plan(plan)
        all_warnings.extend(plan_warnings)
        
        print(f"  ✓ План валиден")
        
        # --- Загрузка и валидация views (если указан) ---
        if args.views_file:
            print(f"\nВалидация представлений: {args.views_file}")
            views = load_yaml(args.views_file)
            
            # Валидация через JSON Schema (если запрошено)
            if args.schema:
                views_schema_path = args.views_schema or (schemas_dir / 'views.schema.json')
                
                print(f"  Проверка JSON Schema: {views_schema_path}")
                views_schema = load_json_schema(views_schema_path)
                schema_warnings = validate_with_schema(views, views_schema, 'views')
                all_warnings.extend(schema_warnings)
            
            # Семантическая валидация
            print("  Семантическая валидация...")
            views_warnings = validate_views(views, plan)
            all_warnings.extend(views_warnings)
            
            print(f"  ✓ Представления валидны")
        
        # --- Вывод предупреждений ---
        if all_warnings:
            print("\nПредупреждения:")
            for warning in all_warnings:
                print(f"  ⚠ {warning}")
        
        print("\n✓ Валидация завершена успешно")
        sys.exit(0)
        
    except ValidationError as e:
        print(f"\n{e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nПрервано пользователем", file=sys.stderr)
        sys.exit(130)


if __name__ == '__main__':
    main()
