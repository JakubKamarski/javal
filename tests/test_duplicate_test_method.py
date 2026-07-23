from __future__ import annotations

import subprocess
from pathlib import Path

from validator.java.analyzer import JavaAnalyzer, analyze_java_tree
from validator.java.rules.testing.duplicate_test_method import DuplicateTestMethodRule

CHECK_ID = "java-testing-duplicate-test-method"


def _findings(source: str):
    analyzer = JavaAnalyzer(rules=[DuplicateTestMethodRule()])
    return [
        finding
        for finding in analyzer.analyze_source("SampleServiceTest.java", source)
        if finding.check == CHECK_ID
    ]


def _test_method(name: str, when: str, then: str = "") -> str:
    return f'''\
    @Test
    void {name}() {{
        // GIVEN
        // WHEN
        {when}
        // THEN
        {then}
    }}
'''


def _test_class(*methods: str) -> str:
    return "class SampleServiceTest {\n    private Service service;\n\n" + "\n".join(methods) + "}\n"


def test_flags_equivalent_normal_response_tests_for_the_same_resolved_signature():
    source = _test_class(
        _test_method("findByCode_GivenFirstCode_WhenCalled_ThenReturnsValue", 'service.findByCode("A");'),
        _test_method("findByCode_GivenSecondCode_WhenCalled_ThenReturnsValue", 'service.findByCode("B");'),
    )

    findings = _findings(source)

    assert len(findings) == 1
    assert "2 test methods" in findings[0].summary
    assert "Service.findByCode(String)" in findings[0].summary
    assert "normal-response" in findings[0].summary
    assert "@ParameterizedTest" in findings[0].suggestion


def test_ignores_tests_for_distinct_methods():
    source = _test_class(
        _test_method("findByCode_GivenCode_WhenCalled_ThenReturnsValue", 'service.findByCode("A");'),
        _test_method("findByName_GivenName_WhenCalled_ThenReturnsValue", 'service.findByName("A");'),
    )

    assert _findings(source) == []


def test_ignores_overloads_with_distinct_arities():
    source = _test_class(
        _test_method("find_GivenCode_WhenCalled_ThenReturnsValue", 'service.find("A");'),
        _test_method("find_GivenCodeAndType_WhenCalled_ThenReturnsValue", 'service.find("A", type);'),
    )

    assert _findings(source) == []


def test_keeps_exception_and_normal_response_tests_separate():
    source = _test_class(
        _test_method("find_GivenCode_WhenCalled_ThenReturnsValue", 'service.find("A");'),
        _test_method(
            "find_GivenMissingCode_WhenCalled_ThenThrows",
            'assertThrows(IllegalArgumentException.class, () -> service.find("A"));',
        ),
    )

    assert _findings(source) == []


def test_flags_multiple_equivalent_exception_tests():
    source = _test_class(
        _test_method(
            "find_GivenMissingCode_WhenCalled_ThenThrows",
            'assertThrows(IllegalArgumentException.class, () -> service.find("A"));',
        ),
        _test_method(
            "find_GivenBlankCode_WhenCalled_ThenThrows",
            'assertThatThrownBy(() -> service.find(""))\n'
            "            .isInstanceOf(IllegalArgumentException.class);",
        ),
    )

    findings = _findings(source)

    assert len(findings) == 1
    assert "exception path" in findings[0].summary


def test_flags_equivalent_exception_constructor_tests():
    source = _test_class(
        _test_method(
            "sampleEndpointGivenBlankUrl_WhenCreated_ThenThrows",
            'Throwable exception = catchThrowable(() -> new SampleEndpoint("", "user"));',
            "assertThat(exception).isInstanceOf(IllegalArgumentException.class);",
        ),
        _test_method(
            "sampleEndpointGivenBlankUser_WhenCreated_ThenThrows",
            'Throwable exception = catchThrowable(() -> new SampleEndpoint("url", ""));',
            "assertThat(exception).isInstanceOf(IllegalArgumentException.class);",
        ),
    )

    findings = _findings(source)

    assert len(findings) == 1
    assert "new SampleEndpoint(String, String)" in findings[0].summary
    assert "exception path" in findings[0].summary
    assert "catchThrowable" in findings[0].suggestion


