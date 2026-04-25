# Protobuf

Zero-dependency proto3 encoder/decoder using Python dataclass schemas -- stdlib only, Python 3.10+.

## Overview

The `protobuf` module encodes and decodes Protocol Buffers (proto3) wire format using plain Python dataclasses as message schemas. No `protoc` compiler, no `.proto` files, no C extensions.

| File | Description | Dependencies |
|------|-------------|--------------|
| `protobuf/protobuf.py` | Proto3 encoder/decoder | None (stdlib only) |

### Key Features

- **Dataclass schemas** — define messages with `@message` decorator + `field(number)`
- **Full proto3 scalar support** — int32/64, uint32/64, sint32/64, fixed32/64, sfixed32/64, float32, double, bool, string, bytes
- **Composite types** — nested messages, `repeated[T]`, `map_field[K, V]`, enums (`IntEnum`)
- **Oneof groups** — field grouping via `oneof="group_name"` parameter
- **Proto3 semantics** — zero-value fields not serialized, packed repeated scalars by default
- **Unknown field preservation** — unknown fields survive parse → serialize round-trips
- **Dict conversion** — `to_dict()` / `from_dict()` for JSON-friendly representation
- **Size calculation** — `byte_size()` computes serialized size without allocating bytes
- **No codegen** — no `.proto` files, no `protoc`, no build step

## How to Use in Your Project

```bash
cp protobuf/protobuf.py your_project/
```

```python
from protobuf import message, field, int32, repeated
```

## Usage Examples

### Basic Message

```python
from protobuf import message, field, int32

@message
class Person:
    name: str = field(1)
    id: int32 = field(2)
    email: str = field(3)

person = Person(name="Alice", id=123, email="alice@example.com")
data = person.serialize()    # bytes
parsed = Person.parse(data)  # Person instance
print(parsed.name)           # "Alice"
```

### All Scalar Types

```python
from protobuf import (
    message, field,
    int32, int64, uint32, uint64, sint32, sint64,
    fixed32, fixed64, sfixed32, sfixed64,
    float32, double, bool_,
)

@message
class Scalars:
    a: int32 = field(1)       # varint, 32-bit signed
    b: int64 = field(2)       # varint, 64-bit signed
    c: uint32 = field(3)      # varint, 32-bit unsigned
    d: uint64 = field(4)      # varint, 64-bit unsigned
    e: sint32 = field(5)      # varint + ZigZag, 32-bit
    f: sint64 = field(6)      # varint + ZigZag, 64-bit
    g: fixed32 = field(7)     # 4-byte little-endian unsigned
    h: fixed64 = field(8)     # 8-byte little-endian unsigned
    i: sfixed32 = field(9)    # 4-byte little-endian signed
    j: sfixed64 = field(10)   # 8-byte little-endian signed
    k: float32 = field(11)    # 4-byte IEEE 754
    l: double = field(12)     # 8-byte IEEE 754
    m: bool_ = field(13)      # varint (0 or 1)
    n: str = field(14)        # UTF-8 length-delimited
    o: bytes = field(15)      # raw length-delimited
```

### Nested Messages

```python
@message
class Address:
    street: str = field(1)
    city: str = field(2)

@message
class Company:
    name: str = field(1)
    address: Address = field(2)

company = Company(name="Acme", address=Address(street="123 Main St", city="Springfield"))
data = company.serialize()
parsed = Company.parse(data)
print(parsed.address.city)  # "Springfield"
```

### Repeated Fields

```python
from protobuf import message, field, int32, repeated

@message
class NumberList:
    values: repeated[int32] = field(1)  # packed encoding
    names: repeated[str] = field(2)     # length-delimited per element

obj = NumberList(values=[1, 2, 3, 4, 5], names=["a", "b", "c"])
parsed = NumberList.parse(obj.serialize())
print(parsed.values)  # [1, 2, 3, 4, 5]
print(parsed.names)   # ["a", "b", "c"]
```

### Map Fields

