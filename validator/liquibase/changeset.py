from __future__ import annotations

import re
from dataclasses import dataclass

CHANGE_SET_OPEN_PATTERN = re.compile(r"<changeSet\b", re.IGNORECASE)
CHANGE_SET_CLOSE_PATTERN = re.compile(r"</changeSet>", re.IGNORECASE)
CHANGE_SET_SELF_CLOSE_PATTERN = re.compile(r"<changeSet\b[^>]*/>", re.IGNORECASE)
ID_ATTR_PATTERN = re.compile(r"""\bid\s*=\s*["']([^"']+)["']""", re.IGNORECASE)
AUTHOR_ATTR_PATTERN = re.compile(r"""\bauthor\s*=\s*["']([^"']*)["']""", re.IGNORECASE)


@dataclass(frozen=True)
class ChangeSet:
    changeset_id: str
    author: str
    start_line: int
    end_line: int


def parse_changesets(source: str) -> list[ChangeSet]:
    changesets: list[ChangeSet] = []
    lines = source.splitlines()

    index = 0
    while index < len(lines):
        line_number = index + 1
        line = lines[index]

        if CHANGE_SET_SELF_CLOSE_PATTERN.search(line):
            changesets.append(_build_changeset(line, line_number, line_number))
            index += 1
            continue

        if CHANGE_SET_OPEN_PATTERN.search(line):
            start_line = line_number
            attrs = line
            depth = 1
            index += 1
            while index < len(lines) and depth > 0:
                current_line = lines[index]
                current_line_number = index + 1
                depth += len(CHANGE_SET_OPEN_PATTERN.findall(current_line))
                depth -= len(CHANGE_SET_CLOSE_PATTERN.findall(current_line))
                if depth == 0:
                    changesets.append(_build_changeset(attrs, start_line, current_line_number))
                index += 1
            continue

        index += 1

    return changesets


def _build_changeset(attrs: str, start_line: int, end_line: int) -> ChangeSet:
    return ChangeSet(
        changeset_id=_extract_attr(ID_ATTR_PATTERN, attrs),
        author=_extract_attr(AUTHOR_ATTR_PATTERN, attrs),
        start_line=start_line,
        end_line=end_line,
    )


def _extract_attr(pattern: re.Pattern[str], text: str) -> str:
    match = pattern.search(text)
    return match.group(1) if match else ""
