from __future__ import annotations

from pathlib import Path

TODO_HEADER = """# javal todos

False positives and validator bugs reported during validation runs.

"""


def default_todo_path() -> Path:
    return Path(__file__).resolve().parent.parent / "todo.md"


def format_todo_line(file: Path, line: int, description: str) -> str:
    path = str(file.expanduser().resolve())
    return f"- [ ] `{path}:{line}` — {description.strip()}"


def append_todo(
    file: Path,
    line: int,
    description: str,
    *,
    todo_path: Path | None = None,
) -> str:
    normalized_description = description.strip()
    if not normalized_description:
        raise ValueError("Description must not be empty.")

    if line < 0:
        raise ValueError(f"Line number must be non-negative: {line}")

    target = todo_path or default_todo_path()
    entry = format_todo_line(file, line, normalized_description)

    if not target.exists():
        target.write_text(TODO_HEADER, encoding="utf-8")

    with target.open("a", encoding="utf-8") as handle:
        handle.write(f"{entry}\n")

    return entry
