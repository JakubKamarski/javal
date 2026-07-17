from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from validator.java.source_paths import (
    IT_SUFFIX,
    UNIT_TEST_SUFFIX,
    integration_test_base_name,
    is_main_source_file,
    is_test_source_file,
    unit_test_base_name,
)

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


def required_test_exists(
    main_source: Path, class_name: str, requirement: SubjectTestRequirement
) -> bool:
    test_class_name = expected_test_class_name(class_name, requirement)
    expected_test_path = resolve_expected_test_path(main_source, test_class_name)
    if expected_test_path.is_file():
        return True
    if requirement.test_suffix == IT_SUFFIX:
        return _has_integration_test_variant(expected_test_path.parent, class_name)
    return False


def _has_integration_test_variant(test_dir: Path, class_name: str) -> bool:
    if not test_dir.is_dir():
        return False
    for candidate in test_dir.glob(f"{class_name}*{IT_SUFFIX}.java"):
        if candidate.is_file():
            return True
    return False


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
