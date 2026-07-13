from __future__ import annotations

from validator.java.ast.modifiers import (
    enclosing_class_declaration,
    enclosing_record_declaration,
    annotation_simple_name,
    node_has_annotation,
    node_has_modifier,
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
    return node_has_annotation(context, method_node, "Bean")


def _enclosing_class_name(context: JavaFileContext, method_node) -> str | None:
    class_node = enclosing_class_declaration(method_node)
    if class_node is None:
        return None
    identifier = next((child for child in class_node.children if child.type == "identifier"), None)
    return context.text(identifier) if identifier is not None else None


def _is_static_factory_method(context: JavaFileContext, method_node) -> bool:
    if not node_has_modifier(context, method_node, "static"):
        return False
    class_name = _enclosing_class_name(context, method_node)
    if class_name is None:
        return False
    return_type = next(
        (
            context.text(child)
            for child in method_node.children
            if child.type in {"type_identifier", "generic_type", "scoped_type_identifier"}
        ),
        "",
    )
    return return_type == class_name or return_type.startswith(f"{class_name}<")


def method_source_provider_names(context: JavaFileContext) -> set[str]:
    names: set[str] = set()
    for annotation in context.walk("annotation"):
        if annotation_simple_name(context, annotation) != "MethodSource":
            continue
        for literal in _descendants(annotation):
            if literal.type == "string_literal":
                names.add(context.text(literal).strip('"'))
    return names


def _descendants(node):
    stack = list(node.children)
    while stack:
        current = stack.pop()
        yield current
        stack.extend(current.children)


def _method_name_identifier(method_node):
    children = method_node.children
    for index, child in enumerate(children):
        if child.type != "identifier":
            continue
        if index + 1 < len(children) and children[index + 1].type == "formal_parameters":
            return child
    return next((child for child in children if child.type == "identifier"), None)


def iter_method_declarations(context: JavaFileContext):
    method_source_names = method_source_provider_names(context)
    for node in context.walk("method_declaration"):
        identifier = _method_name_identifier(node)
        if identifier is None:
            continue
        yield MethodDeclaration(
            name=context.text(identifier),
            line=node.start_point[0] + 1,
            node=node,
            is_configuration_bean=_is_configuration_bean_method(context, node),
            is_static_factory=_is_static_factory_method(context, node),
            is_method_source_provider=context.text(identifier) in method_source_names,
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
