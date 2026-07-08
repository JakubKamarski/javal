from __future__ import annotations

import subprocess
from pathlib import Path

from validator.git_scope import TaskScope
from validator.report import Finding, Report

CHECK_ID = "git-uncommitted-changes"


def list_uncommitted_paths(repo: Path) -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(repo), "status", "--porcelain", "--untracked-files=all"],
        capture_output=True,
        text=True,
        check=True,
    )
    paths: list[str] = []
    for line in result.stdout.splitlines():
        if len(line) < 4:
            continue
        entry = line[3:].strip()
        if not entry:
            continue
        if " -> " in entry:
            entry = entry.split(" -> ", 1)[1]
        paths.append(entry)
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
        return report
