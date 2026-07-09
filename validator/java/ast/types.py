from __future__ import annotations

import re

from validator.java.context import JavaFileContext

_STANDARD_TYPE_PARAMETER_NAME = re.compile(r"^[A-Z]$")
_BARE_NOSONAR_LINE = re.compile(r"//\s*NOSONAR\s*$")
_DESCRIPTIVE_NOSONAR_LINE = re.compile(r"NOSONAR\s*:")
_GENERIC_TYPE_DECLARATIONS = (
    "class_declaration",
    "interface_declaration",
    "record_declaration",
)
_BODY_NODE_TYPES = frozenset({"class_body", "interface_body"})


def is_standard_type_parameter_name(name: str) -> bool:
    return bool(_STANDARD_TYPE_PARAMETER_NAME.match(name))


def is_bare_nosonar_line(line: str) -> bool:
    return bool(_BARE_NOSONAR_LINE.search(line))


def is_descriptive_nosonar_line(line: str) -> bool:
    return "NOSONAR" in line and bool(_DESCRIPTIVE_NOSONAR_LINE.search(line))


def iter_type_parameter_names(context: JavaFileContext, type_parameters_node) -> list[str]:
    names: list[str] = []
    for child in type_parameters_node.children:
        if child.type != "type_parameter":
            continue
        identifier = next(
            (grandchild for grandchild in child.children if grandchild.type == "type_identifier"),
            None,
        )
        if identifier is not None:
            names.append(context.text(identifier))
    return names


def declaration_header_line_numbers(node) -> set[int]:
    body = next((child for child in node.children if child.type in _BODY_NODE_TYPES), None)
    start_line = node.start_point[0] + 1
    if body is None:
        return {start_line}
    end_line = body.start_point[0] + 1
    return set(range(start_line, end_line + 1))


def method_signature_line_numbers(node) -> set[int]:
    formal_parameters = next(
        (child for child in node.children if child.type == "formal_parameters"),
        None,
    )
    start_line = node.start_point[0] + 1
    if formal_parameters is None:
        return {start_line}
    end_line = formal_parameters.start_point[0] + 1
    return set(range(start_line, end_line + 1))


def declaration_simple_name(context: JavaFileContext, node) -> str:
    identifier = next((child for child in node.children if child.type == "identifier"), None)
    return context.text(identifier) if identifier is not None else "<unknown>"


def _method_name_identifier(method_node):
    children = method_node.children
    for index, child in enumerate(children):
        if child.type != "identifier":
            continue
        if index + 1 < len(children) and children[index + 1].type == "formal_parameters":
            return child
    return next((child for child in children if child.type == "identifier"), None)


def method_simple_name(context: JavaFileContext, node) -> str:
    identifier = _method_name_identifier(node)
    return context.text(identifier) if identifier is not None else "<unknown>"


def iter_generic_type_declarations(context: JavaFileContext):
    for node_type in _GENERIC_TYPE_DECLARATIONS:
        for node in context.walk(node_type):
            type_parameters = next(
                (child for child in node.children if child.type == "type_parameters"),
                None,
            )
            if type_parameters is None:
                continue
            names = iter_type_parameter_names(context, type_parameters)
            if not names:
                continue
            yield node, names


def iter_generic_method_declarations(context: JavaFileContext):
    for node in context.walk("method_declaration"):
        type_parameters = next(
            (child for child in node.children if child.type == "type_parameters"),
            None,
        )
        if type_parameters is None:
            continue
        names = iter_type_parameter_names(context, type_parameters)
        if not names:
            continue
        yield node, names


def lines_have_nosonar(context: JavaFileContext, line_numbers: set[int]) -> bool:
    lines = context.source.splitlines()
    for line_number in line_numbers:
        if line_number < 1 or line_number > len(lines):
            continue
        if "NOSONAR" in lines[line_number - 1]:
            return True
    return False


def header_has_nosonar(context: JavaFileContext, node) -> bool:
    return lines_have_nosonar(context, declaration_header_line_numbers(node))
