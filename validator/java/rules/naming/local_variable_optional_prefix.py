from __future__ import annotations

import re

from validator.java.ast import is_optional_type, iter_local_variable_declarations
from validator.java.context import JavaFileContext
from validator.java.rules.base import JavaRule, RuleViolation
from validator.java.rules.naming._support import NAMING_SUGGESTION

_OPTIONAL_PREFIX_PATTERN = re.compile(r"^optional[A-Z]")


class LocalVariableOptionalPrefixRule(JavaRule):
    @property
    def check_id(self) -> str:
        return "java-naming-local-variable-optional-prefix"

    def apply(self, context: JavaFileContext) -> list[RuleViolation]:
        violations: list[RuleViolation] = []

        for variable in iter_local_variable_declarations(context):
            if not is_optional_type(variable.type_text):
                continue
            if _OPTIONAL_PREFIX_PATTERN.match(variable.name):
                continue
            violations.append(
                RuleViolation(
                    summary=(
                        f"Local variable '{variable.name}' has type '{variable.type_text}' "
                        "but lacks the 'optional' prefix."
                    ),
                    line=variable.line,
                    suggestion=NAMING_SUGGESTION,
                )
            )

        return violations
