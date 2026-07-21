from __future__ import annotations

from validator.java.context import JavaFileContext
from validator.java.rules.base import JavaRule, RuleViolation
from validator.java.rules.style._lombok import lombok_constructor_candidates


class LombokRequiredArgsConstructorRule(JavaRule):
    @property
    def check_id(self) -> str:
        return "java-lombok-required-args-constructor"

    def apply(self, context: JavaFileContext) -> list[RuleViolation]:
        return [
            RuleViolation(
                summary=(
                    f"Constructor of '{candidate.class_name}' only assigns required fields; "
                    "replace it with Lombok @RequiredArgsConstructor."
                ),
                line=candidate.constructor.start_point[0] + 1,
                suggestion="Use @RequiredArgsConstructor with an explicit access level when needed.",
            )
            for candidate in lombok_constructor_candidates(context)
        ]
