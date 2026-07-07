from __future__ import annotations

ALLOWED_METHOD_PREFIXES = (
    "build",
    "get",
    "create",
    "update",
    "remove",
    "resolve",
    "calculate",
    "retrieve",
    "filter",
    "find",
    "provide",
    "map",
    "group",
    "convert",
    "validate",
    "is",
    "has",
    "can",
    "should",
    "of",
    "from",
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
}

BARE_PARTICIPLE_PREFIXES = ("distinct", "sorted", "grouped", "filtered")

COLLECTION_TYPE_TOKENS = ("List", "Set", "Map")

NAMING_SUGGESTION = "Rename the symbol to follow agents/rule-java-naming.md."


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
