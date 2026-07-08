from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from validator.java.analyzer import JavaAnalyzer, analyze_java_tree
from validator.java.rules.testing.duplicate_it_and_test import (
    DuplicateItAndTestRule,
    integration_test_base_name,
    unit_test_base_name,
)

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "java" / "testing"
CHECK_ID = "java-testing-duplicate-it-and-test"


def test_unit_test_base_name_extracts_subject():
    assert unit_test_base_name("SampleTrackerServiceTest") == "SampleTrackerService"
    assert unit_test_base_name("SampleTrackerServiceIT") is None
    assert unit_test_base_name("SampleTrackerServiceITTest") is None


def test_integration_test_base_name_extracts_subject():
    assert integration_test_base_name("SampleTrackerServiceIT") == "SampleTrackerService"
    assert integration_test_base_name("SampleTrackerServiceTest") is None


def test_duplicate_it_and_test_rule_flags_pair_in_fixture_tree():
    analyzer = JavaAnalyzer(tree_rules=[DuplicateItAndTestRule()])
    report = analyzer.analyze_tree(FIXTURES_DIR)

    findings = [finding for finding in report.findings if finding.check == CHECK_ID]
    assert len(findings) == 1
    assert findings[0].file.endswith("SampleTrackerServiceTest.java")
    assert "SampleTrackerService" in findings[0].summary
    assert "SampleTrackerServiceIT.java" in findings[0].suggestion


def test_duplicate_it_and_test_rule_ignores_unit_test_without_it_pair():
    analyzer = JavaAnalyzer(tree_rules=[DuplicateItAndTestRule()])
    report = analyzer.analyze_tree(FIXTURES_DIR)

    findings = [finding for finding in report.findings if finding.check == CHECK_ID]
    assert all("SampleTrackingScheduler" not in finding.summary for finding in findings)


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True)


def _init_repo_with_duplicate_test_pair(repo: Path, task_id: str) -> None:
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test User")

    test_dir = repo / "src" / "test" / "java" / "demo"
    test_dir.mkdir(parents=True)
    (test_dir / "SampleTrackerServiceIT.java").write_text(
        "package demo;\n\nclass SampleTrackerServiceIT {\n}\n",
        encoding="utf-8",
    )
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "Initial commit")

    (test_dir / "SampleTrackerServiceTest.java").write_text(
        "package demo;\n\nclass SampleTrackerServiceTest {\n}\n",
        encoding="utf-8",
    )
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", f"{task_id} | Add duplicate unit test")


def _init_repo_with_preexisting_duplicate_pair(repo: Path) -> None:
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test User")

    test_dir = repo / "src" / "test" / "java" / "demo"
    test_dir.mkdir(parents=True)
    (test_dir / "SampleTrackerServiceIT.java").write_text(
        "package demo;\n\nclass SampleTrackerServiceIT {\n}\n",
        encoding="utf-8",
    )
    (test_dir / "SampleTrackerServiceTest.java").write_text(
        "package demo;\n\nclass SampleTrackerServiceTest {\n}\n",
        encoding="utf-8",
    )
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "Initial commit")


def test_analyze_java_tree_reports_duplicate_pair_for_task_changed_test(tmp_path):
    task_id = "PLOG-9999"
    _init_repo_with_duplicate_test_pair(tmp_path, task_id)

    report = analyze_java_tree(tmp_path, task_id=task_id)

    findings = [finding for finding in report.invalid_findings if finding.check == CHECK_ID]
    assert len(findings) == 1
    assert findings[0].file.endswith("SampleTrackerServiceTest.java")


def test_analyze_java_tree_flags_preexisting_pair_when_task_adds_it_after_unit_test(tmp_path):
    task_id = "PLOG-9999"
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Test User")

    test_dir = tmp_path / "src" / "test" / "java" / "demo"
    test_dir.mkdir(parents=True)
    (test_dir / "SampleTrackerServiceTest.java").write_text(
        "package demo;\n\nclass SampleTrackerServiceTest {\n}\n",
        encoding="utf-8",
    )
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "PLOG-1111 | Add unit test from earlier task")

    (test_dir / "SampleTrackerServiceIT.java").write_text(
        "package demo;\n\nclass SampleTrackerServiceIT {\n}\n",
        encoding="utf-8",
    )
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", f"{task_id} | Add integration test")

    report = analyze_java_tree(tmp_path, task_id=task_id)

    findings = [finding for finding in report.invalid_findings if finding.check == CHECK_ID]
    assert len(findings) == 1
    assert findings[0].file.endswith("SampleTrackerServiceTest.java")


def test_analyze_java_tree_flags_preexisting_pair_globally_even_when_task_touches_unrelated_file(
    tmp_path,
):
    task_id = "PLOG-9999"
    _init_repo_with_preexisting_duplicate_pair(tmp_path)

    unrelated = tmp_path / "src" / "main" / "java" / "demo" / "Other.java"
    unrelated.parent.mkdir(parents=True)
    unrelated.write_text("package demo;\n\nclass Other {\n}\n", encoding="utf-8")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", f"{task_id} | Touch unrelated file")

    report = analyze_java_tree(tmp_path, task_id=task_id)

    findings = [finding for finding in report.invalid_findings if finding.check == CHECK_ID]
    assert len(findings) == 1
    assert findings[0].file.endswith("SampleTrackerServiceTest.java")
