from __future__ import annotations

from validator.java.ast import (
    iter_method_declarations,
    parse_gwt_section_line_ranges,
)
from validator.java.ast.test_actions import action_from_when
from validator.java.context import JavaFileContext
from validator.java.rules.base import JavaRule, RuleViolation
from validator.java.rules.testing._support import TESTING_SUGGESTION


class TestMethodPrefixRule(JavaRule):
    file_applicability = "test"

    @property
    def check_id(self) -> str:
        return "java-testing-test-method-prefix"

    def apply(self, context: JavaFileContext) -> list[RuleViolation]:
        violations: list[RuleViolation] = []

        for method in iter_method_declarations(context):
            if not method.is_test:
                continue

            when_range = parse_gwt_section_line_ranges(context, method.node).get("WHEN")
            if when_range is None:
                continue

            action = action_from_when(context, method.node, when_range)
            if action is None:
                continue
            method_under_test = action.method_name

            if method.name.startswith(method_under_test):
                continue

            violations.append(
                RuleViolation(
                    summary=(
                        f"Test method '{method.name}' must start with the tested method "
                        f"'{method_under_test}'."
                    ),
                    line=method.line,
                    suggestion=TESTING_SUGGESTION,
                )
            )

        return violations
