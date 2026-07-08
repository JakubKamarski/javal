from __future__ import annotations

from tests.conftest import FIXTURES_DIR, violation_summaries

VAR_SAMPLE = FIXTURES_DIR / "VarLocalVariableSample.java"


def test_var_local_variable_declarations_are_flagged(analyzer):
    summaries = violation_summaries(analyzer, "VarLocalVariableSample.java", "java-local-variable-no-var")
    assert any("shipments" in summary for summary in summaries)
    assert any("stream" in summary for summary in summaries)
    assert any("waybill" in summary for summary in summaries)
    assert len(summaries) == 3


def test_explicit_local_variable_types_are_allowed(analyzer):
    findings = analyzer.analyze_file(VAR_SAMPLE)
    var_findings = [finding for finding in findings if finding.check == "java-local-variable-no-var"]
    assert all(finding.line != 10 for finding in var_findings)


def test_clean_service_has_no_var_violations(analyzer):
    summaries = violation_summaries(analyzer, "CleanService.java", "java-local-variable-no-var")
    assert summaries == []
