import pytest
from pathlib import Path

from validate import main, parse_args, parse_todo_args
from validator.todo import append_todo, default_todo_path, format_todo_line


def test_default_todo_path_points_to_repo_root():
    path = default_todo_path()
    assert path.name == "todo.md"
    assert (path.parent / "validate.py").is_file()


def test_format_todo_line_uses_absolute_path(tmp_path):
    java_file = tmp_path / "src" / "Foo.java"
    java_file.parent.mkdir()
    java_file.write_text("class Foo {}", encoding="utf-8")

    line = format_todo_line(java_file, 42, "False positive: unused-imports")

    assert line == (
        f"- [ ] `{java_file.resolve()}:42` — False positive: unused-imports"
    )


def test_append_todo_creates_header_and_entry(tmp_path):
    todo_path = tmp_path / "todo.md"
    java_file = tmp_path / "Foo.java"
    java_file.write_text("class Foo {}", encoding="utf-8")

    entry = append_todo(
        java_file,
        15,
        "Bug: verb-prefix rule triggers on @Bean method",
        todo_path=todo_path,
    )

    content = todo_path.read_text(encoding="utf-8")
    assert content.startswith("# javal todos\n")
    assert entry in content
    assert content.endswith(
        f"- [ ] `{java_file.resolve()}:15` — Bug: verb-prefix rule triggers on @Bean method\n"
    )


def test_append_todo_appends_without_duplicate_header(tmp_path):
    todo_path = tmp_path / "todo.md"
    java_file = tmp_path / "Foo.java"
    java_file.write_text("class Foo {}", encoding="utf-8")

    append_todo(java_file, 1, "First issue", todo_path=todo_path)
    append_todo(java_file, 2, "Second issue", todo_path=todo_path)

    content = todo_path.read_text(encoding="utf-8")
    assert content.count("# javal todos") == 1
    assert "First issue" in content
    assert "Second issue" in content


def test_append_todo_rejects_empty_description(tmp_path):
    java_file = tmp_path / "Foo.java"
    java_file.write_text("class Foo {}", encoding="utf-8")

    with pytest.raises(ValueError, match="Description must not be empty"):
        append_todo(java_file, 1, "   ", todo_path=tmp_path / "todo.md")


def test_parse_args_routes_to_todo_subcommand():
    args = parse_args(
        [
            "todo",
            "--file",
            "/tmp/Foo.java",
            "--line",
            "42",
            "--description",
            "False positive",
        ]
    )

    assert args.command == "todo"
    assert args.file == Path("/tmp/Foo.java")
    assert args.line == 42
    assert args.description == "False positive"


def test_parse_args_routes_to_validate_by_default():
    args = parse_args(["ABC-5164", "."])

    assert args.command == "validate"
    assert args.task_id == "ABC-5164"
    assert args.repo_path == Path(".")


def test_run_todo_prints_entry_and_returns_zero(tmp_path, monkeypatch, capsys):
    todo_path = tmp_path / "todo.md"
    java_file = tmp_path / "Foo.java"
    java_file.write_text("class Foo {}", encoding="utf-8")
    monkeypatch.setattr("validate.append_todo", lambda *args, **kwargs: append_todo(
        *args, **{**kwargs, "todo_path": todo_path}
    ))

    exit_code = main(
        [
            "todo",
            "--file",
            str(java_file),
            "--line",
            "7",
            "--description",
            "False positive: unused-imports",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "False positive: unused-imports" in captured.out
    assert "unused-imports" in todo_path.read_text(encoding="utf-8")


def test_todo_help_contains_ai_guidance(capsys):
    with pytest.raises(SystemExit) as exc_info:
        parse_todo_args(["--help"])

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "false positive" in captured.out.lower()
    assert "--file" in captured.out
    assert "--line" in captured.out
    assert "--description" in captured.out


def test_validate_help_mentions_todo_subcommand(capsys):
    with pytest.raises(SystemExit) as exc_info:
        parse_args(["--help"])

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "javal todo" in captured.out
