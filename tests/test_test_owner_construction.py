from __future__ import annotations

CHECK_ID = "java-testing-test-owner-construction"


def test_flags_owner_initialized_outside_given_or_global_final_field(analyzer):
    source = """
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

class SampleTest {
    private Subject subject;

    @BeforeEach
    void setUp() {
        subject = new Subject();
    }

    @Test
    void execute_GivenInput_WhenCalled_ThenReturnsValue() {
        // GIVEN
        String input = "input";
        // WHEN
        subject.execute(input);
        // THEN
    }
}
"""

    findings = analyzer.analyze_source("SampleTest.java", source)
    summaries = [finding.summary for finding in findings if finding.check == CHECK_ID]

    assert len(summaries) == 1
    assert "subject.execute" in summaries[0]


def test_allows_owner_initialized_in_given(analyzer):
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


def test_allows_directly_initialized_final_test_field(analyzer):
    source = """
import org.junit.jupiter.api.Test;

class SampleTest {
    private final Subject subject = new Subject();

    @Test
    void execute_GivenInput_WhenCalled_ThenReturnsValue() {
        // GIVEN
        String input = "input";
        // WHEN
        subject.execute(input);
        // THEN
    }
}
"""

    findings = analyzer.analyze_source("SampleTest.java", source)

    assert not any(finding.check == CHECK_ID for finding in findings)


def test_ignores_static_method_calls_without_an_instance_owner(analyzer):
    source = """
import org.junit.jupiter.api.Test;

class SampleTest {
    @Test
    void execute_GivenInput_WhenCalled_ThenReturnsValue() {
        // GIVEN
        String input = "input";
        // WHEN
        Subject.execute(input);
        // THEN
    }
}
"""

    findings = analyzer.analyze_source("SampleTest.java", source)

    assert not any(finding.check == CHECK_ID for finding in findings)
