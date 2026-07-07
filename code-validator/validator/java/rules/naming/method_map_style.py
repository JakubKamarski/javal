from __future__ import annotations

import re

from validator.java.ast import iter_method_declarations
from validator.java.context import JavaFileContext
from validator.java.rules.base import JavaRule, RuleViolation
from validator.java.rules.naming._support import NAMING_SUGGESTION, starts_with_allowed_verb

_MAP_STYLE_PATTERN = re.compile(r"^[a-z][a-zA-Z0-9]*By[A-Z]")


class MethodMapStyleNameRule(JavaRule):
    @property
    def check_id(self) -> str:
        return "java-naming-method-map-style"

    def apply(self, context: JavaFileContext) -> list[RuleViolation]:
        violations: list[RuleViolation] = []

        for method in iter_method_declarations(context):
            if not _MAP_STYLE_PATTERN.match(method.name):
                continue
            if starts_with_allowed_verb(method.name):
                continue
            violations.append(
                RuleViolation(
                    summary=(
                        f"Method '{method.name}' looks like map-style naming; "
                        "methods must lead with a verb (e.g. retrieveStatusByWaybill)."
                    ),
                    line=method.line,
                    suggestion=NAMING_SUGGESTION,
                )
            )

        return violations
