from __future__ import annotations

import re
import subprocess
from pathlib import Path

from validator.courier_repo import is_courier_dedicated_repo
from validator.git_scope import TaskScope, commit_subject_matches_task_id
from validator.report import Finding

CHECK_ID = "git-commit-no-courier-symbol"
CONVENTIONAL_COMMIT_PREFIX = re.compile(
    r"^(?:fix|feat|chore|refactor|test|docs|style|perf|ci|build|revert)"
    r"(?:\([^)]+\))?!?:\s*",
    re.IGNORECASE,
)
DEPLOYMENT_MARKER_PATTERN = re.compile(r"\b(?:FC|DC)\b")
ALLOWED_LEADING_SEGMENTS = frozenset({"HOTFIX"})


def strip_conventional_commit_prefix(subject: str) -> str:
    return CONVENTIONAL_COMMIT_PREFIX.sub("", subject.strip())


def commit_subject_courier_symbol_segments(subject: str, task_id: str) -> tuple[str, ...]:
    normalized = strip_conventional_commit_prefix(subject)
    if not commit_subject_matches_task_id(normalized, task_id):
        return ()

    remainder = re.sub(
        rf"(?<![A-Za-z0-9]){re.escape(task_id)}(?!\d)\s*",
        "",
        normalized,
        count=1,
    ).strip()
    if not remainder.startswith("|"):
        return ()

    segments = [segment.strip() for segment in remainder.split("|") if segment.strip()]
    if not segments:
        return ()

    if segments[0] in ALLOWED_LEADING_SEGMENTS:
        segments = segments[1:]

    if len(segments) <= 1:
        return ()

    return tuple(segments[:-1])


def commit_subject_includes_courier_symbol_segment(subject: str, task_id: str) -> bool:
    if DEPLOYMENT_MARKER_PATTERN.search(subject):
        return False
    return bool(commit_subject_courier_symbol_segments(subject, task_id))


def get_commit_subject(repo: Path, commit: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), "show", commit, "--format=%s", "--no-patch"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def build_courier_symbol_commit_finding(
    repo: Path,
    *,
    commit: str,
    subject: str,
    segments: tuple[str, ...],
) -> Finding:
    short_commit = commit[:7]
    segment_list = ", ".join(f"'{segment}'" for segment in segments)
    return Finding(
        severity="warning",
        check=CHECK_ID,
        summary=(
            f"Commit {short_commit} includes courier symbol segment(s) in the subject"
        ),
        file=str(repo.resolve()),
        line=1,
        details=subject,
        suggestion=(
            f"Use `<TASK-ID> | <Capitalized message>` without MR-style courier segments "
            f"({segment_list}). Deployment-config commits with FC/DC are exempt."
        ),
    )


def build_task_commit_courier_symbol_findings(
    repo: Path,
    scope: TaskScope,
) -> list[Finding]:
    if not is_courier_dedicated_repo(repo):
        return []

    findings: list[Finding] = []
    for commit in scope.commits:
        subject = get_commit_subject(repo, commit)
        segments = commit_subject_courier_symbol_segments(subject, scope.task_id)
        if not segments:
            continue
        findings.append(
            build_courier_symbol_commit_finding(
                repo,
                commit=commit,
                subject=subject,
                segments=segments,
            )
        )
    return findings
