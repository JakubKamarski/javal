from __future__ import annotations

from pathlib import Path

from validator.analyzer_base import allowed_lines_for, changed_files_in_scope, empty_task_scope_pass
from validator.discovery import discover_files
from validator.git_scope import TaskScope, get_git_user_name, build_task_scope
from validator.liquibase.changeset import ChangeSet, parse_changesets
from validator.report import Finding, Report

CHECK_ID = "liquibase-changeset-author"


class LiquibaseAnalyzer:
    def analyze(self, target: Path, scope: TaskScope | None = None) -> Report:
        return self.analyze_tree(target, scope=scope)

    def analyze_tree(self, target: Path, scope: TaskScope | None = None) -> Report:
        report = Report(
            target=str(target.resolve()),
            task_id=scope.task_id if scope else "",
        )
        report.add_check(CHECK_ID)

        if scope is not None:
            return self._analyze_task_scope(target, scope, report)

        changelog_files = discover_changelog_files(target)
        if not changelog_files:
            report.add_pass(CHECK_ID, "No Liquibase changelog files found to analyze.")
            return report

        expected_author = get_git_user_name(target)
        for file_path in changelog_files:
            for finding in self._check_file(file_path, expected_author=expected_author):
                report.add_finding(finding)

        if not report.invalid_findings:
            report.add_pass(
                CHECK_ID,
                f"Analyzed {len(changelog_files)} Liquibase changelog file(s) with no author violations.",
            )
        return report

    def _analyze_task_scope(self, target: Path, scope: TaskScope, report: Report) -> Report:
        if not scope.commits:
            return empty_task_scope_pass(report, CHECK_ID, scope, target)

        changelog_files = changed_files_in_scope(
            scope,
            predicate=is_liquibase_changelog,
        )
        if not changelog_files:
            report.add_pass(
                CHECK_ID,
                f"No added or changed Liquibase changelog lines found for task {scope.task_id}.",
            )
            return report

        expected_author = get_git_user_name(target)
        for file_path in changelog_files:
            allowed_lines = allowed_lines_for(scope, file_path)
            for finding in self._check_file(
                file_path,
                expected_author=expected_author,
                allowed_lines=allowed_lines,
            ):
                report.add_finding(finding)

        if not report.invalid_findings:
            report.add_pass(
                CHECK_ID,
                (
                    f"Checked Liquibase author on task-scoped changeSets in "
                    f"{len(changelog_files)} changelog file(s) for {scope.task_id}."
                ),
            )
        return report

    def _check_file(
        self,
        file_path: Path,
        expected_author: str,
        allowed_lines: set[int] | None = None,
    ) -> list[Finding]:
        source = file_path.read_text(encoding="utf-8")
        findings: list[Finding] = []
        absolute_path = str(file_path.resolve())

        for changeset in parse_changesets(source):
            if allowed_lines is not None and not _changeset_introduced_by_task(
                changeset, allowed_lines
            ):
                continue
            if not changeset.author:
                findings.append(
                    Finding(
                        severity="warning",
                        check=CHECK_ID,
                        summary=(
                            f"ChangeSet '{changeset.changeset_id}' is missing an author attribute"
                        ),
                        file=absolute_path,
                        line=changeset.start_line,
                        suggestion=(
                            f"Set author=\"{expected_author}\" on the changeSet opening tag."
                        ),
                    )
                )
                continue
            if expected_author and changeset.author != expected_author:
                findings.append(
                    Finding(
                        severity="warning",
                        check=CHECK_ID,
                        summary=(
                            f"ChangeSet '{changeset.changeset_id}' author is "
                            f"'{changeset.author}', expected git user.name "
                            f"'{expected_author}'"
                        ),
                        file=absolute_path,
                        line=changeset.start_line,
                        suggestion=(
                            f"Set author=\"{expected_author}\" to match local git config user.name."
                        ),
                    )
                )
        return findings


def is_liquibase_changelog(path: Path) -> bool:
    if not path.is_file() or path.suffix.lower() != ".xml":
        return False
    if path.name.endswith("-changelog.xml") or path.name == "db-changelog.xml":
        return True
    try:
        head = path.read_text(encoding="utf-8", errors="ignore")[:4096]
    except OSError:
        return False
    return "databaseChangeLog" in head


def discover_changelog_files(root: Path) -> list[Path]:
    return discover_files(root, pattern="*.xml", predicate=is_liquibase_changelog)


def _changeset_introduced_by_task(changeset: ChangeSet, allowed_lines: set[int]) -> bool:
    return changeset.start_line in allowed_lines


def analyze_liquibase_tree(
    target: Path,
    task_id: str | None = None,
    scope: TaskScope | None = None,
) -> Report:
    analyzer = LiquibaseAnalyzer()
    if scope is None and task_id is not None:
        scope = build_task_scope(target, task_id)
    return analyzer.analyze_tree(target, scope=scope)
