from __future__ import annotations

from pathlib import Path

from validator.git_scope import build_task_scope
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

    return java_report