```python
from protobuf import message, field, int32, map_field

@message
class Config:
    settings: map_field[str, str] = field(1)
    scores: map_field[str, int32] = field(2)

obj = Config(
    settings={"theme": "dark", "lang": "en"},
    scores={"alice": 95, "bob": 87},
)
parsed = Config.parse(obj.serialize())
print(parsed.settings["theme"])  # "dark"
print(parsed.scores["alice"])    # 95
```

### Enum Fields

```python
from enum import IntEnum
from protobuf import message, field, repeated

class Priority(IntEnum):
    LOW = 0
    MEDIUM = 1
    HIGH = 2
    CRITICAL = 3

@message
class Task:
    title: str = field(1)
    priority: Priority = field(2)
    tags: repeated[Priority] = field(3)

task = Task(title="Deploy", priority=Priority.HIGH, tags=[Priority.LOW, Priority.HIGH])
parsed = Task.parse(task.serialize())
print(parsed.priority)           # Priority.HIGH (== 2)
print(parsed.tags)               # [Priority.LOW, Priority.HIGH]
```

### Oneof Fields

```python
from protobuf import message, field, int32

@message
class Event:
    text: str = field(1, oneof="payload")
    image_url: str = field(2, oneof="payload")
    error_code: int32 = field(3, oneof="payload")
    timestamp: int32 = field(4)

# Only set one field in the oneof group
event = Event(text="hello", timestamp=1234)
parsed = Event.parse(event.serialize())
print(parsed.text)        # "hello"
print(parsed.image_url)   # "" (default)
```

### Dict Conversion

```python
@message
class Item:
    name: str = field(1)
    value: int32 = field(2)

obj = Item(name="widget", value=42)

# To dict (omits zero-value fields)
d = obj.to_dict()
print(d)  # {"name": "widget", "value": 42}

# From dict
restored = Item.from_dict({"name": "widget", "value": 42})
print(restored.name)  # "widget"
```

### Unknown Field Preservation

```python
# Schema evolution: V2 has a field V1 doesn't know about
@message
class PersonV2:
    name: str = field(1)
    age: int32 = field(2)

@message
class PersonV1:
    name: str = field(1)

data = PersonV2(name="Alice", age=30).serialize()

# V1 parser preserves the unknown field 2
v1 = PersonV1.parse(data)
print(v1.name)  # "Alice"

# Re-serializing preserves the unknown field
reparsed = PersonV2.parse(v1.serialize())
print(reparsed.age)  # 30
```

### Size Calculation

```python
from protobuf import message, field, int32, repeated

@message
class Packet:
    id: int32 = field(1)
    payload: bytes = field(2)
    tags: repeated[str] = field(3)

pkt = Packet(id=1, payload=b"hello", tags=["a", "b"])
size = pkt.byte_size()     # compute size without serializing
data = pkt.serialize()
assert size == len(data)   # matches actual serialized length
```

### Complex Real-World Example

```python
from enum import IntEnum
from protobuf import message, field, int32, uint64, bool_, repeated, map_field

class Status(IntEnum):
    DRAFT = 0
    PUBLISHED = 1
    ARCHIVED = 2

@message
class Tag:
    key: str = field(1)
    value: str = field(2)

@message
class Article:
    id: uint64 = field(1)
    title: str = field(2)
    status: Status = field(3)
    tags: repeated[Tag] = field(4)
    metadata: map_field[str, str] = field(5)
    published: bool_ = field(6)

article = Article(
    id=42,
    title="Zero-Dep Protobuf",
    status=Status.PUBLISHED,
    tags=[Tag(key="lang", value="python"), Tag(key="topic", value="serialization")],
    metadata={"author": "Alice", "version": "1.0"},
    published=True,
)

# Serialize → parse round-trip
assert Article.parse(article.serialize()).title == "Zero-Dep Protobuf"

# Dict round-trip
assert Article.from_dict(article.to_dict()).id == 42
```

## API Reference

### `@message` Decorator

```python
@message
class MyMessage:
    ...
```

