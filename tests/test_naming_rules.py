from __future__ import annotations

from pathlib import Path

import pytest

from tests.conftest import FIXTURES_DIR, violation_summaries

BAD_METHODS = FIXTURES_DIR / "BadMethodNamesSample.java"
BAD_VARIABLES = FIXTURES_DIR / "BadVariableNamesSample.java"
CLEAN = FIXTURES_DIR / "CleanService.java"


def test_clean_service_has_no_naming_violations(analyzer):
    findings = analyzer.analyze_file(CLEAN)
    naming = [f for f in findings if f.check.startswith("java-naming")]
    assert naming == []


def test_map_style_method_is_flagged(analyzer):
    summaries = violation_summaries(analyzer, "BadMethodNamesSample.java", "java-naming-method-map-style")
    assert any("statusByWaybill" in summary for summary in summaries)


def test_bare_participle_method_is_flagged(analyzer):
    summaries = violation_summaries(analyzer, "BadMethodNamesSample.java", "java-naming-method-bare-participle")
    assert any("distinctShipments" in summary for summary in summaries)


def test_missing_verb_prefix_methods_are_flagged(analyzer):
    summaries = violation_summaries(analyzer, "BadMethodNamesSample.java", "java-naming-method-verb-prefix")
    assert any("synchronizeStatuses" in summary for summary in summaries)
    assert any("empty" in summary for summary in summaries)


@pytest.mark.parametrize(
    ("fixture_name", "expected_fragment"),
    [
        ("BadVariableNamesSample.java", "shipmentList"),
        ("BadVariableNamesSample.java", "statusMap"),
        ("BadVariableNamesSample.java", "waybillList"),
    ],
)
def test_collection_type_in_variable_name(analyzer, fixture_name, expected_fragment):
    summaries = violation_summaries(analyzer, fixture_name, "java-naming-variable-collection-type")
    assert any(expected_fragment in summary for summary in summaries)


def test_hungarian_notation_is_flagged(analyzer):
    summaries = violation_summaries(analyzer, "BadVariableNamesSample.java", "java-naming-variable-hungarian")
    assert any("strCustomerName" in summary for summary in summaries)
    assert any("intCount" in summary for summary in summaries)


def test_constant_upper_snake_case_is_enforced(analyzer):
    summaries = violation_summaries(analyzer, "BadVariableNamesSample.java", "java-naming-constant-upper-snake")
    assert any("defaultComparator" in summary for summary in summaries)


def test_value_by_key_variable_is_allowed(analyzer):
    findings = analyzer.analyze_file(BAD_VARIABLES)
    collection_findings = [
        f for f in findings if f.check == "java-naming-variable-collection-type" and "valueByWaybill" in f.summary
    ]
    assert collection_findings == []


def test_domain_mapping_word_does_not_embed_collection_type(analyzer):
    findings = analyzer.analyze_file(BAD_VARIABLES)
    collection_findings = [
        f
        for f in findings
        if f.check == "java-naming-variable-collection-type" and "shipmentStatusMappingByRawStatus" in f.summary
    ]
    assert collection_findings == []
