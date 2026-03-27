# TOON 序列化

零依赖的 TOON（Token-Oriented Object Notation，面向 Token 的对象表示法）编码器和解码器。TOON 是一种紧凑、人类可读的序列化格式，专为 LLM 上下文设计，相比 JSON 可减少 30-60% 的 Token 使用量。

## 特性

- **紧凑编码**：比 JSON 减少 30-60% 的 Token
- **人类可读**：类 YAML 的缩进结构 + 类 CSV 的表格数组
- **往返保真**：`decode(encode(data)) == data`（JSON 兼容类型）
- **类型归一化**：支持 Python 类型（datetime、Decimal、set、Path、tuple）
- **多种分隔符**：逗号、制表符、管道符
- **严格/宽松模式**：可配置的解码验证

## 快速开始

```python
from toon import encode, decode

# 将 Python 数据编码为 TOON
data = {"name": "Alice", "age": 30, "active": True}
text = encode(data)
# name: Alice
# age: 30
# active: true

# 将 TOON 解码回 Python
result = decode(text)
assert result == data

# 表格数组非常紧凑
employees = [
    {"id": 1, "name": "Alice", "dept": "eng"},
    {"id": 2, "name": "Bob", "dept": "sales"},
]
print(encode(employees))
# [2]{id,name,dept}:
#   1,Alice,eng
#   2,Bob,sales
```

## API

### `encode(value, options=None)`

将 Python 值编码为 TOON 格式。

- **value**：任何 JSON 可序列化值，以及 Python 类型（datetime、Decimal、set、Path、tuple）
- **options**：可选的 `EncodeOptions` 字典，包含 `indent`、`delimiter`、`lengthMarker`

### `decode(text, options=None)`

将 TOON 格式字符串解码为 Python 值。

- **text**：TOON 格式字符串
- **options**：可选的 `DecodeOptions` 字典，包含 `indent`、`strict`

### `ToonDecodeError`

TOON 解码失败时抛出的异常。

## 编码选项

```python
from toon import encode, EncodeOptions

data = [1, 2, 3]

# 制表符分隔
encode(data, EncodeOptions(delimiter="\t"))
# [3	]: 1	2	3

# 管道符分隔
encode(data, EncodeOptions(delimiter="|"))
# [3|]: 1|2|3

# 带长度标记
encode(data, EncodeOptions(lengthMarker="#"))
# [#3]: 1,2,3

# 自定义缩进
encode({"a": {"b": 1}}, EncodeOptions(indent=4))
# a:
#     b: 1
```

## TOON 格式概览

### 对象

```
name: Alice
age: 30
active: true
```

### 内联数组

```
[3]: 1,2,3
```

### 表格数组

```
[2]{id,name}:
  1,Alice
  2,Bob
```

### 嵌套结构

```
user:
  name: Alice
  tags[2]: dev,python
```

## 类型归一化

| Python 类型 | TOON 表示 |
|------------|----------|
| `None` | `null` |
| `bool` | `true` / `false` |
| `int`、`float` | 数值字面量 |
| `str` | 无引号或有引号 |
| `datetime` | ISO 8601 字符串 |
| `Decimal` | 浮点值 |
| `set`、`frozenset` | 排序后的数组 |
| `tuple` | 数组（保持顺序） |
| `Path` | 字符串路径 |
| `inf`、`nan` | `null` |
| `-0.0` | `0` |
| 可调用对象 | `null` |

## 与 toon_format 的对比

| 特性 | zerodep TOON | toon_format |
|------|-------------|-------------|
| 依赖 | 无（仅标准库） | `typing-extensions` |
| 文件数 | 单文件 | 18 个源文件 |
| Token 计数 | 不包含 | 需要 `tiktoken` |
| CLI | 不包含 | 包含 |
| 编码/解码 | 完整支持 | 完整支持 |
| 编码速度 | 5.3 - 695.7 μs | 7.8 - 952.6 μs（慢 1.3-1.5x） |
| 解码速度 | 13.4 - 1,463.3 μs | 15.4 - 1,559.1 μs（慢约 1.1x） |
| 相比 JSON 节省 | 减少 38-71% 字符 | 相同（格式一致） |
