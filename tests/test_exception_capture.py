from __future__ import annotations

from validator.java.analyzer import JavaAnalyzer
from validator.java.rules.testing.exception_capture import ExceptionCaptureRule

CHECK_ID = "java-testing-exception-capture"


def _findings(source: str):
    analyzer = JavaAnalyzer(rules=[ExceptionCaptureRule()])
    return [
        finding
        for finding in analyzer.analyze_source("SampleServiceTest.java", source)
        if finding.check == CHECK_ID
    ]


def test_flags_deferred_throwing_callable():
    source = '''\
class SampleServiceTest {
    @Test
    void findGivenInvalidCode_WhenCalled_ThenThrows() {
        // GIVEN
        // WHEN
        ThrowingCallable creation = () -> new SampleEndpoint("");
        // THEN
        assertThatThrownBy(creation).isInstanceOf(IllegalArgumentException.class);
    }
}
'''

    findings = _findings(source)

    assert len(findings) == 1
    assert findings[0].line == 6
    assert "Throwable exception" in findings[0].summary


def test_flags_direct_exception_assertion():
    source = '''\
class SampleServiceTest {
    @Test
    void findGivenInvalidCode_WhenCalled_ThenThrows() {
        // GIVEN
        // WHEN
        // THEN
        assertThatThrownBy(() -> service.find("")).isInstanceOf(IllegalArgumentException.class);
    }
}
'''

    findings = _findings(source)

    assert len(findings) == 1


def test_accepts_exception_captured_in_when():
    source = '''\
class SampleServiceTest {
    @Test
    void findGivenInvalidCode_WhenCalled_ThenThrows() {
        // GIVEN
        // WHEN
        Throwable exception = catchThrowable(() -> service.find(""));
        // THEN
        assertThat(exception).isInstanceOf(IllegalArgumentException.class);
    }
}
'''

    assert _findings(source) == []
