from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from validator.java.context import JavaFileContext
from validator.report import Finding, Severity


@dataclass(frozen=True)
class RuleViolation:
    summary: str
    line: int
    details: str = ""
    suggestion: str = ""
    severity: Severity = "warning"

    def to_finding(self, check_id: str, file_path: str) -> Finding:
        return Finding(
            severity=self.severity,
            check=check_id,
            summary=self.summary,
            file=file_path,
            line=self.line,
            details=self.details,
            suggestion=self.suggestion,
        )


class JavaRule(ABC):
    @property
    @abstractmethod
    def check_id(self) -> str:
        """Stable identifier used in validation reports."""

    @abstractmethod
    def apply(self, context: JavaFileContext) -> list[RuleViolation]:
        """Inspect one Java file and return zero or more violations."""
