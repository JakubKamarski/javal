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
    line_authors: dict[str, dict[int, str]]
    commit_changed_lines: tuple[tuple[str, dict[str, set[int]]], ...]

    @property
    def java_files(self) -> list[Path]:
        return sorted(Path(path) for path in self.changed_lines if path.endswith(".java"))

    def author_for_line(self, file_path: Path, line_number: int) -> str:
        return self.line_authors.get(str(file_path.resolve()), {}).get(line_number, "")


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


def resolve_git_repo_root(start: Path) -> Path:
    candidate = start.resolve()
    if candidate.is_file():
        candidate = candidate.parent
    result = subprocess.run(
        ["git", "-C", str(candidate), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise ValueError(f"Not a git repository: {start}")
    return Path(result.stdout.strip()).resolve()


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
        if current_file is None:
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


def get_commit_author(repo: Path, commit: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), "show", commit, "--format=%an", "--no-patch"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def collect_task_changed_lines(repo: Path, task_id: str) -> TaskScope:
    commits = list_task_commits(repo, task_id)
    if not commits:
        return TaskScope(
            task_id=task_id,
            commits=(),
            changed_lines={},
            line_authors={},
            commit_changed_lines=(),
        )

    merged: dict[str, set[int]] = defaultdict(set)
    line_authors: dict[str, dict[int, str]] = defaultdict(dict)
    commit_changed_lines: list[tuple[str, dict[str, set[int]]]] = []
    for commit in commits:
        author = get_commit_author(repo, commit)
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
        per_commit: dict[str, set[int]] = defaultdict(set)
        for relative_path, lines in parse_unified_diff(result.stdout).items():
            merged[relative_path].update(lines)
            absolute_path = str((repo / relative_path).resolve())
            per_commit[absolute_path].update(lines)
            for line_number in lines:
                line_authors[absolute_path][line_number] = author
        commit_changed_lines.append((commit, dict(per_commit)))

    absolute_changed = {
        str((repo / relative_path).resolve()): line_numbers
        for relative_path, line_numbers in merged.items()
    }
    return TaskScope(
        task_id=task_id,
        commits=tuple(commits),
        changed_lines=absolute_changed,
        line_authors=dict(line_authors),
        commit_changed_lines=tuple(commit_changed_lines),
    )


def collect_worktree_changed_lines(repo: Path) -> dict[str, set[int]]:
    from validator.git_workspace import list_uncommitted_paths

    merged: dict[str, set[int]] = defaultdict(set)

    result = subprocess.run(
        ["git", "-C", str(repo), "diff", "HEAD", "-U0", "--no-renames"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 0:
        for relative_path, lines in parse_unified_diff(result.stdout).items():
            absolute_path = str((repo / relative_path).resolve())
            merged[absolute_path].update(lines)

    for relative_path in list_uncommitted_paths(repo):
        absolute_path = str((repo / relative_path).resolve())
        if absolute_path in merged:
            continue
        file_path = Path(absolute_path)
        if not file_path.is_file():
            continue
        try:
            line_count = len(file_path.read_text(encoding="utf-8").splitlines())
        except OSError:
            continue
        if line_count:
            merged[absolute_path].update(range(1, line_count + 1))

    return dict(merged)


def get_git_user_name(repo: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), "config", "user.name"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def build_task_scope(repo: Path, task_id: str) -> TaskScope:
    validate_task_id(task_id)
    ensure_git_repo(repo)
    return collect_task_changed_lines(repo, task_id)
