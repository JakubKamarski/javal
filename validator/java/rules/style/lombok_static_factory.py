from __future__ import annotations

from validator.java.context import JavaFileContext
from validator.java.rules.base import JavaRule, RuleViolation
from validator.java.rules.style._lombok import (
    is_direct_static_factory,
    lombok_constructor_candidates,
)


class LombokStaticFactoryRule(JavaRule):
    @property
    def check_id(self) -> str:
        return "java-lombok-static-factory"

    def apply(self, context: JavaFileContext) -> list[RuleViolation]:
        violations: list[RuleViolation] = []
        for candidate in lombok_constructor_candidates(context):
            class_body = candidate.constructor.parent
            if class_body.type != "class_body":
                continue
            for method in (child for child in class_body.children if child.type == "method_declaration"):
                if not is_direct_static_factory(
                    context,
                    candidate.class_name,
                    method,
                    candidate.parameter_names,
                ):
                    continue
                method_name = next(
                    (context.text(child) for child in method.children if child.type == "identifier"),
                    "factory",
                )
                violations.append(
                    RuleViolation(
                        summary=(
                            f"Static factory '{method_name}' only delegates to the constructor; "
                            "generate it with Lombok @RequiredArgsConstructor(staticName = ...)."
                        ),
                        line=method.start_point[0] + 1,
                        suggestion=(
                            f'Use @RequiredArgsConstructor(staticName = "{method_name}") and remove '
                            "the delegating factory method."
                        ),
                    )
                )
        return violations
