# Validate

Zero-dependency runtime validator for TypedDict and dataclass types with JSON Schema generation -- stdlib only, Python 3.10+.

> **Replaces:** `pydantic` (validation), `cattrs`, `typeguard`, `marshmallow`

## Overview

The Validate module provides runtime validation of arbitrary data against stdlib type annotations (`TypedDict`, `dataclass`, `Annotated` constraints) and generates JSON Schema from the same type definitions -- all without any third-party dependencies.

| File | Description | Dependencies |
|------|-------------|--------------|
| `validate.py` | Pure Python implementation | None (stdlib only: `typing`, `dataclasses`, `re`) |

The module supports TypedDict and dataclass validation, `Annotated` constraints (Gt, Ge, Lt, Le, MinLen, MaxLen, Match, Predicate), `FieldValidator` for per-field transformation and validation, `model_validator` for cross-field checks, `Union`/`Optional`/`Literal` types, discriminated unions, nested structures, optional type coercion, structured error collection with dotted field paths, and JSON Schema generation.

!!! note "v0.4.1 Performance & Correctness"
    Internal field-introspection helpers (`_typeddict_fields`, `_dataclass_fields`, `_find_discriminator`) are now cached with `functools.lru_cache`, avoiding redundant `get_type_hints()` calls and providing **8-10x speedup** for complex nested TypedDict structures. A new `_strip_required()` helper correctly unwraps `Required[T]`/`NotRequired[T]` wrappers so that discriminated union matching works reliably when union members use these annotations.

## How to Use in Your Project

Just copy the single `.py` file into your project:

```bash
cp validate/validate.py your_project/
```

Then import directly:

```python
from validate import validate, json_schema, ValidationError
from validate import Gt, Ge, Lt, Le, MinLen, MaxLen, Match, Predicate
from validate import FieldValidator, model_validator
```

!!! note "typing_extensions"
    On Python 3.10, `typing_extensions` is needed for `Required`/`NotRequired` support. On 3.11+ everything comes from stdlib `typing`.

## Usage Examples

### Basic TypedDict Validation

```python
from typing import TypedDict
from validate import validate, ValidationError

class User(TypedDict):
    name: str
    age: int

# Valid data passes through
validate({"name": "Alice", "age": 30}, User)

# Invalid data raises ValidationError with all errors
try:
    validate({"name": 123, "age": "thirty"}, User)
except ValidationError as e:
    for err in e.errors:
        print(f"{err.path}: expected {err.expected}, got {err.actual}")
        # name: expected str, got int
        # age: expected int, got str
```

### Annotated Constraints

```python
from typing import Annotated, TypedDict
from validate import validate, Gt, Ge, Le, MinLen, MaxLen, Match

class Product(TypedDict):
    name: Annotated[str, MinLen(1), MaxLen(100)]
    price: Annotated[float, Gt(0)]
    quantity: Annotated[int, Ge(0), Le(10000)]
    sku: Annotated[str, Match(r"[A-Z]{2}-\d{4}")]

validate({
    "name": "Widget",
    "price": 9.99,
    "quantity": 100,
    "sku": "AB-1234",
}, Product)
```

### Nested Structures

```python
from typing import TypedDict
from validate import validate

class Address(TypedDict):
    street: str
    city: str
    zip_code: str

class UserProfile(TypedDict):
    name: str
    address: Address

# Errors include dotted paths like "address.street"
validate({
    "name": "Alice",
    "address": {"street": "123 Main St", "city": "NYC", "zip_code": "10001"},
}, UserProfile)
```

### Optional and Union Types

```python
from typing import Literal, Optional, TypedDict, Union
from validate import validate

class TextContent(TypedDict):
    kind: Literal["text"]
    text: str

class ImageContent(TypedDict):
    kind: Literal["image"]
    url: str

# Discriminated union -- dispatches via shared "kind" field
Content = Union[TextContent, ImageContent]

validate({"kind": "text", "text": "hello"}, Content)
validate({"kind": "image", "url": "https://..."}, Content)
```

### Required / NotRequired Fields

