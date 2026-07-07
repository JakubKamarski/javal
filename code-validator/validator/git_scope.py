from __future__ import annotations

import re
import subprocess
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

TASK_ID_PATTERN = re.compile(r"^[A-Z][A-Z0-9]*-\d+$")
HUNK_HEADER_PATTERN = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


@dataclass(frozen=True)
class TaskScope:
    task_id: str
    commits: tuple[str, ...]
    changed_lines: dict[str, set[int]]

    @property
    def java_files(self) -> list[Path]:
        return sorted(Path(path) for path in self.changed_lines if path.endswith(".java"))


def validate_task_id(task_id: str) -> str:
    normalized = task_id.strip()
    if not TASK_ID_PATTERN.fullmatch(normalized):
        raise ValueError(f"Invalid task id '{task_id}'. Expected format like PLOG-5164.")
    return normalized


def resolve_repo_path(repo_path: Path | None) -> Path:
    target = Path.cwd() if repo_path is None else repo_path
    resolved = target.expanduser().resolve()
    if not resolved.is_dir():
        raise ValueError(f"Not a directory: {resolved}")
    return resolved


def ensure_git_repo(repo: Path) -> None:
    result = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "--is-inside-work-tree"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0 or result.stdout.strip() != "true":
        raise ValueError(f"Not a git repository: {repo}")


def list_task_commits(repo: Path, task_id: str) -> list[str]:
    prefix = f"{task_id} |"
    result = subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "log",
            "--format=%H",
            f"--grep=^{re.escape(prefix)}",
            "-E",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    commits = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return list(reversed(commits))


def parse_unified_diff(diff_text: str) -> dict[str, set[int]]:
    changed: dict[str, set[int]] = defaultdict(set)
    current_file: str | None = None

    for line in diff_text.splitlines():
        if line.startswith("+++ b/"):
            current_file = line[6:]
            continue
        if line.startswith("+++ ") and not line.startswith("+++ /dev/null"):
            current_file = line[4:]
            continue
        if line.startswith("--- "):
            continue
        if current_file is None or not current_file.endswith(".java"):
            continue
        if not line.startswith("@@"):
            continue

        match = HUNK_HEADER_PATTERN.match(line)
        if not match:
            continue

        new_start = int(match.group(1))
        new_count = int(match.group(2) or "1")
        if new_count == 0:
            continue

        for line_number in range(new_start, new_start + new_count):
            changed[current_file].add(line_number)

    return dict(changed)


def collect_task_changed_lines(repo: Path, task_id: str) -> TaskScope:
    commits = list_task_commits(repo, task_id)
    if not commits:
        return TaskScope(task_id=task_id, commits=(), changed_lines={})

    merged: dict[str, set[int]] = defaultdict(set)
    for commit in commits:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(repo),
                "show",
                commit,
                "-U0",
                "--format=",
                "--no-renames",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        for relative_path, lines in parse_unified_diff(result.stdout).items():
            merged[relative_path].update(lines)

    absolute_changed = {
        str((repo / relative_path).resolve()): line_numbers
        for relative_path, line_numbers in merged.items()
    }
    return TaskScope(task_id=task_id, commits=tuple(commits), changed_lines=absolute_changed)


def build_task_scope(repo: Path, task_id: str) -> TaskScope:
    validate_task_id(task_id)
    ensure_git_repo(repo)
    return collect_task_changed_lines(repo, task_id)
