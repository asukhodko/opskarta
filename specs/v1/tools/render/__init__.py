"""
opskarta renderers package.

Contains reference implementations of renderers for generating
various representations from plan and views files.

Available renderers:
- plan2gantt: Mermaid Gantt chart generation
- plan2dag: Mermaid DAG flowchart generation

Usage as modules:
    python -m render.plan2gantt --help
    python -m render.plan2dag --help

Usage as library (lazy imports to avoid RuntimeWarning):
    from render.plan2gantt import render_gantt_mermaid
    from render.plan2dag import render_dag_mermaid
"""

# Lazy imports to avoid RuntimeWarning when running as module
# Import directly when needed: from render.plan2gantt import render_gantt_mermaid

__all__ = ['plan2gantt', 'plan2dag']
