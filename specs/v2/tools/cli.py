"""
Command-line interface for opskarta v2.

This module provides CLI commands for validating and rendering
opskarta v2 plan files.

Commands:
- validate: Validate one or more plan files
- render: Render plans in various formats (gantt, tree, list, deps)

Usage examples:
    # Validate one or more plan files
    python -m specs.v2.tools.cli validate plan.yaml
    python -m specs.v2.tools.cli validate main.yaml nodes.yaml schedule.yaml

    # Render with different formats
    python -m specs.v2.tools.cli render gantt plan.yaml
    python -m specs.v2.tools.cli render tree plan.yaml --view backlog
    python -m specs.v2.tools.cli render list plan.yaml --view tasks_only
    python -m specs.v2.tools.cli render deps plan.yaml

Requirements covered:
- 5.11: CLI SHALL accept list of files as command line arguments
- 5.12: WHEN CLI receives multiple files THEN CLI SHALL pass them to Loader as Plan_Set
"""

import argparse
import sys
from typing import Optional, Sequence

from specs.v2.tools.loader import load_plan_set, LoadError, MergeConflictError
from specs.v2.tools.validator import validate as validate_plan, format_error
from specs.v2.tools.scheduler import compute_schedule
from specs.v2.tools.effort import compute_effort_metrics
from specs.v2.tools.render import render_gantt, render_tree, render_list, render_deps


