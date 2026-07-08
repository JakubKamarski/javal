from validator.report import Finding, Report


def _sample_finding(java_file: str, line: int = 3) -> Finding:
    return Finding(
        severity="warning",
        check="unused-imports",
        summary="Unused import 'Set'",
        file=java_file,
        line=line,
    )


def test_display_path_absolute_is_default(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    java_file = repo / "Sample.java"
    java_file.write_text("class Sample {}", encoding="utf-8")

    finding = _sample_finding(str(java_file))

    assert finding.display_path(repo) == str(java_file.resolve())


def test_display_path_relative(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    java_file = repo / "Sample.java"
    java_file.write_text("class Sample {}", encoding="utf-8")

    finding = _sample_finding(str(java_file))

    assert finding.display_path(repo, path_format="relative") == "Sample.java"


def test_display_path_filename(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    java_file = repo / "src" / "Sample.java"
    java_file.parent.mkdir()
    java_file.write_text("class Sample {}", encoding="utf-8")

    finding = _sample_finding(str(java_file))

    assert finding.display_path(repo, path_format="filename") == "Sample.java"


def test_log_line_uses_absolute_path_by_default(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    java_file = repo / "Sample.java"
    java_file.write_text("class Sample {}", encoding="utf-8")

    finding = _sample_finding(str(java_file))

    assert finding.log_line(repo) == f"{java_file.resolve()}|3|Unused import 'Set'"


def test_log_line_uses_relative_path_when_requested(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    java_file = repo / "Sample.java"
    java_file.write_text("class Sample {}", encoding="utf-8")

    finding = _sample_finding(str(java_file))

    assert (
        finding.log_line(repo, path_format="relative")
        == "Sample.java|3|Unused import 'Set'"
    )


def test_log_line_uses_filename_when_requested(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    java_file = repo / "src" / "Sample.java"
    java_file.parent.mkdir()
    java_file.write_text("class Sample {}", encoding="utf-8")

    finding = _sample_finding(str(java_file))

    assert (
        finding.log_line(repo, path_format="filename")
        == "Sample.java|3|Unused import 'Set'"
    )


def test_task_todo_line_format(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    java_file = repo / "Sample.java"
    java_file.write_text("class Sample {}", encoding="utf-8")

    finding = Finding(
        severity="warning",
        check="java-naming",
        summary="Method 'statusByWaybill' looks like map-style naming",
        file=str(java_file),
        line=15,
    )
    absolute_path = str(java_file.resolve())

    assert (
        finding.task_todo_line(repo)
        == f"- [ ] `{absolute_path}:15` — Method 'statusByWaybill' looks like map-style naming"
    )
    assert (
        finding.task_todo_line(repo, done=True)
        == f"- [x] `{absolute_path}:15` — Method 'statusByWaybill' looks like map-style naming"
    )
    assert (
        finding.task_todo_line(repo, path_format="relative")
        == "- [ ] `Sample.java:15` — Method 'statusByWaybill' looks like map-style naming"
    )
    assert (
        finding.task_todo_line(repo, path_format="filename")
        == "- [ ] `Sample.java:15` — Method 'statusByWaybill' looks like map-style naming"
    )


def test_report_to_task_todos_with_no_findings():
    report = Report(target="/repo")
    assert report.to_task_todos() == "- [x] No validation findings."


def test_report_to_task_todos_lists_invalid_findings(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    java_file = repo / "Bad.java"
    java_file.write_text("class Bad {}", encoding="utf-8")

    report = Report(target=str(repo.resolve()))
    report.add_finding(
        Finding(
            severity="warning",
            check="unused-imports",
            summary="Unused import 'List'",
            file=str(java_file),
            line=2,
        )
    )

    lines = report.to_task_todos().splitlines()
    assert len(lines) == 1
    assert lines[0].startswith("- [ ] `")
    assert str(java_file.resolve()) in lines[0]
    assert "Unused import 'List'" in lines[0]

    relative_lines = report.to_task_todos(path_format="relative").splitlines()
    assert "`Bad.java:2`" in relative_lines[0]


def test_report_to_log_lines_respects_path_format(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    java_file = repo / "Bad.java"
    java_file.write_text("class Bad {}", encoding="utf-8")

    report = Report(target=str(repo.resolve()))
    report.add_finding(
        Finding(
            severity="warning",
            check="unused-imports",
            summary="Unused import 'List'",
            file=str(java_file),
            line=2,
        )
    )

    assert report.to_log_lines() == (
        f"{java_file.resolve()}|2|Unused import 'List'"
    )
    assert report.to_log_lines(path_format="relative") == (
        "Bad.java|2|Unused import 'List'"
    )
    assert report.to_log_lines(path_format="filename") == (
        "Bad.java|2|Unused import 'List'"
    )
