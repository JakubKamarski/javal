from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from validator.git_scope import TaskScope
from validator.report import Report


def empty_task_scope_pass(
    report: Report,
    check_id: str,
    scope: TaskScope,
    target: Path,
) -> Report:
    report.add_pass(check_id, f"No commits found for task {scope.task_id} in {target}.")
    return report


def changed_files_in_scope(
    scope: TaskScope,
    *,
    predicate: Callable[[Path], bool],
) -> list[Path]:
    return sorted(
        Path(path)
        for path in scope.changed_lines
        if predicate(Path(path)) and Path(path).is_file()
    )


def allowed_lines_for(scope: TaskScope, file_path: Path) -> set[int]:
    return scope.changed_lines[str(file_path.resolve())]
