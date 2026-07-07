from __future__ import annotations

from validator.java.ast import iter_variable_declarations
from validator.java.context import JavaFileContext
from validator.java.rules.base import JavaRule, RuleViolation
from validator.java.rules.naming._support import NAMING_SUGGESTION, embedded_collection_type_token


class VariableCollectionTypeInNameRule(JavaRule):
    @property
    def check_id(self) -> str:
        return "java-naming-variable-collection-type"

    def apply(self, context: JavaFileContext) -> list[RuleViolation]:
        violations: list[RuleViolation] = []

        for variable in iter_variable_declarations(context):
            if variable.is_constant:
                continue
            token = embedded_collection_type_token(variable.name)
            if token is None:
                continue
            violations.append(
                RuleViolation(
                    summary=(
                        f"Variable '{variable.name}' embeds collection type '{token}'; "
                        "use domain plural names or valueByKey pattern."
                    ),
                    line=variable.line,
                    suggestion=NAMING_SUGGESTION,
                )
            )

        return violations
