from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from validator.java.ast.modifiers import is_public_top_level_type
from validator.java.ast.variables import declaration_type_text, is_constant_field
from validator.java.context import JavaFileContext
from validator.java.rules.applicability import context_for
from validator.java.rules.testing._support import (
    expected_test_class_name,
    is_test_source_file,
    resolve_expected_test_path,
    subject_test_requirement,
)

_PRIMITIVE_TYPES = frozenset(
    {
        "boolean",
        "byte",
        "char",
        "double",
        "float",
        "int",
        "long",
        "short",
        "void",
        "String",
    }
)


def production_class_paths(java_files: list[Path]) -> dict[str, Path]:
    return {
        path.stem: path
        for path in java_files
        if not is_test_source_file(path)
    }


def build_injected_by_index(
    class_to_path: dict[str, Path],
    *,
    contexts: dict[str, JavaFileContext] | None = None,
) -> dict[str, set[str]]:
    injected_by: dict[str, set[str]] = defaultdict(set)

    for class_name, path in class_to_path.items():
        context = context_for(path, contexts)
        for dependency in iter_injected_type_names(context):
            if dependency in class_to_path and dependency != class_name:
                injected_by[dependency].add(class_name)

    return dict(injected_by)


def iter_injected_type_names(context: JavaFileContext) -> set[str]:
    types: set[str] = set()

    for node in context.walk("field_declaration"):
        if is_constant_field(context, node):
            continue
        type_name = simple_injected_type_name(declaration_type_text(context, node))
        if type_name:
            types.add(type_name)

    for constructor in context.walk("constructor_declaration"):
        formal_parameters = next(
            (child for child in constructor.children if child.type == "formal_parameters"),
            None,
        )
        if formal_parameters is None:
            continue
        for formal in formal_parameters.children:
            if formal.type != "formal_parameter":
                continue
            type_name = simple_injected_type_name(declaration_type_text(context, formal))
            if type_name:
                types.add(type_name)

    return types


def simple_injected_type_name(type_text: str) -> str:
    normalized = type_text.strip()
    if not normalized:
        return ""

    if "<" in normalized and ">" in normalized:
        inner = normalized[normalized.index("<") + 1 : normalized.rindex(">")]
        if "," in inner:
            return ""
        normalized = inner.strip()

    simple_name = normalized.rsplit(".", maxsplit=1)[-1]
    if simple_name in _PRIMITIVE_TYPES:
        return ""
    return simple_name


def is_covered_by_ancestor_it(
    class_name: str,
    class_to_path: dict[str, Path],
    injected_by: dict[str, set[str]],
    *,
    contexts: dict[str, JavaFileContext] | None = None,
) -> bool:
    visiting: set[str] = set()
    pending = list(injected_by.get(class_name, ()))

    while pending:
        injector = pending.pop()
        if injector in visiting:
            continue
        visiting.add(injector)

        if has_required_it_file(injector, class_to_path, contexts=contexts):
            return True

        pending.extend(injected_by.get(injector, ()))

    return False


def has_required_it_file(
    class_name: str,
    class_to_path: dict[str, Path],
    *,
    contexts: dict[str, JavaFileContext] | None = None,
) -> bool:
    requirement = subject_test_requirement(class_name)
    if requirement is None:
        return False

    source_path = class_to_path.get(class_name)
    if source_path is None:
        return False

    context = context_for(source_path, contexts)
    if requirement.requires_public_class and not is_public_top_level_type(context, class_name):
        return False

    test_class_name = expected_test_class_name(class_name, requirement)
    expected_test_path = resolve_expected_test_path(source_path, test_class_name)
    return expected_test_path.is_file()