```python
from typing import TypedDict
from typing_extensions import NotRequired, Required
from validate import validate

class Config(TypedDict):
    host: str
    port: Required[int]
    debug: NotRequired[bool]

validate({"host": "localhost", "port": 8080}, Config)            # ok
validate({"host": "localhost", "port": 8080, "debug": True}, Config)  # ok
```

### Dataclass Validation

```python
import dataclasses
from validate import validate

@dataclasses.dataclass
class Point:
    x: float
    y: float
    z: float = 0.0

# Validates dict data against the dataclass definition
validate({"x": 1.0, "y": 2.0}, Point)           # ok, z has default
validate({"x": 1.0, "y": 2.0, "z": 3.0}, Point) # ok
```

### Type Coercion

```python
from validate import validate

# Strict mode (default) -- rejects type mismatches
# validate("42", int)  # raises ValidationError

# Coercion mode -- converts compatible types
result = validate("42", int, coerce=True)   # returns 42
result = validate("3.14", float, coerce=True)  # returns 3.14
```

### JSON Schema Generation

```python
from typing import Annotated, TypedDict
from validate import json_schema, Gt, MinLen, MaxLen

class Item(TypedDict):
    name: Annotated[str, MinLen(1), MaxLen(100)]
    price: Annotated[float, Gt(0)]
    tags: list[str]

schema = json_schema(Item)
# {
#   "type": "object",
#   "properties": {
#     "name": {"type": "string", "minLength": 1, "maxLength": 100},
#     "price": {"type": "number", "exclusiveMinimum": 0},
#     "tags": {"type": "array", "items": {"type": "string"}}
#   },
#   "required": ["name", "price", "tags"],
#   "title": "Item"
# }
```

### Custom Predicate

```python
from typing import Annotated
from validate import validate, Predicate

EvenInt = Annotated[int, Predicate(lambda x: x % 2 == 0, "must be even")]

validate(4, EvenInt)   # ok
validate(3, EvenInt)   # raises: Constraint must be even failed
```

### Field Validators

`FieldValidator` is like `Predicate` but can **transform** the value and raises exceptions to signal failure (instead of returning bool). Use it with `Annotated` for per-field validation and normalization.

```python
from typing import Annotated, TypedDict
from validate import validate, FieldValidator, MinLen

def strip_lower(v: str) -> str:
    """Strip whitespace and lowercase."""
    v = v.strip().lower()
    if not v:
        raise ValueError("must not be empty after stripping")
    return v

class User(TypedDict):
    username: Annotated[str, FieldValidator(strip_lower, "strip_lower"), MinLen(2)]
    age: int

# FieldValidator transforms the value, then MinLen checks the result
validate({"username": "  ALICE  ", "age": 30}, User)
```

Multiple `FieldValidator`s compose left-to-right -- the output of one feeds into the next:

```python
Cleaned = Annotated[
    str,
    FieldValidator(lambda v: v.strip(), "strip"),
    FieldValidator(lambda v: v.lower(), "lower"),
]
validate("  HELLO  ", Cleaned)  # returns "hello"
```

### Model Validators

`model_validator` registers a cross-field validator on a TypedDict or dataclass type. It runs **after** all field validation passes.

```python
from typing import TypedDict
from validate import validate, model_validator

class RegisterForm(TypedDict):
    password: str
    confirm: str

@model_validator(RegisterForm)
def passwords_match(data: dict) -> dict:
    if data["password"] != data["confirm"]:
        raise ValueError("passwords do not match")
    return data

validate({"password": "secret", "confirm": "secret"}, RegisterForm)   # ok
validate({"password": "secret", "confirm": "wrong"}, RegisterForm)    # raises
```

Key behaviors:

- Model validators only run if **all field validations pass** (no type errors, no missing fields)
- Validators receive the full data dict and should return it (possibly modified)
- Raise `ValueError` or `AssertionError` to signal failure
- Multiple validators on the same type run in registration order

## API Reference

### `validate(data, tp, *, coerce=False)`

