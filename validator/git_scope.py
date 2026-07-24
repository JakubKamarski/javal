from __future__ import annotations

import re
import subprocess
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

TRACKER_TASK_ID_PATTERN = re.compile(r"^[A-Z][A-Z0-9]*-\d+$")
MAINTENANCE_TASK_ID_PATTERN = re.compile(
    r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*-update$"
)
HUNK_HEADER_PATTERN = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")
BLAME_HEADER_PATTERN = re.compile(r"^([0-9a-f]{40}) \d+ (\d+)(?: \d+)?$")
SCOPED_FILE_SUFFIXES = frozenset({".java", ".xml"})


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
    if not (
        TRACKER_TASK_ID_PATTERN.fullmatch(normalized)
        or MAINTENANCE_TASK_ID_PATTERN.fullmatch(normalized)
    ):
        raise ValueError(
            f"Invalid task id '{task_id}'. "
            "Expected format like ABC-1234 or sample-tool-update."
        )
    return normalized


def validate_iteration(task_id: str, iteration: int | None) -> int | None:
    is_maintenance = MAINTENANCE_TASK_ID_PATTERN.fullmatch(task_id) is not None
    if is_maintenance:
        if iteration is None:
            raise ValueError(
                f"Maintenance task {task_id} requires a positive --iteration."
            )
        if iteration <= 0:
            raise ValueError(f"Iteration must be positive: {iteration}")
        return iteration
    if iteration is not None:
        raise ValueError(
            f"--iteration is only valid for maintenance task ids ending in -update: "
            f"{task_id}"
        )
    return None


def task_scope_token(task_id: str, iteration: int | None = None) -> str:
    normalized = validate_task_id(task_id)
    normalized_iteration = validate_iteration(normalized, iteration)
    if normalized_iteration is None:
        return normalized
    return f"{normalized}#{normalized_iteration}"


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


def commit_subject_matches_task_id(
    subject: str,
    task_id: str,
    iteration: int | None = None,
) -> bool:
    token = task_scope_token(task_id, iteration)
    if iteration is not None:
        return subject == token or subject.startswith(f"{token} | ")
    return re.search(
        rf"(?<![A-Za-z0-9]){re.escape(token)}(?!\d)",
        subject,
    ) is not None


def list_task_commits(
    repo: Path,
    task_id: str,
    iteration: int | None = None,
) -> list[str]:
    result = subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "log",
            "--format=%H%x00%s",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    commits = []
    for line in result.stdout.splitlines():
        commit, separator, subject = line.partition("\0")
        if separator and commit_subject_matches_task_id(subject, task_id, iteration):
            commits.append(commit)
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


def list_commit_changed_paths(repo: Path, commit: str) -> list[str]:
    result = subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "diff-tree",
            "--root",
            "--no-commit-id",
            "--name-only",
            "-r",
            "-z",
            "-M",
            commit,
        ],
        capture_output=True,
        check=True,
    )
    return [
        raw_path.decode(errors="surrogateescape")
        for raw_path in result.stdout.split(b"\0")
        if raw_path
    ]


def blame_current_lines(repo: Path, relative_path: str) -> dict[int, str]:
    result = subprocess.run(
        ["git", "-C", str(repo), "blame", "--line-porcelain", "HEAD", "--", relative_path],
        capture_output=True,
        text=True,
        check=True,
    )
    commit_by_line: dict[int, str] = {}
    for output_line in result.stdout.splitlines():
        match = BLAME_HEADER_PATTERN.fullmatch(output_line)
        if match is None:
            continue
        commit_by_line[int(match.group(2))] = match.group(1)
    return commit_by_line


def is_scoped_source_path(relative_path: str) -> bool:
    return Path(relative_path).suffix.lower() in SCOPED_FILE_SUFFIXES


def collect_task_changed_lines(
    repo: Path,
    task_id: str,
    iteration: int | None = None,
) -> TaskScope:
    commits = list_task_commits(repo, task_id, iteration)
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
    author_by_commit = {commit: get_commit_author(repo, commit) for commit in commits}
    paths_by_commit = {
        commit: list_commit_changed_paths(repo, commit)
        for commit in commits
    }
    commit_lines_by_sha: dict[str, dict[str, set[int]]] = {
        commit: {} for commit in commits
    }

    for commit in commits:
        for relative_path in paths_by_commit[commit]:
            if not is_scoped_source_path(relative_path):
                continue
            absolute_path = str((repo / relative_path).resolve())
            if Path(absolute_path).is_file():
                commit_lines_by_sha[commit].setdefault(absolute_path, set())

    candidate_paths = sorted(
        {
            relative_path
            for changed_paths in paths_by_commit.values()
            for relative_path in changed_paths
            if is_scoped_source_path(relative_path) and (repo / relative_path).is_file()
        }
    )
    task_commits = set(commits)
    for relative_path in candidate_paths:
        absolute_path = str((repo / relative_path).resolve())
        for line_number, commit in blame_current_lines(repo, relative_path).items():
            if commit not in task_commits:
                continue
            merged[absolute_path].add(line_number)
            line_authors[absolute_path][line_number] = author_by_commit[commit]
            commit_lines_by_sha[commit].setdefault(absolute_path, set()).add(line_number)

    return TaskScope(
        task_id=task_id,
        commits=tuple(commits),
        changed_lines=dict(merged),
        line_authors=dict(line_authors),
        commit_changed_lines=tuple(
            (commit, commit_lines_by_sha[commit]) for commit in commits
        ),
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
        except (OSError, UnicodeError):
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


def build_task_scope(
    repo: Path,
    task_id: str,
    iteration: int | None = None,
) -> TaskScope:
    normalized = validate_task_id(task_id)
    normalized_iteration = validate_iteration(normalized, iteration)
    repo_root = resolve_git_repo_root(repo)
    ensure_git_repo(repo_root)
    return collect_task_changed_lines(repo_root, normalized, normalized_iteration)
