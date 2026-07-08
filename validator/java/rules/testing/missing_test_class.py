from __future__ import annotations

from pathlib import Path

from validator.git_scope import TaskScope
from validator.java.context import JavaFileContext
from validator.java.rules.base import TreeJavaRule
from validator.java.rules.testing._support import (
    TESTING_SUGGESTION,
    expected_test_class_name,
    is_main_source_file,
    is_test_source_file,
    resolve_expected_test_path,
    subject_test_requirement,
)
from validator.report import Finding


def _node_has_modifier(context: JavaFileContext, node, modifier: str) -> bool:
    modifiers = next((child for child in node.children if child.type == "modifiers"), None)
    if modifiers is None:
        return False
    return modifier in context.text(modifiers).split()


def _top_level_type_name(context: JavaFileContext, node_type: str, type_name: str) -> object | None:
    for node in context.walk(node_type):
        identifier = next((child for child in node.children if child.type == "identifier"), None)
        if identifier is not None and context.text(identifier) == type_name:
            return node
    return None


def _is_public_top_level_type(context: JavaFileContext, type_name: str) -> bool:
    for node_type in ("class_declaration", "interface_declaration"):
        node = _top_level_type_name(context, node_type, type_name)
        if node is not None:
            return _node_has_modifier(context, node, "public")
    return False


def _is_abstract_top_level_type(context: JavaFileContext, type_name: str) -> bool:
    node = _top_level_type_name(context, "class_declaration", type_name)
    if node is None:
        return False
    return _node_has_modifier(context, node, "abstract")


def _has_query_annotation(context: JavaFileContext) -> bool:
    for node in context.walk("marker_annotation", "annotation"):
        text = context.text(node)
        if text == "@Query" or text.startswith("@Query("):
            return True
    return False


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
    @property
    def check_id(self) -> str:
        return "java-testing-missing-test-class"

    def apply_tree(
        self,
        java_files: list[Path],
        scope: TaskScope | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []

        for source_path in _production_sources_to_check(java_files, scope):
            finding = self._check_production_source(source_path)
            if finding is not None:
                findings.append(finding)

        return findings

    def _check_production_source(self, source_path: Path) -> Finding | None:
        class_name = source_path.stem
        requirement = subject_test_requirement(class_name)
        if requirement is None:
            return None

        context = JavaFileContext.from_path(source_path)
        if _is_abstract_top_level_type(context, class_name):
            return None
        if requirement.requires_public_class and not _is_public_top_level_type(context, class_name):
            return None
        if requirement.requires_query_annotation and not _has_query_annotation(context):
            return None

        test_class_name = expected_test_class_name(class_name, requirement)
        expected_test_path = resolve_expected_test_path(source_path, test_class_name)
        if expected_test_path.is_file():
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
