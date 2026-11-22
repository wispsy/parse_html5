# API

## Parsing

`parse(source, *, fragment=False, options=None)` returns a `Document`.
`parse_fragment(source, *, options=None)` returns a `Fragment`.
`decode_entities(value)` decodes named and numeric HTML character references.

`ParseOptions` is the public reserved options type.

## AST

All nodes are immutable dataclasses. `Node` carries optional `span` and
`source` values. `SourceSpan` stores code-point offsets and 1-based line and
column locations. `Element` carries normalized lowercase name, immutable
attributes and immutable children.

## Rendering

`render(node, *, safe=True)` returns a string. Safe rendering escapes text
and attribute values, rejects invalid element and attribute names, removes
event-handler attributes and blocks executable URL schemes. Pass
`safe=False` only for application-controlled trusted AST values.
