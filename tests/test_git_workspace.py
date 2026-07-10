from __future__ import annotations

import subprocess
from pathlib import Path

from validator.analyze import analyze_repo
from validator.git_workspace import CHECK_ID, build_uncommitted_changes_finding, list_uncommitted_paths


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True)


def _init_clean_repo(repo: Path) -> None:
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test User")

    source = repo / "src" / "Main.java"
    source.parent.mkdir(parents=True)
    source.write_text("package demo;\n\npublic class Main {\n}\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "Initial commit")


def test_list_uncommitted_paths_on_clean_repo(tmp_path):
    _init_clean_repo(tmp_path)

    assert list_uncommitted_paths(tmp_path) == []


def test_list_uncommitted_paths_includes_modified_and_untracked(tmp_path):
    _init_clean_repo(tmp_path)

    source = tmp_path / "src" / "Main.java"
    source.write_text("package demo;\n\npublic class Main {\n    // changed\n}\n", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("draft", encoding="utf-8")

    paths = list_uncommitted_paths(tmp_path)

    assert "src/Main.java" in paths
    assert "notes.txt" in paths


def test_list_uncommitted_paths_preserves_spaces_and_arrow_text(tmp_path):
    _init_clean_repo(tmp_path)
    unusual_path = tmp_path / "draft -> notes.txt"
    unusual_path.write_text("draft", encoding="utf-8")

    assert "draft -> notes.txt" in list_uncommitted_paths(tmp_path)


def test_build_uncommitted_changes_finding_returns_none_for_clean_repo(tmp_path):
    _init_clean_repo(tmp_path)

    assert build_uncommitted_changes_finding(tmp_path) is None


def test_build_uncommitted_changes_finding_warns_about_dirty_repo(tmp_path):
    _init_clean_repo(tmp_path)

    (tmp_path / "draft.txt").write_text("wip", encoding="utf-8")

    finding = build_uncommitted_changes_finding(tmp_path)

    assert finding is not None
    assert finding.check == CHECK_ID
    assert finding.severity == "warning"
    assert finding.file.endswith("draft.txt")
    assert "uncommitted" in finding.summary.lower()
    assert "draft.txt" in finding.details
    assert "Commit local changes" in finding.suggestion


def test_analyze_repo_reports_uncommitted_changes(tmp_path):
    _init_clean_repo(tmp_path)
    (tmp_path / "draft.txt").write_text("wip", encoding="utf-8")

    report = analyze_repo(tmp_path, task_id="ABC-9999")

    findings = [finding for finding in report.invalid_findings if finding.check == CHECK_ID]
    assert len(findings) == 1


def test_analyze_repo_does_not_decode_untracked_binary_files(tmp_path):
    _init_clean_repo(tmp_path)
    (tmp_path / "image.bin").write_bytes(b"\xff\xfe\x00\x01")

    report = analyze_repo(tmp_path, task_id="ABC-9999")

    findings = [finding for finding in report.invalid_findings if finding.check == CHECK_ID]
    assert len(findings) == 1


def test_analyze_repo_skips_uncommitted_warning_on_clean_repo(tmp_path):
    _init_clean_repo(tmp_path)

    report = analyze_repo(tmp_path, task_id="ABC-9999")

    findings = [finding for finding in report.findings if finding.check == CHECK_ID]
    assert findings == []
