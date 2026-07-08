from __future__ import annotations

from validator.java.ast import iter_var_declarations
from validator.java.context import JavaFileContext
from validator.java.rules.base import JavaRule, RuleViolation

_STYLE_SUGGESTION = "Declare an explicit type instead of 'var'; see agents/rule-java.md."


class LocalVariableNoVarRule(JavaRule):
    @property
    def check_id(self) -> str:
        return "java-local-variable-no-var"

    def apply(self, context: JavaFileContext) -> list[RuleViolation]:
        violations: list[RuleViolation] = []

        for declaration in iter_var_declarations(context):
            violations.append(
                RuleViolation(
                    summary=(
                        f"Variable '{declaration.name}' uses 'var'; "
                        "declare an explicit local variable type."
                    ),
                    line=declaration.line,
                    suggestion=_STYLE_SUGGESTION,
                )
            )

        return violations
