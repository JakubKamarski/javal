from __future__ import annotations

import pytest

from tests.conftest import findings_for
from validator.java.analyzer import JavaAnalyzer
from validator.java.rules.style.type_header_one_line import TypeHeaderOneLineRule

CHECK_ID = "java-style-type-header-one-line"


def test_split_headers_for_all_type_declarations_are_flagged(analyzer):
    findings = findings_for(analyzer, "TypeHeaderFormattingSample.java", CHECK_ID)

    assert {finding.summary.split("'")[1] for finding in findings} == {
        "TypeHeaderFormattingSample",
        "NestedType",
        "SplitRecord",
        "SplitState",
        "SplitMarker",
    }


def test_annotations_above_a_single_line_header_are_allowed():
    findings = _analyze(
        """@Deprecated
public sealed class CompactType permits CompactSubtype {
}
"""
    )

    assert findings == []


def test_modifier_split_from_declaration_is_flagged_on_first_continuation_line():
    findings = _analyze(
        """public
sealed class SplitModifierType permits SplitModifierSubtype {
}
"""
    )

    assert len(findings) == 1
    assert findings[0].line == 2


@pytest.mark.parametrize(
    ("projected_length", "expected_findings"),
    [
        (120, 1),
        (121, 0),
    ],
)
def test_multiline_header_respects_projected_length_boundary(
    projected_length,
    expected_findings,
):
    type_name = "A" * (projected_length - len("class  {"))

    findings = _analyze(f"class {type_name}\n{{\n}}\n")

    assert len(findings) == expected_findings


def test_nested_declaration_indentation_counts_toward_projected_length():
    type_name = "A" * (121 - 4 - len("class  {"))
    source = f"""class Outer {{
    class {type_name}
    {{
    }}
}}
"""

    findings = _analyze(source)

    assert findings == []


def test_long_single_line_header_is_allowed():
    type_name = "A" * 113

    findings = _analyze(f"class {type_name} {{\n}}\n")

    assert findings == []


def _analyze(source: str):
    analyzer = JavaAnalyzer(rules=[TypeHeaderOneLineRule()])
    return analyzer.analyze_source("TypeHeaderSample.java", source)
