from __future__ import annotations

from validator.java.ast import (
    iter_method_declarations,
    line_in_range,
    parse_gwt_section_line_ranges,
)
from validator.java.ast.variables import descendants
from validator.java.context import JavaFileContext
from validator.java.rules.base import JavaRule, RuleViolation
from validator.java.rules.testing._support import TESTING_SUGGESTION

EXCLUDED_INVOCATION_METHODS = frozenset(
    {
        "assertThat",
        "assertThatThrownBy",
        "assertEquals",
        "assertTrue",
        "assertFalse",
        "assertNull",
        "assertNotNull",
        "assertThrows",
        "assertDoesNotThrow",
        "verify",
        "when",
        "mock",
        "spy",
        "doReturn",
        "doThrow",
        "doAnswer",
        "isEqualTo",
        "isNotEmpty",
        "isEmpty",
        "containsExactly",
        "containsExactlyInAnyOrder",
        "extracting",
        "tuple",
        "hasSize",
        "contains",
        "startsWith",
        "endsWith",
        "of",
        "empty",
    }
)

STATEMENT_TYPES = frozenset(
    {
        "local_variable_declaration",
        "expression_statement",
    }
)


def _node_within(node, ancestor) -> bool:
    return node.start_byte >= ancestor.start_byte and node.end_byte <= ancestor.end_byte


def _invocation_method_name(context: JavaFileContext, node) -> str | None:
    if node.type != "method_invocation":
        return None

    children = node.children
    for index, child in enumerate(children):
        if child.type != "argument_list" or index == 0:
            continue
        previous = children[index - 1]
        if previous.type == "identifier":
            return context.text(previous)
    return None


def _is_nested_invocation(outer, inner) -> bool:
    return outer.start_byte < inner.start_byte and outer.end_byte > inner.end_byte


def _outermost_invocations(statement_node) -> list:
    invocations = [node for node in descendants(statement_node) if node.type == "method_invocation"]
    return [
        invocation
        for invocation in invocations
        if not any(
            _is_nested_invocation(other, invocation)
            for other in invocations
            if other is not invocation
        )
    ]


def _method_under_test_from_when(context: JavaFileContext, method_node, when_range: tuple[int, int]) -> str | None:
    block = next((child for child in method_node.children if child.type == "block"), None)
    if block is None:
        return None

    for statement in block.children:
        if statement.type not in STATEMENT_TYPES:
            continue
        if not line_in_range(statement.start_point[0] + 1, when_range):
            continue

        for invocation in _outermost_invocations(statement):
            method_name = _invocation_method_name(context, invocation)
            if method_name is None or method_name in EXCLUDED_INVOCATION_METHODS:
                continue
            return method_name

    return None


class TestMethodPrefixRule(JavaRule):
    file_applicability = "test"

    @property
    def check_id(self) -> str:
        return "java-testing-test-method-prefix"

    def apply(self, context: JavaFileContext) -> list[RuleViolation]:
        violations: list[RuleViolation] = []

        for method in iter_method_declarations(context):
            if not method.is_test:
                continue

            when_range = parse_gwt_section_line_ranges(context, method.node).get("WHEN")
            if when_range is None:
                continue

            method_under_test = _method_under_test_from_when(context, method.node, when_range)
            if method_under_test is None:
                continue

            if method.name.startswith(method_under_test):
                continue

            violations.append(
                RuleViolation(
                    summary=(
                        f"Test method '{method.name}' must start with the tested method "
                        f"'{method_under_test}'."
                    ),
                    line=method.line,
                    suggestion=TESTING_SUGGESTION,
                )
            )

        return violations
