import parse_html5
from parse_html5 import (
    Comment,
    Doctype,
    Document,
    Element,
    Fragment,
    Text,
)


def test_document_entities_comments_and_doctype():
    document = parse_html5.parse('<!DOCTYPE html><!-- note --><p>A &amp; &#66;</p>')
    assert isinstance(document, Document)
    assert isinstance(document.children[0], Doctype)
    assert document.children[0].value.lower() == "doctype html"
    assert isinstance(document.children[1], Comment)
    paragraph = document.children[2]
    assert isinstance(paragraph, Element)
    assert "".join(child.value for child in paragraph.children if isinstance(child, Text)) == "A & B"
    assert document.source == '<!DOCTYPE html><!-- note --><p>A &amp; &#66;</p>'


def test_fragment_void_attributes_and_optional_paragraph_closure():
    fragment = parse_html5.parse_fragment('<p class="lead">One<p>Two<img src="x.jpg" alt="X">')
    assert isinstance(fragment, Fragment)
    assert len(fragment.children) == 2
    first, second = fragment.children
    assert isinstance(first, Element) and first.name == "p"
    assert first.attributes[0].name == "class"
    assert first.attributes[0].value == "lead"
    assert isinstance(second, Element) and second.name == "p"
    img = second.children[1]
    assert isinstance(img, Element) and img.void
    assert img.name == "img"


def test_source_spans_and_raw_text():
    document = parse_html5.parse("<div>\n<script>if (a < b) x();</script>\n</div>")
    div = document.children[0]
    script = next(child for child in div.children if isinstance(child, Element))
    assert isinstance(script, Element)
    raw = script.children[0]
    assert isinstance(raw, Text)
    assert raw.raw
    assert raw.source == "if (a < b) x();"
    assert raw.span is not None
    assert raw.span.start >= 0


def test_decode_entities():
    assert parse_html5.decode_entities("Tom &amp; Jerry &#x1F600;") == "Tom & Jerry 😀"
