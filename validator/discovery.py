from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

SKIP_DIRS = frozenset({".git", "target", "build", "out", ".idea", "node_modules"})


def should_skip_path(path: Path) -> bool:
    return any(part in SKIP_DIRS for part in path.parts)


def discover_files(
    root: Path,
    *,
    pattern: str,
    predicate: Callable[[Path], bool] | None = None,
) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob(pattern):
        if should_skip_path(path):
            continue
        if predicate is not None and not predicate(path):
            continue
        files.append(path)
    return sorted(files)
