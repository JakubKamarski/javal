from __future__ import annotations

from validator.java.context import JavaFileContext


def gwt_section_markers(context: JavaFileContext, method_node) -> list[tuple[str, int]]:
    block = next((child for child in method_node.children if child.type == "block"), None)
    if block is None:
        return []

    markers: list[tuple[str, int]] = []
    for node in block.children:
        if node.type != "line_comment":
            continue
        label = context.text(node).strip().removeprefix("//").strip().upper()
        if label in {"GIVEN", "WHEN", "THEN"}:
            markers.append((label, node.start_point[0] + 1))
    return markers


def parse_gwt_section_line_ranges(context: JavaFileContext, method_node) -> dict[str, tuple[int, int]]:
    markers = gwt_section_markers(context, method_node)

    if not markers:
        return {}

    method_end_line = method_node.end_point[0] + 1
    sections: dict[str, tuple[int, int]] = {}
    for index, (label, marker_line) in enumerate(markers):
        start_line = marker_line + 1
        if index + 1 < len(markers):
            end_line = markers[index + 1][1] - 1
        else:
            end_line = method_end_line - 1
        sections[label] = (start_line, end_line)

    return sections


def line_in_range(line: int, line_range: tuple[int, int]) -> bool:
    start_line, end_line = line_range
    return start_line <= line <= end_line
