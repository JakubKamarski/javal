#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from validator.git_scope import build_task_scope, resolve_repo_path, validate_task_id
from validator.java.analyzer import analyze_java_tree


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate Java code changed within a task branch.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  javal PLOG-5164\n"
            "  javal PLOG-5164 .\n"
            "  javal PLOG-5164 projects/locus-fc-orlen\n"
            "  javal PLOG-5164 --format task worktrees/PLOG-5164/locus-fc-orlen\n"
        ),
    )
    parser.add_argument(
        "task_id",
        help="Task id used in commit messages (e.g. PLOG-5164).",
    )
    parser.add_argument(
        "repo_path",
        nargs="?",
        default=".",
        type=Path,
        help="Repository path to analyze. Defaults to the current working directory.",
    )
    parser.add_argument(
        "--format",
        choices=("log", "markdown", "task"),
        default="log",
        help="Output format: log (default), markdown report, or task-file todo list.",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress progress messages on stderr.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        task_id = validate_task_id(args.task_id)
        target = resolve_repo_path(args.repo_path)
        scope = build_task_scope(target, task_id)
    except ValueError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2

    if not args.quiet:
        commit_count = len(scope.commits)
        line_count = sum(len(lines) for lines in scope.changed_lines.values())
        java_files = sum(1 for path in scope.changed_lines if path.endswith(".java"))
        print(
            f"[javal] task={task_id} repo={target} commits={commit_count} "
            f"java_files={java_files} changed_lines={line_count}",
            file=sys.stderr,
        )

    report = analyze_java_tree(target, task_id=task_id)

    if args.format == "markdown":
        print(report.to_markdown())
    elif args.format == "task":
        print(report.to_task_todos())
    else:
        output = report.to_log_lines()
        if output:
            print(output)

    return 1 if report.invalid_findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
