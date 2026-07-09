from __future__ import annotations

from validator.java.ast import (
    iter_local_variable_declarations,
    iter_method_declarations,
    line_in_range,
    parse_gwt_section_line_ranges,
)
from validator.java.context import JavaFileContext
from validator.java.rules.base import JavaRule, RuleViolation
from validator.java.rules.testing._support import TESTING_SUGGESTION

GENERIC_WHEN_VARIABLE_NAMES = frozenset(
    {
        "result",
        "output",
        "value",
        "response",
    }
)


def _node_within(node, ancestor) -> bool:
    return node.start_byte >= ancestor.start_byte and node.end_byte <= ancestor.end_byte


class TestWhenGenericVariableRule(JavaRule):
    file_applicability = "test"

    @property
    def check_id(self) -> str:
        return "java-testing-when-generic-variable"

    def apply(self, context: JavaFileContext) -> list[RuleViolation]:
        violations: list[RuleViolation] = []

        for method in iter_method_declarations(context):
            if not method.is_test:
                continue

            sections = parse_gwt_section_line_ranges(context, method.node)
            when_range = sections.get("WHEN")
            if when_range is None:
                continue

            for variable in iter_local_variable_declarations(context):
                if not _node_within(variable.node, method.node):
                    continue
                if not line_in_range(variable.line, when_range):
                    continue
                if variable.name not in GENERIC_WHEN_VARIABLE_NAMES:
                    continue
                violations.append(
                    RuleViolation(
                        summary=(
                            f"Test method '{method.name}' declares generic WHEN variable "
                            f"'{variable.name}'; use a descriptive domain name."
                        ),
                        line=variable.line,
                        suggestion=TESTING_SUGGESTION,
                    )
                )

        return violations