Turns a class into a proto3 message. Applies `@dataclass` (if needed), builds an internal descriptor, and injects:

- `serialize() -> bytes` — encode to proto3 wire format
- `parse(data: bytes) -> Self` — class method, decode from wire format
- `to_dict() -> dict` — recursive dict conversion (zero-value fields omitted)
- `from_dict(data: dict) -> Self` — class method, create from dict
- `byte_size() -> int` — compute serialized size without materializing bytes

### `field(number, *, default=..., default_factory=..., oneof=None)`

| Parameter | Type | Description |
|-----------|------|-------------|
| `number` | `int` | Proto field number (>= 1) |
| `default` | `Any` | Default value |
| `default_factory` | `callable` | Factory for mutable defaults |
| `oneof` | `str \| None` | Oneof group name |

### Scalar Type Aliases

All are `Annotated[base_type, ProtoScalar(...)]`:

| Alias | Python Type | Wire Type | Description |
|-------|-------------|-----------|-------------|
| `int32` | `int` | VARINT | 32-bit signed |
| `int64` | `int` | VARINT | 64-bit signed |
| `uint32` | `int` | VARINT | 32-bit unsigned |
| `uint64` | `int` | VARINT | 64-bit unsigned |
| `sint32` | `int` | VARINT | ZigZag 32-bit |
| `sint64` | `int` | VARINT | ZigZag 64-bit |
| `fixed32` | `int` | FIXED32 | 4-byte unsigned LE |
| `fixed64` | `int` | FIXED64 | 8-byte unsigned LE |
| `sfixed32` | `int` | FIXED32 | 4-byte signed LE |
| `sfixed64` | `int` | FIXED64 | 8-byte signed LE |
| `float32` | `float` | FIXED32 | IEEE 754 single |
| `double` | `float` | FIXED64 | IEEE 754 double |
| `bool_` | `bool` | VARINT | 0 or 1 |

Bare `str`, `bytes`, `int`, `float`, `bool` can also be used directly (defaults: str→STRING, bytes→BYTES, int→INT64, float→DOUBLE, bool→BOOL).

### Composite Types

| Type | Usage | Description |
|------|-------|-------------|
| `repeated[T]` | `values: repeated[int32] = field(1)` | Repeated field (packed for scalars) |
| `map_field[K, V]` | `attrs: map_field[str, int32] = field(1)` | Map field |
| `IntEnum` subclass | `status: MyEnum = field(1)` | Enum field |

### Low-Level Wire Functions

For advanced use, the module also exports:

- `encode_varint(value) -> bytes`
- `decode_varint(data, pos) -> (value, new_pos)`
- `zigzag_encode(value) -> int`
- `zigzag_decode(value) -> int`
- `make_tag(field_number, wire_type) -> bytes`
- `decode_tag(data, pos) -> (field_number, wire_type, new_pos)`

## Notes and Caveats

!!! warning "Proto3 Only"
    This module implements proto3 semantics only. Proto2 features (`required`, `extensions`, `groups`) are not supported.

!!! info "No .proto Parsing"
    Schemas are defined in Python, not in `.proto` files. There is no `protoc` code generation. If you need `.proto` interop, define equivalent Python schemas manually.

!!! tip "Enum Zero Values"
    Proto3 requires every enum to have a zero value as the default. The module follows this convention — an enum field at value 0 is treated as the default and not serialized.

!!! info "Unknown Fields"
    Unknown fields (from newer schema versions) are preserved in `_unknown_fields` and re-emitted on `serialize()`. This enables forward-compatible schema evolution.

- **Wire compatibility**: Output is wire-compatible with standard proto3 implementations (google-protobuf, etc.).
- **Python version**: Requires Python 3.10+.
- **Performance**: Pure Python — suitable for configuration, metadata, and moderate-throughput use cases. For high-throughput scenarios, consider google-protobuf with C extensions.

## Benchmark

See [Protobuf Benchmark](../benchmarks/protobuf.md) for performance measurements.
