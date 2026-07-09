from __future__ import annotations

from validator.java.ast.types import (
    declaration_header_line_numbers,
    declaration_simple_name,
    header_has_nosonar,
    is_descriptive_nosonar_line,
    is_standard_type_parameter_name,
    iter_generic_method_declarations,
    iter_generic_type_declarations,
    lines_have_nosonar,
    method_signature_line_numbers,
    method_simple_name,
)
from validator.java.context import JavaFileContext
from validator.java.rules.base import JavaRule, RuleViolation

_SINGULAR_NOSONAR = (
    "// NOSONAR: descriptive business generic name is clearer than a single-letter type parameter."
)
_PLURAL_NOSONAR = (
    "// NOSONAR: descriptive business generic names are clearer than single-letter type parameters."
)
_BARE_METHOD_NOSONAR = "// NOSONAR"


class GenericTypeNosonarRule(JavaRule):
    @property
    def check_id(self) -> str:
        return "java-sonar-generic-type-nosonar"

    def apply(self, context: JavaFileContext) -> list[RuleViolation]:
        violations: list[RuleViolation] = []
        violations.extend(self._check_type_headers(context))
        violations.extend(self._check_method_signatures(context))
        return violations

    def _check_type_headers(self, context: JavaFileContext) -> list[RuleViolation]:
        violations: list[RuleViolation] = []

        for node, type_parameter_names in iter_generic_type_declarations(context):
            non_standard_names = [
                name for name in type_parameter_names if not is_standard_type_parameter_name(name)
            ]
            if not non_standard_names:
                continue
            if header_has_nosonar(context, node):
                continue

            declaration_name = declaration_simple_name(context, node)
            header_line = min(declaration_header_line_numbers(node))
            suggestion = _PLURAL_NOSONAR if len(non_standard_names) > 1 else _SINGULAR_NOSONAR
            violations.append(
                RuleViolation(
                    summary=(
                        f"Type '{declaration_name}' uses non-standard type parameter name(s) "
                        f"({', '.join(non_standard_names)}) without a NOSONAR suppression on the header."
                    ),
                    line=header_line,
                    suggestion=suggestion,
                )
            )

        return violations

    def _check_method_signatures(self, context: JavaFileContext) -> list[RuleViolation]:
        violations: list[RuleViolation] = []
        lines = context.source.splitlines()

        for node, type_parameter_names in iter_generic_method_declarations(context):
            non_standard_names = [
                name for name in type_parameter_names if not is_standard_type_parameter_name(name)
            ]
            if not non_standard_names:
                continue

            signature_lines = method_signature_line_numbers(node)
            method_name = method_simple_name(context, node)
            first_signature_line = min(signature_lines)

            if not lines_have_nosonar(context, signature_lines):
                violations.append(
                    RuleViolation(
                        summary=(
                            f"Method '{method_name}' uses non-standard type parameter name(s) "
                            f"({', '.join(non_standard_names)}) without a NOSONAR suppression on the signature."
                        ),
                        line=first_signature_line,
                        suggestion=_BARE_METHOD_NOSONAR,
                    )
                )
                continue

            descriptive_line = next(
                (
                    line_number
                    for line_number in sorted(signature_lines)
                    if line_number >= 1
                    and line_number <= len(lines)
                    and is_descriptive_nosonar_line(lines[line_number - 1])
                ),
                None,
            )
            if descriptive_line is not None:
                violations.append(
                    RuleViolation(
                        summary=(
                            f"Method '{method_name}' uses a descriptive NOSONAR comment on the signature; "
                            "use bare // NOSONAR on method-level generic suppressions."
                        ),
                        line=descriptive_line,
                        suggestion=_BARE_METHOD_NOSONAR,
                    )
                )

        return violations
