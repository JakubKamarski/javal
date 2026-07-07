from __future__ import annotations

import re
from dataclasses import dataclass

from validator.java.context import JavaFileContext


@dataclass(frozen=True)
class MethodDeclaration:
    name: str
    line: int
    node: object


@dataclass(frozen=True)
class VariableDeclaration:
    name: str
    line: int
    is_constant: bool
    node: object


@dataclass(frozen=True)
class ImportDeclaration:
    symbol: str
    line: int
    text: str
    node: object


def iter_method_declarations(context: JavaFileContext):
    for node in context.walk("method_declaration"):
        identifier = next((child for child in node.children if child.type == "identifier"), None)
        if identifier is None:
            continue
        yield MethodDeclaration(
            name=context.text(identifier),
            line=node.start_point[0] + 1,
            node=node,
        )


def _variable_names(context: JavaFileContext, node) -> list[tuple[str, int]]:
    names: list[tuple[str, int]] = []

    if node.type == "formal_parameter":
        identifier = next((child for child in node.children if child.type == "identifier"), None)
        if identifier is not None:
            names.append((context.text(identifier), identifier.start_point[0] + 1))
        return names

    for declarator in _descendants(node):
        if declarator.type != "variable_declarator":
            continue
        identifier = next((child for child in declarator.children if child.type == "identifier"), None)
        if identifier is not None:
            names.append((context.text(identifier), identifier.start_point[0] + 1))
    return names


def _descendants(node):
    stack = list(node.children)
    seen = set()
    while stack:
        current = stack.pop()
        if id(current) in seen:
            continue
        seen.add(id(current))
        yield current
        stack.extend(current.children)


def _is_constant_field(context: JavaFileContext, node) -> bool:
    text = context.text(node)
    return "static" in text and "final" in text


def iter_variable_declarations(context: JavaFileContext):
    for node_type, constant_only in (
        ("field_declaration", True),
        ("local_variable_declaration", False),
        ("formal_parameter", False),
    ):
        for node in context.walk(node_type):
            is_constant = constant_only and _is_constant_field(context, node)
            for name, line in _variable_names(context, node):
                yield VariableDeclaration(
                    name=name,
                    line=line,
                    is_constant=is_constant,
                    node=node,
                )


def _imported_symbol(context: JavaFileContext, import_node) -> str | None:
    if any(child.type == "asterisk" for child in import_node.children):
        return None

    scoped = next((child for child in import_node.children if child.type == "scoped_identifier"), None)
    if scoped is None:
        return None

    parts = context.text(scoped).split(".")
    return parts[-1] if parts else None


def iter_import_declarations(context: JavaFileContext):
    for import_node in context.walk("import_declaration"):
        symbol = _imported_symbol(context, import_node)
        if symbol is None:
            continue
        yield ImportDeclaration(
            symbol=symbol,
            line=import_node.start_point[0] + 1,
            text=context.text(import_node).strip(),
            node=import_node,
        )


def collect_identifier_usages(context: JavaFileContext) -> set[str]:
    import_ranges = [
        (node.start_byte, node.end_byte) for node in context.walk("import_declaration")
    ]

    def in_import(byte_offset: int) -> bool:
        return any(start <= byte_offset < end for start, end in import_ranges)

    usages: set[str] = set()
    for node_type in ("identifier", "type_identifier"):
        for node in context.walk(node_type):
            if in_import(node.start_byte):
                continue
            usages.add(context.text(node))

    for node in context.walk("marker_annotation"):
        match = re.match(r"@([A-Za-z_][\w$]*)", context.text(node))
        if match:
            usages.add(match.group(1))

    return usages
