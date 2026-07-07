from __future__ import annotations

import re

from validator.java.ast import iter_variable_declarations
from validator.java.context import JavaFileContext
from validator.java.rules.base import JavaRule, RuleViolation
from validator.java.rules.naming._support import NAMING_SUGGESTION

_UPPER_SNAKE_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*$")


class ConstantUpperSnakeCaseRule(JavaRule):
    @property
    def check_id(self) -> str:
        return "java-naming-constant-upper-snake"

    def apply(self, context: JavaFileContext) -> list[RuleViolation]:
        violations: list[RuleViolation] = []

        for variable in iter_variable_declarations(context):
            if not variable.is_constant:
                continue
            if _UPPER_SNAKE_PATTERN.fullmatch(variable.name):
                continue
            violations.append(
                RuleViolation(
                    summary=f"Constant '{variable.name}' should use UPPER_SNAKE_CASE.",
                    line=variable.line,
                    suggestion=NAMING_SUGGESTION,
                )
            )

        return violations
