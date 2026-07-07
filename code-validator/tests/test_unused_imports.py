from tests.conftest import FIXTURES_DIR, violation_summaries
from validator.java.context import JavaFileContext
from validator.java.rules.unused_import import UnusedImportRule


def test_clean_service_has_no_unused_imports(analyzer):
    findings = analyzer.analyze_file(FIXTURES_DIR / "CleanService.java")
    unused = [finding for finding in findings if finding.check == "unused-imports"]
    assert unused == []


def test_unused_imports_sample_flags_set_and_hashset(analyzer):
    summaries = violation_summaries(analyzer, "UnusedImportsSample.java", "unused-imports")
    assert any("Set" in summary for summary in summaries)
    assert any("HashSet" in summary for summary in summaries)


def test_unused_import_rule_reports_symbol():
    rule = UnusedImportRule()
    context = JavaFileContext.from_path(FIXTURES_DIR / "UnusedImportsSample.java")
    violations = rule.apply(context)
    symbols = {violation.summary for violation in violations}
    assert "Unused import 'Set'" in symbols
    assert "Unused import 'HashSet'" in symbols
