# Protobuf

零依赖 proto3 编解码器，使用 Python dataclass 定义消息 schema——仅标准库，Python 3.10+。

> **可替代:** `protobuf`（google）、`betterproto`

## 概述

`protobuf` 模块使用 Python dataclass 作为消息 schema，对 Protocol Buffers（proto3）线格式进行编码和解码。无需 `protoc` 编译器、`.proto` 文件或 C 扩展。

| 文件 | 描述 | 依赖 |
|------|------|------|
| `protobuf/protobuf.py` | Proto3 编解码器 | 无（仅标准库） |

### 核心特性

- **Dataclass schema** —— 通过 `@message` 装饰器 + `field(number)` 定义消息
- **完整 proto3 标量支持** —— int32/64、uint32/64、sint32/64、fixed32/64、sfixed32/64、float32、double、bool、string、bytes
- **复合类型** —— 嵌套消息、`repeated[T]`、`map_field[K, V]`、枚举（`IntEnum`）
- **Oneof 分组** —— 通过 `oneof="group_name"` 参数进行字段分组
- **Proto3 语义** —— 零值字段不序列化，repeated 标量默认 packed 编码
- **未知字段保留** —— 未知字段在 parse → serialize 往返中保留
- **字典转换** —— `to_dict()` / `from_dict()` 提供 JSON 友好的表示
- **大小计算** —— `byte_size()` 计算序列化大小而不分配 bytes
- **无代码生成** —— 无需 `.proto` 文件、`protoc` 或构建步骤

## 如何在你的项目中使用

```bash
cp protobuf/protobuf.py your_project/
```

```python
from protobuf import message, field, int32, repeated
```

## 使用示例

### 基本消息

```python
from protobuf import message, field, int32

@message
class Person:
    name: str = field(1)
    id: int32 = field(2)
    email: str = field(3)

person = Person(name="Alice", id=123, email="alice@example.com")
data = person.serialize()    # bytes
parsed = Person.parse(data)  # Person 实例
print(parsed.name)           # "Alice"
```

### 所有标量类型

```python
from protobuf import (
    message, field,
    int32, int64, uint32, uint64, sint32, sint64,
    fixed32, fixed64, sfixed32, sfixed64,
    float32, double, bool_,
)

@message
class Scalars:
    a: int32 = field(1)       # varint，32 位有符号
    b: int64 = field(2)       # varint，64 位有符号
    c: uint32 = field(3)      # varint，32 位无符号
    d: uint64 = field(4)      # varint，64 位无符号
    e: sint32 = field(5)      # varint + ZigZag，32 位
    f: sint64 = field(6)      # varint + ZigZag，64 位
    g: fixed32 = field(7)     # 4 字节小端无符号
    h: fixed64 = field(8)     # 8 字节小端无符号
    i: sfixed32 = field(9)    # 4 字节小端有符号
    j: sfixed64 = field(10)   # 8 字节小端有符号
    k: float32 = field(11)    # 4 字节 IEEE 754
    l: double = field(12)     # 8 字节 IEEE 754
    m: bool_ = field(13)      # varint（0 或 1）
    n: str = field(14)        # UTF-8 长度定界
    o: bytes = field(15)      # 原始长度定界
```

### 嵌套消息

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

### Repeated 字段

```python
from protobuf import message, field, int32, repeated

@message
class NumberList:
    values: repeated[int32] = field(1)  # packed 编码
    names: repeated[str] = field(2)     # 每个元素长度定界

obj = NumberList(values=[1, 2, 3, 4, 5], names=["a", "b", "c"])
parsed = NumberList.parse(obj.serialize())
print(parsed.values)  # [1, 2, 3, 4, 5]
print(parsed.names)   # ["a", "b", "c"]
```

### Map 字段

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

### 枚举字段

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

### Oneof 字段

```python
from protobuf import message, field, int32

@message
class Event:
    text: str = field(1, oneof="payload")
    image_url: str = field(2, oneof="payload")
    error_code: int32 = field(3, oneof="payload")
    timestamp: int32 = field(4)

# 在 oneof 组中只设置一个字段
event = Event(text="hello", timestamp=1234)
parsed = Event.parse(event.serialize())
print(parsed.text)        # "hello"
print(parsed.image_url)   # ""（默认值）
```

### 字典转换

```python
@message
class Item:
    name: str = field(1)
    value: int32 = field(2)

obj = Item(name="widget", value=42)

# 转为字典（省略零值字段）
d = obj.to_dict()
print(d)  # {"name": "widget", "value": 42}

# 从字典创建
restored = Item.from_dict({"name": "widget", "value": 42})
print(restored.name)  # "widget"
```

### 未知字段保留

```python
# Schema 演进：V2 有 V1 不知道的字段
@message
class PersonV2:
    name: str = field(1)
    age: int32 = field(2)

@message
class PersonV1:
    name: str = field(1)

data = PersonV2(name="Alice", age=30).serialize()

# V1 解析器保留未知字段 2
v1 = PersonV1.parse(data)
print(v1.name)  # "Alice"

# 重新序列化时保留未知字段
reparsed = PersonV2.parse(v1.serialize())
print(reparsed.age)  # 30
```

