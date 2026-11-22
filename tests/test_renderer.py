import parse_html5
from parse_html5 import Attribute, Element, Text


def test_safe_render_escapes_text_and_attributes():
    document = parse_html5.parse('<p title="a &quot;b&quot;"><script>alert("x")</script><b onclick="run()">x < y</b></p>')
    output = document.to_html()
    assert '<p title="a &quot;b&quot;">' in output
    assert 'onclick=' not in output
    assert 'alert("x")' in output
    assert "x &lt; y" in output


def test_unsafe_urls_are_removed_and_void_elements_do_not_close():
    element = Element(
        "a",
        (Attribute("href", "javascript:alert(1)"),),
        (Text("link"),),
    )
    assert parse_html5.render(element) == "<a>link</a>"
    assert parse_html5.render(Element("br", void=True)) == "<br>"


def test_fragment_render():
    fragment = parse_html5.parse_fragment('<p>one</p><p>two &amp; three</p>')
    assert parse_html5.render(fragment) == "<p>one</p><p>two &amp; three</p>"
