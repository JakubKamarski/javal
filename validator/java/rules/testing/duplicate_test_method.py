from __future__ import annotations

from collections import defaultdict

from validator.java.ast import iter_method_declarations, parse_gwt_section_line_ranges
from validator.java.ast.modifiers import enclosing_class_declaration
from validator.java.ast.test_actions import TestAction, action_from_when
from validator.java.context import JavaFileContext
from validator.java.rules.base import JavaRule, RuleViolation


class DuplicateTestMethodRule(JavaRule):
    file_applicability = "test"

    @property
    def check_id(self) -> str:
        return "java-testing-duplicate-test-method"

    def apply(self, context: JavaFileContext) -> list[RuleViolation]:
        grouped_methods: dict[tuple[int, TestAction], list] = defaultdict(list)

        for method in iter_method_declarations(context):
            if not method.is_test:
                continue

            when_range = parse_gwt_section_line_ranges(context, method.node).get("WHEN")
            if when_range is None:
                continue

            action = action_from_when(context, method.node, when_range)
            if action is None:
                continue

            test_class = enclosing_class_declaration(method.node)
            if test_class is None:
                continue
            grouped_methods[(test_class.start_byte, action)].append(method)

        violations: list[RuleViolation] = []
        for (_class_start, action), methods in grouped_methods.items():
            if len(methods) < 2:
                continue
            violations.append(
                RuleViolation(
                    summary=(
                        f"{len(methods)} test methods in the same class invoke "
                        f"'{action.method_name}/{action.argument_count}' on the "
                        f"{_path_label(action)} path. Merge them into one parameterized test."
                    ),
                    line=methods[-1].line,
                    suggestion=(
                        "Merge these tests into one @ParameterizedTest; keep exception-path "
                        "cases separate from normal-response cases (per agents/rule-testing.md)."
                    ),
                )
            )
        return violations


def _path_label(action: TestAction) -> str:
    if action.path == "exception":
        return "exception"
    return "normal-response"
