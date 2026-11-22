"""Immutable HTML nodes with source locations."""

from __future__ import annotations

from dataclasses import dataclass, field
from html import escape
from typing import Iterable


@dataclass(frozen=True)
class SourceSpan:
    start: int
    end: int
    line: int
    column: int
    end_line: int
    end_column: int

    def __post_init__(self) -> None:
        if self.start < 0 or self.end < self.start:
            raise ValueError("Invalid source span.")


@dataclass(frozen=True)
class Attribute:
    name: str
    value: str
    span: SourceSpan | None = field(default=None, compare=False, repr=False)
    source: str | None = field(default=None, compare=False, repr=False)

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not isinstance(self.value, str):
            raise TypeError("Attribute name and value must be strings.")


@dataclass(frozen=True, kw_only=True)
class Node:
    span: SourceSpan | None = field(default=None, compare=False, repr=False)
    source: str | None = field(default=None, compare=False, repr=False)

    def to_html(self, *, safe: bool = True) -> str:
        from .renderer import render

        return render(self, safe=safe)


@dataclass(frozen=True)
class Text(Node):
    value: str
    raw: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise TypeError("Text requires a string.")


@dataclass(frozen=True)
class Comment(Node):
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise TypeError("Comment requires a string.")


@dataclass(frozen=True)
class Doctype(Node):
    value: str


@dataclass(frozen=True)
class ProcessingInstruction(Node):
    value: str


@dataclass(frozen=True)
class Element(Node):
    name: str
    attributes: tuple[Attribute, ...] = ()
    children: tuple[Node, ...] = ()
    void: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name:
            raise TypeError("Element name must be a non-empty string.")
        if not all(isinstance(attribute, Attribute) for attribute in self.attributes):
            raise TypeError("Element attributes must be Attribute values.")
        if not all(isinstance(child, Node) for child in self.children):
            raise TypeError("Element children must be HTML nodes.")


@dataclass(frozen=True)
class Fragment(Node):
    children: tuple[Node, ...] = ()

    def __post_init__(self) -> None:
        if not all(isinstance(child, Node) for child in self.children):
            raise TypeError("Fragment children must be HTML nodes.")


@dataclass(frozen=True)
class Document(Node):
    children: tuple[Node, ...] = ()
    fragment: bool = False

    def __post_init__(self) -> None:
        if not all(isinstance(child, Node) for child in self.children):
            raise TypeError("Document children must be HTML nodes.")


VOID_ELEMENTS = frozenset({
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
})

RAW_TEXT_ELEMENTS = frozenset({"script", "style"})


def escape_text(value: str) -> str:
    return escape(value, quote=False)


def escape_attribute(value: str) -> str:
    return escape(value, quote=True)
