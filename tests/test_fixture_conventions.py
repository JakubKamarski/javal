from __future__ import annotations

from pathlib import Path

from tests.sanitization_patterns import BANNED_REPO_PATTERNS

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES_DIR = REPO_ROOT / "fixtures"


def _iter_fixture_files() -> list[Path]:
    return [path for path in FIXTURES_DIR.rglob("*") if path.is_file()]


def _collect_violations(paths: list[Path]) -> list[str]:
    violations: list[str] = []
    for path in paths:
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        relative = path.relative_to(REPO_ROOT)
        for pattern, reason in BANNED_REPO_PATTERNS:
            if pattern.search(content):
                violations.append(f"{relative}: contains {reason}")
    return violations


def test_fixtures_use_minimal_anonymized_data():
    assert _collect_violations(_iter_fixture_files()) == []
