from __future__ import annotations

import re

from validator.java.ast import iter_variable_declarations
from validator.java.context import JavaFileContext
from validator.java.rules.base import JavaRule, RuleViolation
from validator.java.rules.naming._support import NAMING_SUGGESTION

_HUNGARIAN_PATTERN = re.compile(r"^(str|int|bool|obj)[A-Z]")


class VariableHungarianNotationRule(JavaRule):
    @property
    def check_id(self) -> str:
        return "java-naming-variable-hungarian"

    def apply(self, context: JavaFileContext) -> list[RuleViolation]:
        violations: list[RuleViolation] = []

        for variable in iter_variable_declarations(context):
            if variable.is_constant:
                continue
            if not _HUNGARIAN_PATTERN.match(variable.name):
                continue
            violations.append(
                RuleViolation(
                    summary=(
                        f"Variable '{variable.name}' uses Hungarian notation; "
                        "use camelCase without type prefixes."
                    ),
                    line=variable.line,
                    suggestion=NAMING_SUGGESTION,
                )
            )

        return violations
