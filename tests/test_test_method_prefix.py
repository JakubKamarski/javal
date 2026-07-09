from __future__ import annotations

from tests.conftest import violation_summaries

CHECK_ID = "java-testing-test-method-prefix"
FIXTURE = "BadTestMethodPrefixSampleTest.java"


def test_bad_test_method_prefix_is_flagged(analyzer):
    summaries = violation_summaries(analyzer, FIXTURE, CHECK_ID)
    assert any("shouldFindAllByShipmentIdInWithShipmentFetched" in summary for summary in summaries)
    assert any("findAllByShipmentIdIn" in summary for summary in summaries)


def test_valid_test_method_prefix_is_allowed(analyzer):
    summaries = violation_summaries(analyzer, FIXTURE, CHECK_ID)
    assert all("findAllByShipmentIdIn_WithShipmentFetched" not in summary for summary in summaries)


def test_test_without_when_section_is_ignored(analyzer):
    summaries = violation_summaries(analyzer, FIXTURE, CHECK_ID)
    assert all("checkStatusWithoutSections" not in summary for summary in summaries)
