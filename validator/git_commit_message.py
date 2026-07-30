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


def courier_identifier_aliases(courier_identifier: str) -> tuple[tuple[str, ...], ...]:
    identifier_parts = tuple(re.findall(r"[A-Za-z0-9]+", courier_identifier))
    if not identifier_parts:
        return ()

    aliases = [identifier_parts]
    base_last_part = re.sub(r"\d+$", "", identifier_parts[-1])
    if base_last_part and base_last_part != identifier_parts[-1]:
        aliases.append((*identifier_parts[:-1], base_last_part))
    return tuple(aliases)


def courier_identifier_pattern(courier_identifier: str) -> re.Pattern[str] | None:
    aliases = courier_identifier_aliases(courier_identifier)
    if not aliases:
        return None

    variants = sorted(
        (
            r"[^A-Za-z0-9]+".join(re.escape(part) for part in alias)
            for alias in aliases
        ),
        key=len,
        reverse=True,
    )
    return re.compile(
        rf"(?<![A-Za-z0-9])(?:{'|'.join(variants)})(?![A-Za-z0-9])",
        re.IGNORECASE,
    )


def commit_subject_courier_identifier_occurrences(
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
    pattern = courier_identifier_pattern(courier_identifier)
    if pattern is None:
        return ()

    return tuple(match.group(0) for match in pattern.finditer(remainder))


def commit_subject_includes_courier_identifier(
    subject: str,
    task_id: str,
    courier_identifier: str,
) -> bool:
    return bool(
        commit_subject_courier_identifier_occurrences(
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


def build_courier_identifier_commit_finding(
    repo: Path,
    *,
    commit: str,
    subject: str,
    occurrences: tuple[str, ...],
) -> Finding:
    short_commit = commit[:7]
    occurrence_list = ", ".join(f"'{occurrence}'" for occurrence in occurrences)
    return Finding(
        severity="warning",
        check=CHECK_ID,
        summary=f"Commit {short_commit} includes the courier identifier in the subject",
        file=str(repo.resolve()),
        line=1,
        details=subject,
        suggestion=(
            f"Use `<TASK-ID> | <message>` without repeating this repository's courier "
            f"identifier as a standalone token ({occurrence_list})."
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
        occurrences = commit_subject_courier_identifier_occurrences(
            subject,
            scope.task_id,
            courier_identifier,
        )
        if not occurrences:
            continue
        findings.append(
            build_courier_identifier_commit_finding(
                repo,
                commit=commit,
                subject=subject,
                occurrences=occurrences,
            )
        )
    return findings
