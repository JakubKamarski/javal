from __future__ import annotations

import os
import subprocess
from pathlib import Path

from validator.courier_repo import is_courier_dedicated_repo
from validator.git_commit_message import (
    CHECK_ID as COMMIT_MESSAGE_CHECK_ID,
    build_task_commit_courier_symbol_findings,
)
from validator.git_scope import TaskScope
from validator.report import Finding, Report

CHECK_ID = "git-uncommitted-changes"


def list_uncommitted_paths(repo: Path) -> list[str]:
    result = subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "status",
            "--porcelain=v1",
            "-z",
            "--untracked-files=all",
        ],
        capture_output=True,
        check=True,
    )
    paths: list[str] = []
    entries = result.stdout.split(b"\0")
    index = 0
    while index < len(entries):
        entry = entries[index]
        index += 1
        if len(entry) < 4:
            continue
        status = entry[:2].decode("ascii")
        paths.append(os.fsdecode(entry[3:]))
        if "R" in status or "C" in status:
            index += 1
    return paths


def build_uncommitted_changes_finding(repo: Path) -> Finding | None:
    relative_paths = list_uncommitted_paths(repo)
    if not relative_paths:
        return None

    absolute_paths = [str((repo / relative_path).resolve()) for relative_path in relative_paths]
    primary_path = absolute_paths[0]
    details = "\n".join(relative_paths)
    count = len(relative_paths)
    summary = (
        f"Repository has {count} uncommitted change(s)"
        if count > 1
        else "Repository has uncommitted changes"
    )

    return Finding(
        severity="warning",
        check=CHECK_ID,
        summary=summary,
        file=primary_path,
        line=1,
        details=details,
        suggestion="Commit local changes before finishing validation.",
    )


class GitWorkspaceAnalyzer:
    def analyze(self, target: Path, scope: TaskScope | None = None) -> Report:
        report = Report(
            target=str(target.resolve()),
            task_id=scope.task_id if scope else "",
        )
        report.add_check(CHECK_ID)
        finding = build_uncommitted_changes_finding(target)
        if finding is not None:
            report.add_finding(finding)

        if scope is not None and scope.commits and is_courier_dedicated_repo(target):
            report.add_check(COMMIT_MESSAGE_CHECK_ID)
            commit_findings = build_task_commit_courier_symbol_findings(target, scope)
            for commit_finding in commit_findings:
                report.add_finding(commit_finding)

        return report
