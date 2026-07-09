from __future__ import annotations

from pathlib import Path

from validator.analyzer_base import allowed_lines_for, changed_files_in_scope, empty_task_scope_pass
from validator.discovery import discover_files
from validator.git_scope import TaskScope, build_task_scope
from validator.java.context import JavaFileContext
from validator.java.rules.applicability import filter_paths, matches_file_applicability
from validator.java.rules.base import JavaRule, TreeJavaRule
from validator.java.rules.registry import default_java_rules, default_tree_java_rules
from validator.report import Finding, Report


class JavaAnalyzer:
    def __init__(
        self,
        rules: list[JavaRule] | None = None,
        tree_rules: list[TreeJavaRule] | None = None,
    ) -> None:
        self._rules = rules if rules is not None else default_java_rules()
        self._tree_rules = tree_rules if tree_rules is not None else default_tree_java_rules()
        self._context_cache: dict[str, JavaFileContext] = {}

    @property
    def rules(self) -> list[JavaRule]:
        return list(self._rules)

    @property
    def tree_rules(self) -> list[TreeJavaRule]:
        return list(self._tree_rules)

    def analyze(self, target: Path, scope: TaskScope | None = None) -> Report:
        return self.analyze_tree(target, scope=scope)

    def analyze_source(self, path: str, source: str) -> list[Finding]:
        context = JavaFileContext.from_source(path, source)
        self._store_context(context)
        return self._apply_rules(context)

    def analyze_file(self, file_path: Path) -> list[Finding]:
        context = self._get_or_load_context(file_path)
        return self._apply_rules(context)

    def analyze_tree(self, target: Path, scope: TaskScope | None = None) -> Report:
        self._context_cache.clear()

        report = Report(
            target=str(target.resolve()),
            task_id=scope.task_id if scope else "",
        )
        for rule in self._rules:
            report.add_check(rule.check_id)
        for rule in self._tree_rules:
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

        self._apply_tree_rules(java_files, report)

        if not report.invalid_findings:
            report.add_pass(
                "java-analysis",
                f"Analyzed {len(java_files)} Java file(s) with no rule violations.",
            )

        return report

    def _analyze_task_scope(self, target: Path, scope: TaskScope, report: Report) -> Report:
        if not scope.commits:
            return empty_task_scope_pass(report, "java-analysis", scope, target)

        java_files = changed_files_in_scope(
            scope,
            predicate=lambda path: path.suffix == ".java",
        )
        if not java_files:
            report.add_pass(
                "java-analysis",
                f"No added or changed Java lines found for task {scope.task_id}.",
            )
            return report

        analyzed_lines = 0
        for file_path in java_files:
            allowed_lines = allowed_lines_for(scope, file_path)
            analyzed_lines += len(allowed_lines)
            for finding in self.analyze_file(file_path):
                if finding.line in allowed_lines:
                    report.add_finding(finding)

        all_java_files = discover_java_files(target)
        self._apply_tree_rules(all_java_files, report, scope=scope)

        if not report.invalid_findings:
            report.add_pass(
                "java-analysis",
                (
                    f"Analyzed {len(java_files)} Java file(s) and {analyzed_lines} "
                    f"task-scoped line(s) from {len(scope.commits)} commit(s) for {scope.task_id}."
                ),
            )

        return report

    def _store_context(self, context: JavaFileContext) -> None:
        absolute_path = str(Path(context.path).resolve())
        self._context_cache[absolute_path] = context

    def _get_or_load_context(self, file_path: Path) -> JavaFileContext:
        absolute_path = str(file_path.resolve())
        cached = self._context_cache.get(absolute_path)
        if cached is not None:
            return cached

        context = JavaFileContext.from_path(file_path)
        self._context_cache[absolute_path] = context
        return context

    def _apply_rules(self, context: JavaFileContext) -> list[Finding]:
        findings: list[Finding] = []
        absolute_path = str(Path(context.path).resolve())
        file_path = Path(context.path)
        for rule in self._rules:
            if not matches_file_applicability(file_path, rule.meta.file_applicability):
                continue
            if not rule.applies_to(context):
                continue
            for violation in rule.apply(context):
                finding = violation.to_finding(rule.check_id, absolute_path)
                findings.append(finding)
        return findings

    def _apply_tree_rules(
        self,
        java_files: list[Path],
        report: Report,
        scope: TaskScope | None = None,
    ) -> None:
        for rule in self._tree_rules:
            eligible_files = filter_paths(java_files, rule.meta.tree_file_applicability)
            for finding in rule.apply_tree(
                eligible_files,
                scope=scope,
                contexts=self._context_cache,
            ):
                report.add_finding(finding)


def discover_java_files(root: Path) -> list[Path]:
    return discover_files(root, pattern="*.java")


def analyze_java_tree(
    target: Path,
    task_id: str | None = None,
    scope: TaskScope | None = None,
    rules: list[JavaRule] | None = None,
) -> Report:
    analyzer = JavaAnalyzer(rules=rules)
    if scope is None and task_id is not None:
        scope = build_task_scope(target, task_id)
    return analyzer.analyze_tree(target, scope=scope)
