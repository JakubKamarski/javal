from __future__ import annotations

from validator.java.ast import iter_method_declarations
from validator.java.context import JavaFileContext
from validator.java.rules.base import JavaRule, RuleViolation
from validator.java.rules.naming._support import (
    NAMING_SUGGESTION,
    STANDARD_METHOD_NAMES,
    starts_with_allowed_verb,
)


class MethodVerbPrefixRule(JavaRule):
    @property
    def check_id(self) -> str:
        return "java-naming-method-verb-prefix"

    def apply(self, context: JavaFileContext) -> list[RuleViolation]:
        violations: list[RuleViolation] = []

        for method in iter_method_declarations(context):
            if method.is_configuration_bean:
                continue
            if method.is_static_factory:
                continue
            if method.is_method_source_provider:
                continue
            if method.is_override:
                continue
            if method.is_test:
                continue
            if method.is_lifecycle:
                continue
            if method.is_record_accessor:
                continue
            if method.name in STANDARD_METHOD_NAMES:
                continue
            if starts_with_allowed_verb(method.name):
                continue
            violations.append(
                RuleViolation(
                    summary=(
                        f"Method '{method.name}' does not start with a required action verb."
                    ),
                    line=method.line,
                    suggestion=NAMING_SUGGESTION,
                )
            )

        return violations
