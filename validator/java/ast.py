from __future__ import annotations

import re
from dataclasses import dataclass

from validator.java.context import JavaFileContext


@dataclass(frozen=True)
class MethodDeclaration:
    name: str
    line: int
    node: object
    is_configuration_bean: bool = False
    is_override: bool = False
    is_test: bool = False
    is_record_accessor: bool = False


@dataclass(frozen=True)
class VariableDeclaration:
    name: str
    line: int
    is_constant: bool
    node: object


@dataclass(frozen=True)
class LocalVariableDeclaration:
    name: str
    line: int
    node: object
    type_text: str


@dataclass(frozen=True)
class VarDeclaration:
    name: str
    line: int


@dataclass(frozen=True)
class ImportDeclaration:
    symbol: str
    line: int
    text: str
    node: object


def _annotation_simple_name(context: JavaFileContext, annotation_node) -> str | None:
    for child in annotation_node.children:
        if child.type == "identifier":
            return context.text(child)
        if child.type == "scoped_identifier":
            return context.text(child).rsplit(".", 1)[-1]
    return None


def _node_has_annotation(context: JavaFileContext, node, *simple_names: str) -> bool:
    modifiers = next((child for child in node.children if child.type == "modifiers"), None)
    if modifiers is None:
        return False

    wanted = set(simple_names)
    for child in modifiers.children:
        if child.type not in ("marker_annotation", "annotation"):
            continue
        name = _annotation_simple_name(context, child)
        if name in wanted:
            return True
    return False


def _enclosing_class_declaration(node):
    current = node.parent
    while current is not None:
        if current.type == "class_declaration":
            return current
        current = current.parent
    return None


def _enclosing_record_declaration(node):
    current = node.parent
    while current is not None:
        if current.type == "record_declaration":
            return current
        current = current.parent
    return None


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
    record_node = _enclosing_record_declaration(method_node)
    if record_node is None:
        return False

    identifier = next((child for child in method_node.children if child.type == "identifier"), None)
    if identifier is None:
        return False

    return context.text(identifier) in _record_component_names(context, record_node)


def _is_configuration_bean_method(context: JavaFileContext, method_node) -> bool:
    class_node = _enclosing_class_declaration(method_node)
    if class_node is None:
        return False
    return _node_has_annotation(context, class_node, "Configuration") and _node_has_annotation(
        context, method_node, "Bean"
    )


def iter_method_declarations(context: JavaFileContext):
    for node in context.walk("method_declaration"):
        identifier = next((child for child in node.children if child.type == "identifier"), None)
        if identifier is None:
            continue
        yield MethodDeclaration(
            name=context.text(identifier),
            line=node.start_point[0] + 1,
            node=node,
            is_configuration_bean=_is_configuration_bean_method(context, node),
            is_override=_node_has_annotation(context, node, "Override"),
            is_test=_node_has_annotation(context, node, "Test", "ParameterizedTest"),
            is_record_accessor=_is_record_accessor_method(context, node),
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


def _uses_var_type(context: JavaFileContext, node) -> bool:
    for child in node.children:
        if child.type == "type_identifier" and context.text(child) == "var":
            return True
    return False


def _identifier_name_and_line(context: JavaFileContext, node) -> tuple[str, int] | None:
    identifier = next((child for child in node.children if child.type == "identifier"), None)
    if identifier is None:
        return None
    return context.text(identifier), identifier.start_point[0] + 1


def iter_var_declarations(context: JavaFileContext):
    for node in context.walk("local_variable_declaration"):
        if not _uses_var_type(context, node):
            continue
        for name, line in _variable_names(context, node):
            yield VarDeclaration(name=name, line=line)

    for node_type in ("resource", "enhanced_for_statement"):
        for node in context.walk(node_type):
            if not _uses_var_type(context, node):
                continue
            name_and_line = _identifier_name_and_line(context, node)
            if name_and_line is None:
                continue
            name, line = name_and_line
            yield VarDeclaration(name=name, line=line)


def _declaration_type_text(context: JavaFileContext, node) -> str:
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


def iter_local_variable_declarations(context: JavaFileContext):
    for node in context.walk("local_variable_declaration"):
        type_text = _declaration_type_text(context, node)
        for name, line in _variable_names(context, node):
            yield LocalVariableDeclaration(
                name=name,
                line=line,
                node=node,
                type_text=type_text,
            )


def parse_gwt_section_line_ranges(context: JavaFileContext, method_node) -> dict[str, tuple[int, int]]:
    block = next((child for child in method_node.children if child.type == "block"), None)
    if block is None:
        return {}

    markers: list[tuple[str, int]] = []
    for node in block.children:
        if node.type != "line_comment":
            continue
        label = context.text(node).strip().removeprefix("//").strip().upper()
        if label in {"GIVEN", "WHEN", "THEN"}:
            markers.append((label, node.start_point[0] + 1))

    if not markers:
        return {}

    method_end_line = method_node.end_point[0] + 1
    sections: dict[str, tuple[int, int]] = {}
    for index, (label, marker_line) in enumerate(markers):
        start_line = marker_line + 1
        if index + 1 < len(markers):
            end_line = markers[index + 1][1] - 1
        else:
            end_line = method_end_line - 1
        sections[label] = (start_line, end_line)

    return sections


def line_in_range(line: int, line_range: tuple[int, int]) -> bool:
    start_line, end_line = line_range
    return start_line <= line <= end_line


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
