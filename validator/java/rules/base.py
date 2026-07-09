from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar, Literal

from validator.git_scope import TaskScope
from validator.java.context import JavaFileContext
from validator.java.rules.applicability import FileApplicability
from validator.report import Finding, Severity

TreeScopePolicy = Literal["task_changed", "global"]
RuleScope = Literal["file", "tree"]


@dataclass(frozen=True)
class RuleMeta:
    check_id: str
    category: str
    description: str
    scope: RuleScope
    tree_scope: TreeScopePolicy | None = None
    file_applicability: FileApplicability = "any"
    tree_file_applicability: FileApplicability = "any"


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
    file_applicability: ClassVar[FileApplicability] = "any"

    @property
    @abstractmethod
    def check_id(self) -> str:
        """Stable identifier used in validation reports."""

    @property
    def meta(self) -> RuleMeta:
        return RuleMeta(
            check_id=self.check_id,
            category="java",
            description=self.check_id,
            scope="file",
            file_applicability=self.file_applicability,
        )

    def applies_to(self, context: JavaFileContext) -> bool:
        del context
        return True

    @abstractmethod
    def apply(self, context: JavaFileContext) -> list[RuleViolation]:
        """Inspect one Java file and return zero or more violations."""


class TreeJavaRule(ABC):
    scope_policy: ClassVar[TreeScopePolicy] = "task_changed"
    tree_file_applicability: ClassVar[FileApplicability] = "any"

    @property
    @abstractmethod
    def check_id(self) -> str:
        """Stable identifier used in validation reports."""

    @property
    def meta(self) -> RuleMeta:
        return RuleMeta(
            check_id=self.check_id,
            category="java",
            description=self.check_id,
            scope="tree",
            tree_scope=self.scope_policy,
            tree_file_applicability=self.tree_file_applicability,
        )

    @abstractmethod
    def apply_tree(
        self,
        java_files: list[Path],
        scope: TaskScope | None = None,
        *,
        contexts: dict[str, JavaFileContext] | None = None,
    ) -> list[Finding]:
        """Inspect the Java tree and return zero or more findings."""
