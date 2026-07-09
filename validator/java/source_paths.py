from __future__ import annotations

from pathlib import Path

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


def is_test_source_file(path: Path) -> bool:
    parts = path.resolve().parts
    if "src" in parts and "test" in parts and "java" in parts:
        return True
    stem = path.stem
    return unit_test_base_name(stem) is not None or integration_test_base_name(stem) is not None


def is_main_source_file(path: Path) -> bool:
    parts = path.resolve().parts
    return "src" in parts and "main" in parts and "java" in parts


def is_production_source_file(path: Path) -> bool:
    if is_test_source_file(path):
        return False
    if is_main_source_file(path):
        return True
    return "src" not in path.resolve().parts
