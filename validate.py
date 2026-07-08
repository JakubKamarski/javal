#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from validator.analyze import analyze_repo
from validator.git_scope import build_task_scope, resolve_repo_path, validate_task_id
from validator.java.rules.registry import list_registered_rule_meta
from validator.todo import append_todo

VALIDATE_EPILOG = (
    "Examples:\n"
    "  javal PLOG-5164\n"
    "  javal PLOG-5164 .\n"
    "  javal PLOG-5164 projects/locus-fc-orlen\n"
    "  javal PLOG-5164 --format task worktrees/PLOG-5164/locus-fc-orlen\n"
    "\n"
    "Report validator issues (AI agents):\n"
    "  javal todo --file <path> --line <n> --description \"<issue>\"\n"
    "  Run `javal todo --help` for when and how to use this."
)

TODO_DESCRIPTION = (
    "Report a false positive or validator bug for later maintenance.\n"
    "\n"
    "Use when javal flags code that is correct, or when a rule misfires due to a\n"
    "validator bug. Do NOT use to skip findings you disagree with stylistically —\n"
    "fix the Java source instead."
)

TODO_EPILOG = (
    "Required flags:\n"
    "  --file PATH          Absolute path to the flagged source file\n"
    "  --line N             Line number from the javal finding\n"
    "  --description TEXT   What is wrong (include rule/check name when known)\n"
    "\n"
    "Example:\n"
    "  javal todo \\\n"
    "    --file /abs/path/src/Foo.java \\\n"
    "    --line 42 \\\n"
    "    --description \"False positive: unused-imports — Set is used via static import\"\n"
    "\n"
    "Appends to projects/me-javal/todo.md (local, gitignored). Prints the line on stdout."
)


def parse_list_rules_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="javal list-rules",
        description="List registered Java validation rules.",
    )
    args = parser.parse_args(argv)
    args.command = "list-rules"
    return args


def parse_validate_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate Java code changed within a task branch.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=VALIDATE_EPILOG,
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
        "--path-format",
        choices=("absolute", "relative", "filename"),
        default="absolute",
        help="File path style in output: absolute (default), relative, or filename.",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress progress messages on stderr.",
    )
    args = parser.parse_args(argv)
    args.command = "validate"
    return args


def parse_todo_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="javal todo",
        description=TODO_DESCRIPTION,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=TODO_EPILOG,
    )
    parser.add_argument(
        "--file",
        required=True,
        type=Path,
        help="Absolute path to the flagged source file.",
    )
    parser.add_argument(
        "--line",
        required=True,
        type=int,
        help="Line number from the javal finding.",
    )
    parser.add_argument(
        "--description",
        required=True,
        help="What is wrong (include rule/check name when known).",
    )
    args = parser.parse_args(argv)
    args.command = "todo"
    return args


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    tokens = list(argv if argv is not None else sys.argv[1:])
    if tokens and tokens[0] == "todo":
        return parse_todo_args(tokens[1:])
    if tokens and tokens[0] == "list-rules":
        return parse_list_rules_args(tokens[1:])
    return parse_validate_args(tokens)


def run_todo(args: argparse.Namespace) -> int:
    try:
        line = append_todo(args.file, args.line, args.description)
    except ValueError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2

    print(line)
    return 0


def run_list_rules(args: argparse.Namespace) -> int:
    del args
    for meta in list_registered_rule_meta():
        scope = meta.scope
        if meta.tree_scope:
            scope = f"{scope}/{meta.tree_scope}"
        print(f"{meta.check_id}\t{scope}\t{meta.description}")
    return 0


def run_validate(args: argparse.Namespace) -> int:
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
        changelog_files = sum(
            1 for path in scope.changed_lines if path.endswith(".xml")
        )
        print(
            f"[javal] task={task_id} repo={target} commits={commit_count} "
            f"java_files={java_files} changelog_files={changelog_files} "
            f"changed_lines={line_count}",
            file=sys.stderr,
        )

    report = analyze_repo(target, scope=scope)

    path_format = args.path_format
    if args.format == "markdown":
        print(report.to_markdown(path_format=path_format))
    elif args.format == "task":
        print(report.to_task_todos(path_format=path_format))
    else:
        output = report.to_log_lines(path_format=path_format)
        if output:
            print(output)

    return 1 if report.invalid_findings else 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.command == "todo":
        return run_todo(args)
    if args.command == "list-rules":
        return run_list_rules(args)
    return run_validate(args)


if __name__ == "__main__":
    raise SystemExit(main())
