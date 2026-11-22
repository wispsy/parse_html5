# parse-html5

Source-preserving HTML5 parsing and safe typed HTML rendering.
Python 3.14+, with no runtime dependencies.

```sh
python -m pip install parse-html5
```

```python
from parse_html5 import parse, parse_fragment, render

document = parse('<main><h1>Hello &amp; welcome</h1><br></main>')
assert document.children[0].name == "main"
assert document.children[0].source.startswith("<main>")
assert "&amp;" not in render(document)  # Text is escaped as needed

fragment = parse_fragment('<p>one</p><p>two</p>')
assert len(fragment.children) == 2
assert render(fragment) == "<p>one</p><p>two</p>"
```

The public AST uses immutable dataclasses for documents, fragments, elements,
text, comments, doctypes, processing instructions and attributes. Each node
can retain its exact source slice and code-point source span. HTML entities
are decoded through the stdlib entity table.

Rendering escapes element text and attribute values by default. It omits
event-handler attributes and unsafe executable URL schemes. The renderer
does not claim to be a full HTML sanitizer; callers that accept untrusted
HTML should apply application-specific policy.

Void elements and raw-text elements are recognized. Optional HTML end tags
receive common correction behavior, including paragraph, list-item, table,
definition-list and option closures.

Development and distribution qualification:

```sh
uv sync --locked
uv run --frozen python -m pytest
uv run --frozen python scripts/check_distribution.py --output-dir /tmp/parse-html5-candidate
```
