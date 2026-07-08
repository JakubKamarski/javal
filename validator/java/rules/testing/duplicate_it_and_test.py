from __future__ import annotations

from pathlib import Path

from validator.java.rules.base import TreeJavaRule
from validator.report import Finding

UNIT_TEST_SUFFIX = "Test"
IT_SUFFIX = "IT"


def unit_test_base_name(stem: str) -> str | None:
    if not stem.endswith(UNIT_TEST_SUFFIX):
        return None
    if stem.endswith(f"{IT_SUFFIX}{UNIT_TEST_SUFFIX}"):
        return None
    base = stem[: -len(UNIT_TEST_SUFFIX)]
    return base or None


def integration_test_base_name(stem: str) -> str | None:
    if not stem.endswith(IT_SUFFIX):
        return None
    base = stem[: -len(IT_SUFFIX)]
    return base or None


class DuplicateItAndTestRule(TreeJavaRule):
    @property
    def check_id(self) -> str:
        return "java-testing-duplicate-it-and-test"

    def apply_tree(self, java_files: list[Path], scope=None) -> list[Finding]:
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
        for key, unit_path in unit_tests.items():
            it_path = integration_tests.get(key)
            if it_path is None:
                continue

            base_name = key[1]
            findings.append(
                Finding(
                    severity="warning",
                    check=self.check_id,
                    summary=(
                        f"Subject '{base_name}' has both unit test and integration test files"
                    ),
                    file=str(unit_path.resolve()),
                    line=1,
                    details=f"Found {unit_path.name} and {it_path.name}.",
                    suggestion=(
                        f"Merge all tests into a single integration test file ({it_path.name})."
                    ),
                )
            )

        return findings
