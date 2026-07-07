from __future__ import annotations

from validator.java.ast import iter_method_declarations
from validator.java.context import JavaFileContext
from validator.java.rules.base import JavaRule, RuleViolation
from validator.java.rules.naming._support import BARE_PARTICIPLE_PREFIXES, NAMING_SUGGESTION


class MethodBareParticipleRule(JavaRule):
    @property
    def check_id(self) -> str:
        return "java-naming-method-bare-participle"

    def apply(self, context: JavaFileContext) -> list[RuleViolation]:
        violations: list[RuleViolation] = []

        for method in iter_method_declarations(context):
            for prefix in BARE_PARTICIPLE_PREFIXES:
                if not method.name.startswith(prefix):
                    continue
                violations.append(
                    RuleViolation(
                        summary=(
                            f"Method '{method.name}' starts with bare participle '{prefix}'; "
                            "use verb-first naming (e.g. filterDistinctShipments)."
                        ),
                        line=method.line,
                        suggestion=NAMING_SUGGESTION,
                    )
                )
                break

        return violations
