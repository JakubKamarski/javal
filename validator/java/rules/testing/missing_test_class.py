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
from validator.java.rules.applicability import context_for
from validator.java.rules.base import TreeJavaRule
from validator.java.rules.testing._support import (
    IT_SUFFIX,
    TESTING_SUGGESTION,
    expected_test_class_name,
    is_main_source_file,
    resolve_expected_test_path,
    subject_test_requirement,
)
from validator.java.rules.testing._injection_coverage import (
    ProductionType,
    build_injected_by_index,
    is_covered_by_ancestor_it,
    production_types_by_path,
)
from validator.report import Finding


def _sources_to_check(java_files: list[Path], scope: TaskScope | None) -> list[Path]:
    if scope is not None:
        if not scope.commits:
            return []
        changed_paths = set(scope.changed_lines)
        return [path for path in java_files if str(path.resolve()) in changed_paths]

    return [path for path in java_files if not is_main_source_file(path)]


class MissingTestClassRule(TreeJavaRule):
    scope_policy = "task_changed"
    tree_file_applicability = "production"

    @property
    def check_id(self) -> str:
        return "java-testing-missing-test-class"

    def apply_tree(
        self,
        java_files: list[Path],
        scope: TaskScope | None = None,
        *,
        contexts: dict[str, JavaFileContext] | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        production_types = production_types_by_path(java_files, contexts=contexts)
        injected_by = build_injected_by_index(production_types, contexts=contexts)

        for source_path in _sources_to_check(java_files, scope):
            finding = self._check_production_source(
                source_path,
                scope,
                contexts=contexts,
                production_types=production_types,
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
        contexts: dict[str, JavaFileContext] | None = None,
        production_types: dict[Path, ProductionType] | None = None,
        injected_by: dict[Path, set[Path]] | None = None,
    ) -> Finding | None:
        class_name = source_path.stem
        requirement = subject_test_requirement(class_name)
        if requirement is None:
            return None

        context = context_for(source_path, contexts)
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
            and production_types is not None
            and injected_by is not None
            and is_covered_by_ancestor_it(
                source_path,
                production_types,
                injected_by,
                contexts=contexts,
            )
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
