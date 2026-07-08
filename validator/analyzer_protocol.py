from __future__ import annotations

from pathlib import Path
from typing import Protocol

from validator.git_scope import TaskScope
from validator.report import Report


class Analyzer(Protocol):
    def analyze(self, target: Path, scope: TaskScope | None = None) -> Report:
        """Run checks against a repository tree, optionally limited to task scope."""
