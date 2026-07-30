from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from validator.java.ast.gwt import line_in_range
from validator.java.ast.variables import declaration_type_text, descendants, variable_names
from validator.java.context import JavaFileContext

EXCLUDED_INVOCATION_METHODS = frozenset(
    {
        "assertThat",
        "assertThatThrownBy",
        "catchThrowable",
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
        "catchThrowable",
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
    line: int
    has_inline_arguments: bool = False
    is_constructor: bool = False
    receiver_name: str | None = None
    inline_receiver_method_name: str | None = None
    receiver_type: str | None = None
    argument_types: tuple[str, ...] = ()


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
        actions.extend(_statement_actions(context, statement, method_node))

    if len(actions) != 1:
        return None
    return actions[0]


def _statement_actions(context: JavaFileContext, statement_node, method_node) -> list[TestAction]:
    invocations = [node for node in descendants(statement_node) if node.type == "method_invocation"]
    exception_wrappers = [
        invocation
        for invocation in invocations
        if _invocation_method_name(context, invocation) in EXCEPTION_ASSERTION_METHODS
    ]
    if exception_wrappers:
        if len(exception_wrappers) != 1:
            return []
        return _exception_actions(context, exception_wrappers[0], method_node)

    actions: list[TestAction] = []
    for invocation in _outermost_invocations(invocations):
        method_name = _invocation_method_name(context, invocation)
        if method_name is None or method_name in EXCLUDED_INVOCATION_METHODS:
            continue
        template_actions = _template_callback_actions(context, invocation, method_node)
        if template_actions is not None:
            actions.extend(template_actions)
            continue
        actions.append(_test_action(context, invocation, method_name, "normal", method_node))
    creations = [node for node in descendants(statement_node) if node.type == "object_creation_expression"]
    actions.extend(
        _constructor_action(context, creation, "normal", method_node)
        for creation in _outermost_creations(creations, invocations)
    )
    return actions


def _template_callback_actions(context: JavaFileContext, invocation, method_node) -> list[TestAction] | None:
    receiver_type = _receiver_type(context, invocation, method_node)
    if receiver_type is None or not _is_template_type(receiver_type):
        return None

    callbacks = [node for node in descendants(invocation) if node.type == "lambda_expression"]
    if not callbacks:
        return None
    if len(callbacks) != 1:
        return []

    actions = [
        _test_action(context, nested, method_name, "normal", method_node)
        for nested in _outermost_invocations(
            [node for node in descendants(callbacks[0]) if node.type == "method_invocation"]
        )
        if (method_name := _invocation_method_name(context, nested)) is not None
        and method_name not in EXCLUDED_INVOCATION_METHODS
    ]
    return actions if len(actions) == 1 else []


def _is_template_type(type_text: str) -> bool:
    simple_type = type_text.split("<", 1)[0].rsplit(".", 1)[-1]
    return simple_type.endswith("Template")


def _exception_actions(context: JavaFileContext, exception_wrapper, method_node) -> list[TestAction]:
    actions: list[TestAction] = []
    for lambda_expression in descendants(exception_wrapper):
        if lambda_expression.type != "lambda_expression":
            continue
        invocations = [node for node in descendants(lambda_expression) if node.type == "method_invocation"]
        for invocation in _outermost_invocations(invocations):
            method_name = _invocation_method_name(context, invocation)
            if method_name is None or method_name in EXCLUDED_INVOCATION_METHODS:
                continue
            actions.append(_test_action(context, invocation, method_name, "exception", method_node))
        creations = [node for node in descendants(lambda_expression) if node.type == "object_creation_expression"]
        actions.extend(
            _constructor_action(context, creation, "exception", method_node)
            for creation in _outermost_creations(creations, invocations)
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


def has_inline_arguments(invocation) -> bool:
    argument_list = next(
        (child for child in invocation.children if child.type == "argument_list"),
        None,
    )
    if argument_list is None:
        return False
    return any(
        child.is_named and child.type not in {"field_access", "identifier", "super", "this"}
        for child in argument_list.children
    )


def _test_action(
    context: JavaFileContext,
    invocation,
    method_name: str,
    path: Literal["normal", "exception"],
    method_node,
) -> TestAction:
    receiver_type = _receiver_type(context, invocation, method_node)
    argument_types = _argument_types(context, invocation, method_node)
    return TestAction(
        method_name=method_name,
        argument_count=_argument_count(invocation),
        path=path,
        line=invocation.start_point[0] + 1,
        has_inline_arguments=has_inline_arguments(invocation),
        receiver_name=_receiver_name(context, invocation),
        inline_receiver_method_name=_inline_receiver_method_name(context, invocation),
        receiver_type=receiver_type,
        argument_types=argument_types or (),
    )


def _constructor_action(
    context: JavaFileContext,
    creation,
    path: Literal["normal", "exception"],
    method_node,
) -> TestAction:
    created_type = _expression_type(context, creation, _variable_types(context, method_node))
    argument_types = _argument_types(context, creation, method_node)
    return TestAction(
        method_name=created_type or "new",
        argument_count=_argument_count(creation),
        path=path,
        line=creation.start_point[0] + 1,
        has_inline_arguments=has_inline_arguments(creation),
        is_constructor=True,
        receiver_type=created_type,
        argument_types=argument_types or (),
    )


def _receiver_name(context: JavaFileContext, invocation) -> str | None:
    argument_index = next(
        (index for index, child in enumerate(invocation.children) if child.type == "argument_list"),
        0,
    )
    if argument_index < 3 or invocation.children[0].type != "identifier":
        return None
    return context.text(invocation.children[0])


def _inline_receiver_method_name(context: JavaFileContext, invocation) -> str | None:
    argument_index = next(
        (index for index, child in enumerate(invocation.children) if child.type == "argument_list"),
        0,
    )
    if argument_index < 3 or invocation.children[0].type != "method_invocation":
        return None
    return _invocation_method_name(context, invocation.children[0])


def _receiver_type(context: JavaFileContext, invocation, method_node) -> str | None:
    receiver_name = _receiver_name(context, invocation)
    if receiver_name is None:
        return None
    return _variable_types(context, method_node).get(receiver_name)


def _argument_types(context: JavaFileContext, invocation, method_node) -> tuple[str, ...] | None:
    argument_list = next(
        (child for child in invocation.children if child.type == "argument_list"),
        None,
    )
    if argument_list is None:
        return ()
    variable_types = _variable_types(context, method_node)
    resolved = tuple(
        _expression_type(context, child, variable_types)
        for child in argument_list.children
        if child.is_named
    )
    return None if any(item is None for item in resolved) else resolved


def _variable_types(context: JavaFileContext, method_node) -> dict[str, str]:
    types: dict[str, str] = {}
    for node_type in ("field_declaration", "formal_parameter", "local_variable_declaration"):
        for declaration in context.walk(node_type):
            if node_type == "local_variable_declaration" and not _is_within(declaration, method_node):
                continue
            type_text = declaration_type_text(context, declaration)
            if not type_text:
                continue
            for name, _line in variable_names(context, declaration):
                types.setdefault(name, type_text)
    return types


def _is_within(node, ancestor) -> bool:
    current = node.parent
    while current is not None:
        if current == ancestor:
            return True
        current = current.parent
    return False


def _expression_type(context: JavaFileContext, node, variable_types: dict[str, str]) -> str | None:
    if node.type == "identifier":
        return variable_types.get(context.text(node))
    if node.type == "string_literal":
        return "String"
    if node.type == "character_literal":
        return "char"
    if node.type == "decimal_integer_literal":
        return "int"
    if node.type == "decimal_floating_point_literal":
        return "double"
    if node.type in {"true", "false"}:
        return "boolean"
    if node.type == "object_creation_expression":
        return next(
            (
                context.text(child)
                for child in node.children
                if child.type in {"type_identifier", "generic_type"}
            ),
            None,
        )
    if node.type == "cast_expression":
        return next(
            (
                context.text(child)
                for child in node.children
                if child.type in {"type_identifier", "generic_type"}
            ),
            None,
        )
    return None


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


def _outermost_creations(creations: list, invocations: list) -> list:
    return [
        creation
        for creation in creations
        if not any(_is_nested_invocation(invocation, creation) for invocation in invocations)
        if not any(
            _is_nested_invocation(other, creation)
            for other in creations
            if other is not creation
        )
    ]


def _is_nested_invocation(outer, inner) -> bool:
    return outer.start_byte <= inner.start_byte and outer.end_byte > inner.end_byte
