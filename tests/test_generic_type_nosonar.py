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
    assert not any("GoodMethodGenericNosonarSample" in finding.summary for finding in findings)


def test_nosonar_on_header_suppresses_finding(analyzer):
    findings = findings_for(analyzer, "GenericTypeNosonarSample.java", "java-sonar-generic-type-nosonar")
    assert findings == []


def test_method_level_missing_nosonar_is_flagged(analyzer):
    summaries = violation_summaries(
        analyzer,
        "BadGenericMethodNosonarSample.java",
        "java-sonar-generic-type-nosonar",
    )
    assert any("createNoOp" in summary for summary in summaries)
    assert any("run" in summary for summary in summaries)


def test_class_header_nosonar_does_not_suppress_method_level_finding(analyzer):
    summaries = violation_summaries(
        analyzer,
        "BadGenericMethodNosonarSample.java",
        "java-sonar-generic-type-nosonar",
    )
    assert any("BadGenericMethodNosonarSample" not in summary and "createNoOp" in summary for summary in summaries)


def test_descriptive_method_nosonar_is_flagged(analyzer):
    summaries = violation_summaries(
        analyzer,
        "BadGenericMethodNosonarSample.java",
        "java-sonar-generic-type-nosonar",
    )
    assert any("descriptive NOSONAR comment on the signature" in summary for summary in summaries)


def test_standard_method_generic_does_not_require_nosonar(analyzer):
    findings = findings_for(analyzer, "BadGenericMethodNosonarSample.java", "java-sonar-generic-type-nosonar")
    assert not any("GoodStandardMethodGenericSample" in finding.summary for finding in findings)
    assert not any("identity" in finding.summary for finding in findings)
