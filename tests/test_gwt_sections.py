from __future__ import annotations

from validator.java.analyzer import JavaAnalyzer
from validator.java.rules.testing.gwt_sections import TestGwtSectionsRule

CHECK_ID = "java-testing-gwt-sections"


def _findings(source: str):
    analyzer = JavaAnalyzer(rules=[TestGwtSectionsRule()])
    return [
        finding
        for finding in analyzer.analyze_source("SampleTest.java", source)
        if finding.check == CHECK_ID
    ]


def test_flags_missing_duplicate_and_out_of_order_required_sections():
    source = """
class SampleTest {
    @Test
    void execute_GivenMissingWhen_ThenReturnsValue() {
        // GIVEN
        Subject subject = new Subject();
        // THEN
        assertThat(subject).isNotNull();
    }

    @Test
    void execute_GivenDuplicate_WhenCalled_ThenReturnsValue() {
        // GIVEN
        Subject subject = new Subject();
        // WHEN
        subject.execute();
        // WHEN
        subject.executeAgain();
        // THEN
        assertThat(subject).isNotNull();
    }

    @Test
    void execute_WhenCalled_GivenOutOfOrder_ThenReturnsValue() {
        // WHEN
        subject.execute();
        // GIVEN
        Subject subject = new Subject();
        // THEN
        assertThat(subject).isNotNull();
    }
}
"""

    findings = _findings(source)

    assert len(findings) == 3
    assert all("exactly one // WHEN and // THEN" in finding.summary for finding in findings)


def test_allows_non_empty_given_when_then_sections():
    source = """
class SampleTest {
    @Test
    void execute_GivenInput_WhenCalled_ThenReturnsValue() {
        // GIVEN
        Subject subject = new Subject();
        // WHEN
        String value = subject.execute();
        // THEN
        assertThat(value).isEqualTo("value");
    }
}
"""

    assert _findings(source) == []


def test_allows_omitted_given_when_no_setup_precedes_when():
    source = """
class SampleTest {
    @Test
    void execute_WhenCalled_ThenReturnsValue() {
        // WHEN
        String value = subject.execute();
        // THEN
        assertThat(value).isEqualTo("value");
    }
}
"""

    assert _findings(source) == []


def test_flags_each_empty_section_at_its_marker():
    source = """
class SampleTest {
    @Test
    void execute_GivenEmpty_WhenCalled_ThenReturnsValue() {
        // GIVEN
        // setup belongs here
        // WHEN
        subject.execute();
        // THEN
        assertThat(subject).isNotNull();
    }

    @Test
    void execute_GivenInput_WhenEmpty_ThenReturnsValue() {
        // GIVEN
        Subject subject = new Subject();
        // WHEN
        // action belongs here
        // THEN
        assertThat(subject).isNotNull();
    }

    @Test
    void execute_GivenInput_WhenCalled_ThenEmpty() {
        // GIVEN
        Subject subject = new Subject();
        // WHEN
        subject.execute();
        // THEN
        // assertion belongs here
    }
}
"""

    findings = _findings(source)

    assert len(findings) == 3
    assert [finding.line for finding in findings] == [5, 17, 29]
    assert "empty // GIVEN section" in findings[0].summary
    assert "empty // WHEN section" in findings[1].summary
    assert "empty // THEN section" in findings[2].summary


def test_flags_setup_before_when_when_given_is_omitted():
    source = """
class SampleTest {
    @Test
    void execute_GivenInput_WhenCalled_ThenReturnsValue() {
        Subject subject = new Subject();
        // WHEN
        String value = subject.execute();
        // THEN
        assertThat(value).isEqualTo("value");
    }
}
"""

    findings = _findings(source)

    assert len(findings) == 1
    assert findings[0].line == 5
    assert "without a // GIVEN section" in findings[0].summary
    assert "Add // GIVEN before the setup" in findings[0].summary


def test_empty_given_suggests_extracting_inline_when_arguments():
    source = """
class SampleTest {
    @Test
    void find_GivenMissingCode_WhenCalled_ThenReturnsValue() {
        // GIVEN
        // WHEN
        String value = subject.find("missing");
        // THEN
        assertThat(value).isEmpty();
    }
}
"""

    findings = _findings(source)

    assert len(findings) == 1
    assert "inline constructor or method arguments" in findings[0].suggestion
    assert "remove // GIVEN only when no setup or inputs exist" in findings[0].suggestion
    assert findings[0].suggestion in findings[0].summary


def test_reported_exception_shape_suggests_filling_given_and_when():
    source = """
class SampleTest {
    @Test
    void create_GivenInvalidSize_WhenCalled_ThenThrows() {
        // GIVEN

        // WHEN
        // THEN
        assertThatIllegalArgumentException()
            .isThrownBy(() -> new SampleRule(repository, 0))
            .withMessageContaining("size must be positive");
    }
}
"""

    findings = _findings(source)

    assert len(findings) == 2
    assert "inline constructor or method arguments" in findings[0].suggestion
    assert "Move the tested action into // WHEN" in findings[1].suggestion
    assert all(finding.suggestion in finding.summary for finding in findings)


def test_empty_given_uses_fallback_when_when_has_no_extractable_arguments():
    source = """
class SampleTest {
    @Test
    void refresh_WhenCalled_ThenCompletes() {
        // GIVEN
        // WHEN
        subject.refresh();
        // THEN
        assertThat(subject).isNotNull();
    }
}
"""

    findings = _findings(source)

    assert len(findings) == 1
    assert findings[0].suggestion.startswith("Fill // GIVEN")
