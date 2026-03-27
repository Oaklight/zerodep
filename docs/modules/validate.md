# 验证器

零依赖的 TypedDict/dataclass 运行时验证器，支持 Annotated 约束注解和 JSON Schema 生成。仅使用标准库，Python 3.10+。

## 概述

`validate.py` 是一个单文件验证模块，可对任意数据进行 TypedDict/dataclass 类型注解的运行时验证，并从同一类型定义生成 JSON Schema。**无需任何 pip 依赖**。

| 文件 | 说明 | 依赖 |
|------|------|------|
| `validate.py` | 纯 Python 实现 | 无（仅标准库：`typing`、`dataclasses`、`re`） |

## 功能特性

- **TypedDict 验证** -- 必需/可选字段、嵌套结构、`Required`/`NotRequired`
- **dataclass 验证** -- 与 TypedDict 相同的验证逻辑
- **Annotated 约束** -- `Gt`、`Ge`、`Lt`、`Le`、`MinLen`、`MaxLen`、`Match`、`Predicate`
- **Union / Optional** -- 包含 discriminated union 的自动检测
- **Literal** -- 枚举值验证
- **错误收集** -- 收集所有错误后一次抛出，附带点号/方括号路径
- **类型强转** -- 可选的 `coerce=True` 模式（str→int、str→float 等）
- **JSON Schema 生成** -- 从 TypedDict/dataclass 生成 JSON Schema

## 快速开始

### TypedDict 验证

```python
from typing import TypedDict
from validate import validate, ValidationError

class User(TypedDict):
    name: str
    age: int

validate({"name": "Alice", "age": 30}, User)  # 通过

try:
    validate({"name": 123, "age": "thirty"}, User)
except ValidationError as e:
    for err in e.errors:
        print(f"{err.path}: 期望 {err.expected}，实际 {err.actual}")
```

### Annotated 约束

```python
from typing import Annotated, TypedDict
from validate import validate, Gt, Ge, Le, MinLen, MaxLen

class Product(TypedDict):
    name: Annotated[str, MinLen(1), MaxLen(100)]
    price: Annotated[float, Gt(0)]
    quantity: Annotated[int, Ge(0), Le(10000)]

validate({"name": "Widget", "price": 9.99, "quantity": 100}, Product)
```

### 嵌套结构

```python
from typing import TypedDict
from validate import validate

class Address(TypedDict):
    street: str
    city: str

class User(TypedDict):
    name: str
    address: Address

# 错误路径包含嵌套字段：如 "address.street"
validate({
    "name": "Alice",
    "address": {"street": "123 Main St", "city": "NYC"},
}, User)
```

### Discriminated Union

```python
from typing import Literal, TypedDict, Union
from validate import validate

class TextContent(TypedDict):
    kind: Literal["text"]
    text: str

class ImageContent(TypedDict):
    kind: Literal["image"]
    url: str

Content = Union[TextContent, ImageContent]

validate({"kind": "text", "text": "hello"}, Content)    # 自动识别 TextContent
validate({"kind": "image", "url": "https://..."}, Content)  # 自动识别 ImageContent
```

### 类型强转

```python
from validate import validate

# 严格模式（默认）—— 拒绝类型不匹配
# validate("42", int)  # 抛出 ValidationError

# 强转模式 —— 自动转换兼容类型
result = validate("42", int, coerce=True)     # 返回 42
result = validate("3.14", float, coerce=True) # 返回 3.14
```

### JSON Schema 生成

```python
from typing import Annotated, TypedDict
from validate import json_schema, Gt, MinLen, MaxLen

class Item(TypedDict):
    name: Annotated[str, MinLen(1), MaxLen(100)]
    price: Annotated[float, Gt(0)]

schema = json_schema(Item)
# {
#   "type": "object",
#   "properties": {
#     "name": {"type": "string", "minLength": 1, "maxLength": 100},
#     "price": {"type": "number", "exclusiveMinimum": 0}
#   },
#   "required": ["name", "price"],
#   "title": "Item"
# }
```

