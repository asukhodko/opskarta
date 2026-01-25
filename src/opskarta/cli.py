from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict

from .errors import OpskartaError, SchedulingError, ValidationError
from .io import load_yaml
from .validation import validate_plan, validate_views
from .render.mermaid_gantt import render_mermaid_gantt


def _cmd_validate(args: argparse.Namespace) -> int:
    plan = load_yaml(args.plan)
    validate_plan(plan)

    if args.views:
        views = load_yaml(args.views)
        project_id = plan["meta"]["id"]
        validate_views(views, project_id)

    print("OK")
    return 0


def _cmd_render_gantt(args: argparse.Namespace) -> int:
    plan = load_yaml(args.plan)
    validate_plan(plan)

    views = load_yaml(args.views)
    project_id = plan["meta"]["id"]
    validate_views(views, project_id)

    gantt_views = views.get("gantt_views") or {}
    if args.view not in gantt_views:
        available = ", ".join(sorted(gantt_views.keys()))
        raise OpskartaError(f"Unknown view: {args.view!r}. Available: {available}")

    view_obj = gantt_views[args.view]
    out = render_mermaid_gantt(plan=plan, view=view_obj)
    sys.stdout.write(out)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="opskarta", description="opskarta reference CLI")
    sub = p.add_subparsers(dest="command", required=True)

    p_val = sub.add_parser("validate", help="Validate opskarta plan/views files")
    p_val.add_argument("plan", help="Path to *.plan.yaml")
    p_val.add_argument("views", nargs="?", help="Path to *.views.yaml (optional)")
    p_val.set_defaults(func=_cmd_validate)

    p_render = sub.add_parser("render", help="Render outputs from plan+views")
    render_sub = p_render.add_subparsers(dest="render_command", required=True)

    p_gantt = render_sub.add_parser("gantt", help="Render Mermaid Gantt")
    p_gantt.add_argument("--plan", required=True, help="Path to *.plan.yaml")
    p_gantt.add_argument("--views", required=True, help="Path to *.views.yaml")
    p_gantt.add_argument("--view", required=True, help="View id inside gantt_views")
    p_gantt.set_defaults(func=_cmd_render_gantt)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        return int(args.func(args))
    except (ValidationError, SchedulingError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    except OpskartaError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
