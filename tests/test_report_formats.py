from validator.report import Finding, Report


def test_log_line_uses_absolute_path_and_pipe_format(tmp_path):
    java_file = tmp_path / "Sample.java"
    java_file.write_text("class Sample {}", encoding="utf-8")

    finding = Finding(
        severity="warning",
        check="unused-imports",
        summary="Unused import 'Set'",
        file=str(java_file),
        line=3,
    )

    assert finding.log_line() == f"{java_file.resolve()}|3|Unused import 'Set'"


def test_task_todo_line_format(tmp_path):
    java_file = tmp_path / "Sample.java"
    java_file.write_text("class Sample {}", encoding="utf-8")

    finding = Finding(
        severity="warning",
        check="java-naming",
        summary="Method 'statusByWaybill' looks like map-style naming",
        file=str(java_file),
        line=15,
    )

    assert (
        finding.task_todo_line()
        == f"- [ ] `{java_file.resolve()}:15` — Method 'statusByWaybill' looks like map-style naming"
    )
    assert (
        finding.task_todo_line(done=True)
        == f"- [x] `{java_file.resolve()}:15` — Method 'statusByWaybill' looks like map-style naming"
    )


def test_report_to_task_todos_with_no_findings():
    report = Report(target="/repo")
    assert report.to_task_todos() == "- [x] No validation findings."


def test_report_to_task_todos_lists_invalid_findings(tmp_path):
    java_file = tmp_path / "Bad.java"
    java_file.write_text("class Bad {}", encoding="utf-8")

    report = Report(target=str(tmp_path))
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
    assert "Unused import 'List'" in lines[0]
