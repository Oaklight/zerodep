# YAML 解析器

YAML 解析器与序列化器（常用子集）-- 零依赖，仅标准库，Python 3.10+。

## 概述

YAML 模块提供了一个安全的 YAML 解析器和序列化器，覆盖 YAML 规范中最常用的子集。它设计为 `PyYAML` 的 `safe_load` / `safe_dump` 在典型配置文件和数据交换场景下的直接替代品，无需任何外部依赖。

| 文件 | 说明 | 依赖 |
|------|------|------|
| `yaml.py` | 纯 Python YAML 解析器与序列化器 | 无（仅标准库） |

解析过程中仅生成**安全类型**：`dict`、`list`、`str`、`int`、`float`、`bool` 和 `None`。

## 如何在你的项目中使用

只需将 `.py` 文件复制到你的项目中：

```bash
cp yaml/yaml.py your_project/
```

然后直接导入：

```python
from yaml import load, dump
```

## API 参考

### `load(text)`

解析 YAML 字符串并返回 Python 对象。等价于 PyYAML 的 `yaml.safe_load()`。

```python
def load(text: str) -> Any
```

**参数：**

| 名称 | 类型 | 说明 |
|------|------|------|
| `text` | `str` | YAML 文档字符串。 |

**返回值：** `Any` -- 解析后的 Python 对象（`dict`、`list`、`str`、`int`、`float`、`bool` 或 `None`）。

**异常：** YAML 格式错误时抛出 `YAMLError`。

**示例：**

```python
data = load("name: Alice\nage: 30")
# {'name': 'Alice', 'age': 30}
```

---

### `load_all(text)`

解析多文档 YAML 字符串。每个 YAML 文档（以 `---` 分隔）产生一个 Python 对象。

```python
def load_all(text: str) -> Iterator[Any]
```

**参数：**

| 名称 | 类型 | 说明 |
|------|------|------|
| `text` | `str` | 多文档 YAML 字符串。 |

**产出：** 逐个产出解析后的 Python 对象，每个文档一个。

**示例：**

```python
for doc in load_all("---\na: 1\n---\nb: 2"):
    print(doc)
# {'a': 1}
# {'b': 2}
```

---

### `dump(data, stream, *, default_flow_style, indent, sort_keys, allow_unicode)`

将 Python 对象序列化为 YAML 字符串。

```python
def dump(
    data: Any,
    stream: IO[str] | None = None,
    *,
    default_flow_style: bool | None = None,
    indent: int = 2,
    sort_keys: bool = True,
    allow_unicode: bool = True,
) -> str | None
```

**参数：**

| 名称 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `data` | `Any` | *（必填）* | 待序列化的 Python 对象。 |
| `stream` | `IO[str] \| None` | `None` | 如果提供，将结果写入该流并返回 `None`。 |
| `default_flow_style` | `bool \| None` | `None` | `True` 使用流式（内联）风格，`False` 使用块风格，`None` 自动选择。 |
| `indent` | `int` | `2` | 每级缩进的空格数。 |
| `sort_keys` | `bool` | `True` | 按字母顺序排列映射的键。 |
| `allow_unicode` | `bool` | `True` | 允许输出中包含 Unicode 字符。 |

**返回值：** 当 `stream` 为 `None` 时返回 `str`，否则返回 `None`。

**示例：**

```python
text = dump({"name": "Alice", "age": 30})
print(text)
# age: 30
# name: Alice
```

---

### `dump_all(documents, stream, *, default_flow_style, indent, sort_keys, allow_unicode)`

将多个 Python 对象序列化为多文档 YAML 字符串。

```python
def dump_all(
    documents: list[Any] | tuple[Any, ...],
    stream: IO[str] | None = None,
    *,
    default_flow_style: bool | None = None,
    indent: int = 2,
    sort_keys: bool = True,
    allow_unicode: bool = True,
) -> str | None
```

**参数：**

| 名称 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `documents` | `list[Any] \| tuple[Any, ...]` | *（必填）* | 待序列化的 Python 对象的可迭代集合。 |
| `stream` | `IO[str] \| None` | `None` | 如果提供，将结果写入该流并返回 `None`。 |
| `default_flow_style` | `bool \| None` | `None` | `True` 使用流式风格，`False` 使用块风格，`None` 自动选择。 |
| `indent` | `int` | `2` | 每级缩进的空格数。 |
| `sort_keys` | `bool` | `True` | 按字母顺序排列映射的键。 |
| `allow_unicode` | `bool` | `True` | 允许输出中包含 Unicode 字符。 |

