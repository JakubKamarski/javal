from __future__ import annotations

import subprocess
from pathlib import Path

from validator.java.analyzer import JavaAnalyzer, analyze_java_tree
from validator.java.rules.testing.missing_test_class import MissingTestClassRule

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "java" / "testing"
CHECK_ID = "java-testing-missing-test-class"


def findings_for(analyzer: JavaAnalyzer) -> list:
    report = analyzer.analyze_tree(FIXTURES_DIR)
    return [finding for finding in report.findings if finding.check == CHECK_ID]


def test_missing_test_class_rule_flags_facade_without_it():
    analyzer = JavaAnalyzer(tree_rules=[MissingTestClassRule()])
    findings = findings_for(analyzer)
    assert any("SampleShipmentFacade" in finding.summary for finding in findings)
    assert any("SampleShipmentFacadeIT" in finding.summary for finding in findings)


def test_missing_test_class_rule_flags_mapper_without_test():
    analyzer = JavaAnalyzer(tree_rules=[MissingTestClassRule()])
    findings = findings_for(analyzer)
    assert any("SampleStatusMapper" in finding.summary for finding in findings)
    assert any("SampleStatusMapperTest" in finding.summary for finding in findings)


def test_missing_test_class_rule_flags_repository_with_query_without_it():
    analyzer = JavaAnalyzer(tree_rules=[MissingTestClassRule()])
    findings = findings_for(analyzer)
    assert any("SampleShipmentRepository" in finding.summary for finding in findings)
    assert any("SampleShipmentRepositoryIT" in finding.summary for finding in findings)


def test_missing_test_class_rule_ignores_repository_without_query():
    analyzer = JavaAnalyzer(tree_rules=[MissingTestClassRule()])
    findings = findings_for(analyzer)
    assert all("SampleShipmentDerivedRepository" not in finding.summary for finding in findings)


def test_missing_test_class_rule_ignores_package_private_facade():
    analyzer = JavaAnalyzer(tree_rules=[MissingTestClassRule()])
    findings = findings_for(analyzer)
    assert all("PackagePrivateFacade" not in finding.summary for finding in findings)


def test_missing_test_class_rule_passes_when_required_tests_exist():
    analyzer = JavaAnalyzer(tree_rules=[MissingTestClassRule()])
    findings = findings_for(analyzer)
    assert all("SampleTrackerService" not in finding.summary for finding in findings)
    assert all("SampleTrackingScheduler" not in finding.summary for finding in findings)


def test_missing_test_class_rule_ignores_unscoped_gateway():
    analyzer = JavaAnalyzer(tree_rules=[MissingTestClassRule()])
    findings = findings_for(analyzer)
    assert all("SampleTrackerGateway" not in finding.summary for finding in findings)


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True)


def test_analyze_java_tree_reports_missing_test_for_task_changed_main_source(tmp_path):
    task_id = "PLOG-9999"
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Test User")

    main_dir = tmp_path / "src" / "main" / "java" / "demo"
    main_dir.mkdir(parents=True)
    (main_dir / "SampleShipmentFacade.java").write_text(
        "package demo;\n\npublic class SampleShipmentFacade {\n}\n",
        encoding="utf-8",
    )
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", f"{task_id} | Add facade without IT")

    report = analyze_java_tree(tmp_path, task_id=task_id)
    findings = [finding for finding in report.invalid_findings if finding.check == CHECK_ID]
    assert len(findings) == 1
    assert findings[0].file.endswith("SampleShipmentFacade.java")
    assert "SampleShipmentFacadeIT" in findings[0].summary


def test_analyze_java_tree_skips_preexisting_main_source_not_changed_in_task(tmp_path):
    task_id = "PLOG-9999"
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Test User")

    main_dir = tmp_path / "src" / "main" / "java" / "demo"
    main_dir.mkdir(parents=True)
    (main_dir / "SampleShipmentFacade.java").write_text(
        "package demo;\n\npublic class SampleShipmentFacade {\n}\n",
        encoding="utf-8",
    )
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "PLOG-1111 | Add facade without IT")

    unrelated = tmp_path / "src" / "main" / "java" / "demo" / "Other.java"
    unrelated.write_text("package demo;\n\nclass Other {\n}\n", encoding="utf-8")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", f"{task_id} | Touch unrelated file")

    report = analyze_java_tree(tmp_path, task_id=task_id)
    findings = [finding for finding in report.invalid_findings if finding.check == CHECK_ID]
    assert findings == []


def test_analyze_java_tree_flags_repository_when_task_adds_query_method(tmp_path):
    task_id = "PLOG-9999"
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Test User")

    main_dir = tmp_path / "src" / "main" / "java" / "demo"
    main_dir.mkdir(parents=True)
    (main_dir / "SampleShipmentRepository.java").write_text(
        "package demo;\n\n"
        "import org.springframework.data.jpa.repository.Query;\n"
        "import org.springframework.data.repository.Repository;\n\n"
        "public interface SampleShipmentRepository extends Repository<Object, Long> {\n\n"
        '    @Query("select s from Object s where s.waybill = :waybill")\n'
        "    Object findByWaybill(String waybill);\n"
        "}\n",
        encoding="utf-8",
    )
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", f"{task_id} | Add repository with @Query")

    report = analyze_java_tree(tmp_path, task_id=task_id)
    findings = [finding for finding in report.invalid_findings if finding.check == CHECK_ID]
    assert len(findings) == 1
    assert findings[0].file.endswith("SampleShipmentRepository.java")
    assert "SampleShipmentRepositoryIT" in findings[0].summary


def test_analyze_java_tree_skips_repository_when_task_only_adds_derived_query(tmp_path):
    task_id = "PLOG-9999"
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Test User")

    main_dir = tmp_path / "src" / "main" / "java" / "demo"
    main_dir.mkdir(parents=True)
    repository = main_dir / "SampleShipmentRepository.java"
    repository.write_text(
        "package demo;\n\n"
        "import org.springframework.data.jpa.repository.Query;\n"
        "import org.springframework.data.repository.Repository;\n\n"
        "public interface SampleShipmentRepository extends Repository<Object, Long> {\n\n"
        '    @Query("select s from Object s where s.waybill = :waybill")\n'
        "    Object findByWaybill(String waybill);\n"
        "}\n",
        encoding="utf-8",
    )
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "PLOG-1111 | Add repository with @Query")

    repository.write_text(
        "package demo;\n\n"
        "import org.springframework.data.jpa.repository.Query;\n"
        "import org.springframework.data.repository.Repository;\n\n"
        "public interface SampleShipmentRepository extends Repository<Object, Long> {\n\n"
        '    @Query("select s from Object s where s.waybill = :waybill")\n'
        "    Object findByWaybill(String waybill);\n\n"
        "    Object findByTrackingNumber(String trackingNumber);\n"
        "}\n",
        encoding="utf-8",
    )
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", f"{task_id} | Add derived query method")

    report = analyze_java_tree(tmp_path, task_id=task_id)
    findings = [finding for finding in report.invalid_findings if finding.check == CHECK_ID]
    assert findings == []
