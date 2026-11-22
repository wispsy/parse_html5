"""Safe typed HTML rendering."""

from __future__ import annotations

from html import escape
import re
from urllib.parse import urlsplit

from .nodes import (
    Attribute,
    Comment,
    Doctype,
    Document,
    Element,
    Fragment,
    ProcessingInstruction,
    RAW_TEXT_ELEMENTS,
    Text,
    VOID_ELEMENTS,
)


UNSAFE_URL_SCHEMES = frozenset({"javascript", "vbscript", "data"})
URL_ATTRIBUTES = frozenset({
    "href", "src", "action", "formaction", "poster", "cite",
    "longdesc", "manifest", "background", "xlink:href",
})
ATTRIBUTE_NAME = re.compile(r"[A-Za-z_:][A-Za-z0-9_.:-]*\Z")
FORBIDDEN_ATTRIBUTES = frozenset({
    "onabort", "onafterprint", "onbeforeprint", "onbeforeunload", "onblur",
    "oncancel", "oncanplay", "oncanplaythrough", "onchange", "onclick",
    "onclose", "oncontextmenu", "oncopy", "oncuechange", "oncut",
    "ondblclick", "ondrag", "ondragend", "ondragenter", "ondragleave",
    "ondragover", "ondragstart", "ondrop", "ondurationchange", "onemptied",
    "onended", "onerror", "onfocus", "onformchange", "onforminput",
    "onhashchange", "oninput", "oninvalid", "onkeydown", "onkeypress",
    "onkeyup", "onload", "onloadeddata", "onloadedmetadata", "onloadstart",
    "onmessage", "onmousedown", "onmouseenter", "onmouseleave",
    "onmousemove", "onmouseout", "onmouseover", "onmouseup", "onpaste",
    "onpause", "onplay", "onplaying", "onpopstate", "onprogress",
    "onratechange", "onreset", "onresize", "onscroll", "onseeked",
    "onseeking", "onselect", "onshow", "onstalled", "onsubmit",
    "onsuspend", "ontimeupdate", "ontoggle", "onunload", "onvolumechange",
    "onwaiting", "onwheel",
})


def _safe_attribute(attribute: Attribute) -> str | None:
    name = attribute.name.lower()
    if not ATTRIBUTE_NAME.fullmatch(name):
        return None
    if name in FORBIDDEN_ATTRIBUTES or name.startswith("on"):
        return None
    if name in URL_ATTRIBUTES:
        stripped = attribute.value.strip()
        if "\\" in stripped:
            return None
        scheme = urlsplit(stripped).scheme.casefold()
        if scheme in UNSAFE_URL_SCHEMES:
            return None
    value = escape(attribute.value, quote=True)
    return f' {name}="{value}"'


def render(node: object, *, safe: bool = True) -> str:
    if isinstance(node, str):
        return escape(node, quote=False)
    if isinstance(node, Text):
        return escape(node.value, quote=False)
    if isinstance(node, Comment):
        if not safe:
            return f"<!--{node.value}-->"
        value = node.value.replace("--", "- -").replace(">", "&gt;")
        return f"<!--{value}-->"
    if isinstance(node, Doctype):
        value = node.value if node.value.isascii() else ""
        return f"<!{value}>"
    if isinstance(node, ProcessingInstruction):
        return f"<?{escape(node.value, quote=False)}>"
    if isinstance(node, (Document, Fragment)):
        return "".join(render(child, safe=safe) for child in node.children)
    if isinstance(node, Element):
        name = node.name.lower()
        if not ATTRIBUTE_NAME.fullmatch(name):
            return "".join(render(child, safe=safe) for child in node.children)
        attrs = "".join(
            rendered
            for attribute in node.attributes
            if (rendered := _safe_attribute(attribute) if safe else
                f' {attribute.name.lower()}="{escape(attribute.value, quote=True)}"')
        )
        if node.void or name in VOID_ELEMENTS:
            return f"<{name}{attrs}>"
        content = "".join(render(child, safe=safe) for child in node.children)
        return f"<{name}{attrs}>{content}</{name}>"
    raise TypeError(f"Cannot render HTML node: {type(node).__name__}")
