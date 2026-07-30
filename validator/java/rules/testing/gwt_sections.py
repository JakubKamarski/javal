from __future__ import annotations

from validator.java.ast import (
    gwt_content_nodes_in_range,
    gwt_section_markers,
    iter_method_declarations,
    parse_gwt_section_line_ranges,
)
from validator.java.ast.test_actions import action_from_when, has_inline_arguments
from validator.java.ast.variables import descendants
from validator.java.context import JavaFileContext
from validator.java.rules.base import JavaRule, RuleViolation

_VALID_SECTION_SEQUENCES = {
    ("GIVEN", "WHEN", "THEN"),
    ("WHEN", "THEN"),
}
_SECTION_ORDER_SUGGESTION = (
    "Use // GIVEN only when setup or inputs exist, followed by non-empty // WHEN and // THEN "
    "sections per agents/rule-testing.md."
)


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

            markers = gwt_section_markers(context, method.node)
            labels = tuple(label for label, _line in markers)
            if labels not in _VALID_SECTION_SEQUENCES:
                violations.append(
                    RuleViolation(
                        summary=(
                            f"Test method '{method.name}' must contain exactly one // WHEN and "
                            "// THEN section in that order, with at most one // GIVEN before them."
                        ),
                        line=method.line,
                        suggestion=_SECTION_ORDER_SUGGESTION,
                    )
                )
                continue

            marker_lines = dict(markers)
            sections = parse_gwt_section_line_ranges(context, method.node)
            if "GIVEN" not in sections:
                pre_when_range = (method.line, marker_lines["WHEN"] - 1)
                unlabeled_content = gwt_content_nodes_in_range(method.node, pre_when_range)
                if unlabeled_content:
                    suggestion = (
                        "Add // GIVEN before the setup; omit it only when no setup or inputs exist."
                    )
                    violations.append(
                        RuleViolation(
                            summary=(
                                f"Test method '{method.name}' has setup or inputs before // WHEN "
                                f"without a // GIVEN section. {suggestion}"
                            ),
                            line=unlabeled_content[0].start_point[0] + 1,
                            suggestion=suggestion,
                        )
                    )

            for label, line_range in sections.items():
                if gwt_content_nodes_in_range(method.node, line_range):
                    continue
                suggestion = _empty_section_suggestion(context, method.node, label, sections)
                violations.append(
                    RuleViolation(
                        summary=(
                            f"Test method '{method.name}' contains an empty // {label} section. "
                            f"{suggestion}"
                        ),
                        line=marker_lines[label],
                        suggestion=suggestion,
                    )
                )

        return violations


def _empty_section_suggestion(
    context: JavaFileContext,
    method_node,
    label: str,
    sections: dict[str, tuple[int, int]],
) -> str:
    if label == "GIVEN":
        if _has_extractable_inline_arguments(context, method_node, sections["WHEN"]):
            return (
                "Move inline constructor or method arguments from the tested action into // GIVEN; "
                "remove // GIVEN only when no setup or inputs exist."
            )
        return (
            "Fill // GIVEN with available setup or inputs when possible; remove it only when none "
            "exist."
        )
    if label == "WHEN":
        return "Move the tested action into // WHEN; keep assertions and verifications in // THEN."
    return "Move assertions or verifications into // THEN."


def _has_extractable_inline_arguments(
    context: JavaFileContext,
    method_node,
    when_range: tuple[int, int],
) -> bool:
    action = action_from_when(context, method_node, when_range)
    if action is not None and action.has_inline_arguments:
        return True

    return any(
        candidate.type in {"method_invocation", "object_creation_expression"}
        and has_inline_arguments(candidate)
        for lambda_expression in descendants(method_node)
        if lambda_expression.type == "lambda_expression"
        for candidate in descendants(lambda_expression)
    )
