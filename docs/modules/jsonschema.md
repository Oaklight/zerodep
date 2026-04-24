# JSON Schema Flattener

Zero-dependency JSON Schema flattening & sanitization -- stdlib only, Python 3.10+.

## Overview

The `jsonschema` module flattens complex JSON Schemas containing `$ref`, `allOf`, `anyOf`, and `oneOf` into simple, LLM-provider-compatible schemas. Designed for tool schemas consumed by Anthropic, OpenAI, and Google GenAI APIs.

| File | Description | Dependencies |
|------|-------------|--------------|
| `jsonschema.py` | Pure Python implementation | None (stdlib only) |

### Key Features

- **`$ref` resolution** -- inline all local `$ref` pointers (`#/$defs/...`, `#/definitions/...`), merge sibling keys
- **`allOf` merging** -- deep-merge multiple sub-schemas with proper semantics (property merge, required union, type intersection, numeric constraint tightening)
- **`anyOf`/`oneOf` simplification** -- nullable detection, single-variant unwrap, multi-variant fallback
- **Schema sanitization** -- strip unsupported keywords (`$schema`, `$id`, `const`, `examples`, etc.), validate `required` subset of `properties`
- **Layered pipeline** -- each phase is independently callable: `resolve_refs` -> `merge_allof` -> `simplify_unions` -> `sanitize`
- **Immutable** -- all functions deep-copy input, never mutate the original schema

## How to Use in Your Project

Copy the module file into your project:

```bash
cp jsonschema/jsonschema.py your_project/
```

Then import:

```python
from jsonschema import flatten_schema
```

## Usage Examples

### One-Call Flattening

```python
from jsonschema import flatten_schema

schema = {
    "type": "object",
    "properties": {
        "user": {"$ref": "#/$defs/User"},
        "role": {
            "anyOf": [
                {"type": "string", "enum": ["admin", "user"]},
                {"type": "null"},
            ],
        },
    },
    "$defs": {
        "User": {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        }
    },
}

result = flatten_schema(schema)
# {
#     "type": "object",
#     "properties": {
#         "user": {
#             "type": "object",
#             "properties": {"name": {"type": "string"}},
#             "required": ["name"],
#         },
#         "role": {
#             "type": "string",
#             "enum": ["admin", "user"],
#             "nullable": True,
#         },
#     },
# }
```

### Step-by-Step Pipeline

```python
from jsonschema import resolve_refs, merge_allof, simplify_unions, sanitize

# Phase 1: Resolve $ref pointers
resolved = resolve_refs(schema)

# Phase 2: Merge allOf sub-schemas
merged = merge_allof(resolved)

# Phase 3: Simplify anyOf/oneOf
simplified = simplify_unions(merged)

# Phase 4: Strip unsupported keys and validate required
clean = sanitize(simplified)
```

### Merging allOf with Deep Semantics

```python
from jsonschema import flatten_schema

schema = {
    "allOf": [
        {
            "type": "object",
            "properties": {
                "age": {"type": "integer", "minimum": 0, "maximum": 150},
            },
            "required": ["age"],
        },
        {
            "type": "object",
            "properties": {
                "age": {"type": "integer", "minimum": 18, "maximum": 120},
                "name": {"type": "string"},
            },
            "required": ["name"],
        },
    ],
}

result = flatten_schema(schema)
# age constraints are tightened: minimum=18 (max of 0,18), maximum=120 (min of 150,120)
# required is the union: ["age", "name"]
```

### Custom Strip Keys

```python
from jsonschema import flatten_schema, UNSUPPORTED_SCHEMA_KEYS

# Add extra keys to strip
extra = UNSUPPORTED_SCHEMA_KEYS | {"title", "description"}
result = flatten_schema(schema, strip_keys=extra)
```

## Pipeline Architecture

```
Input Schema
    |
    v
resolve_refs()      <- Phase 1: collect $defs/definitions, inline $ref, merge sibling keys
    |
    v
merge_allof()       <- Phase 2: recursively find allOf, deep-merge all sub-schemas
    |
    v
simplify_unions()   <- Phase 3: recursively find anyOf/oneOf, detect nullable/single-variant
    |
    v
sanitize()          <- Phase 4: strip unsupported keys, prune required arrays
    |
    v
Output Schema
```

### Deep-Merge Semantics (Phase 2)

| Key | Strategy |
|-----|----------|
| `properties` | Recursively merge each sub-property |
| `required` | Union (deduplicated) |
| `type` | Intersection |
| `minimum`, `minLength`, `minItems` | Take max (more restrictive) |
| `maximum`, `maxLength`, `maxItems` | Take min (more restrictive) |
| `enum` | Intersection |
| `items` | Recursive deep-merge |
| Other keys | Override wins |

## API Reference

### `flatten_schema(schema, *, strip_keys=None)`

One-call full pipeline: resolve -> merge -> simplify -> sanitize.

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `schema` | `dict` | -- | The JSON Schema to flatten. |
| `strip_keys` | `set[str] \| None` | `None` | Keys to strip. Defaults to `UNSUPPORTED_SCHEMA_KEYS`. |

**Returns:** `dict` -- the flattened schema.

### `resolve_refs(schema)`

Resolve local `$ref` pointers and inline definitions.

### `merge_allof(schema)`

Deep-merge `allOf` sub-schemas into a single schema.

### `simplify_unions(schema)`

Simplify `anyOf`/`oneOf`: nullable detection, single-variant unwrap.

### `sanitize(schema, *, strip_keys=None)`

Strip unsupported keywords and validate `required` is a subset of `properties`.

### `UNSUPPORTED_SCHEMA_KEYS`

Default set of JSON Schema keywords to strip:

`$schema`, `$id`, `$comment`, `$anchor`, `$dynamicAnchor`, `$dynamicRef`, `contentEncoding`, `contentMediaType`, `contentSchema`, `deprecated`, `readOnly`, `writeOnly`, `examples`, `propertyNames`, `const`

## Comparison with Alternatives

| Feature | zerodep jsonschema | allof-merge (JS) | llm-rosetta |
|---------|-------------------|------------------|-------------|
| Language | Python | JavaScript | Python |
| Dependencies | None (stdlib) | json-crawl | httpx, pydantic |
| `$ref` resolution | All contexts | Inside allOf only | Basic |
| `allOf` deep-merge | Full semantics | Full semantics | Single-element only |
| `anyOf`/`oneOf` simplify | Yes | No | Shallow (dict.update) |
| Schema sanitization | Yes | No | Yes |
| `required` validation | Yes | No | No |
| Standalone | Yes (single file) | Package | Part of gateway |

**When to use zerodep:** You need JSON Schema flattening in Python with zero dependencies, especially for LLM tool schemas.

**When to use allof-merge:** You're working in Node.js and only need `$ref` + `allOf` resolution.

## Benchmark

Performance comparison against `allof-merge` (JavaScript) across five schema complexity tiers.

See [JSON Schema Benchmark](../benchmarks/jsonschema.md) for detailed results.
