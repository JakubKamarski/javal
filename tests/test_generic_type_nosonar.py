from __future__ import annotations

from tests.conftest import findings_for, violation_summaries


def test_non_standard_generic_type_without_nosonar_is_flagged(analyzer):
    summaries = violation_summaries(
        analyzer,
        "BadGenericTypeNosonarSample.java",
        "java-sonar-generic-type-nosonar",
    )
    assert any("BadGenericTypeNosonarSample" in summary for summary in summaries)
    assert any("BadGenericTypeNosonarInterface" in summary for summary in summaries)
    assert any("BadGenericTypeNosonarRecord" in summary for summary in summaries)
    assert any("BadMixedGenericTypeNosonarSample" in summary for summary in summaries)


def test_standard_generic_type_does_not_require_nosonar(analyzer):
    findings = findings_for(analyzer, "GenericTypeNosonarSample.java", "java-sonar-generic-type-nosonar")
    assert not any("StandardGenericTypeSample" in finding.summary for finding in findings)


def test_nosonar_on_header_suppresses_finding(analyzer):
    findings = findings_for(analyzer, "GenericTypeNosonarSample.java", "java-sonar-generic-type-nosonar")
    assert findings == []
