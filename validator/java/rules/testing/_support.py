from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

UNIT_TEST_SUFFIX = "Test"
IT_SUFFIX = "IT"

TESTING_SUGGESTION = "Add the required test class per agents/rule-testing.md."

DUPLICATE_IT_AND_TEST_SUGGESTION_TEMPLATE = (
    "Merge all tests into {it_file} and remove the unit test file "
    "(per agents/rule-testing.md)."
)


@dataclass(frozen=True)
class SubjectTestRequirement:
    subject_suffix: str
    test_suffix: str
    summary_template: str
    requires_public_class: bool = False
    requires_query_annotation: bool = False


SUBJECT_TEST_REQUIREMENTS: tuple[SubjectTestRequirement, ...] = (
    SubjectTestRequirement(
        subject_suffix="Facade",
        test_suffix=IT_SUFFIX,
        summary_template="Public facade '{subject}' requires integration test '{test_class}'.",
        requires_public_class=True,
    ),
    SubjectTestRequirement(
        subject_suffix="Scheduler",
        test_suffix=UNIT_TEST_SUFFIX,
        summary_template="Scheduler '{subject}' requires unit test '{test_class}'.",
    ),
    SubjectTestRequirement(
        subject_suffix="Listener",
        test_suffix=UNIT_TEST_SUFFIX,
        summary_template="Listener '{subject}' requires unit test '{test_class}'.",
    ),
    SubjectTestRequirement(
        subject_suffix="Mapper",
        test_suffix=UNIT_TEST_SUFFIX,
        summary_template="Mapper '{subject}' requires unit test '{test_class}'.",
    ),
    SubjectTestRequirement(
        subject_suffix="Service",
        test_suffix=IT_SUFFIX,
        summary_template="Service '{subject}' requires integration test '{test_class}'.",
    ),
    SubjectTestRequirement(
        subject_suffix="Repository",
        test_suffix=IT_SUFFIX,
        summary_template="Repository '{subject}' with @Query requires integration test '{test_class}'.",
        requires_query_annotation=True,
    ),
)

EXCLUDED_SUBJECT_SUFFIXES = ("Controller",)


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


def subject_test_requirement(class_name: str) -> SubjectTestRequirement | None:
    if any(class_name.endswith(suffix) for suffix in EXCLUDED_SUBJECT_SUFFIXES):
        return None

    for requirement in SUBJECT_TEST_REQUIREMENTS:
        if class_name.endswith(requirement.subject_suffix):
            return requirement
    return None


def expected_test_class_name(class_name: str, requirement: SubjectTestRequirement) -> str:
    return f"{class_name}{requirement.test_suffix}"


def resolve_expected_test_path(main_source: Path, test_class_name: str) -> Path:
    mapped = _map_main_source_to_test_source(main_source, test_class_name)
    if mapped is not None:
        return mapped
    return main_source.parent / f"{test_class_name}.java"


def _map_main_source_to_test_source(main_source: Path, test_class_name: str) -> Path | None:
    resolved = main_source.resolve()
    parts = list(resolved.parts)
    try:
        src_index = parts.index("src")
    except ValueError:
        return None

    if src_index + 2 >= len(parts):
        return None
    if parts[src_index + 1] != "main" or parts[src_index + 2] != "java":
        return None

    parts[src_index + 1] = "test"
    parts[-1] = f"{test_class_name}.java"
    return Path(*parts)
