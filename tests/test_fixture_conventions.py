from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES_DIR = REPO_ROOT / "fixtures"

BANNED_FIXTURE_PATTERNS: tuple[re.Pattern[str], str] = (
    (re.compile(r"/Users/"), "absolute filesystem path"),
    (re.compile(r"\bworktrees/"), "worktree path"),
    (re.compile(r"\bprojects/locus-"), "real repository path"),
    (re.compile(r"\blocus-fc-"), "real module name"),
    (re.compile(r"\bFanCourier\b"), "real domain name"),
    (re.compile(r"\bZasilkovna\b"), "real domain name"),
    (re.compile(r"\bWB-[A-Z0-9-]+\b"), "production-style waybill test data"),
    (re.compile(r"com\.lpp\.locus"), "real package name"),
    (re.compile(r"wiremock|WireMock", re.IGNORECASE), "production integration stack"),
)


def _iter_fixture_files() -> list[Path]:
    return [path for path in FIXTURES_DIR.rglob("*") if path.is_file()]


def test_fixtures_use_minimal_anonymized_data():
    violations: list[str] = []
    for path in _iter_fixture_files():
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        relative = path.relative_to(REPO_ROOT)
        for pattern, reason in BANNED_FIXTURE_PATTERNS:
            if pattern.search(content):
                violations.append(f"{relative}: contains {reason}")
    assert violations == []
