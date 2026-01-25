from pathlib import Path

from opskarta.io import load_yaml
from opskarta.validation import validate_plan, validate_views
from opskarta.render.mermaid_gantt import render_mermaid_gantt


def test_render_mermaid_gantt_smoke():
    root = Path(__file__).resolve().parents[1]
    plan = load_yaml(root / "examples" / "hello.plan.yaml")
    views = load_yaml(root / "examples" / "hello.views.yaml")

    validate_plan(plan)
    validate_views(views, plan["meta"]["id"])

    view = views["gantt_views"]["overview"]
    out = render_mermaid_gantt(plan=plan, view=view)

    assert "gantt" in out
    assert "section" in out
    assert "prep" in out
