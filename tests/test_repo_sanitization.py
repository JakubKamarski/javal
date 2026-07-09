from __future__ import annotations

from pathlib import Path

from tests.sanitization_patterns import BANNED_REPO_PATTERNS

REPO_ROOT = Path(__file__).resolve().parents[1]

SCAN_PATHS = (
    REPO_ROOT / "README.md",
    REPO_ROOT / "validate.py",
    REPO_ROOT / "tests",
    REPO_ROOT / "validator",
)

EXCLUDED_RELATIVE_PATHS = frozenset(
    {
        "tests/sanitization_patterns.py",
        "tests/test_fixture_conventions.py",
        "tests/test_repo_sanitization.py",
    }
)


def _iter_scanned_files() -> list[Path]:
    files: list[Path] = []
    for root in SCAN_PATHS:
        if root.is_file():
            files.append(root)
            continue
        files.extend(path for path in root.rglob("*") if path.is_file())
    return files


def test_repo_content_is_sanitized():
    violations: list[str] = []
    for path in _iter_scanned_files():
        relative = path.relative_to(REPO_ROOT).as_posix()
        if relative in EXCLUDED_RELATIVE_PATHS:
            continue
        if path.suffix not in {".py", ".md"}:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern, reason in BANNED_REPO_PATTERNS:
            if pattern.search(content):
                violations.append(f"{relative}: contains {reason}")
    assert violations == []