### 自定义谓词

```python
from typing import Annotated
from validate import validate, Predicate

EvenInt = Annotated[int, Predicate(lambda x: x % 2 == 0, "必须为偶数")]

validate(4, EvenInt)   # 通过
validate(3, EvenInt)   # 抛出 ValidationError
```

## API 参考

### `validate(data, tp, *, coerce=False)`

对数据进行类型注解验证。

**参数：**

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `data` | `Any` | -- | 待验证的数据 |
| `tp` | `type` | -- | TypedDict、dataclass 或任意类型注解 |
| `coerce` | `bool` | `False` | 为 True 时尝试类型强转（如 str→int） |

**返回值：** 验证通过的数据（可能经过强转）。

**异常：** `ValidationError`，包含所有收集到的错误。

---

### `json_schema(tp, *, title=None)`

从类型注解生成 JSON Schema 字典。

**参数：**

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `tp` | `type` | -- | TypedDict、dataclass 或任意类型注解 |
| `title` | `str \| None` | `None` | 可选标题，默认使用类型的 `__name__` |

**返回值：** JSON Schema 字典（draft 2020-12 兼容子集）。

---

### 约束注解

所有约束均为 frozen dataclass，配合 `typing.Annotated` 使用。

| 约束 | 含义 | JSON Schema 映射 |
|------|------|------------------|
| `Gt(val)` | `> val` | `exclusiveMinimum` |
| `Ge(val)` | `>= val` | `minimum` |
| `Lt(val)` | `< val` | `exclusiveMaximum` |
| `Le(val)` | `<= val` | `maximum` |
| `MinLen(val)` | `len >= val` | `minLength` / `minItems` |
| `MaxLen(val)` | `len <= val` | `maxLength` / `maxItems` |
| `Match(pattern)` | `re.fullmatch` | `pattern` |
| `Predicate(fn, desc)` | 自定义谓词 | *（不映射）* |

---

### `ValidationError`

验证失败时抛出。继承自 `Exception`。

| 属性 | 类型 | 说明 |
|------|------|------|
| `errors` | `list[ErrorDetail]` | 所有验证错误列表 |

### `ErrorDetail`

描述单个验证错误的数据类。

| 属性 | 类型 | 说明 |
|------|------|------|
| `path` | `str` | 点号/方括号路径（如 `"items[2].name"`） |
| `expected` | `str` | 期望的类型或约束 |
| `actual` | `str` | 实际的类型或值 |
| `message` | `str` | 人可读的错误信息 |

## 与 pydantic 的对比

| 特性 | zerodep validate | pydantic v2 |
|------|-----------------|-------------|
| 依赖 | 无（仅标准库） | `pydantic-core`（Rust） |
| 类型系统 | 增强 stdlib TypedDict/dataclass | 自定义 `BaseModel` |
| 验证方式 | `validate(data, TypedDict)` | `Model.model_validate(data)` |
| 约束 | `Annotated[int, Gt(0)]` | `Annotated[int, Field(gt=0)]` |
| JSON Schema | `json_schema(TypedDict)` | `Model.model_json_schema()` |
| Discriminated union | 自动检测 Literal 字段 | 需显式声明 `Discriminator` |
| 单文件 | 是（~500 行） | 否（Rust 扩展包） |

**何时使用 zerodep：** 已使用 TypedDict/dataclass，需要验证 + JSON Schema，不想引入新类型系统和外部依赖。

**何时使用 pydantic：** 需要极致性能、序列化、自定义验证器或 pydantic 生态（FastAPI、SQLModel 等）。

## 性能测试

与 pydantic v2 在简单/嵌套/约束验证和 JSON Schema 生成等场景下进行对比。

详见 [验证器性能测试](../benchmarks/validate.md)。
