from __future__ import annotations

from functools import lru_cache

from tree_sitter import Language, Parser
import tree_sitter_java as tsjava

# tree-sitter-java can desync on multi-byte Unicode dashes in comments, which corrupts
# later method names and hides identifier usages in the rest of the file.
_UNICODE_DASH_REPLACEMENTS = str.maketrans(
    {
        "\u2012": "-",  # figure dash
        "\u2013": "-",  # en dash
        "\u2014": "-",  # em dash
        "\u2015": "-",  # horizontal bar
    }
)


def normalize_java_source(source: str) -> str:
    return source.translate(_UNICODE_DASH_REPLACEMENTS)


@lru_cache(maxsize=1)
def get_parser() -> Parser:
    language = Language(tsjava.language())
    return Parser(language)


def parse_java(source: str):
    normalized = normalize_java_source(source)
    return get_parser().parse(bytes(normalized, "utf8"))


def node_text(source: str, node) -> str:
    normalized = normalize_java_source(source)
    return normalized[node.start_byte : node.end_byte]


def walk_nodes(root, *node_types: str):
    stack = [root]
    while stack:
        node = stack.pop()
        if not node_types or node.type in node_types:
            yield node
        stack.extend(reversed(node.children))