def create_parser() -> argparse.ArgumentParser:
    """
    Create the argument parser for the CLI.
    
    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        prog="opskarta",
        description="opskarta v2 - Plan validation and rendering tool",
    )
    
    subparsers = parser.add_subparsers(
        dest="command",
        title="commands",
        description="Available commands",
        required=True,
    )
    
    # Validate command
    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate one or more plan files",
        description="Load and validate plan files, reporting any errors found.",
    )
    validate_parser.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help="YAML plan file(s) to validate",
    )
    
    # Render command with subcommands
    render_parser = subparsers.add_parser(
        "render",
        help="Render plan in various formats",
        description="Render plan files in different output formats.",
    )
    
    render_subparsers = render_parser.add_subparsers(
        dest="format",
        title="formats",
        description="Available render formats",
        required=True,
    )
    
    # Gantt subcommand
    gantt_parser = render_subparsers.add_parser(
        "gantt",
        help="Render as Mermaid Gantt diagram",
        description="Generate a Mermaid Gantt diagram from the plan.",
    )
    gantt_parser.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help="YAML plan file(s) to render",
    )
    gantt_parser.add_argument(
        "--view",
        metavar="VIEW_ID",
        help="View ID to use for filtering and formatting",
    )
    
    # Tree subcommand
    tree_parser = render_subparsers.add_parser(
        "tree",
        help="Render as hierarchical tree",
        description="Generate a hierarchical tree view of the plan.",
    )
    tree_parser.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help="YAML plan file(s) to render",
    )
    tree_parser.add_argument(
        "--view",
        metavar="VIEW_ID",
        help="View ID to use for filtering and sorting",
    )
    
    # List subcommand
    list_parser = render_subparsers.add_parser(
        "list",
        help="Render as flat list",
        description="Generate a flat list view of the plan.",
    )
    list_parser.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help="YAML plan file(s) to render",
    )
    list_parser.add_argument(
        "--view",
        metavar="VIEW_ID",
        help="View ID to use for filtering and sorting",
    )
    
    # Deps subcommand
    deps_parser = render_subparsers.add_parser(
        "deps",
        help="Render as dependency graph",
        description="Generate a Mermaid flowchart showing dependencies.",
    )
    deps_parser.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help="YAML plan file(s) to render",
    )
    deps_parser.add_argument(
        "--view",
        metavar="VIEW_ID",
        help="View ID to use for filtering",
    )
    
    return parser


def cmd_validate(files: list[str]) -> int:
    """
    Execute the validate command.
    
    Loads and validates the specified plan files, printing any
    validation errors found.
    
    Args:
        files: List of YAML file paths to validate
        
    Returns:
        Exit code: 0 if valid, 1 if errors found
        
    Requirements:
        - 5.11: Accept list of files as arguments
        - 5.12: Pass multiple files to Loader as Plan_Set
    """
    try:
        # Load and merge plan files
        plan = load_plan_set(files)
        
        # Validate the merged plan
        result = validate_plan(plan)
        
        if result.is_valid:
            print("OK")
            
            # Print warnings if any
            for warning in result.warnings:
                print(format_error(warning), file=sys.stderr)
            
            return 0
        else:
            # Print errors
            for error in result.errors:
                print(format_error(error), file=sys.stderr)
            
            # Print warnings
            for warning in result.warnings:
                print(format_error(warning), file=sys.stderr)
            
            return 1
            
    except LoadError as e:
        print(f"[error] [loading] {e}", file=sys.stderr)
        return 1
    except MergeConflictError as e:
        print(f"[error] [merge] {e}", file=sys.stderr)
        return 1


def cmd_render_gantt(files: list[str], view_id: Optional[str]) -> int:
    """
    Execute the render gantt command.
    
    Loads plan files, computes schedule, and renders as Mermaid Gantt.
    
    Args:
        files: List of YAML file paths
        view_id: Optional view ID for filtering/formatting
        
    Returns:
        Exit code: 0 on success, 1 on error
    """
    try:
        # Load and merge plan files
        plan = load_plan_set(files)
        
        # Validate first
        result = validate_plan(plan)
        if not result.is_valid:
            for error in result.errors:
                print(format_error(error), file=sys.stderr)
            return 1
        
        # Compute effort metrics
        compute_effort_metrics(plan)
        
        # Compute schedule
        compute_schedule(plan)
        
        # Render gantt (view_id is required for gantt)
        # If no view_id provided, use empty string to render all scheduled nodes
        output = render_gantt(plan, view_id or "")
        print(output)
        
        return 0
        
    except LoadError as e:
        print(f"[error] [loading] {e}", file=sys.stderr)
        return 1
    except MergeConflictError as e:
        print(f"[error] [merge] {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"[error] [render] {e}", file=sys.stderr)
        return 1


def cmd_render_tree(files: list[str], view_id: Optional[str]) -> int:
    """
    Execute the render tree command.
    
    Loads plan files and renders as hierarchical tree.
    
    Args:
        files: List of YAML file paths
        view_id: Optional view ID for filtering/sorting
        
    Returns:
        Exit code: 0 on success, 1 on error
    """
    try:
        # Load and merge plan files
        plan = load_plan_set(files)
        
        # Validate first
        result = validate_plan(plan)
        if not result.is_valid:
            for error in result.errors:
                print(format_error(error), file=sys.stderr)
            return 1
        
        # Compute effort metrics
        compute_effort_metrics(plan)
        
        # Render tree
        output = render_tree(plan, view_id)
        print(output)
        
        return 0
        
    except LoadError as e:
        print(f"[error] [loading] {e}", file=sys.stderr)
        return 1
    except MergeConflictError as e:
        print(f"[error] [merge] {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"[error] [render] {e}", file=sys.stderr)
        return 1


def cmd_render_list(files: list[str], view_id: Optional[str]) -> int:
    """
    Execute the render list command.
    
    Loads plan files and renders as flat list.
    
    Args:
        files: List of YAML file paths
        view_id: Optional view ID for filtering/sorting
        
    Returns:
        Exit code: 0 on success, 1 on error
    """
    try:
        # Load and merge plan files
        plan = load_plan_set(files)
        
        # Validate first
        result = validate_plan(plan)
        if not result.is_valid:
            for error in result.errors:
                print(format_error(error), file=sys.stderr)
            return 1
        
        # Compute effort metrics
        compute_effort_metrics(plan)
        
        # Render list
        output = render_list(plan, view_id)
        print(output)
        
        return 0
        
    except LoadError as e:
        print(f"[error] [loading] {e}", file=sys.stderr)
        return 1
    except MergeConflictError as e:
        print(f"[error] [merge] {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"[error] [render] {e}", file=sys.stderr)
        return 1


def cmd_render_deps(files: list[str], view_id: Optional[str]) -> int:
    """
    Execute the render deps command.
    
    Loads plan files and renders as dependency graph.
    
    Args:
        files: List of YAML file paths
        view_id: Optional view ID for filtering
        
    Returns:
        Exit code: 0 on success, 1 on error
    """
    try:
        # Load and merge plan files
        plan = load_plan_set(files)
        
        # Validate first
        result = validate_plan(plan)
        if not result.is_valid:
            for error in result.errors:
                print(format_error(error), file=sys.stderr)
            return 1
        
        # Compute effort metrics
        compute_effort_metrics(plan)
        
        # Render deps
        output = render_deps(plan, view_id)
        print(output)
        
        return 0
        
    except LoadError as e:
        print(f"[error] [loading] {e}", file=sys.stderr)
        return 1
    except MergeConflictError as e:
        print(f"[error] [merge] {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"[error] [render] {e}", file=sys.stderr)
        return 1


def main(argv: Optional[Sequence[str]] = None) -> int:
    """
    Main entry point for the CLI.
    
    Args:
        argv: Command line arguments (defaults to sys.argv[1:])
        
    Returns:
        Exit code
    """
    parser = create_parser()
    args = parser.parse_args(argv)
    
    if args.command == "validate":
        return cmd_validate(args.files)
    
    elif args.command == "render":
        if args.format == "gantt":
            return cmd_render_gantt(args.files, args.view)
        elif args.format == "tree":
            return cmd_render_tree(args.files, args.view)
        elif args.format == "list":
            return cmd_render_list(args.files, args.view)
        elif args.format == "deps":
            return cmd_render_deps(args.files, args.view)
    
    # Should not reach here due to required subparsers
    return 1


if __name__ == "__main__":
    sys.exit(main())
