from __future__ import annotations

from validator.java.ast.models import (
    LocalVariableDeclaration,
    VarDeclaration,
    VariableDeclaration,
)
from validator.java.context import JavaFileContext


def descendants(node):
    stack = list(node.children)
    seen = set()
    while stack:
        current = stack.pop()
        if id(current) in seen:
            continue
        seen.add(id(current))
        yield current
        stack.extend(current.children)


def variable_names(context: JavaFileContext, node) -> list[tuple[str, int]]:
    names: list[tuple[str, int]] = []

    if node.type == "formal_parameter":
        identifier = next((child for child in node.children if child.type == "identifier"), None)
        if identifier is not None:
            names.append((context.text(identifier), identifier.start_point[0] + 1))
        return names

    for declarator in descendants(node):
        if declarator.type != "variable_declarator":
            continue
        identifier = next((child for child in declarator.children if child.type == "identifier"), None)
        if identifier is not None:
            names.append((context.text(identifier), identifier.start_point[0] + 1))
    return names


def is_constant_field(context: JavaFileContext, node) -> bool:
    modifiers = next((child for child in node.children if child.type == "modifiers"), None)
    if modifiers is None:
        return False
    modifier_names = context.text(modifiers).split()
    return "static" in modifier_names and "final" in modifier_names


def uses_var_type(context: JavaFileContext, node) -> bool:
    for child in node.children:
        if child.type == "type_identifier" and context.text(child) == "var":
            return True
    return False


def identifier_name_and_line(context: JavaFileContext, node) -> tuple[str, int] | None:
    identifier = next((child for child in node.children if child.type == "identifier"), None)
    if identifier is None:
        return None
    return context.text(identifier), identifier.start_point[0] + 1


def declaration_type_text(context: JavaFileContext, node) -> str:
    for child in node.children:
        if child.type in (
            "type_identifier",
            "generic_type",
            "scoped_type_identifier",
            "array_type",
            "integral_type",
            "floating_point_type",
            "boolean_type",
        ):
            return context.text(child)
    return ""


def is_optional_type(type_text: str) -> bool:
    normalized = type_text.strip()
    if not normalized:
        return False
    return normalized == "Optional" or normalized.startswith("Optional<") or normalized.endswith(".Optional<")


def iter_var_declarations(context: JavaFileContext):
    for node in context.walk("local_variable_declaration"):
        if not uses_var_type(context, node):
            continue
        for name, line in variable_names(context, node):
            yield VarDeclaration(name=name, line=line)

    for node_type in ("resource", "enhanced_for_statement"):
        for node in context.walk(node_type):
            if not uses_var_type(context, node):
                continue
            name_and_line = identifier_name_and_line(context, node)
            if name_and_line is None:
                continue
            name, line = name_and_line
            yield VarDeclaration(name=name, line=line)


def iter_local_variable_declarations(context: JavaFileContext):
    for node in context.walk("local_variable_declaration"):
        type_text = declaration_type_text(context, node)
        for name, line in variable_names(context, node):
            yield LocalVariableDeclaration(
                name=name,
                line=line,
                node=node,
                type_text=type_text,
            )


def iter_variable_declarations(context: JavaFileContext):
    for node_type, constant_only in (
        ("field_declaration", True),
        ("local_variable_declaration", False),
        ("formal_parameter", False),
    ):
        for node in context.walk(node_type):
            is_constant = constant_only and is_constant_field(context, node)
            for name, line in variable_names(context, node):
                yield VariableDeclaration(
                    name=name,
                    line=line,
                    is_constant=is_constant,
                    node=node,
                )
