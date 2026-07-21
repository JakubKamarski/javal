from __future__ import annotations

from dataclasses import dataclass

from validator.java.context import JavaFileContext


@dataclass(frozen=True)
class LombokConstructorCandidate:
    class_name: str
    constructor: object
    parameter_names: tuple[str, ...]


def lombok_constructor_candidates(context: JavaFileContext) -> list[LombokConstructorCandidate]:
    candidates: list[LombokConstructorCandidate] = []

    for class_node in context.walk("class_declaration"):
        class_name = _declaration_name(context, class_node)
        if class_name is None:
            continue

        required_fields = _required_field_names(context, class_node)
        if not required_fields:
            continue

        for constructor in _direct_children(class_node, "constructor_declaration"):
            if _has_annotations(constructor):
                continue
            parameter_names = _formal_parameter_names(context, constructor)
            if set(parameter_names) != required_fields or len(parameter_names) != len(required_fields):
                continue
            if _assigns_required_fields(context, constructor, required_fields, set(parameter_names)):
                candidates.append(
                    LombokConstructorCandidate(
                        class_name=class_name,
                        constructor=constructor,
                        parameter_names=tuple(parameter_names),
                    )
                )

    return candidates


def is_direct_static_factory(
    context: JavaFileContext,
    class_name: str,
    method_node,
    parameter_names: tuple[str, ...],
) -> bool:
    if _has_annotations(method_node) or not _has_modifier(context, method_node, "static"):
        return False
    if _return_type(context, method_node) != class_name:
        return False

    method_parameters = tuple(_formal_parameter_names(context, method_node))
    if method_parameters != parameter_names:
        return False

    body = next((child for child in method_node.children if child.type == "block"), None)
    if body is None:
        return False
    statements = [child for child in body.children if child.type not in {"{", "}"}]
    if len(statements) != 1 or statements[0].type != "return_statement":
        return False

    creation = next(
        (child for child in statements[0].children if child.type == "object_creation_expression"),
        None,
    )
    if creation is None or _created_type(context, creation) != class_name:
        return False

    arguments = next((child for child in creation.children if child.type == "argument_list"), None)
    if arguments is None:
        return not parameter_names
    argument_names = tuple(
        context.text(child)
        for child in arguments.children
        if child.type == "identifier"
    )
    return argument_names == parameter_names


def _direct_children(node, node_type: str):
    body = next((child for child in node.children if child.type == "class_body"), None)
    if body is None:
        return []
    return [child for child in body.children if child.type == node_type]


def _required_field_names(context: JavaFileContext, class_node) -> set[str]:
    names: set[str] = set()
    for field in _direct_children(class_node, "field_declaration"):
        if not _has_modifier(context, field, "final") or _has_modifier(context, field, "static"):
            continue
        for declarator in (child for child in field.children if child.type == "variable_declarator"):
            if any(child.type == "=" for child in declarator.children):
                continue
            identifier = next((child for child in declarator.children if child.type == "identifier"), None)
            if identifier is not None:
                names.add(context.text(identifier))
    return names


def _assigns_required_fields(
    context: JavaFileContext,
    constructor,
    required_fields: set[str],
    parameter_names: set[str],
) -> bool:
    body = next((child for child in constructor.children if child.type == "constructor_body"), None)
    if body is None:
        return False
    statements = [child for child in body.children if child.type not in {"{", "}"}]
    if len(statements) != len(required_fields):
        return False

    assignments: dict[str, str] = {}
    for statement in statements:
        if statement.type != "expression_statement":
            return False
        assignment = next(
            (child for child in statement.children if child.type == "assignment_expression"),
            None,
        )
        if assignment is None:
            return False
        field_access = next((child for child in assignment.children if child.type == "field_access"), None)
        identifiers = [child for child in assignment.children if child.type == "identifier"]
        if field_access is None or len(identifiers) != 1:
            return False
        field_name = _field_access_name(context, field_access)
        parameter_name = context.text(identifiers[0])
        if field_name is None or parameter_name not in parameter_names:
            return False
        assignments[field_name] = parameter_name

    return set(assignments) == required_fields and set(assignments.values()) == parameter_names


def _formal_parameter_names(context: JavaFileContext, declaration) -> list[str]:
    parameters = next((child for child in declaration.children if child.type == "formal_parameters"), None)
    if parameters is None:
        return []
    names: list[str] = []
    for parameter in parameters.children:
        if parameter.type not in {"formal_parameter", "spread_parameter"}:
            continue
        identifier = next((child for child in parameter.children if child.type == "identifier"), None)
        if identifier is None:
            return []
        names.append(context.text(identifier))
    return names


def _declaration_name(context: JavaFileContext, node) -> str | None:
    identifier = next((child for child in node.children if child.type == "identifier"), None)
    return context.text(identifier) if identifier is not None else None


def _field_access_name(context: JavaFileContext, field_access) -> str | None:
    children = field_access.children
    if len(children) != 3 or children[0].type != "this" or children[2].type != "identifier":
        return None
    return context.text(children[2])


def _return_type(context: JavaFileContext, method_node) -> str:
    type_node = next(
        (
            child
            for child in method_node.children
            if child.type in {"type_identifier", "generic_type", "scoped_type_identifier"}
        ),
        None,
    )
    return context.text(type_node) if type_node is not None else ""


def _created_type(context: JavaFileContext, creation_node) -> str:
    type_node = next(
        (
            child
            for child in creation_node.children
            if child.type in {"type_identifier", "generic_type", "scoped_type_identifier"}
        ),
        None,
    )
    return context.text(type_node) if type_node is not None else ""


def _has_annotations(node) -> bool:
    modifiers = next((child for child in node.children if child.type == "modifiers"), None)
    return modifiers is not None and any(
        child.type in {"annotation", "marker_annotation"} for child in modifiers.children
    )


def _has_modifier(context: JavaFileContext, node, modifier: str) -> bool:
    modifiers = next((child for child in node.children if child.type == "modifiers"), None)
    return modifiers is not None and modifier in context.text(modifiers).split()
