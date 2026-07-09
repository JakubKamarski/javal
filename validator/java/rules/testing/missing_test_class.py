from __future__ import annotations

from pathlib import Path

from validator.git_scope import TaskScope
from validator.java.ast import (
    has_query_annotation,
    has_task_changed_query_method,
    is_abstract_top_level_type,
    is_public_top_level_type,
)
from validator.java.context import JavaFileContext
from validator.java.rules.base import TreeJavaRule
from validator.java.rules.testing._support import (
    IT_SUFFIX,
    TESTING_SUGGESTION,
    expected_test_class_name,
    is_main_source_file,
    is_test_source_file,
    resolve_expected_test_path,
    subject_test_requirement,
)
from validator.java.rules.testing._injection_coverage import (
    build_injected_by_index,
    is_covered_by_ancestor_it,
    production_class_paths,
)
from validator.report import Finding


def _production_sources_to_check(java_files: list[Path], scope: TaskScope | None) -> list[Path]:
    if scope is not None:
        if not scope.commits:
            return []
        changed_paths = set(scope.changed_lines)
        return [
            path
            for path in java_files
            if str(path.resolve()) in changed_paths and _is_checkable_production_source(path)
        ]

    return [
        path
        for path in java_files
        if _is_checkable_production_source(path) and not is_main_source_file(path)
    ]


def _is_checkable_production_source(path: Path) -> bool:
    if is_test_source_file(path):
        return False
    if is_main_source_file(path):
        return True
    return "src" not in path.resolve().parts


class MissingTestClassRule(TreeJavaRule):
    scope_policy = "task_changed"

    @property
    def check_id(self) -> str:
        return "java-testing-missing-test-class"

    def apply_tree(
        self,
        java_files: list[Path],
        scope: TaskScope | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        class_to_path = production_class_paths(java_files)
        injected_by = build_injected_by_index(class_to_path)

        for source_path in _production_sources_to_check(java_files, scope):
            finding = self._check_production_source(
                source_path,
                scope,
                class_to_path=class_to_path,
                injected_by=injected_by,
            )
            if finding is not None:
                findings.append(finding)

        return findings

    def _check_production_source(
        self,
        source_path: Path,
        scope: TaskScope | None = None,
        *,
        class_to_path: dict[str, Path] | None = None,
        injected_by: dict[str, set[str]] | None = None,
    ) -> Finding | None:
        class_name = source_path.stem
        requirement = subject_test_requirement(class_name)
        if requirement is None:
            return None

        context = JavaFileContext.from_path(source_path)
        if is_abstract_top_level_type(context, class_name):
            return None
        if requirement.requires_public_class and not is_public_top_level_type(context, class_name):
            return None
        if requirement.requires_query_annotation:
            if not has_query_annotation(context):
                return None
            if scope is not None:
                changed_lines = scope.changed_lines.get(str(source_path.resolve()), set())
                if not has_task_changed_query_method(context, changed_lines):
                    return None

        test_class_name = expected_test_class_name(class_name, requirement)
        expected_test_path = resolve_expected_test_path(source_path, test_class_name)
        if expected_test_path.is_file():
            return None

        if (
            requirement.test_suffix == IT_SUFFIX
            and requirement.subject_suffix == "Service"
            and class_to_path is not None
            and injected_by is not None
            and is_covered_by_ancestor_it(class_name, class_to_path, injected_by)
        ):
            return None

        return Finding(
            severity="warning",
            check=self.check_id,
            summary=requirement.summary_template.format(
                subject=class_name,
                test_class=test_class_name,
            ),
            file=str(source_path.resolve()),
            line=1,
            details=f"Expected test file: {expected_test_path.name}",
            suggestion=TESTING_SUGGESTION,
        )
