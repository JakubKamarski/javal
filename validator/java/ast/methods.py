from __future__ import annotations

from validator.java.ast.modifiers import (
    enclosing_class_declaration,
    enclosing_record_declaration,
    node_has_annotation,
)
from validator.java.ast.models import MethodDeclaration
from validator.java.context import JavaFileContext


def _record_component_names(context: JavaFileContext, record_node) -> set[str]:
    names: set[str] = set()
    formal_parameters = next(
        (child for child in record_node.children if child.type == "formal_parameters"),
        None,
    )
    if formal_parameters is None:
        return names

    for parameter in formal_parameters.children:
        if parameter.type != "formal_parameter":
            continue
        identifier = next((child for child in parameter.children if child.type == "identifier"), None)
        if identifier is not None:
            names.add(context.text(identifier))
    return names


def _is_record_accessor_method(context: JavaFileContext, method_node) -> bool:
    record_node = enclosing_record_declaration(method_node)
    if record_node is None:
        return False

    identifier = _method_name_identifier(method_node)
    if identifier is None:
        return False

    return context.text(identifier) in _record_component_names(context, record_node)


def _is_configuration_bean_method(context: JavaFileContext, method_node) -> bool:
    class_node = enclosing_class_declaration(method_node)
    if class_node is None:
        return False
    return node_has_annotation(context, class_node, "Configuration") and node_has_annotation(
        context, method_node, "Bean"
    )


def _method_name_identifier(method_node):
    children = method_node.children
    for index, child in enumerate(children):
        if child.type != "identifier":
            continue
        if index + 1 < len(children) and children[index + 1].type == "formal_parameters":
            return child
    return next((child for child in children if child.type == "identifier"), None)


def iter_method_declarations(context: JavaFileContext):
    for node in context.walk("method_declaration"):
        identifier = _method_name_identifier(node)
        if identifier is None:
            continue
        yield MethodDeclaration(
            name=context.text(identifier),
            line=node.start_point[0] + 1,
            node=node,
            is_configuration_bean=_is_configuration_bean_method(context, node),
            is_override=node_has_annotation(context, node, "Override"),
            is_test=node_has_annotation(context, node, "Test", "ParameterizedTest"),
            is_lifecycle=node_has_annotation(
                context,
                node,
                "BeforeEach",
                "AfterEach",
                "BeforeAll",
                "AfterAll",
            ),
            is_record_accessor=_is_record_accessor_method(context, node),
        )
