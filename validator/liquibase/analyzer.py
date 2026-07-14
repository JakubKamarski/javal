from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from unicodedata import combining, normalize
from xml.parsers.expat import ExpatError

from validator.analyzer_base import allowed_lines_for, changed_files_in_scope, empty_task_scope_pass
from validator.discovery import discover_files
from validator.git_scope import (
    TaskScope,
    collect_worktree_changed_lines,
    get_git_user_name,
    build_task_scope,
)
from validator.liquibase.changeset import ChangeSet, parse_changesets
from validator.report import Finding, Report

CHECK_ID = "liquibase-changeset-author"


@dataclass(frozen=True)
class AuthorExpectation:
    name: str
    source_label: str


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
        worktree_lines = collect_worktree_changed_lines(target)
        local_author = get_git_user_name(target)
        changelog_files = _changelog_files_in_scope(scope, worktree_lines)

        if not scope.commits and not changelog_files:
            return empty_task_scope_pass(report, CHECK_ID, scope, target)

        if not changelog_files:
            report.add_pass(
                CHECK_ID,
                f"No added or changed Liquibase changelog lines found for task {scope.task_id}.",
            )
            return report

        for file_path in changelog_files:
            absolute_path = str(file_path.resolve())
            allowed_lines = allowed_lines_for(scope, file_path) | worktree_lines.get(
                absolute_path, set()
            )
            uncommitted_lines = worktree_lines.get(absolute_path, set())

            def expected_author_for_line(
                line: int,
                *,
                _file_path: Path = file_path,
                _uncommitted_lines: set[int] = uncommitted_lines,
                _local_author: str = local_author,
            ) -> AuthorExpectation:
                if line in _uncommitted_lines:
                    return AuthorExpectation(_local_author, "git user.name")
                return AuthorExpectation(
                    scope.author_for_line(_file_path, line),
                    "commit author",
                )

            for finding in self._check_file(
                file_path,
                allowed_lines=allowed_lines,
                expected_author_for_line=expected_author_for_line,
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
        expected_author: str = "",
        allowed_lines: set[int] | None = None,
        expected_author_for_line: Callable[[int], AuthorExpectation] | None = None,
    ) -> list[Finding]:
        source = file_path.read_text(encoding="utf-8")
        findings: list[Finding] = []
        absolute_path = str(file_path.resolve())

        try:
            changesets = parse_changesets(source)
        except ExpatError as error:
            return [
                Finding(
                    severity="warning",
                    check=CHECK_ID,
                    summary=f"Cannot parse Liquibase changelog: {error}",
                    file=absolute_path,
                    line=error.lineno,
                    suggestion="Correct the XML before validating changeSet authors.",
                )
            ]

        for changeset in changesets:
            if allowed_lines is not None and not _changeset_introduced_by_task(
                changeset, allowed_lines
            ):
                continue
            if expected_author_for_line is not None:
                expectation = expected_author_for_line(changeset.start_line)
                expected = expectation.name
                expected_label = expectation.source_label
            else:
                expected = expected_author
                expected_label = "git user.name"
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
                            f"Set author=\"{expected}\" on the changeSet opening tag."
                            if expected
                            else "Set author on the changeSet opening tag."
                        ),
                    )
                )
                continue
            if expected and not _author_names_match(changeset.author, expected):
                suggestion = (
                    f"Set author=\"{expected}\" to match the introducing commit author."
                    if expected_label == "commit author"
                    else f"Set author=\"{expected}\" to match local git config user.name."
                )
                findings.append(
                    Finding(
                        severity="warning",
                        check=CHECK_ID,
                        summary=(
                            f"ChangeSet '{changeset.changeset_id}' author is "
                            f"'{changeset.author}', expected {expected_label} "
                            f"'{expected}'"
                        ),
                        file=absolute_path,
                        line=changeset.start_line,
                        suggestion=suggestion,
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


def _author_names_match(author: str, expected_author: str) -> bool:
    normalized_author = _normalize_author_name(author)
    normalized_expected_author = _normalize_author_name(expected_author)
    if normalized_author == normalized_expected_author:
        return True

    author_given_name, author_surname = _split_author_name(normalized_author)
    expected_given_name, expected_surname = _split_author_name(normalized_expected_author)
    if author_given_name != expected_given_name or not author_surname or not expected_surname:
        return False

    expected_surname_components = expected_surname.split("-")
    return len(expected_surname_components) > 1 and author_surname in expected_surname_components


def _normalize_author_name(name: str) -> str:
    normalized = normalize("NFKD", name).casefold()
    without_diacritics = "".join(character for character in normalized if not combining(character))
    return " ".join(without_diacritics.split())


def _split_author_name(name: str) -> tuple[str, str]:
    given_name, separator, surname = name.partition(" ")
    return given_name, surname if separator else ""


def _changelog_files_in_scope(
    scope: TaskScope,
    worktree_lines: dict[str, set[int]],
) -> list[Path]:
    changelog_files = changed_files_in_scope(scope, predicate=is_liquibase_changelog)
    known_paths = {str(path.resolve()) for path in changelog_files}

    for absolute_path in worktree_lines:
        if absolute_path in known_paths:
            continue
        file_path = Path(absolute_path)
        if is_liquibase_changelog(file_path):
            changelog_files.append(file_path)
            known_paths.add(absolute_path)

    return sorted(changelog_files)


def analyze_liquibase_tree(
    target: Path,
    task_id: str | None = None,
    scope: TaskScope | None = None,
) -> Report:
    analyzer = LiquibaseAnalyzer()
    if scope is None and task_id is not None:
        scope = build_task_scope(target, task_id)
    return analyzer.analyze_tree(target, scope=scope)
