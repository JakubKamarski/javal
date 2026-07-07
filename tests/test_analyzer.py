from __future__ import annotations

from pathlib import Path

from validator.java.analyzer import JavaAnalyzer, analyze_java_tree
from validator.java.rules.registry import default_java_rules

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "java"


def test_default_registry_exposes_one_class_per_rule():
    rules = default_java_rules()
    check_ids = [rule.check_id for rule in rules]

    assert len(check_ids) == len(set(check_ids))
    assert "unused-imports" in check_ids
    assert "java-naming-method-verb-prefix" in check_ids


def test_analyzer_runs_all_rules_on_fixture_tree():
    report = analyze_java_tree(FIXTURES_DIR)
    assert "unused-imports" in report.checks_run
    assert "java-naming-method-map-style" in report.checks_run
    assert any(f.check == "unused-imports" for f in report.findings)


def test_java_analyzer_can_run_subset_of_rules():
    analyzer = JavaAnalyzer(rules=[default_java_rules()[0]])
    findings = analyzer.analyze_file(FIXTURES_DIR / "UnusedImportsSample.java")
    assert findings
    assert all(finding.check == "unused-imports" for finding in findings)
