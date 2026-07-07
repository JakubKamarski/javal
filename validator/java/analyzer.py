from __future__ import annotations

from pathlib import Path

from validator.git_scope import TaskScope
from validator.java.context import JavaFileContext
from validator.java.rules.base import JavaRule
from validator.java.rules.registry import default_java_rules
from validator.report import Finding, Report

SKIP_DIRS = {".git", "target", "build", "out", ".idea", "node_modules"}


class JavaAnalyzer:
    def __init__(self, rules: list[JavaRule] | None = None) -> None:
        self._rules = rules if rules is not None else default_java_rules()

    @property
    def rules(self) -> list[JavaRule]:
        return list(self._rules)

    def analyze_source(self, path: str, source: str) -> list[Finding]:
        context = JavaFileContext.from_source(path, source)
        return self._apply_rules(context)

    def analyze_file(self, file_path: Path) -> list[Finding]:
        context = JavaFileContext.from_path(file_path)
        return self._apply_rules(context)

    def analyze_tree(self, target: Path, scope: TaskScope | None = None) -> Report:
        report = Report(
            target=str(target.resolve()),
            task_id=scope.task_id if scope else "",
        )
        for rule in self._rules:
            report.add_check(rule.check_id)

        if scope is not None:
            return self._analyze_task_scope(target, scope, report)

        java_files = discover_java_files(target)
        if not java_files:
            report.add_pass("java-analysis", "No Java files found to analyze.")
            return report

        for file_path in java_files:
            for finding in self.analyze_file(file_path):
                report.add_finding(finding)

        if not report.invalid_findings:
            report.add_pass(
                "java-analysis",
                f"Analyzed {len(java_files)} Java file(s) with no rule violations.",
            )

        return report

    def _analyze_task_scope(self, target: Path, scope: TaskScope, report: Report) -> Report:
        if not scope.commits:
            report.add_pass(
                "java-analysis",
                f"No commits found for task {scope.task_id} in {target}.",
            )
            return report

        java_files = [
            Path(path)
            for path in scope.changed_lines
            if path.endswith(".java") and Path(path).is_file()
        ]
        if not java_files:
            report.add_pass(
                "java-analysis",
                f"No added or changed Java lines found for task {scope.task_id}.",
            )
            return report

        analyzed_lines = 0
        for file_path in sorted(java_files):
            allowed_lines = scope.changed_lines[str(file_path.resolve())]
            analyzed_lines += len(allowed_lines)
            for finding in self.analyze_file(file_path):
                if finding.line in allowed_lines:
                    report.add_finding(finding)

        if not report.invalid_findings:
            report.add_pass(
                "java-analysis",
                (
                    f"Analyzed {len(java_files)} Java file(s) and {analyzed_lines} "
                    f"task-scoped line(s) from {len(scope.commits)} commit(s) for {scope.task_id}."
                ),
            )

        return report

    def _apply_rules(self, context: JavaFileContext) -> list[Finding]:
        findings: list[Finding] = []
        absolute_path = str(Path(context.path).resolve())
        for rule in self._rules:
            for violation in rule.apply(context):
                finding = violation.to_finding(rule.check_id, absolute_path)
                findings.append(finding)
        return findings


def discover_java_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*.java"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        files.append(path)
    return sorted(files)


def analyze_java_tree(
    target: Path,
    task_id: str | None = None,
    rules: list[JavaRule] | None = None,
) -> Report:
    analyzer = JavaAnalyzer(rules=rules)
    if task_id is None:
        return analyzer.analyze_tree(target)

    from validator.git_scope import build_task_scope

    scope = build_task_scope(target, task_id)
    return analyzer.analyze_tree(target, scope=scope)