**返回值：** 当 `stream` 为 `None` 时返回 `str`，否则返回 `None`。

**示例：**

```python
text = dump_all([{"a": 1}, {"b": 2}])
print(text)
# a: 1
# ---
# b: 2
```

---

### `class YAMLError(Exception)`

YAML 解析失败时抛出。包含发生错误的行号信息。

```python
class YAMLError(Exception): ...
```

## 用法示例

### 解析配置文件

```python
from yaml import load

config_text = """
server:
  host: 0.0.0.0
  port: 8080
  debug: false

database:
  url: postgres://localhost/mydb
  pool_size: 5

logging:
  level: INFO
  handlers:
    - console
    - file
"""

config = load(config_text)
print(config["server"]["port"])   # 8080
print(config["logging"]["level"]) # 'INFO'
```

### 输出数据为 YAML

```python
from yaml import dump

data = {
    "users": [
        {"name": "Alice", "role": "admin"},
        {"name": "Bob", "role": "user"},
    ],
    "version": 2,
}

text = dump(data)
print(text)
```

### 多文档流

```python
from yaml import load_all, dump_all

# 解析
yaml_text = """---
name: service-a
port: 8001
---
name: service-b
port: 8002
"""
for doc in load_all(yaml_text):
    print(doc["name"], doc["port"])

# 序列化
output = dump_all([
    {"name": "service-a", "port": 8001},
    {"name": "service-b", "port": 8002},
])
print(output)
```

### 流式风格输出

```python
from yaml import dump

data = {"colors": ["red", "green", "blue"], "count": 3}
print(dump(data, default_flow_style=True))
# {colors: [red, green, blue], count: 3}
```

### 写入文件

```python
from yaml import dump

config = {"debug": True, "workers": 4}

with open("config.yaml", "w") as f:
    dump(config, f)
```

## 支持的 YAML 子集

### 支持的功能

- **标量：** 字符串、整数（十进制、十六进制 `0x`、八进制 `0`、二进制 `0b`）、浮点数、布尔值（`true`/`false`/`yes`/`no`/`on`/`off`）、空值（`null`/`~`）、特殊浮点数（`.inf`、`.nan`）
- **映射：** 块风格和流式风格（`{key: value}`）
- **序列：** 块风格和流式风格（`[a, b, c]`）
- **块标量：** 字面量（`|`）和折叠（`>`），支持截断指示符（`-`、`+`）
- **引号字符串：** 单引号和双引号，支持转义序列
- **注释：** 行注释（`#`）和行内注释
- **多文档流：** `---` 和 `...` 标记
- **嵌套结构：** 任意深度嵌套的映射和序列
- **下划线分隔符：** 数值字面量中的 `1_000_000`

### 不支持的功能

- **锚点和别名**（`&anchor`、`*alias`）
- **标签**（`!!str`、`!custom`）
- **合并键**（`<<:`）
- **复杂映射键**（多行键、序列/映射作为键）
- **指令**（`%YAML`、`%TAG`）

## 注意事项

!!! warning "YAML 1.1 布尔值兼容性"
    此解析器遵循 YAML 1.1 约定，将 `yes`、`no`、`on`、`off`（不区分大小写）视为布尔值。如果你需要将这些作为字面字符串使用，请用引号包裹：`"yes"`、`'no'`。这与 PyYAML 的默认行为一致，但与仅识别 `true` 和 `false` 的 YAML 1.2 有所不同。

!!! info "仅安全类型"
    此模块在解析过程中仅生成安全的 Python 类型：`dict`、`list`、`str`、`int`、`float`、`bool` 和 `None`。不会构造任何任意 Python 对象，因此可以安全地用于处理不可信的输入。这等价于 PyYAML 的 `safe_load()` -- 没有 `unsafe_load()` 的等价物。

- **Python 版本：** 需要 Python 3.10+（使用了 `X | Y` 联合类型标注语法）。
- **循环引用：** 序列化器会检测循环引用，并抛出 `YAMLError` 而不是进入无限递归。
- **键排序：** 默认情况下，`dump()` 按字母顺序排列映射的键。传入 `sort_keys=False` 可保留插入顺序。
- **模块名冲突：** 如果你在项目中将文件命名为 `yaml.py`，它可能会覆盖系统安装的 `PyYAML` 包。这对于零依赖使用来说是有意为之，但请注意潜在的冲突。

## 性能测试

与 `PyYAML` 在三种输入大小（小、中、大）下进行 load 和 dump 操作的对比测试。

详见 [YAML 性能测试](../benchmarks/yaml.md)。
