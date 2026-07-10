from __future__ import annotations

from dataclasses import dataclass
from xml.parsers import expat


@dataclass(frozen=True)
class ChangeSet:
    changeset_id: str
    author: str
    start_line: int
    end_line: int


def parse_changesets(source: str) -> list[ChangeSet]:
    changesets: list[ChangeSet] = []
    open_changesets: list[tuple[str, str, int]] = []
    parser = expat.ParserCreate(namespace_separator="}")

    def local_name(name: str) -> str:
        return name.rsplit("}", maxsplit=1)[-1]

    def start_element(name: str, attributes: dict[str, str]) -> None:
        if local_name(name) != "changeSet":
            return
        normalized_attributes = {
            local_name(attribute_name): value
            for attribute_name, value in attributes.items()
        }
        open_changesets.append(
            (
                normalized_attributes.get("id", ""),
                normalized_attributes.get("author", ""),
                parser.CurrentLineNumber,
            )
        )

    def end_element(name: str) -> None:
        if local_name(name) != "changeSet" or not open_changesets:
            return
        changeset_id, author, start_line = open_changesets.pop()
        changesets.append(
            ChangeSet(
                changeset_id=changeset_id,
                author=author,
                start_line=start_line,
                end_line=parser.CurrentLineNumber,
            )
        )

    parser.StartElementHandler = start_element
    parser.EndElementHandler = end_element
    parser.Parse(source, True)
    return changesets
