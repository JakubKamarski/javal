from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from validator.git_scope import (
    build_task_scope,
    commit_subject_matches_task_id,
    list_task_commits,
    parse_unified_diff,
    resolve_repo_path,
    validate_task_id,
)
from validator.java.analyzer import analyze_java_tree
from validate import main


SAMPLE_DIFF = """\
diff --git a/src/Main.java b/src/Main.java
index 1111111..2222222 100644
--- a/src/Main.java
+++ b/src/Main.java
@@ -0,0 +1,8 @@
+package demo;
+
+import java.util.Set;
+import java.util.List;
+
+public class Main {
+    private List<String> shipmentList;
+}
"""


def test_validate_task_id_accepts_standard_format():
    assert validate_task_id("ABC-5164") == "ABC-5164"


def test_validate_task_id_rejects_invalid_format():
    with pytest.raises(ValueError):
        validate_task_id("plog-5164")


@pytest.mark.parametrize(
    ("subject", "task_id", "expected"),
    [
        ("ABC-1234 | Add feature", "ABC-1234", True),
        ("ABC-1234 Add feature", "ABC-1234", True),
        ("ABC-1234: Fix bug", "ABC-1234", True),
        ("ABC-1234", "ABC-1234", True),
        ("ABC-12345 | Extended id", "ABC-1234", False),
        ("ABC-12340", "ABC-1234", False),
        ("XYZ-1234 | Other task", "ABC-1234", False),
        ("Initial commit", "ABC-1234", False),
    ],
)
def test_commit_subject_matches_task_id(subject, task_id, expected):
    assert commit_subject_matches_task_id(subject, task_id) is expected


def test_list_task_commits_accepts_task_id_without_pipe_separator(tmp_path):
    task_id = "ABC-7777"
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Test User")
    (tmp_path / "file.txt").write_text("initial\n", encoding="utf-8")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "Initial commit")
    (tmp_path / "file.txt").write_text("initial\nchanged\n", encoding="utf-8")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", f"{task_id} Add without pipe")
    (tmp_path / "file.txt").write_text("initial\nchanged\nmore\n", encoding="utf-8")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "ABC-1111 | Other task")

    commits = list_task_commits(tmp_path, task_id)

    assert len(commits) == 1


def test_resolve_repo_path_defaults_to_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert resolve_repo_path(None) == tmp_path.resolve()


def test_resolve_repo_path_supports_relative_path(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    monkeypatch.chdir(tmp_path)
    assert resolve_repo_path(Path("repo")) == repo.resolve()


def test_parse_unified_diff_collects_new_file_lines():
    changed = parse_unified_diff(SAMPLE_DIFF)
    assert changed == {"src/Main.java": {1, 2, 3, 4, 5, 6, 7, 8}}


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True)


def _init_repo_with_task_commit(repo: Path, task_id: str) -> None:
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test User")

    java_dir = repo / "src"
    java_dir.mkdir()
    (java_dir / "Clean.java").write_text(
        "package demo;\n\npublic class Clean {\n    public String retrieveName() { return \"ok\"; }\n}\n",
        encoding="utf-8",
    )
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "Initial commit")

    (java_dir / "Bad.java").write_text(
        "package demo;\n\nimport java.util.Set;\n\npublic class Bad {\n"
        "    public Map<String, String> statusByWaybill() { return null; }\n}\n",
        encoding="utf-8",
    )
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", f"{task_id} | Add bad sample")


def test_build_task_scope_collects_only_task_commit_lines(tmp_path):
    task_id = "ABC-9999"
    _init_repo_with_task_commit(tmp_path, task_id)

    scope = build_task_scope(tmp_path, task_id)

    assert len(scope.commits) == 1
    bad_file = str((tmp_path / "src/Bad.java").resolve())
    assert bad_file in scope.changed_lines
    assert 3 in scope.changed_lines[bad_file]
    assert scope.author_for_line(tmp_path / "src/Bad.java", 3) == "Test User"


def test_analyze_java_tree_reports_only_task_changed_lines(tmp_path):
    task_id = "ABC-9999"
    _init_repo_with_task_commit(tmp_path, task_id)

    report = analyze_java_tree(tmp_path, task_id=task_id)

    summaries = [finding.summary for finding in report.invalid_findings]
    assert any("statusByWaybill" in summary for summary in summaries)
    assert all("retrieveName" not in summary for summary in summaries)


def test_task_scope_tracks_current_lines_after_later_task_commit_shifts_file(tmp_path):
    task_id = "ABC-9999"
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Test User")
    source = tmp_path / "Sample.java"
    source.write_text(
        "package demo;\n\nclass Sample {\n    String getName() { return \"ok\"; }\n}\n",
        encoding="utf-8",
    )
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "Initial commit")

    source.write_text(source.read_text(encoding="utf-8").replace("getName", "label"), encoding="utf-8")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", f"{task_id} | Introduce invalid method")

    source.write_text(source.read_text(encoding="utf-8").replace("package demo;", "package demo;\n\n"), encoding="utf-8")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", f"{task_id} | Reformat header")

    report = analyze_java_tree(tmp_path, task_id=task_id)

    assert any("label" in finding.summary for finding in report.invalid_findings)


def test_cli_resolves_nested_path_to_repository_root(tmp_path, capsys):
    task_id = "ABC-9999"
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Test User")
    module = tmp_path / "module"
    module.mkdir()
    source = module / "Sample.java"
    source.write_text("class Sample {}\n", encoding="utf-8")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "Initial commit")
    source.write_text("import java.util.List;\nclass Sample {}\n", encoding="utf-8")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", f"{task_id} | Add unused import")

    exit_code = main([task_id, str(module)])

    assert exit_code == 1
    assert "Unused import 'List'" in capsys.readouterr().out


def test_cli_fails_when_task_has_no_matching_commits(tmp_path, capsys):
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Test User")
    (tmp_path / "Sample.java").write_text("class Sample {}\n", encoding="utf-8")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "Initial commit")

    exit_code = main(["ABC-9999", str(tmp_path)])

    assert exit_code == 2
    assert "No commits found for task ABC-9999" in capsys.readouterr().err


def test_task_scope_ignores_committed_binary_files(tmp_path):
    task_id = "ABC-9999"
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Test User")
    (tmp_path / "image.bin").write_bytes(b"\xff\xfe\x00\x01")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", f"{task_id} | Add binary artifact")

    scope = build_task_scope(tmp_path, task_id)

    assert len(scope.commits) == 1
    assert scope.changed_lines == {}
