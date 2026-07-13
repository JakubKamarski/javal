from __future__ import annotations

from collections import defaultdict

from validator.java.ast import iter_method_declarations, parse_gwt_section_line_ranges
from validator.java.ast.gwt import line_in_range
from validator.java.ast.variables import descendants
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
        grouped_methods: dict[
            tuple[int, str, str, tuple[str, ...], tuple[str, ...]], list
        ] = defaultdict(list)

        for method in iter_method_declarations(context):
            if not method.is_test:
                continue

            when_range = parse_gwt_section_line_ranges(context, method.node).get("WHEN")
            if when_range is None:
                continue

            action = action_from_when(context, method.node, when_range)
            if action is None:
                continue
            if action.path == "exception":
                continue
            if action.receiver_type is None or len(action.argument_types) != action.argument_count:
                continue

            test_class = enclosing_class_declaration(method.node)
            if test_class is None:
                continue
            then_range = parse_gwt_section_line_ranges(context, method.node).get("THEN")
            if then_range is None:
                continue
            grouped_methods[
                (
                    test_class.start_byte,
                    action.receiver_type,
                    action.method_name,
                    action.argument_types,
                    _then_fingerprint(context, method.node, then_range),
                )
            ].append(method)

        violations: list[RuleViolation] = []
        for (
            _class_start,
            receiver_type,
            method_name,
            argument_types,
            _then_shape,
        ), methods in grouped_methods.items():
            if len(methods) < 2:
                continue
            violations.append(
                RuleViolation(
                    summary=(
                        f"{len(methods)} test methods in the same class invoke "
                        f"'{receiver_type}.{method_name}({', '.join(argument_types)})' on "
                        "the normal-response path with equivalent assertions. Merge them into "
                        "one parameterized test."
                    ),
                    line=methods[-1].line,
                    suggestion=(
                        "Merge only equivalent normal-response cases into one @ParameterizedTest; "
                        "keep exception-path cases separate (per agents/rule-testing.md)."
                    ),
                )
            )
        return violations


def _then_fingerprint(context: JavaFileContext, method_node, then_range: tuple[int, int]) -> tuple[str, ...]:
    block = next((child for child in method_node.children if child.type == "block"), None)
    if block is None:
        return ()
    tokens: list[str] = []
    for statement in block.children:
        if not line_in_range(statement.start_point[0] + 1, then_range):
            continue
        for node in descendants(statement):
            if node.type == "method_invocation":
                name = next(
                    (
                        context.text(child)
                        for index, child in enumerate(node.children)
                        if child.type == "identifier"
                        and index + 1 < len(node.children)
                        and node.children[index + 1].type == "argument_list"
                    ),
                    "",
                )
                tokens.append(f"call:{name}")
            elif node.is_named and node.type not in {"identifier", "string_literal", "decimal_integer_literal", "decimal_floating_point_literal"}:
                tokens.append(node.type)
    return tuple(tokens)
