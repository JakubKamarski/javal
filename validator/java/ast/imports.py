from __future__ import annotations

import re

from validator.java.ast.models import ImportDeclaration
from validator.java.context import JavaFileContext


def imported_symbol(context: JavaFileContext, import_node) -> str | None:
    if any(child.type == "asterisk" for child in import_node.children):
        return None

    scoped = next((child for child in import_node.children if child.type == "scoped_identifier"), None)
    if scoped is None:
        return None

    parts = context.text(scoped).split(".")
    return parts[-1] if parts else None


def iter_import_declarations(context: JavaFileContext):
    for import_node in context.walk("import_declaration"):
        symbol = imported_symbol(context, import_node)
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
