from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from validator.java.rules.registry import registered_check_ids
from validator.report import Finding

TODO_HEADER = """# javal todos

False positives and validator bugs reported during validation runs.

"""


def default_todo_path() -> Path:
    return Path(__file__).resolve().parent.parent / "todo.md"


def default_todo_registry_path() -> Path:
    return Path(__file__).resolve().parent.parent / "todo.jsonl"


def format_todo_line(file: Path, line: int, description: str) -> str:
    path = str(file.expanduser().resolve())
    return f"- [ ] `{path}:{line}` — {description.strip()}"


def source_line_hash(file: Path, line: int) -> str:
    resolved = file.expanduser().resolve()
    if not resolved.is_file():
        raise ValueError(f"Not a file: {resolved}")
    try:
        lines = resolved.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as error:
        raise ValueError(f"Cannot read source file {resolved}: {error}") from error
    if line <= 0 or line > len(lines):
        raise ValueError(
            f"Line {line} does not exist in {resolved}; file has {len(lines)} line(s)."
        )
    return hashlib.sha256(lines[line - 1].encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class TodoFingerprint:
    check: str
    file: str
    line: int
    source_line_hash: str

    @classmethod
    def from_finding(cls, finding: Finding) -> TodoFingerprint | None:
        if not finding.file or finding.line <= 0:
            return None
        try:
            fingerprint = source_line_hash(Path(finding.file), finding.line)
        except ValueError:
            return None
        return cls(
            check=finding.check,
            file=str(Path(finding.file).expanduser().resolve()),
            line=finding.line,
            source_line_hash=fingerprint,
        )


def load_todo_fingerprints(
    registry_path: Path | None = None,
) -> frozenset[TodoFingerprint]:
    target = registry_path or default_todo_registry_path()
    if not target.is_file():
        return frozenset()

    fingerprints: set[TodoFingerprint] = set()
    try:
        raw_lines = target.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError):
        return frozenset()
    for raw_line in raw_lines:
        try:
            record = json.loads(raw_line)
            fingerprint = TodoFingerprint(
                check=record["check"],
                file=record["file"],
                line=record["line"],
                source_line_hash=record["source_line_hash"],
            )
        except (json.JSONDecodeError, KeyError, TypeError):
            continue
        if (
            isinstance(fingerprint.check, str)
            and isinstance(fingerprint.file, str)
            and isinstance(fingerprint.line, int)
            and isinstance(fingerprint.source_line_hash, str)
        ):
            fingerprints.add(fingerprint)
    return frozenset(fingerprints)


def partition_accounted_findings(
    findings: Iterable[Finding],
    *,
    registry_path: Path | None = None,
) -> tuple[list[Finding], list[Finding]]:
    registered = load_todo_fingerprints(registry_path)
    unaccounted: list[Finding] = []
    accounted: list[Finding] = []
    for finding in findings:
        if not finding.is_invalid:
            unaccounted.append(finding)
            continue
        fingerprint = TodoFingerprint.from_finding(finding)
        if fingerprint is not None and fingerprint in registered:
            accounted.append(finding)
        else:
            unaccounted.append(finding)
    return unaccounted, accounted


def append_todo(
    file: Path,
    line: int,
    description: str,
    *,
    check: str | None = None,
    todo_path: Path | None = None,
    registry_path: Path | None = None,
) -> str:
    normalized_description = description.strip()
    if not normalized_description:
        raise ValueError("Description must not be empty.")

    if line < 0:
        raise ValueError(f"Line number must be non-negative: {line}")

    record: dict[str, object] | None = None
    if check is not None:
        normalized_check = check.strip()
        if normalized_check not in registered_check_ids():
            raise ValueError(f"Unknown check id: {check}")
        fingerprint = source_line_hash(file, line)
        record = {
            "check": normalized_check,
            "description": normalized_description,
            "file": str(file.expanduser().resolve()),
            "line": line,
            "source_line_hash": fingerprint,
        }

    target = todo_path or default_todo_path()
    entry = format_todo_line(file, line, normalized_description)

    if not target.exists():
        target.write_text(TODO_HEADER, encoding="utf-8")

    with target.open("a", encoding="utf-8") as handle:
        handle.write(f"{entry}\n")

    if record is not None:
        registry = registry_path or default_todo_registry_path()
        with registry.open("a", encoding="utf-8") as handle:
            handle.write(f"{json.dumps(record, sort_keys=True)}\n")

    return entry
