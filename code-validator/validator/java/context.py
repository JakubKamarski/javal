from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from validator.java.parser import node_text, parse_java, walk_nodes


@dataclass(frozen=True)
class JavaFileContext:
    path: str
    source: str
    root: object

    @classmethod
    def from_path(cls, file_path: Path) -> JavaFileContext:
        source = file_path.read_text(encoding="utf-8")
        return cls.from_source(str(file_path), source)

    @classmethod
    def from_source(cls, path: str, source: str) -> JavaFileContext:
        root = parse_java(source).root_node
        return cls(path=path, source=source, root=root)

    def text(self, node) -> str:
        return node_text(self.source, node)

    def walk(self, *node_types: str):
        return walk_nodes(self.root, *node_types)
