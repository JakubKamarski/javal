from __future__ import annotations

import re

from validator.java.context import JavaFileContext
from validator.java.rules.base import JavaRule, RuleViolation

_ILLEGAL_ARGUMENT_EXCEPTION_RE = re.compile(
    r"\s*throw\s+new\s+(?:java\.lang\.)?IllegalArgumentException\s*\("
)


class ApacheCommonsValidateRule(JavaRule):
    """Require Validate for direct argument guards."""

    file_applicability = "production"

    @property
    def check_id(self) -> str:
        return "java-style-apache-commons-validate"

    def apply(self, context: JavaFileContext) -> list[RuleViolation]:
        violations: list[RuleViolation] = []

        for if_statement in context.walk("if_statement"):
            if not self._is_direct_argument_guard(context, if_statement):
                continue
            violations.append(
                RuleViolation(
                    summary=(
                        "Use Apache Commons Lang Validate instead of a direct if guard that "
                        "only throws IllegalArgumentException."
                    ),
                    line=if_statement.start_point[0] + 1,
                    suggestion=(
                        "Use Validate.notNull(...) for null rejection; otherwise use "
                        "Validate.isTrue(...) with the valid condition."
                    ),
                )
            )

        return violations

    @classmethod
    def _is_direct_argument_guard(cls, context: JavaFileContext, if_statement) -> bool:
        named_children = [child for child in if_statement.children if child.is_named]
        if len(named_children) != 2 or named_children[0].type != "parenthesized_expression":
            return False

        return cls._is_illegal_argument_exception(context, named_children[1])

    @staticmethod
    def _is_illegal_argument_exception(context: JavaFileContext, node) -> bool:
        if node.type == "block":
            statements = [child for child in node.children if child.is_named]
            if len(statements) != 1:
                return False
            node = statements[0]

        return node.type == "throw_statement" and bool(
            _ILLEGAL_ARGUMENT_EXCEPTION_RE.match(context.text(node))
        )
