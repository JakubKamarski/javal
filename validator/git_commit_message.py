from __future__ import annotations

import re
import subprocess
from pathlib import Path

from validator.courier_repo import find_courier_identifier
from validator.git_scope import TaskScope, commit_subject_matches_task_id
from validator.report import Finding

CHECK_ID = "git-commit-no-courier-symbol"
CONVENTIONAL_COMMIT_PREFIX = re.compile(
    r"^(?:fix|feat|chore|refactor|test|docs|style|perf|ci|build|revert)"
    r"(?:\([^)]+\))?!?:\s*",
    re.IGNORECASE,
)


def strip_conventional_commit_prefix(subject: str) -> str:
    return CONVENTIONAL_COMMIT_PREFIX.sub("", subject.strip())


def normalize_identifier(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def matches_courier_identifier(segment: str, courier_identifier: str) -> bool:
    normalized_segment = normalize_identifier(segment)
    normalized_courier = normalize_identifier(courier_identifier)
    if not normalized_segment or not normalized_courier:
        return False
    normalized_courier_base = re.sub(r"\d+$", "", normalized_courier)
    return normalized_segment.startswith(normalized_courier) or (
        normalized_courier_base != normalized_courier
        and normalized_segment.startswith(normalized_courier_base)
    )


def commit_subject_courier_symbol_segments(
    subject: str,
    task_id: str,
    courier_identifier: str,
) -> tuple[str, ...]:
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

    return tuple(
        segment
        for segment in segments
        if matches_courier_identifier(segment, courier_identifier)
    )


def commit_subject_includes_courier_symbol_segment(
    subject: str,
    task_id: str,
    courier_identifier: str,
) -> bool:
    return bool(
        commit_subject_courier_symbol_segments(
            subject,
            task_id,
            courier_identifier,
        )
    )


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
            f"Use `<TASK-ID> | <message>` without repeating this repository's courier "
            f"identifier as a standalone segment ({segment_list})."
        ),
    )


def build_task_commit_courier_symbol_findings(
    repo: Path,
    scope: TaskScope,
) -> list[Finding]:
    courier_identifier = find_courier_identifier(repo)
    if courier_identifier is None:
        return []

    findings: list[Finding] = []
    for commit in scope.commits:
        subject = get_commit_subject(repo, commit)
        segments = commit_subject_courier_symbol_segments(
            subject,
            scope.task_id,
            courier_identifier,
        )
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
