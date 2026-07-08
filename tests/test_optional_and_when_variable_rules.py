from __future__ import annotations

from tests.conftest import FIXTURES_DIR, violation_summaries

OPTIONAL_FIXTURE = FIXTURES_DIR / "BadOptionalLocalVariableSample.java"
WHEN_FIXTURE = FIXTURES_DIR / "BadTestWhenVariableSample.java"
CLEAN = FIXTURES_DIR / "CleanService.java"


def test_optional_local_variable_without_prefix_is_flagged(analyzer):
    summaries = violation_summaries(
        analyzer,
        "BadOptionalLocalVariableSample.java",
        "java-naming-local-variable-optional-prefix",
    )
    assert any("waybill" in summary for summary in summaries)
    assert all("optionalWaybill" not in summary for summary in summaries)


def test_optional_field_is_not_flagged(analyzer):
    findings = analyzer.analyze_file(OPTIONAL_FIXTURE)
    optional_prefix_findings = [
        finding
        for finding in findings
        if finding.check == "java-naming-local-variable-optional-prefix"
        and "optionalField" in finding.summary
    ]
    assert optional_prefix_findings == []


def test_clean_service_has_no_optional_prefix_violations(analyzer):
    summaries = violation_summaries(analyzer, "CleanService.java", "java-naming-local-variable-optional-prefix")
    assert summaries == []


def test_generic_when_variable_is_flagged(analyzer):
    summaries = violation_summaries(
        analyzer,
        "BadTestWhenVariableSample.java",
        "java-testing-when-generic-variable",
    )
    assert any("result" in summary for summary in summaries)
    assert any("checkStatus_GivenWaybill_WhenChecked_ThenReturnsStatus" in summary for summary in summaries)


def test_descriptive_when_variable_is_allowed(analyzer):
    summaries = violation_summaries(
        analyzer,
        "BadTestWhenVariableSample.java",
        "java-testing-when-generic-variable",
    )
    assert all("shipmentStatus" not in summary for summary in summaries)


def test_test_without_when_section_is_ignored(analyzer):
    summaries = violation_summaries(
        analyzer,
        "BadTestWhenVariableSample.java",
        "java-testing-when-generic-variable",
    )
    assert all("checkStatusWithoutSections" not in summary for summary in summaries)
