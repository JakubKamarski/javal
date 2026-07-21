from __future__ import annotations

from validator.java.ast import gwt_section_markers, iter_method_declarations
from validator.java.context import JavaFileContext
from validator.java.rules.base import JavaRule, RuleViolation
from validator.java.rules.testing._support import TESTING_SUGGESTION

_EXPECTED_SECTIONS = ("GIVEN", "WHEN", "THEN")


class TestGwtSectionsRule(JavaRule):
    file_applicability = "test"

    @property
    def check_id(self) -> str:
        return "java-testing-gwt-sections"

    def apply(self, context: JavaFileContext) -> list[RuleViolation]:
        violations: list[RuleViolation] = []

        for method in iter_method_declarations(context):
            if not method.is_test:
                continue

            labels = tuple(label for label, _line in gwt_section_markers(context, method.node))
            if labels == _EXPECTED_SECTIONS:
                continue

            violations.append(
                RuleViolation(
                    summary=(
                        f"Test method '{method.name}' must contain exactly one "
                        "// GIVEN, // WHEN, and // THEN section in that order."
                    ),
                    line=method.line,
                    suggestion=TESTING_SUGGESTION,
                )
            )

        return violations
