from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from validator.java.analyzer import JavaAnalyzer
from validator.java.rules.registry import default_java_rules, default_tree_java_rules
from validator.java.rules.testing.test_method_prefix import TestMethodPrefixRule
from validator.java.rules.testing.when_generic_variable import TestWhenGenericVariableRule

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "java"


def test_test_only_rules_skip_production_fixture(analyzer: JavaAnalyzer):
    summaries = [
        finding.summary
        for finding in analyzer.analyze_file(FIXTURES_DIR / "CleanService.java")
        if finding.check
        in {
            "java-testing-test-method-prefix",
            "java-testing-when-generic-variable",
        }
    ]
    assert summaries == []


def test_test_only_rules_run_on_test_fixture(analyzer: JavaAnalyzer):
    test_rules = [TestMethodPrefixRule(), TestWhenGenericVariableRule()]
    production_rules = [
        rule
        for rule in default_java_rules()
        if rule.check_id
        not in {
            "java-testing-test-method-prefix",
            "java-testing-when-generic-variable",
        }
    ]
    scoped_analyzer = JavaAnalyzer(rules=[*production_rules, *test_rules])

    findings = scoped_analyzer.analyze_file(FIXTURES_DIR / "BadTestMethodPrefixSampleTest.java")
    assert any(finding.check == "java-testing-test-method-prefix" for finding in findings)


def test_registered_test_rules_declare_test_applicability():
    test_rule_ids = {
        "java-testing-test-method-prefix",
        "java-testing-when-generic-variable",
    }
    for rule in default_java_rules():
        if rule.check_id in test_rule_ids:
            assert rule.meta.file_applicability == "test"


def test_registered_tree_rules_declare_tree_applicability():
    expectations = {
        "java-testing-duplicate-it-and-test": "test",
        "java-testing-missing-test-class": "production",
        "java-jpa-entity-serial-version-uid": "production",
    }
    for rule in default_tree_java_rules():
        assert rule.meta.tree_file_applicability == expectations[rule.check_id]


@patch("validator.java.context.parse_java")
def test_analyze_tree_parses_each_file_once(mock_parse_java, tmp_path: Path):
    java_file = tmp_path / "SampleService.java"
    java_file.write_text(
        "package demo;\n"
        "class SampleService {\n"
        "  void run() {}\n"
        "}\n",
        encoding="utf-8",
    )

    def fake_parse(source: str):
        del source
        from validator.java.parser import parse_java as real_parse_java

        return real_parse_java(
            "package demo;\nclass SampleService {\n  void run() {}\n}\n"
        )

    mock_parse_java.side_effect = fake_parse

    analyzer = JavaAnalyzer(tree_rules=[])
    analyzer.analyze_tree(tmp_path)

    assert mock_parse_java.call_count == 1


@patch("validator.java.context.parse_java")
def test_tree_rules_reuse_cached_context(mock_parse_java, tmp_path: Path):
    java_file = tmp_path / "SampleFacade.java"
    java_file.write_text(
        "package demo;\n"
        "class SampleFacade {\n"
        "  void run() {}\n"
        "}\n",
        encoding="utf-8",
    )

    from validator.java.parser import parse_java as real_parse_java

    mock_parse_java.side_effect = lambda source: real_parse_java(source)

    analyzer = JavaAnalyzer(rules=[])
    analyzer.analyze_tree(tmp_path)

    assert mock_parse_java.call_count == 1