### 大小计算

```python
from protobuf import message, field, int32, repeated

@message
class Packet:
    id: int32 = field(1)
    payload: bytes = field(2)
    tags: repeated[str] = field(3)

pkt = Packet(id=1, payload=b"hello", tags=["a", "b"])
size = pkt.byte_size()     # 不序列化直接计算大小
data = pkt.serialize()
assert size == len(data)   # 与实际序列化长度一致
```

### 复杂实际示例

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

# 序列化 → 解析往返
assert Article.parse(article.serialize()).title == "Zero-Dep Protobuf"

# 字典往返
assert Article.from_dict(article.to_dict()).id == 42
```

## API 参考

### `@message` 装饰器

```python
@message
class MyMessage:
    ...
```

将类转换为 proto3 消息。应用 `@dataclass`（如未应用），构建内部描述符，注入以下方法：

- `serialize() -> bytes` —— 编码为 proto3 线格式
- `parse(data: bytes) -> Self` —— 类方法，从线格式解码
- `to_dict() -> dict` —— 递归字典转换（省略零值字段）
- `from_dict(data: dict) -> Self` —— 类方法，从字典创建
- `byte_size() -> int` —— 计算序列化大小而不实际分配 bytes

### `field(number, *, default=..., default_factory=..., oneof=None)`

| 参数 | 类型 | 描述 |
|------|------|------|
| `number` | `int` | Proto 字段编号（>= 1） |
| `default` | `Any` | 默认值 |
| `default_factory` | `callable` | 可变默认值的工厂函数 |
| `oneof` | `str \| None` | Oneof 组名 |

### 标量类型别名

所有类型均为 `Annotated[base_type, ProtoScalar(...)]`：

| 别名 | Python 类型 | 线类型 | 描述 |
|------|-------------|--------|------|
| `int32` | `int` | VARINT | 32 位有符号 |
| `int64` | `int` | VARINT | 64 位有符号 |
| `uint32` | `int` | VARINT | 32 位无符号 |
| `uint64` | `int` | VARINT | 64 位无符号 |
| `sint32` | `int` | VARINT | ZigZag 32 位 |
| `sint64` | `int` | VARINT | ZigZag 64 位 |
| `fixed32` | `int` | FIXED32 | 4 字节无符号小端 |
| `fixed64` | `int` | FIXED64 | 8 字节无符号小端 |
| `sfixed32` | `int` | FIXED32 | 4 字节有符号小端 |
| `sfixed64` | `int` | FIXED64 | 8 字节有符号小端 |
| `float32` | `float` | FIXED32 | IEEE 754 单精度 |
| `double` | `float` | FIXED64 | IEEE 754 双精度 |
| `bool_` | `bool` | VARINT | 0 或 1 |

裸 `str`、`bytes`、`int`、`float`、`bool` 也可直接使用（默认：str→STRING、bytes→BYTES、int→INT64、float→DOUBLE、bool→BOOL）。

### 复合类型

| 类型 | 用法 | 描述 |
|------|------|------|
| `repeated[T]` | `values: repeated[int32] = field(1)` | Repeated 字段（标量默认 packed） |
| `map_field[K, V]` | `attrs: map_field[str, int32] = field(1)` | Map 字段 |
| `IntEnum` 子类 | `status: MyEnum = field(1)` | 枚举字段 |

### 底层线格式函数

供高级用途，模块还导出：

- `encode_varint(value) -> bytes`
- `decode_varint(data, pos) -> (value, new_pos)`
- `zigzag_encode(value) -> int`
- `zigzag_decode(value) -> int`
- `make_tag(field_number, wire_type) -> bytes`
- `decode_tag(data, pos) -> (field_number, wire_type, new_pos)`

## 注意事项

!!! warning "仅支持 Proto3"
    本模块仅实现 proto3 语义。不支持 proto2 特性（`required`、`extensions`、`groups`）。

!!! info "不解析 .proto 文件"
    Schema 在 Python 中定义，而非 `.proto` 文件。没有 `protoc` 代码生成。如需 `.proto` 互操作，请手动定义等效的 Python schema。

!!! tip "枚举零值"
    Proto3 要求每个枚举都有零值作为默认值。本模块遵循此约定——枚举字段值为 0 时视为默认值，不会被序列化。

!!! info "未知字段"
    未知字段（来自更新版本的 schema）保存在 `_unknown_fields` 中，并在 `serialize()` 时重新输出。这实现了前向兼容的 schema 演进。

- **线格式兼容性**：输出与标准 proto3 实现（google-protobuf 等）线格式兼容。
- **Python 版本**：需要 Python 3.10+。
- **性能**：纯 Python 实现——适用于配置、元数据和中等吞吐量场景。高吞吐量场景建议使用带 C 扩展的 google-protobuf。

## 性能测试

参见 [Protobuf 性能测试](../benchmarks/protobuf.md)。
