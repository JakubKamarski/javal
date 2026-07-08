from __future__ import annotations

from tests.conftest import FIXTURES_DIR, violation_summaries
from validator.java.ast.imports import collect_identifier_usages
from validator.java.ast.methods import iter_method_declarations
from validator.java.context import JavaFileContext
from validator.java.parser import normalize_java_source

EM_DASH_FIXTURE = FIXTURES_DIR / "EmDashParseSample.java"


def test_normalize_java_source_replaces_unicode_dashes():
    assert normalize_java_source("a\u2014b\u2013c") == "a-b-c"


def test_em_dash_fixture_parses_full_method_names():
    context = JavaFileContext.from_path(EM_DASH_FIXTURE)
    method_names = {method.name for method in iter_method_declarations(context)}
    assert "executeSecondScenarioWithEquallyLongMethodNameThatMustStayIntactTwo" in method_names
    assert "stubResponse" in method_names
    assert not any(name.startswith("onize") for name in method_names)
    assert not any(len(name) < 10 and "Scenario" in name for name in method_names)


def test_em_dash_fixture_detects_import_usages():
    context = JavaFileContext.from_path(EM_DASH_FIXTURE)
    usages = collect_identifier_usages(context)
    assert "List" in usages
    assert "Test" in usages


def test_em_dash_fixture_has_no_false_positive_findings(analyzer):
    findings = analyzer.analyze_file(EM_DASH_FIXTURE)
    false_positive_checks = {
        "unused-imports",
        "java-naming-method-verb-prefix",
    }
    false_positives = [finding for finding in findings if finding.check in false_positive_checks]
    assert false_positives == []


def test_em_dash_fixture_skips_lifecycle_and_test_methods(analyzer):
    summaries = violation_summaries(analyzer, "EmDashParseSample.java", "java-naming-method-verb-prefix")
    assert summaries == []
