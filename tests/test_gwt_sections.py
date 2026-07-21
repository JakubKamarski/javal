from __future__ import annotations

CHECK_ID = "java-testing-gwt-sections"


def test_flags_missing_duplicate_and_out_of_order_gwt_sections(analyzer):
    source = """
import org.junit.jupiter.api.Test;

class SampleTest {
    @Test
    void execute_GivenInput_WhenCalled_ThenReturnsValue() {
        // WHEN
        subject.execute();
        // THEN
    }

    @Test
    void execute_GivenDuplicate_WhenCalled_ThenReturnsValue() {
        // GIVEN
        Subject subject = new Subject();
        // WHEN
        subject.execute();
        // WHEN
        subject.execute();
        // THEN
    }

    @Test
    void execute_GivenOutOfOrder_WhenCalled_ThenReturnsValue() {
        // WHEN
        subject.execute();
        // GIVEN
        Subject subject = new Subject();
        // THEN
    }
}
"""

    findings = analyzer.analyze_source("SampleTest.java", source)
    summaries = [finding.summary for finding in findings if finding.check == CHECK_ID]

    assert len(summaries) == 3
    assert any("GivenInput" in summary for summary in summaries)
    assert any("GivenDuplicate" in summary for summary in summaries)
    assert any("GivenOutOfOrder" in summary for summary in summaries)


def test_allows_exactly_one_ordered_gwt_section_set(analyzer):
    source = """
import org.junit.jupiter.api.Test;

class SampleTest {
    @Test
    void execute_GivenInput_WhenCalled_ThenReturnsValue() {
        // GIVEN
        Subject subject = new Subject();
        // WHEN
        subject.execute();
        // THEN
    }
}
"""

    findings = analyzer.analyze_source("SampleTest.java", source)

    assert not any(finding.check == CHECK_ID for finding in findings)
