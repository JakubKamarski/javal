from __future__ import annotations

from validator.java.ast import collect_identifier_usages, iter_import_declarations
from validator.java.context import JavaFileContext
from validator.java.rules.base import JavaRule, RuleViolation


class UnusedImportRule(JavaRule):
    @property
    def check_id(self) -> str:
        return "unused-imports"

    def apply(self, context: JavaFileContext) -> list[RuleViolation]:
        usages = collect_identifier_usages(context)
        violations: list[RuleViolation] = []

        for import_decl in iter_import_declarations(context):
            if import_decl.symbol in usages:
                continue
            violations.append(
                RuleViolation(
                    summary=f"Unused import '{import_decl.symbol}'",
                    line=import_decl.line,
                    details=import_decl.text,
                    suggestion=(
                        f"Remove the unused import or reference '{import_decl.symbol}' in this file."
                    ),
                )
            )

        return violations
