from __future__ import annotations

import subprocess
from pathlib import Path

from validator.java.rules.base import TreeJavaRule
from validator.java.rules.testing._support import (
    DUPLICATE_IT_AND_TEST_SUGGESTION_TEMPLATE,
    integration_test_base_name,
    unit_test_base_name,
)
from validator.report import Finding

__all__ = [
    "DuplicateItAndTestRule",
    "integration_test_base_name",
    "unit_test_base_name",
]


class DuplicateItAndTestRule(TreeJavaRule):
    scope_policy = "task_changed"
    tree_file_applicability = "test"

    @property
    def check_id(self) -> str:
        return "java-testing-duplicate-it-and-test"

    def apply_tree(
        self,
        java_files: list[Path],
        scope=None,
        *,
        contexts=None,
    ) -> list[Finding]:
        del contexts
        if scope is not None and not scope.commits:
            return []
        unit_tests: dict[tuple[Path, str], Path] = {}
        integration_tests: dict[tuple[Path, str], Path] = {}

        for path in java_files:
            parent = path.parent.resolve()
            unit_base = unit_test_base_name(path.stem)
            if unit_base is not None:
                unit_tests[(parent, unit_base)] = path
                continue

            it_base = integration_test_base_name(path.stem)
            if it_base is not None:
                integration_tests[(parent, it_base)] = path

        findings: list[Finding] = []
        repo_root = _repo_root(java_files)
        for key, unit_path in unit_tests.items():
            it_path = integration_tests.get(key)
            if it_path is None:
                continue

            introduced_path = _introduced_pair_path(repo_root, unit_path, it_path, scope)
            if scope is not None and introduced_path is None:
                continue

            base_name = key[1]
            findings.append(
                Finding(
                    severity="warning",
                    check=self.check_id,
                    summary=(
                        f"Subject '{base_name}' has both unit test and integration test files "
                        f"— merge all into {it_path.name}."
                    ),
                    file=str((introduced_path or unit_path).resolve()),
                    line=1,
                    details=f"Found {unit_path.name} and {it_path.name}.",
                    suggestion=DUPLICATE_IT_AND_TEST_SUGGESTION_TEMPLATE.format(
                        it_file=it_path.name,
                    ),
                )
            )

        return findings


def _repo_root(java_files: list[Path]) -> Path | None:
    if not java_files:
        return None
    result = subprocess.run(
        ["git", "-C", str(java_files[0].parent), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    return Path(result.stdout.strip()) if result.returncode == 0 else None


def _introduced_pair_path(
    repo_root: Path | None,
    unit_path: Path,
    it_path: Path,
    scope,
) -> Path | None:
    if scope is None:
        return None
    if repo_root is None:
        return None
    unit_relative = unit_path.resolve().relative_to(repo_root).as_posix()
    it_relative = it_path.resolve().relative_to(repo_root).as_posix()
    for commit, _file_changes in scope.commit_changed_lines:
        if _path_exists_at_revision(repo_root, f"{commit}^", unit_relative) and _path_exists_at_revision(repo_root, f"{commit}^", it_relative):
            continue
        if not (
            _path_exists_at_revision(repo_root, commit, unit_relative)
            and _path_exists_at_revision(repo_root, commit, it_relative)
        ):
            continue
        if not _path_exists_at_revision(repo_root, f"{commit}^", unit_relative):
            return unit_path
        return it_path
    return None


def _path_exists_at_revision(repo_root: Path, revision: str, relative_path: str) -> bool:
    return subprocess.run(
        ["git", "-C", str(repo_root), "cat-file", "-e", f"{revision}:{relative_path}"],
        capture_output=True,
        check=False,
    ).returncode == 0
