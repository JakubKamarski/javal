from __future__ import annotations

from pathlib import Path

import pytest

from validator.java.analyzer import JavaAnalyzer
from validator.java.context import JavaFileContext
from validator.java.rules.naming.constant_upper_snake import ConstantUpperSnakeCaseRule
from validator.java.rules.naming.method_bare_participle import MethodBareParticipleRule
from validator.java.rules.naming.method_map_style import MethodMapStyleNameRule
from validator.java.rules.naming.method_verb_prefix import MethodVerbPrefixRule
from validator.java.rules.naming.variable_collection_type import VariableCollectionTypeInNameRule
from validator.java.rules.naming.variable_hungarian_notation import VariableHungarianNotationRule
from validator.java.rules.unused_import import UnusedImportRule

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "java"


@pytest.fixture
def analyzer() -> JavaAnalyzer:
    return JavaAnalyzer()


def fixture_path(name: str) -> Path:
    return FIXTURES_DIR / name


def findings_for(analyzer: JavaAnalyzer, fixture_name: str, check_id: str | None = None):
    findings = analyzer.analyze_file(fixture_path(fixture_name))
    if check_id is None:
        return findings
    return [finding for finding in findings if finding.check == check_id]


def violation_summaries(analyzer: JavaAnalyzer, fixture_name: str, check_id: str) -> list[str]:
    return [finding.summary for finding in findings_for(analyzer, fixture_name, check_id)]
