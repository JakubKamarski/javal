from __future__ import annotations

from validator.java.ast.modifiers import node_has_annotation, node_has_modifier, node_line_numbers
from validator.java.ast.variables import variable_names
from validator.java.context import JavaFileContext

SERIAL_VERSION_UID = "serialVersionUID"


def iter_jpa_entity_class_declarations(context: JavaFileContext):
    for node in context.walk("class_declaration"):
        if node_has_annotation(context, node, "Entity"):
            yield node


def entity_class_name(context: JavaFileContext, class_node) -> str:
    identifier = next((child for child in class_node.children if child.type == "identifier"), None)
    if identifier is None:
        return ""
    return context.text(identifier)


def iter_persistent_field_declarations(context: JavaFileContext, class_node):
    class_body = next((child for child in class_node.children if child.type == "class_body"), None)
    if class_body is None:
        return

    for child in class_body.children:
        if child.type != "field_declaration":
            continue
        if node_has_modifier(context, child, "static"):
            continue
        if node_has_annotation(context, child, "Transient"):
            continue
        names = [name for name, _line in variable_names(context, child)]
        if names == [SERIAL_VERSION_UID]:
            continue
        yield child


def find_serial_version_uid_field(context: JavaFileContext, class_node):
    class_body = next((child for child in class_node.children if child.type == "class_body"), None)
    if class_body is None:
        return None

    for child in class_body.children:
        if child.type != "field_declaration":
            continue
        names = [name for name, _line in variable_names(context, child)]
        if SERIAL_VERSION_UID in names:
            return child
    return None


def persistent_field_lines(context: JavaFileContext, class_node) -> set[int]:
    lines: set[int] = set()
    for field in iter_persistent_field_declarations(context, class_node):
        lines.update(node_line_numbers(field))
    return lines


def serial_version_uid_lines(context: JavaFileContext, class_node) -> set[int]:
    field = find_serial_version_uid_field(context, class_node)
    if field is None:
        return set()
    return node_line_numbers(field)
