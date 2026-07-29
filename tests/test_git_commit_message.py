from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from validator.analyze import analyze_repo
from validator.git_commit_message import (
    CHECK_ID,
    commit_subject_courier_symbol_segments,
    commit_subject_includes_courier_symbol_segment,
)
from validator.git_scope import build_task_scope


@pytest.mark.parametrize(
    ("subject", "task_id", "courier_identifier", "expected"),
    [
        ("ABC-1234 | Add shipment status", "ABC-1234", "sample", False),
        ("ABC-1234 | TRACKING | Publish status updates", "ABC-1234", "sample", False),
        ("ABC-1234 | HOTFIX | Fix production issue", "ABC-1234", "sample", False),
        ("ABC-1234 | Validation fixes", "ABC-1234", "sample", False),
        ("ABC-1234 Add without pipe", "ABC-1234", "sample", False),
        ("fix: ABC-1234 Handle timeout", "ABC-1234", "sample", False),
        ("ABC-1234 | SAMPLE | Add shipment status", "ABC-1234", "sample", True),
        ("ABC-1234 | SAMPLE_COURIER | Add shipment status", "ABC-1234", "sample", True),
        (
            "ABC-1234 | TRACKING | SAMPLE-COURIER | Add shipment status",
            "ABC-1234",
            "sample",
            True,
        ),
        (
            "ABC-1234 | HOTFIX | SAMPLE | Fix production issue",
            "ABC-1234",
            "sample",
            True,
        ),
        ("ABC-1234 | OTHER | Add shipment status", "ABC-1234", "sample", False),
        ("ABC-1234 | GENERIC | Add shipment status", "ABC-1234", "sample2", False),
        ("ABC-1234 | SAMPLE | Add shipment status", "ABC-1234", "sample2", True),
    ],
)
def test_commit_subject_includes_courier_symbol_segment(
    subject,
    task_id,
    courier_identifier,
    expected,
):
    assert commit_subject_includes_courier_symbol_segment(
        subject,
        task_id,
        courier_identifier,
    ) is expected


@pytest.mark.parametrize(
    ("subject", "task_id", "courier_identifier", "expected"),
    [
        ("ABC-1234 | TRACKING | Add feature", "ABC-1234", "sample", ()),
        ("ABC-1234 | SAMPLE | Add feature", "ABC-1234", "sample", ("SAMPLE",)),
        (
            "ABC-1234 | SAMPLE | sample-module | Add feature",
            "ABC-1234",
            "sample",
            ("SAMPLE", "sample-module"),
        ),
        ("ABC-1234 | HOTFIX | Add feature", "ABC-1234", "sample", ()),
    ],
)
def test_commit_subject_courier_symbol_segments(
    subject,
    task_id,
    courier_identifier,
    expected,
):
    assert commit_subject_courier_symbol_segments(
        subject,
        task_id,
        courier_identifier,
    ) == expected


def _write_courier_application_properties(repo: Path, courier_name: str = "sample") -> None:
    config_dir = repo / "src" / "main" / "resources"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "application.properties").write_text(
        f"server.servlet.context-path=/demo-courier-{courier_name}/rs\n",
        encoding="utf-8",
    )


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def test_analyze_repo_flags_task_commit_with_courier_symbol_segment(tmp_path):
    task_id = "ABC-9001"
    repo = tmp_path / "hermes"
    repo.mkdir()
    _write_courier_application_properties(repo, "hermes")
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test User")
    sample = repo / "Sample.txt"
    sample.write_text("initial\n", encoding="utf-8")
    _git(repo, "add", "Sample.txt")
    _git(repo, "commit", "-m", "Initial commit")

    sample.write_text("initial\nchanged\n", encoding="utf-8")
    _git(repo, "add", "Sample.txt")
    _git(
        repo,
        "commit",
        "-m",
        f"{task_id} | HERMES | Add shipment status",
    )

    report = analyze_repo(repo, task_id=task_id)
    findings = [finding for finding in report.invalid_findings if finding.check == CHECK_ID]

    assert len(findings) == 1
    assert "courier symbol segment" in findings[0].summary.lower()


def test_analyze_repo_skips_courier_symbol_check_outside_courier_dedicated_repo(tmp_path):
    task_id = "ABC-9004"
    repo = tmp_path / "shared-lib"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test User")
    sample = repo / "Sample.txt"
    sample.write_text("initial\n", encoding="utf-8")
    _git(repo, "add", "Sample.txt")
    _git(repo, "commit", "-m", "Initial commit")

    sample.write_text("initial\nchanged\n", encoding="utf-8")
    _git(repo, "add", "Sample.txt")
    _git(
        repo,
        "commit",
        "-m",
        f"{task_id} | SampleCourier | Add shipment status",
    )

    report = analyze_repo(repo, task_id=task_id)
    findings = [finding for finding in report.findings if finding.check == CHECK_ID]

    assert findings == []


def test_analyze_repo_accepts_task_commit_without_courier_symbol_segment(tmp_path):
    task_id = "ABC-9002"
    repo = tmp_path / "sample-courier"
    repo.mkdir()
    _write_courier_application_properties(repo, "sample2")
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test User")
    sample = repo / "Sample.txt"
    sample.write_text("initial\n", encoding="utf-8")
    _git(repo, "add", "Sample.txt")
    _git(repo, "commit", "-m", "Initial commit")

    sample.write_text("initial\nchanged\n", encoding="utf-8")
    _git(repo, "add", "Sample.txt")
    _git(repo, "commit", "-m", f"{task_id} | TRACKING | Add shipment status")

    report = analyze_repo(repo, task_id=task_id)
    findings = [finding for finding in report.findings if finding.check == CHECK_ID]

    assert findings == []


def test_build_task_scope_does_not_flag_commits_without_courier_segments(tmp_path):
    task_id = "ABC-9003"
    repo = tmp_path / "sample-courier"
    repo.mkdir()
    _write_courier_application_properties(repo, "sample")
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test User")
    sample = repo / "Sample.txt"
    sample.write_text("initial\n", encoding="utf-8")
    _git(repo, "add", "Sample.txt")
    _git(repo, "commit", "-m", "Initial commit")
    sample.write_text("initial\nchanged\n", encoding="utf-8")
    _git(repo, "add", "Sample.txt")
    _git(repo, "commit", "-m", f"{task_id} | HOTFIX | Fix production issue")

    scope = build_task_scope(repo, task_id)
    report = analyze_repo(repo, scope=scope)
    findings = [finding for finding in report.findings if finding.check == CHECK_ID]

    assert len(scope.commits) == 1
    assert findings == []
