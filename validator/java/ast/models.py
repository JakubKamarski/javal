from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MethodDeclaration:
    name: str
    line: int
    node: object
    is_configuration_bean: bool = False
    is_override: bool = False
    is_test: bool = False
    is_lifecycle: bool = False
    is_record_accessor: bool = False


@dataclass(frozen=True)
class VariableDeclaration:
    name: str
    line: int
    is_constant: bool
    node: object


@dataclass(frozen=True)
class LocalVariableDeclaration:
    name: str
    line: int
    node: object
    type_text: str


@dataclass(frozen=True)
class VarDeclaration:
    name: str
    line: int


@dataclass(frozen=True)
class ImportDeclaration:
    symbol: str
    line: int
    text: str
    node: object
