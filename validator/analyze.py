from __future__ import annotations

from pathlib import Path

from validator.analyzer_protocol import Analyzer
from validator.git_scope import TaskScope, build_task_scope
from validator.git_workspace import GitWorkspaceAnalyzer
from validator.java.analyzer import JavaAnalyzer
from validator.liquibase.analyzer import LiquibaseAnalyzer
from validator.report import Report

DEFAULT_ANALYZERS: tuple[Analyzer, ...] = (
    JavaAnalyzer(),
    LiquibaseAnalyzer(),
    GitWorkspaceAnalyzer(),
)


def analyze_repo(
    target: Path,
    scope: TaskScope | None = None,
    *,
    task_id: str | None = None,
    analyzers: tuple[Analyzer, ...] | None = None,
) -> Report:
    if scope is None and task_id is not None:
        scope = build_task_scope(target, task_id)

    active_analyzers = DEFAULT_ANALYZERS if analyzers is None else analyzers
    reports = [analyzer.analyze(target, scope) for analyzer in active_analyzers]
    return Report.merge(reports)
