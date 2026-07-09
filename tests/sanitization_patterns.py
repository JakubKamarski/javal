from __future__ import annotations

import re

BANNED_REPO_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"/Users/"), "absolute filesystem path"),
    (re.compile(r"\bworktrees/"), "worktree path"),
    (re.compile(r"\bprojects/locus-"), "real repository path"),
    (re.compile(r"\blocus-fc-"), "real module name"),
    (re.compile(r"\blocus-common-"), "real module name"),
    (re.compile(r"\bPLOG-\d+"), "real task id"),
    (re.compile(r"\bSL-\d+"), "real task id"),
    (re.compile(r"\bFanCourier\b"), "real domain name"),
    (re.compile(r"\bZasilkovna\b"), "real domain name"),
    (re.compile(r"\bDpdBaltics\b"), "real domain name"),
    (re.compile(r"\bWB-[A-Z0-9-]+\b"), "production-style waybill test data"),
    (re.compile(r"com\.lpp\.locus"), "real package name"),
    (re.compile(r"wiremock|WireMock", re.IGNORECASE), "production integration stack"),
    (re.compile(r"\bPartitionThrottle\b"), "production class name"),
    (re.compile(r"\bShipmentStatusT\b"), "production-style generic name"),
    (re.compile(r"\bGroupKeyT\b"), "production-style generic name"),
    (re.compile(r"\bTrackableItemT\b"), "production-style generic name"),
)