def test_keeps_exception_tests_with_distinct_exception_types_separate():
    source = _test_class(
        _test_method(
            "findGivenInvalidCode_WhenCalled_ThenThrows",
            'Throwable exception = catchThrowable(() -> service.find(""));',
            "assertThat(exception).isInstanceOf(IllegalArgumentException.class);",
        ),
        _test_method(
            "findGivenMissingCode_WhenCalled_ThenThrows",
            'Throwable exception = catchThrowable(() -> service.find("missing"));',
            "assertThat(exception).isInstanceOf(IllegalStateException.class);",
        ),
    )

    assert _findings(source) == []


def test_keeps_nested_test_classes_separate():
    source = _test_class(
        _test_method("find_GivenOuterCase_WhenCalled_ThenReturnsValue", 'service.find("A");'),
        '''\
    @Nested
    class NestedCases {
'''
        + _test_method("find_GivenNestedCase_WhenCalled_ThenReturnsValue", 'service.find("B");')
        + "    }\n",
    )

    assert _findings(source) == []


def test_ignores_tests_without_a_recognizable_when_action():
    source = _test_class(
        '''\
    @Test
    void find_GivenFirstCase_WhenCalled_ThenReturnsValue() {
        assertTrue(true);
    }
''',
        '''\
    @Test
    void find_GivenSecondCase_WhenCalled_ThenReturnsValue() {
        assertTrue(true);
    }
''',
    )

    assert _findings(source) == []


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True)


def test_reports_the_later_test_when_it_is_in_task_scope(tmp_path):
    task_id = "ABC-1234"
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Test User")

    test_path = tmp_path / "src" / "test" / "java" / "demo" / "SampleServiceTest.java"
    test_path.parent.mkdir(parents=True)
    test_path.write_text(
        _test_class(_test_method("find_GivenFirstCode_WhenCalled_ThenReturnsValue", 'service.find("A");')),
        encoding="utf-8",
    )
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "Initial test")

    test_path.write_text(
        _test_class(
            _test_method("find_GivenFirstCode_WhenCalled_ThenReturnsValue", 'service.find("A");'),
            _test_method("find_GivenSecondCode_WhenCalled_ThenReturnsValue", 'service.find("B");'),
        ),
        encoding="utf-8",
    )
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", f"{task_id} | Add duplicate case")

    report = analyze_java_tree(tmp_path, task_id=task_id)
    findings = [finding for finding in report.invalid_findings if finding.check == CHECK_ID]

    assert len(findings) == 1
    assert findings[0].line > 1


def test_ignores_same_method_name_with_distinct_argument_types():
    source = _test_class(
        _test_method("find_GivenCode_WhenCalled_ThenReturnsValue", 'service.find("A");'),
        _test_method("find_GivenId_WhenCalled_ThenReturnsValue", "service.find(1);"),
    )

    assert _findings(source) == []


def test_flags_method_calls_with_constructed_arguments():
    source = _test_class(
        _test_method("saveGivenFirstRecord_WhenCalled_ThenReturns", 'service.save(new SampleRecord("A"));'),
        _test_method("saveGivenSecondRecord_WhenCalled_ThenReturns", 'service.save(new SampleRecord("B"));'),
    )

    findings = _findings(source)

    assert len(findings) == 1
    assert "Service.save(SampleRecord)" in findings[0].summary


def test_ignores_same_signature_with_distinct_assertion_shapes():
    source = _test_class(
        _test_method(
            "find_GivenFirstCase_WhenCalled_ThenReturnsValue",
            'service.find("A");',
            'assertThat(result).isEqualTo("A");',
        ),
        _test_method(
            "find_GivenSecondCase_WhenCalled_ThenReturnsValue",
            'service.find("B");',
            'assertThat(result).isEmpty();',
        ),
    )

    assert _findings(source) == []
