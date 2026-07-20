from __future__ import annotations

from validator.java.ast import iter_multiline_type_declaration_headers
from validator.java.context import JavaFileContext
from validator.java.rules.base import JavaRule, RuleViolation

MAX_COMPACT_TYPE_HEADER_LENGTH = 120


class TypeHeaderOneLineRule(JavaRule):
    @property
    def check_id(self) -> str:
        return "java-style-type-header-one-line"

    def apply(self, context: JavaFileContext) -> list[RuleViolation]:
        violations: list[RuleViolation] = []

        for header in iter_multiline_type_declaration_headers(context):
            if header.projected_line_length > MAX_COMPACT_TYPE_HEADER_LENGTH:
                continue

            violations.append(
                RuleViolation(
                    summary=(
                        f"Type declaration '{header.name}' is split across lines, but its "
                        f"one-line header would use {header.projected_line_length} columns "
                        f"(limit {MAX_COMPACT_TYPE_HEADER_LENGTH})."
                    ),
                    line=header.continuation_line,
                    suggestion=(
                        "Keep the modifiers and complete type declaration through the opening "
                        f"'{{' on one line when it fits within {MAX_COMPACT_TYPE_HEADER_LENGTH} "
                        "columns."
                    ),
                )
            )

        return violations
