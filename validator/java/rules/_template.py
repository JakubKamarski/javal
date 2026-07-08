"""Template for new javal Java rules — copy and adapt; do not register this module."""

from __future__ import annotations

from pathlib import Path

from validator.git_scope import TaskScope
from validator.java.context import JavaFileContext
from validator.java.rules.base import JavaRule, RuleViolation, TreeJavaRule
from validator.report import Finding


class ExampleFileRule(JavaRule):
    """Per-file rule: implement apply() and register in registry.default_java_rules()."""

    @property
    def check_id(self) -> str:
        return "example-file-rule"

    def apply(self, context: JavaFileContext) -> list[RuleViolation]:
        del context
        return []


class ExampleTreeRule(TreeJavaRule):
    """Repo-wide rule: set scope_policy and register in registry.default_tree_java_rules()."""

    scope_policy = "task_changed"  # or "global" for whole-repo scans

    @property
    def check_id(self) -> str:
        return "example-tree-rule"

    def apply_tree(
        self,
        java_files: list[Path],
        scope: TaskScope | None = None,
    ) -> list[Finding]:
        del java_files, scope
        return []
