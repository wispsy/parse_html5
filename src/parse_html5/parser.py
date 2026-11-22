"""A dependency-free source-preserving HTML5 parser."""

from __future__ import annotations

from dataclasses import dataclass
from html import unescape
from html.parser import HTMLParser
from typing import Iterable

from .nodes import (
    Attribute,
    Comment,
    Doctype,
    Document,
    Element,
    Fragment,
    ProcessingInstruction,
    RAW_TEXT_ELEMENTS,
    SourceSpan,
    Text,
    VOID_ELEMENTS,
)


class ParseError(ValueError):
    pass


@dataclass(frozen=True)
class ParseOptions:
    """Reserved parsing options; parsing is currently source-preserving."""


class _Builder:
    def __init__(self, name: str, attrs: tuple[Attribute, ...], span: SourceSpan | None, source: str | None) -> None:
        self.name = name
        self.attrs = attrs
        self.span = span
        self.source = source
        self.children: list[object] = []


class _HTML5Parser(HTMLParser):
    def __init__(self, source: str) -> None:
        super().__init__(convert_charrefs=False)
        self.source = source
        self.root: list[object] = []
        self.stack: list[_Builder] = []
        self.line_starts = [0]
        for index, char in enumerate(source):
            if char == "\n":
                self.line_starts.append(index + 1)

    def _offset(self, line: int, column: int) -> int:
        line_index = max(0, line - 1)
        if line_index >= len(self.line_starts):
            return len(self.source)
        return min(len(self.source), self.line_starts[line_index] + column)

    def _span(self, start_line: int, start_column: int, end: int) -> SourceSpan:
        start = self._offset(start_line, start_column)
        line_index = __import__("bisect").bisect_right(self.line_starts, end) - 1
        line_index = max(0, line_index)
        line = line_index + 1
        column = end - self.line_starts[line_index]
        return SourceSpan(start, end, start_line, start_column, line, column)

    def _slice_to_tag_end(self) -> tuple[int, str, SourceSpan]:
        line, column = self.getpos()
        start = self._offset(line, column)
        end = self.source.find(">", start)
        if end < 0:
            end = len(self.source)
        else:
            end += 1
        return start, self.source[start:end], self._span(line, column, end)

    def _append(self, node: object) -> None:
        if self.stack:
            self.stack[-1].children.append(node)
        else:
            self.root.append(node)

    def _close_at(self, index: int, end: int | None = None) -> None:
        builders = self.stack[index:]
        del self.stack[index:]
        for builder in reversed(builders):
            span = builder.span
            source = builder.source
            if end is not None and span is not None:
                line_index = __import__("bisect").bisect_right(self.line_starts, end) - 1
                line_index = max(0, line_index)
                span = SourceSpan(span.start, end, span.line, span.column,
                                  line_index + 1, end - self.line_starts[line_index])
                source = self.source[span.start:end]
            element = Element(
                builder.name,
                tuple(builder.attrs),
                tuple(builder.children),
                builder.name in VOID_ELEMENTS,
                span=span,
                source=source,
            )
            if self.stack:
                self.stack[-1].children.append(element)
            else:
                self.root.append(element)

    def _close(self, name: str, end: int | None = None) -> bool:
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index].name == name:
                self._close_at(index, end)
                return True
        return False

    def _autoclose_before_start(self, name: str) -> None:
        optional = {
            "p": {"address", "article", "aside", "blockquote", "div", "dl", "fieldset",
                   "footer", "form", "h1", "h2", "h3", "h4", "h5", "h6", "header",
                   "hr", "main", "nav", "ol", "p", "pre", "section", "table", "ul"},
            "li": {"li"},
            "dt": {"dt", "dd"},
            "dd": {"dt", "dd"},
            "option": {"option"},
            "rt": {"rt", "rp"},
            "rp": {"rt", "rp"},
            "thead": {"tbody", "tfoot"},
            "tbody": {"thead", "tbody", "tfoot"},
            "tfoot": {"thead", "tbody"},
            "tr": {"tr"},
            "td": {"td", "th", "tr"},
            "th": {"td", "th", "tr"},
        }
        if not self.stack:
            return
        open_names = {builder.name for builder in self.stack}
        for open_name in optional:
            if open_name in open_names and name in optional[open_name]:
                self._close(open_name)
                break

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        name = tag.lower()
        self._autoclose_before_start(name)
        start, raw, span = self._slice_to_tag_end()
        parsed_attrs = tuple(
            Attribute(
                (attr_name or "").lower(),
                unescape(attr_value or ""),
                source=None,
            )
            for attr_name, attr_value in attrs
        )
        if name in VOID_ELEMENTS:
            self._append(Element(name, parsed_attrs, (), True, span=span, source=raw))
            return
        self.stack.append(_Builder(name, parsed_attrs, span, raw))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        name = tag.lower()
        start, raw, span = self._slice_to_tag_end()
        parsed_attrs = tuple(
            Attribute((attr_name or "").lower(), unescape(attr_value or ""), source=None)
            for attr_name, attr_value in attrs
        )
        self._append(Element(name, parsed_attrs, (), name in VOID_ELEMENTS, span=span, source=raw))

    def handle_endtag(self, tag: str) -> None:
        name = tag.lower()
        start, raw, span = self._slice_to_tag_end()
        self._close(name, span.end)

    def handle_data(self, data: str) -> None:
        line, column = self.getpos()
        start = self._offset(line, column)
        end = min(len(self.source), start + len(data))
        span = self._span(line, column, end)
        raw = self.source[start:end]
        in_raw_text = bool(self.stack and self.stack[-1].name in RAW_TEXT_ELEMENTS)
        value = data if in_raw_text else unescape(data)
        self._append(Text(value, in_raw_text, span=span, source=raw))

    def handle_entityref(self, name: str) -> None:
        line, column = self.getpos()
        start = self._offset(line, column)
        raw = "&" + name + ";"
        end = start + len(raw)
        span = self._span(line, column, end)
        self._append(Text(unescape(raw), False, span=span, source=raw))

    def handle_charref(self, name: str) -> None:
        line, column = self.getpos()
        start = self._offset(line, column)
        raw = "&#" + name + ";"
        end = start + len(raw)
        span = self._span(line, column, end)
        self._append(Text(unescape(raw), False, span=span, source=raw))

    def handle_comment(self, data: str) -> None:
        line, column = self.getpos()
        start = self._offset(line, column)
        end = self.source.find("-->", start)
        if end < 0:
            end = len(self.source)
        else:
            end += 3
        raw = self.source[start:end]
        span = self._span(line, column, end)
        self._append(Comment(data, span=span, source=raw))

    def handle_decl(self, decl: str) -> None:
        line, column = self.getpos()
        start = self._offset(line, column)
        end = self.source.find(">", start)
        if end < 0:
            end = len(self.source)
        else:
            end += 1
        raw = self.source[start:end]
        span = self._span(line, column, end)
        self._append(Doctype(decl, span=span, source=raw))

    unknown_decl = handle_decl

    def handle_pi(self, data: str) -> None:
        line, column = self.getpos()
        start = self._offset(line, column)
        end = self.source.find(">", start)
        if end < 0:
            end = len(self.source)
        else:
            end += 1
        raw = self.source[start:end]
        span = self._span(line, column, end)
        self._append(ProcessingInstruction(data, span=span, source=raw))

    def finish(self) -> list[object]:
        while self.stack:
            builder = self.stack.pop()
            element = Element(
                builder.name,
                tuple(builder.attrs),
                tuple(builder.children),
                builder.name in VOID_ELEMENTS,
                span=builder.span,
                source=builder.source,
            )
            if self.stack:
                self.stack[-1].children.append(element)
            else:
                self.root.append(element)
        return self.root


def decode_entities(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError("Entity input must be a string.")
    return unescape(value)


def parse(source: str, *, fragment: bool = False, options: ParseOptions | None = None) -> Document | Fragment:
    if not isinstance(source, str):
        raise TypeError("HTML source must be a string.")
    parser = _HTML5Parser(source)
    parser.feed(source)
    parser.close()
    children = tuple(parser.finish())
    if fragment:
        return Fragment(children, span=SourceSpan(0, len(source), 1, 0, 1 + source.count("\n"),
                         len(source.rsplit("\n", 1)[-1])), source=source)
    return Document(children, fragment=False, span=SourceSpan(
        0, len(source), 1, 0, 1 + source.count("\n"), len(source.rsplit("\n", 1)[-1])), source=source)


def parse_fragment(source: str, *, options: ParseOptions | None = None) -> Fragment:
    return parse(source, fragment=True, options=options)
