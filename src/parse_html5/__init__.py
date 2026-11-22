"""Typed, source-preserving HTML5 parsing and safe rendering."""

from .nodes import (
    Attribute,
    Comment,
    Doctype,
    Document,
    Element,
    Fragment,
    Node,
    ProcessingInstruction,
    SourceSpan,
    Text,
    VOID_ELEMENTS,
)
from .parser import ParseOptions, ParseError, decode_entities, parse, parse_fragment
from .renderer import render

__version__ = "0.1.0"

__all__ = [
    "Attribute",
    "Comment",
    "Doctype",
    "Document",
    "Element",
    "Fragment",
    "Node",
    "ParseError",
    "ParseOptions",
    "ProcessingInstruction",
    "SourceSpan",
    "Text",
    "VOID_ELEMENTS",
    "decode_entities",
    "parse",
    "parse_fragment",
    "render",
    "__version__",
]
