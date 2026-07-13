from __future__ import annotations

from tests.conftest import findings_for, violation_summaries


def test_explanatory_comments_are_flagged(analyzer):
    summaries = violation_summaries(analyzer, "BadCommentSample.java", "java-clean-code-comment")
    assert any("Explanatory comment" in summary for summary in summaries)
    assert len([summary for summary in summaries if "Explanatory comment" in summary]) >= 2


def test_orphan_todo_and_fixme_are_flagged(analyzer):
    summaries = violation_summaries(analyzer, "BadCommentSample.java", "java-clean-code-comment")
    assert any("Orphan TODO/FIXME" in summary for summary in summaries)
    assert len([summary for summary in summaries if "Orphan TODO/FIXME" in summary]) >= 2


def test_allowed_comments_are_not_flagged(analyzer):
    findings = findings_for(analyzer, "GoodCommentSample.java", "java-clean-code-comment")
    assert findings == []


def test_gwt_marker_with_trailing_text_is_allowed(analyzer):
    findings = findings_for(analyzer, "EmDashParseSample.java", "java-clean-code-comment")
    assert findings == []


def test_critical_comment_warning_requires_executor_decision(analyzer):
    findings = analyzer.analyze_source(
        "CriticalCommentSample.java",
        "class CriticalCommentSample {\n    // Local time is intentionally stored as UTC.\n    void synchronize() {}\n}\n",
    )

    comment_finding = next(finding for finding in findings if finding.check == "java-clean-code-comment")

    assert comment_finding.severity == "warning"
    assert "executor must explicitly decide" in comment_finding.suggestion
