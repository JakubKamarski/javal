from __future__ import annotations

import re

from validator.java.ast.modifiers import node_has_modifier
from validator.java.context import JavaFileContext

_DECLARATION_TYPES = frozenset(
    {
        "annotation_type_declaration",
        "class_declaration",
        "constructor_declaration",
        "enum_declaration",
        "field_declaration",
        "interface_declaration",
        "method_declaration",
        "record_declaration",
    }
)
_SUPPRESSION_RE = re.compile(
    r"NOSONAR|CHECKSTYLE|SUPPRESS\s*CHECKSTYLE|PMD|spotless|formatter:\s*(off|on)|noinspection",
    re.IGNORECASE,
)
_DEPRECATION_RE = re.compile(r"deprecat", re.IGNORECASE)
_LICENSE_RE = re.compile(r"copyright|license|licenced|apache|mit\s+license", re.IGNORECASE)
_GWT_MARKER_RE = re.compile(r"^(GIVEN|WHEN|THEN)\b", re.IGNORECASE)
_TODO_FIXME_RE = re.compile(r"\b(TODO|FIXME)\b", re.IGNORECASE)
_TASK_ID_RE = re.compile(r"[A-Z][A-Z0-9]*-\d+")


def comment_body(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("/**"):
        stripped = stripped[3:]
    elif stripped.startswith("/*"):
        stripped = stripped[2:]
    elif stripped.startswith("//"):
        stripped = stripped[2:]
    if stripped.endswith("*/"):
        stripped = stripped[:-2]
    return stripped.strip()


def is_javadoc_comment(text: str) -> bool:
    return text.lstrip().startswith("/**")


def is_suppression_comment(text: str) -> bool:
    return bool(_SUPPRESSION_RE.search(comment_body(text)))


def is_deprecation_comment(text: str) -> bool:
    return bool(_DEPRECATION_RE.search(comment_body(text)))


def is_gwt_marker_comment(text: str) -> bool:
    return bool(_GWT_MARKER_RE.match(comment_body(text)))


def is_license_header_comment(context: JavaFileContext, line: int, text: str) -> bool:
    if not text.lstrip().startswith("/*"):
        return False
    if line > 5:
        return False
    return bool(_LICENSE_RE.search(comment_body(text)))


def has_task_reference(text: str) -> bool:
    return bool(_TASK_ID_RE.search(comment_body(text)))


def is_orphan_todo_fixme(text: str) -> bool:
    body = comment_body(text)
    return bool(_TODO_FIXME_RE.search(body)) and not has_task_reference(text)


def next_declaration_sibling(comment_node):
    parent = comment_node.parent
    if parent is None:
        return None

    children = parent.children
    try:
        start_index = children.index(comment_node)
    except ValueError:
        return None

    for sibling in children[start_index + 1 :]:
        if sibling.type in _DECLARATION_TYPES:
            return sibling
        if sibling.type not in {"line_comment", "block_comment"}:
            break
    return None


def is_public_api_declaration(context: JavaFileContext, node) -> bool:
    if node.type == "method_declaration":
        if node_has_modifier(context, node, "public"):
            return True
        current = node.parent
        while current is not None:
            if current.type == "interface_declaration":
                return True
            current = current.parent
        return False

    if node.type == "constructor_declaration":
        return node_has_modifier(context, node, "public")

    if node.type == "field_declaration":
        return node_has_modifier(context, node, "public")

    if node.type in {"class_declaration", "interface_declaration", "enum_declaration", "record_declaration"}:
        return node_has_modifier(context, node, "public")

    return False


def is_public_api_javadoc(context: JavaFileContext, comment_node, text: str) -> bool:
    if not is_javadoc_comment(text):
        return False
    declaration = next_declaration_sibling(comment_node)
    if declaration is None:
        return False
    return is_public_api_declaration(context, declaration)


def is_allowed_comment(context: JavaFileContext, comment_node, line: int, text: str) -> bool:
    body = comment_body(text)
    if not body:
        return True
    if is_suppression_comment(text):
        return True
    if is_deprecation_comment(text):
        return True
    if is_gwt_marker_comment(text):
        return True
    if is_license_header_comment(context, line, text):
        return True
    if is_public_api_javadoc(context, comment_node, text):
        return True
    if _TODO_FIXME_RE.search(body) and has_task_reference(text):
        return True
    return False


def iter_comments(context: JavaFileContext):
    for node in context.walk("line_comment", "block_comment"):
        yield node, node.start_point[0] + 1, context.text(node)
