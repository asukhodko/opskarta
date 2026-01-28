"""
Пакет рендереров opskarta.

Содержит референсные реализации рендереров для генерации
различных представлений из файлов плана и views.

Доступные рендереры:
- mermaid_gantt: Генерация диаграмм Gantt в формате Mermaid
"""

from .mermaid_gantt import render_mermaid_gantt

__all__ = ['render_mermaid_gantt']
