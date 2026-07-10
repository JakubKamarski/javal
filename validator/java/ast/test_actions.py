from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from validator.java.ast.gwt import line_in_range
from validator.java.ast.variables import descendants
from validator.java.context import JavaFileContext

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
        "assertThrowsExactly",
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

EXCEPTION_ASSERTION_METHODS = frozenset(
    {
        "assertThrows",
        "assertThrowsExactly",
        "assertThatThrownBy",
    }
)

STATEMENT_TYPES = frozenset(
    {
        "local_variable_declaration",
        "expression_statement",
    }
)


@dataclass(frozen=True)
class TestAction:
    method_name: str
    argument_count: int
    path: Literal["normal", "exception"]


def action_from_when(
    context: JavaFileContext,
    method_node,
    when_range: tuple[int, int],
) -> TestAction | None:
    block = next((child for child in method_node.children if child.type == "block"), None)
    if block is None:
        return None

    actions: list[TestAction] = []
    for statement in block.children:
        if statement.type not in STATEMENT_TYPES:
            continue
        if not line_in_range(statement.start_point[0] + 1, when_range):
            continue
        actions.extend(_statement_actions(context, statement))

    if len(actions) != 1:
        return None
    return actions[0]


def _statement_actions(context: JavaFileContext, statement_node) -> list[TestAction]:
    invocations = [node for node in descendants(statement_node) if node.type == "method_invocation"]
    exception_wrappers = [
        invocation
        for invocation in invocations
        if _invocation_method_name(context, invocation) in EXCEPTION_ASSERTION_METHODS
    ]
    if exception_wrappers:
        if len(exception_wrappers) != 1:
            return []
        return _exception_actions(context, exception_wrappers[0])

    actions: list[TestAction] = []
    for invocation in _outermost_invocations(invocations):
        method_name = _invocation_method_name(context, invocation)
        if method_name is None or method_name in EXCLUDED_INVOCATION_METHODS:
            continue
        actions.append(
            TestAction(
                method_name=method_name,
                argument_count=_argument_count(invocation),
                path="normal",
            )
        )
    return actions


def _exception_actions(context: JavaFileContext, exception_wrapper) -> list[TestAction]:
    actions: list[TestAction] = []
    for lambda_expression in descendants(exception_wrapper):
        if lambda_expression.type != "lambda_expression":
            continue
        for invocation in _outermost_invocations(
            [node for node in descendants(lambda_expression) if node.type == "method_invocation"]
        ):
            method_name = _invocation_method_name(context, invocation)
            if method_name is None or method_name in EXCLUDED_INVOCATION_METHODS:
                continue
            actions.append(
                TestAction(
                    method_name=method_name,
                    argument_count=_argument_count(invocation),
                    path="exception",
                )
            )
    return actions


def _invocation_method_name(context: JavaFileContext, node) -> str | None:
    children = node.children
    for index, child in enumerate(children):
        if child.type != "argument_list" or index == 0:
            continue
        previous = children[index - 1]
        if previous.type == "identifier":
            return context.text(previous)
    return None


def _argument_count(invocation) -> int:
    argument_list = next(
        (child for child in invocation.children if child.type == "argument_list"),
        None,
    )
    if argument_list is None:
        return 0
    return sum(child.is_named for child in argument_list.children)


def _outermost_invocations(invocations: list) -> list:
    return [
        invocation
        for invocation in invocations
        if not any(
            _is_nested_invocation(other, invocation)
            for other in invocations
            if other is not invocation
        )
    ]


def _is_nested_invocation(outer, inner) -> bool:
    return outer.start_byte < inner.start_byte and outer.end_byte > inner.end_byte
