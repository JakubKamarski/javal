from __future__ import annotations

from pathlib import Path

from validator.git_scope import build_task_scope
from validator.git_workspace import CHECK_ID as GIT_UNCOMMITTED_CHECK_ID
from validator.git_workspace import build_uncommitted_changes_finding
from validator.java.analyzer import JavaAnalyzer
from validator.liquibase.analyzer import LiquibaseAnalyzer
from validator.report import Report


def analyze_repo(target: Path, task_id: str | None = None) -> Report:
    scope = build_task_scope(target, task_id) if task_id else None

    java_report = JavaAnalyzer().analyze_tree(target, scope=scope)
    liquibase_report = LiquibaseAnalyzer().analyze_tree(target, scope=scope)

    for check in liquibase_report.checks_run:
        java_report.add_check(check)
    for finding in liquibase_report.findings:
        java_report.add_finding(finding)

    java_report.add_check(GIT_UNCOMMITTED_CHECK_ID)
    uncommitted_finding = build_uncommitted_changes_finding(target)
    if uncommitted_finding is not None:
        java_report.add_finding(uncommitted_finding)

    return java_report
