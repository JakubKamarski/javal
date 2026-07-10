from __future__ import annotations

from functools import lru_cache

from tree_sitter import Language, Parser
import tree_sitter_java as tsjava


@lru_cache(maxsize=1)
def get_parser() -> Parser:
    language = Language(tsjava.language())
    return Parser(language)


def parse_java(source_bytes: bytes | str):
    if isinstance(source_bytes, str):
        source_bytes = source_bytes.encode("utf-8")
    return get_parser().parse(source_bytes)


def node_text(source_bytes: bytes, node) -> str:
    return source_bytes[node.start_byte : node.end_byte].decode("utf-8")


def walk_nodes(root, *node_types: str):
    stack = [root]
    while stack:
        node = stack.pop()
        if not node_types or node.type in node_types:
            yield node
        stack.extend(reversed(node.children))
