from __future__ import annotations

from pathlib import Path
from typing import Literal

from validator.java.context import JavaFileContext
from validator.java.source_paths import (
    is_main_source_file,
    is_production_source_file,
    is_test_source_file,
)

FileApplicability = Literal["any", "test", "main", "production"]


def matches_file_applicability(path: Path, kind: FileApplicability) -> bool:
    if kind == "any":
        return True
    if kind == "test":
        return is_test_source_file(path)
    if kind == "main":
        return is_main_source_file(path)
    if kind == "production":
        return is_production_source_file(path)
    return True


def filter_paths(paths: list[Path], kind: FileApplicability) -> list[Path]:
    if kind == "any":
        return list(paths)
    return [path for path in paths if matches_file_applicability(path, kind)]


def context_for(
    path: Path,
    contexts: dict[str, JavaFileContext] | None,
) -> JavaFileContext:
    absolute_path = str(path.resolve())
    if contexts is not None and absolute_path in contexts:
        return contexts[absolute_path]
    return JavaFileContext.from_path(path)
