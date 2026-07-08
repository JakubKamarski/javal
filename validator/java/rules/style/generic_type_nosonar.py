from __future__ import annotations

from validator.java.ast.types import (
    declaration_header_line_numbers,
    declaration_simple_name,
    header_has_nosonar,
    is_standard_type_parameter_name,
    iter_generic_type_declarations,
)
from validator.java.context import JavaFileContext
from validator.java.rules.base import JavaRule, RuleViolation

_SINGULAR_NOSONAR = (
    "// NOSONAR: descriptive business generic name is clearer than a single-letter type parameter."
)
_PLURAL_NOSONAR = (
    "// NOSONAR: descriptive business generic names are clearer than single-letter type parameters."
)


class GenericTypeNosonarRule(JavaRule):
    @property
    def check_id(self) -> str:
        return "java-sonar-generic-type-nosonar"

    def apply(self, context: JavaFileContext) -> list[RuleViolation]:
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
