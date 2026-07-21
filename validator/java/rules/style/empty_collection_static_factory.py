from __future__ import annotations

import re

from validator.java.context import JavaFileContext
from validator.java.rules.base import JavaRule, RuleViolation

_COLLECTION_TYPES = frozenset({"List", "Map", "Set"})
_EMPTY_FACTORY_RE = re.compile(
    r"(?:java\.util\.)?(List|Map|Set)\.(?:<[^>]+>)?of\(\)$"
)
_COLLECTIONS_METHODS = {
    "List": "Collections.emptyList()",
    "Map": "Collections.emptyMap()",
    "Set": "Collections.emptySet()",
}


class EmptyCollectionStaticFactoryRule(JavaRule):
    @property
    def check_id(self) -> str:
        return "java-style-empty-collection-static-factory"

    def apply(self, context: JavaFileContext) -> list[RuleViolation]:
        violations: list[RuleViolation] = []

        for invocation in context.walk("method_invocation"):
            collection_type = self._empty_collection_type(context, invocation)
            if collection_type is None:
                continue
            replacement = _COLLECTIONS_METHODS[collection_type]
            violations.append(
                RuleViolation(
                    summary=(
                        f"Use '{replacement}' instead of empty '{collection_type}.of()'."
                    ),
                    line=invocation.start_point[0] + 1,
                    suggestion="Use the matching immutable empty collection factory from java.util.Collections.",
                )
            )

        return violations

    @staticmethod
    def _empty_collection_type(context: JavaFileContext, invocation) -> str | None:
        argument_list = next(
            (child for child in invocation.children if child.type == "argument_list"),
            None,
        )
        if argument_list is None or any(child.is_named for child in argument_list.children):
            return None

        invocation_text = re.sub(r"\s+", "", context.text(invocation))
        match = _EMPTY_FACTORY_RE.fullmatch(invocation_text)
        if match is None:
            return None
        collection_type = match.group(1)
        return collection_type if collection_type in _COLLECTION_TYPES else None