Validate data against a type annotation.

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `data` | `Any` | -- | The data to validate. |
| `tp` | `type` | -- | A TypedDict class, dataclass class, or any type annotation. |
| `coerce` | `bool` | `False` | If True, attempt type coercion (e.g. str to int). |

**Returns:** The validated (and possibly coerced) data.

**Raises:** `ValidationError` with all errors collected.

---

### `json_schema(tp, *, title=None)`

Generate a JSON Schema dict from a type annotation.

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `tp` | `type` | -- | A TypedDict class, dataclass class, or any type annotation. |
| `title` | `str \| None` | `None` | Optional title. Defaults to the type's `__name__`. |

**Returns:** A JSON Schema dict (draft 2020-12 compatible subset).

---

### Constraint Annotations

All constraints are frozen dataclasses usable with `typing.Annotated`.

| Constraint | Meaning | JSON Schema |
|------------|---------|-------------|
| `Gt(val)` | `> val` | `exclusiveMinimum` |
| `Ge(val)` | `>= val` | `minimum` |
| `Lt(val)` | `< val` | `exclusiveMaximum` |
| `Le(val)` | `<= val` | `maximum` |
| `MinLen(val)` | `len >= val` | `minLength` / `minItems` |
| `MaxLen(val)` | `len <= val` | `maxLength` / `maxItems` |
| `Match(pattern)` | `re.fullmatch` | `pattern` |
| `Predicate(fn, desc)` | Custom check | *(not mapped)* |
| `FieldValidator(fn, desc)` | Custom transform + validate | *(not mapped)* |

---

### `model_validator(tp)`

Decorator to register a cross-field validator on a TypedDict or dataclass type.

**Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `tp` | `type` | The TypedDict or dataclass type to attach the validator to. |

**Returns:** A decorator that registers the function and returns it unchanged.

The registered function receives the full data dict after all field validation passes. It should return the dict (possibly modified) or raise `ValueError` / `AssertionError`.

---

### `ValidationError`

Raised when validation fails. Subclass of `Exception`.

| Attribute | Type | Description |
|-----------|------|-------------|
| `errors` | `list[ErrorDetail]` | All validation errors found. |

### `ErrorDetail`

Dataclass describing a single validation error.

| Field | Type | Description |
|-------|------|-------------|
| `path` | `str` | Dotted/bracketed path (e.g. `"items[2].name"`). |
| `expected` | `str` | Expected type or constraint. |
| `actual` | `str` | Actual type or value. |
| `message` | `str` | Human-readable error message. |

## Comparison with pydantic

| Feature | zerodep validate | pydantic v2 |
|---------|-----------------|-------------|
| Dependencies | None (stdlib only) | `pydantic-core` (Rust) |
| Type system | Enhances stdlib TypedDict/dataclass | Custom `BaseModel` |
| Validation | `validate(data, TypedDict)` | `Model.model_validate(data)` |
| Constraints | `Annotated[int, Gt(0)]` | `Annotated[int, Field(gt=0)]` |
| JSON Schema | `json_schema(TypedDict)` | `Model.model_json_schema()` |
| Error collection | Yes (all errors) | Yes (all errors) |
| Discriminated unions | Auto-detected via Literal fields | Explicit `Discriminator` |
| Coercion | `coerce=True` flag | Default behavior (strict mode opt-in) |
| Serialization | No | Yes |
| Custom validators | `FieldValidator`, `model_validator`, `Predicate` | `@field_validator`, `@model_validator` |
| Performance | Pure Python (~3.3 us simple with caching; beats pydantic on bulk data) | Rust core (~0.6 us simple) |
| Implementation | Single file (~500 lines) | Package (Rust extension) |

**When to use zerodep:** You want zero dependencies, already use TypedDict/dataclass, and need validation + JSON Schema without adopting a new type system.

**When to use pydantic:** You need maximum performance, serialization, or pydantic's ecosystem (FastAPI, SQLModel, etc.).

## Benchmark

Benchmarked against `pydantic` v2 across simple/nested/constrained validation and JSON Schema generation.

See [Validate Benchmark](../benchmarks/validate.md) for detailed results.
