from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from validator.java.ast.modifiers import is_public_top_level_type
from validator.java.ast.variables import declaration_type_text, is_constant_field
from validator.java.context import JavaFileContext
from validator.java.rules.applicability import context_for
from validator.java.rules.testing._support import (
    is_test_source_file,
    required_test_exists,
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


@dataclass(frozen=True)
class ProductionType:
    path: Path
    package_name: str
    source_root: Path | None

    @property
    def class_name(self) -> str:
        return self.path.stem

    @property
    def qualified_name(self) -> str:
        if not self.package_name:
            return self.class_name
        return f"{self.package_name}.{self.class_name}"


def _package_name(context: JavaFileContext) -> str:
    package = next(context.walk("package_declaration"), None)
    if package is None:
        return ""
    text = context.text(package).strip()
    return text.removeprefix("package").removesuffix(";").strip()


def _source_root(path: Path) -> Path | None:
    resolved = path.resolve()
    parts = resolved.parts
    matches = [
        index
        for index in range(len(parts) - 2)
        if parts[index : index + 3] == ("src", "main", "java")
    ]
    if not matches:
        return None
    return Path(*parts[: matches[-1] + 3])


def production_types_by_path(
    java_files: list[Path],
    *,
    contexts: dict[str, JavaFileContext] | None = None,
) -> dict[Path, ProductionType]:
    production_types: dict[Path, ProductionType] = {}
    for path in java_files:
        if is_test_source_file(path):
            continue
        resolved = path.resolve()
        context = context_for(resolved, contexts)
        production_types[resolved] = ProductionType(
            path=resolved,
            package_name=_package_name(context),
            source_root=_source_root(resolved),
        )
    return production_types


def build_injected_by_index(
    production_types: dict[Path, ProductionType],
    *,
    contexts: dict[str, JavaFileContext] | None = None,
) -> dict[Path, set[Path]]:
    injected_by: dict[Path, set[Path]] = defaultdict(set)
    candidates_by_name: dict[str, list[ProductionType]] = defaultdict(list)
    candidates_by_qualified_name: dict[str, list[ProductionType]] = defaultdict(list)
    for production_type in production_types.values():
        candidates_by_name[production_type.class_name].append(production_type)
        candidates_by_qualified_name[production_type.qualified_name].append(production_type)

    for injector in production_types.values():
        context = context_for(injector.path, contexts)
        imported_type_by_name = _explicit_imports(context)
        for dependency in iter_injected_type_names(context):
            injected = _resolve_injected_type(
                dependency,
                injector,
                imported_type_by_name,
                candidates_by_name,
                candidates_by_qualified_name,
            )
            if injected is not None and injected.path != injector.path:
                injected_by[injected.path].add(injector.path)

    return dict(injected_by)


def _explicit_imports(context: JavaFileContext) -> dict[str, str]:
    imported_type_by_name: dict[str, str] = {}
    for node in context.walk("import_declaration"):
        text = context.text(node).strip().removeprefix("import").removesuffix(";").strip()
        if text.startswith("static ") or text.endswith(".*"):
            continue
        imported_type_by_name[text.rsplit(".", maxsplit=1)[-1]] = text
    return imported_type_by_name


def _resolve_injected_type(
    reference: str,
    injector: ProductionType,
    imported_type_by_name: dict[str, str],
    candidates_by_name: dict[str, list[ProductionType]],
    candidates_by_qualified_name: dict[str, list[ProductionType]],
) -> ProductionType | None:
    simple_name = reference.rsplit(".", maxsplit=1)[-1]
    qualified_reference = reference if "." in reference else imported_type_by_name.get(simple_name)
    if qualified_reference:
        qualified_candidates = candidates_by_qualified_name.get(qualified_reference, [])
        if len(qualified_candidates) == 1:
            return qualified_candidates[0]

    candidates = candidates_by_name.get(simple_name, [])
    same_package = [
        candidate
        for candidate in candidates
        if candidate.package_name == injector.package_name
    ]
    if len(same_package) == 1:
        return same_package[0]

    same_source_root = [
        candidate
        for candidate in same_package
        if candidate.source_root is not None and candidate.source_root == injector.source_root
    ]
    if len(same_source_root) == 1:
        return same_source_root[0]

    if len(candidates) == 1:
        return candidates[0]
    return None


def iter_injected_type_names(context: JavaFileContext) -> set[str]:
    types: set[str] = set()

    for node in context.walk("field_declaration"):
        if is_constant_field(context, node):
            continue
        type_name = injected_type_reference(declaration_type_text(context, node))
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
            type_name = injected_type_reference(declaration_type_text(context, formal))
            if type_name:
                types.add(type_name)

    return types


def injected_type_reference(type_text: str) -> str:
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
    return normalized


def is_covered_by_ancestor_it(
    source_path: Path,
    production_types: dict[Path, ProductionType],
    injected_by: dict[Path, set[Path]],
    *,
    contexts: dict[str, JavaFileContext] | None = None,
) -> bool:
    visiting: set[Path] = set()
    pending = list(injected_by.get(source_path.resolve(), ()))

    while pending:
        injector = pending.pop()
        if injector in visiting:
            continue
        visiting.add(injector)

        if has_required_it_file(injector, production_types, contexts=contexts):
            return True

        pending.extend(injected_by.get(injector, ()))

    return False


def has_required_it_file(
    source_path: Path,
    production_types: dict[Path, ProductionType],
    *,
    contexts: dict[str, JavaFileContext] | None = None,
) -> bool:
    production_type = production_types.get(source_path.resolve())
    if production_type is None:
        return False
    class_name = production_type.class_name
    requirement = subject_test_requirement(class_name)
    if requirement is None:
        return False

    context = context_for(source_path, contexts)
    if requirement.requires_public_class and not is_public_top_level_type(context, class_name):
        return False

    return required_test_exists(source_path, class_name, requirement)
