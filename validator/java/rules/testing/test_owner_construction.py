from __future__ import annotations

from validator.java.ast import (
    iter_method_declarations,
    line_in_range,
    node_has_modifier,
    parse_gwt_section_line_ranges,
)
from validator.java.ast.test_actions import action_from_when
from validator.java.ast.modifiers import annotation_simple_name, enclosing_class_declaration
from validator.java.ast.variables import variable_names
from validator.java.context import JavaFileContext
from validator.java.rules.base import JavaRule, RuleViolation
from validator.java.rules.testing._support import TESTING_SUGGESTION


class TestOwnerConstructionRule(JavaRule):
    file_applicability = "test"

    @property
    def check_id(self) -> str:
        return "java-testing-test-owner-construction"

    def apply(self, context: JavaFileContext) -> list[RuleViolation]:
        violations: list[RuleViolation] = []

        for method in iter_method_declarations(context):
            if not method.is_test:
                continue

            sections = parse_gwt_section_line_ranges(context, method.node)
            when_range = sections.get("WHEN")
            if when_range is None:
                continue

            action = action_from_when(context, method.node, when_range)
            if action is None or action.receiver_name is None or action.receiver_type is None:
                continue
            if self._is_initialized_in_given(context, method.node, action.receiver_name, sections.get("GIVEN")):
                continue
            if self._is_directly_initialized_final_field(
                context,
                method.node,
                action.receiver_name,
            ):
                continue
            if self._is_framework_managed_integration_test_field(
                context,
                method.node,
                action.receiver_name,
            ):
                continue

            violations.append(
                RuleViolation(
                    summary=(
                        f"Test method '{method.name}' invokes '{action.receiver_name}.{action.method_name}' "
                        "without initializing its owner in // GIVEN or as a directly initialized final field."
                    ),
                    line=action.line,
                    suggestion=TESTING_SUGGESTION,
                )
            )

        return violations

    def _is_initialized_in_given(
        self,
        context: JavaFileContext,
        method_node,
        receiver_name: str,
        given_range: tuple[int, int] | None,
    ) -> bool:
        if given_range is None:
            return False

        for declaration in context.walk("local_variable_declaration"):
            if not self._is_within(declaration, method_node):
                continue
            if not line_in_range(declaration.start_point[0] + 1, given_range):
                continue
            if receiver_name not in {name for name, _line in variable_names(context, declaration)}:
                continue
            if "=" in context.text(declaration):
                return True
        return False

    def _is_framework_managed_integration_test_field(
        self,
        context: JavaFileContext,
        method_node,
        receiver_name: str,
    ) -> bool:
        test_class = enclosing_class_declaration(method_node)
        if test_class is None or not _is_integration_test(context, test_class):
            return False

        for field in context.walk("field_declaration"):
            if enclosing_class_declaration(field) != test_class:
                continue
            if node_has_modifier(context, field, "static"):
                continue
            if receiver_name not in {name for name, _line in variable_names(context, field)}:
                continue
            if _has_annotation(field):
                return True
        return False

    def _is_directly_initialized_final_field(
        self,
        context: JavaFileContext,
        method_node,
        receiver_name: str,
    ) -> bool:
        test_class = enclosing_class_declaration(method_node)
        if test_class is None:
            return False

        for field in context.walk("field_declaration"):
            if enclosing_class_declaration(field) != test_class:
                continue
            if not node_has_modifier(context, field, "final"):
                continue
            if receiver_name not in {name for name, _line in variable_names(context, field)}:
                continue
            if "=" in context.text(field):
                return True
        return False

    @staticmethod
    def _is_within(node, ancestor) -> bool:
        current = node.parent
        while current is not None:
            if current == ancestor:
                return True
            current = current.parent
        return False


def _is_integration_test(context: JavaFileContext, test_class) -> bool:
    class_name = next((context.text(child) for child in test_class.children if child.type == "identifier"), "")
    if class_name.endswith("IT"):
        return True

    modifiers = next((child for child in test_class.children if child.type == "modifiers"), None)
    if modifiers is None:
        return False
    return any(
        (annotation_simple_name(context, child) or "").endswith("IT")
        for child in modifiers.children
        if child.type in ("marker_annotation", "annotation")
    )


def _has_annotation(field) -> bool:
    modifiers = next((child for child in field.children if child.type == "modifiers"), None)
    return modifiers is not None and any(
        child.type in ("marker_annotation", "annotation") for child in modifiers.children
    )
