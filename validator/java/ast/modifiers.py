from __future__ import annotations

from validator.java.context import JavaFileContext


def annotation_simple_name(context: JavaFileContext, annotation_node) -> str | None:
    for child in annotation_node.children:
        if child.type == "identifier":
            return context.text(child)
        if child.type == "scoped_identifier":
            return context.text(child).rsplit(".", 1)[-1]
    return None


def node_has_annotation(context: JavaFileContext, node, *simple_names: str) -> bool:
    modifiers = next((child for child in node.children if child.type == "modifiers"), None)
    if modifiers is None:
        return False

    wanted = set(simple_names)
    for child in modifiers.children:
        if child.type not in ("marker_annotation", "annotation"):
            continue
        name = annotation_simple_name(context, child)
        if name in wanted:
            return True
    return False


def node_has_modifier(context: JavaFileContext, node, modifier: str) -> bool:
    modifiers = next((child for child in node.children if child.type == "modifiers"), None)
    if modifiers is None:
        return False
    return modifier in context.text(modifiers).split()


def top_level_type_name(context: JavaFileContext, node_type: str, type_name: str) -> object | None:
    for node in context.walk(node_type):
        identifier = next((child for child in node.children if child.type == "identifier"), None)
        if identifier is not None and context.text(identifier) == type_name:
            return node
    return None


def is_public_top_level_type(context: JavaFileContext, type_name: str) -> bool:
    for node_type in ("class_declaration", "interface_declaration"):
        node = top_level_type_name(context, node_type, type_name)
        if node is not None:
            return node_has_modifier(context, node, "public")
    return False


SPRING_BOUNDARY_ANNOTATIONS = (
    "Service",
    "Component",
    "Repository",
    "Controller",
    "RestController",
    "Configuration",
    "Transactional",
    "Entity",
)


def has_spring_boundary_annotation(context: JavaFileContext, type_name: str) -> bool:
    for node_type in ("class_declaration", "interface_declaration"):
        node = top_level_type_name(context, node_type, type_name)
        if node is not None:
            return node_has_annotation(context, node, *SPRING_BOUNDARY_ANNOTATIONS)
    return False


def is_abstract_top_level_type(context: JavaFileContext, type_name: str) -> bool:
    node = top_level_type_name(context, "class_declaration", type_name)
    if node is None:
        return False
    return node_has_modifier(context, node, "abstract")


def node_line_numbers(node) -> set[int]:
    return set(range(node.start_point[0] + 1, node.end_point[0] + 2))


def iter_query_method_declarations(context: JavaFileContext):
    for node in context.walk("method_declaration"):
        if node_has_annotation(context, node, "Query"):
            yield node


def has_query_annotation(context: JavaFileContext) -> bool:
    return any(iter_query_method_declarations(context))


def has_task_changed_query_method(context: JavaFileContext, changed_lines: set[int]) -> bool:
    if not changed_lines:
        return False

    for method in iter_query_method_declarations(context):
        if node_line_numbers(method) & changed_lines:
            return True
    return False


def enclosing_class_declaration(node):
    current = node.parent
    while current is not None:
        if current.type == "class_declaration":
            return current
        current = current.parent
    return None


def enclosing_record_declaration(node):
    current = node.parent
    while current is not None:
        if current.type == "record_declaration":
            return current
        current = current.parent
    return None
