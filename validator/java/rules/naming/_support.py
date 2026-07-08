from __future__ import annotations

import re

ALLOWED_METHOD_PREFIXES = (
    "synchronize",
    "calculate",
    "retrieve",
    "validate",
    "compute",
    "convert",
    "execute",
    "process",
    "provide",
    "persist",
    "prepare",
    "request",
    "resolve",
    "reset",
    "remove",
    "update",
    "create",
    "filter",
    "handle",
    "apply",
    "build",
    "check",
    "fetch",
    "find",
    "from",
    "group",
    "load",
    "parse",
    "read",
    "save",
    "send",
    "stub",
    "call",
    "write",
    "should",
    "map",
    "get",
    "has",
    "log",
    "can",
    "is",
    "of",
)

STANDARD_METHOD_NAMES = {
    "equals",
    "hashCode",
    "toString",
    "compareTo",
    "clone",
    "finalize",
    "main",
    "run",
    "close",
    "iterator",
    "next",
    "hasNext",
    "valueOf",
    "values",
    "name",
    "setUp",
    "tearDown",
}

BARE_PARTICIPLE_PREFIXES = ("distinct", "sorted", "grouped", "filtered", "empty")

COLLECTION_TYPE_TOKENS = ("List", "Set", "Map")

NAMING_SUGGESTION = "Rename the symbol to follow agents/rule-java-naming.md."

_CAMEL_CASE_TOKEN_SPLIT = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")


def embedded_collection_type_token(name: str) -> str | None:
    tokens = _CAMEL_CASE_TOKEN_SPLIT.split(name)
    for token in COLLECTION_TYPE_TOKENS:
        if token in tokens:
            return token
    return None


def starts_with_allowed_verb(name: str) -> bool:
    for prefix in sorted(ALLOWED_METHOD_PREFIXES, key=len, reverse=True):
        if not name.startswith(prefix):
            continue
        if len(name) == len(prefix):
            return True
        next_char = name[len(prefix)]
        if next_char.isupper() or next_char == "_":
            return True
    return False
