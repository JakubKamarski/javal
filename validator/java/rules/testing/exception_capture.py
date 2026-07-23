from __future__ import annotations

from validator.java.ast import iter_method_declarations, parse_gwt_section_line_ranges
from validator.java.ast.gwt import line_in_range
from validator.java.ast.test_actions import EXCEPTION_ASSERTION_METHODS, _invocation_method_name
from validator.java.ast.variables import declaration_type_text, descendants, variable_names
from validator.java.context import JavaFileContext
from validator.java.rules.base import JavaRule, RuleViolation
from validator.java.rules.testing._support import TESTING_SUGGESTION


class ExceptionCaptureRule(JavaRule):
    file_applicability = "test"

    @property
    def check_id(self) -> str:
        return "java-testing-exception-capture"

    def apply(self, context: JavaFileContext) -> list[RuleViolation]:
        violations: list[RuleViolation] = []

        for method in iter_method_declarations(context):
            if not method.is_test or not _has_exception_assertion(context, method.node):
                continue

            sections = parse_gwt_section_line_ranges(context, method.node)
            if _has_exception_capture(context, method.node, sections.get("WHEN")):
                continue

            violations.append(
                RuleViolation(
                    summary=(
                        f"Test method '{method.name}' must capture Throwable exception with "
                        "catchThrowable in // WHEN before asserting it in // THEN."
                    ),
                    line=_violation_line(context, method.node),
                    suggestion=(
                        "Use `Throwable exception = catchThrowable(...)` in // WHEN and assert "
                        "the exception in // THEN."
                    ),
                )
            )

        return violations


def _has_exception_assertion(context: JavaFileContext, method_node) -> bool:
    return any(
        _invocation_method_name(context, invocation) in EXCEPTION_ASSERTION_METHODS
        for invocation in descendants(method_node)
        if invocation.type == "method_invocation"
    )


def _has_exception_capture(context: JavaFileContext, method_node, when_range: tuple[int, int] | None) -> bool:
    if when_range is None:
        return False

    for declaration in context.walk("local_variable_declaration"):
        if not _is_within(declaration, method_node):
            continue
        if not line_in_range(declaration.start_point[0] + 1, when_range):
            continue
        if declaration_type_text(context, declaration) != "Throwable":
            continue
        if "exception" not in {name for name, _line in variable_names(context, declaration)}:
            continue
        if any(
            _invocation_method_name(context, invocation) == "catchThrowable"
            for invocation in descendants(declaration)
            if invocation.type == "method_invocation"
        ):
            return True
    return False


def _violation_line(context: JavaFileContext, method_node) -> int:
    for declaration in context.walk("local_variable_declaration"):
        if not _is_within(declaration, method_node):
            continue
        if declaration_type_text(context, declaration).endswith("ThrowingCallable"):
            return declaration.start_point[0] + 1

    return method_node.start_point[0] + 1


def _is_within(node, ancestor) -> bool:
    return node.start_byte >= ancestor.start_byte and node.end_byte <= ancestor.end_byte
