# Frontmatter 解析器

Frontmatter 解析器与序列化器（YAML、TOML、JSON）-- 零依赖，仅标准库，Python 3.10+。

> **可替代:** `python-frontmatter`

## 概述

Frontmatter 模块用于解析和序列化文件头部元数据（frontmatter），支持 YAML、TOML 和 JSON 格式。YAML `---` frontmatter 是 Jekyll、Hugo、Astro、MkDocs、Obsidian 等众多工具使用的事实标准。本模块提供了 [`python-frontmatter`](https://pypi.org/project/python-frontmatter/) 的零依赖替代方案。

| 文件 | 说明 | 依赖 |
|------|------|------|
| `frontmatter.py` | Frontmatter 解析器与序列化器 | `yaml`（兄弟模块） |

## 如何在你的项目中使用

将模块文件及其依赖复制到你的项目中：

```bash
cp frontmatter/frontmatter.py your_project/
cp yaml/yaml.py your_project/
```

然后直接导入：

```python
from frontmatter import loads, dumps, Document
```

## 支持的格式

| 格式 | 分隔符 | 解析器 | 说明 |
|------|--------|--------|------|
| YAML | `---` ... `---` | 兄弟 `yaml` 模块 | 默认格式；覆盖 90% 以上的实际场景 |
| TOML | `+++` ... `+++` | `tomllib`（Python 3.11+ 标准库） | 通过标准库只读解析；内置简单序列化 |
| JSON | `{` ... `}` | 标准库 `json` | 文件开头的 JSON 对象，无需分隔符 |

## API 参考

### `loads(text, *, handler=None)`

解析包含 frontmatter 的文本字符串。

```python
def loads(text: str, *, handler: str | None = None) -> Document
```

**参数：**

| 名称 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `text` | `str` | *（必填）* | 完整的文档文本。 |
| `handler` | `str \| None` | `None` | 强制指定格式（`"yaml"`、`"toml"`、`"json"`）。为 `None` 时自动检测。 |

**返回值：** 包含解析后元数据和正文内容的 `Document`。

**示例：**

```python
doc = loads("---\ntitle: Hello World\ntags: [python, zerodep]\n---\nBody text.")
doc.metadata  # {'title': 'Hello World', 'tags': ['python', 'zerodep']}
doc.content   # 'Body text.'
```

---

### `load(source, *, handler=None)`

从文件解析 frontmatter。

```python
def load(
    source: IO[str] | str | Path,
    *,
    handler: str | None = None,
) -> Document
```

**参数：**

| 名称 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `source` | `IO[str] \| str \| Path` | *（必填）* | 文件路径或打开的文本流。 |
| `handler` | `str \| None` | `None` | 强制指定格式。为 `None` 时自动检测。 |

**返回值：** 包含解析后元数据和正文内容的 `Document`。

**示例：**

```python
doc = load("post.md")
doc = load(Path("post.md"))
with open("post.md") as f:
    doc = load(f)
```

---

### `dumps(doc, *, handler="yaml", **kwargs)`

将 `Document` 序列化为带 frontmatter 的字符串。

```python
def dumps(
    doc: Document,
    *,
    handler: str = "yaml",
    **kwargs: Any,
) -> str
```

**参数：**

| 名称 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `doc` | `Document` | *（必填）* | 待序列化的文档。 |
| `handler` | `str` | `"yaml"` | 输出格式（`"yaml"`、`"toml"`、`"json"`）。 |
| `**kwargs` | `Any` | | 传递给底层序列化器的参数。 |

**返回值：** 包含 frontmatter 和正文的完整文档文本。

**示例：**

```python
doc = Document({"title": "Hello"}, "Body text.")
text = dumps(doc)
# ---
# title: Hello
# ---
# Body text.
```

---

### `dump(doc, dest, *, handler="yaml", **kwargs)`

将 `Document` 序列化到文件。

```python
def dump(
    doc: Document,
    dest: IO[str] | str | Path,
    *,
    handler: str = "yaml",
    **kwargs: Any,
) -> None
```

**参数：**

| 名称 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `doc` | `Document` | *（必填）* | 待序列化的文档。 |
| `dest` | `IO[str] \| str \| Path` | *（必填）* | 文件路径或打开的文本流。 |
| `handler` | `str` | `"yaml"` | 输出格式。 |

---

### `check(text)`

检测文本字符串是否包含 frontmatter。

```python
def check(text: str) -> bool
```

**返回值：** 检测到 frontmatter 时返回 `True`。

---

### `detect_handler(text)`

检测 frontmatter 的格式。

```python
def detect_handler(text: str) -> str | None
```

**返回值：** `"yaml"`、`"toml"`、`"json"` 或 `None`。

---

### `class Document`

包含 frontmatter 元数据和正文内容的数据类。

```python
@dataclasses.dataclass
class Document:
    metadata: dict[str, Any]
    content: str
```

支持对 metadata 的字典式访问：`doc["key"]`、`doc["key"] = val`、`"key" in doc`、`doc.get("key")`、`doc.keys()`、`doc.values()`、`doc.items()`。

---

### 异常

- **`FrontmatterError`** -- 解析错误的基础异常。
- **`HandlerError(FrontmatterError)`** -- 请求的处理器不可用时抛出。

## 用法示例

### 解析带 YAML Frontmatter 的 Markdown 文件

```python
from frontmatter import loads

text = """---
title: My Post
date: 2026-03-28
tags:
  - python
  - zerodep
---
# Introduction

This is the body content.
"""

doc = loads(text)
print(doc.metadata["title"])  # 'My Post'
print(doc.metadata["tags"])   # ['python', 'zerodep']
print(doc.content)            # '# Introduction\n\nThis is the body content.\n'
```

### 创建并序列化文档

```python
from frontmatter import Document, dumps

doc = Document(
    metadata={"title": "New Post", "draft": True},
    content="Hello, world!\n",
)
print(dumps(doc))
# ---
# title: New Post
# draft: true
# ---
# Hello, world!
```

### JSON Frontmatter

```python
from frontmatter import loads

text = '{"title": "Hello", "count": 42}\nSome content after JSON.'
doc = loads(text)
print(doc.metadata)  # {'title': 'Hello', 'count': 42}
```

### TOML Frontmatter（Python 3.11+）

```python
from frontmatter import loads

text = """+++
title = "Hugo Post"
date = 2026-03-28
+++
Content here.
"""

doc = loads(text)
print(doc.metadata["title"])  # 'Hugo Post'
```

### 往返操作：解析、修改、序列化

```python
from frontmatter import load, dump

doc = load("post.md")
doc["draft"] = False
doc["tags"].append("published")
dump(doc, "post.md")
```

## 注意事项

!!! info "YAML 处理器依赖"
    YAML 处理器需要兄弟 `yaml` 模块。请将 `yaml.py` 放在兄弟目录中或 `sys.path` 上。如果没有该模块而尝试 YAML 解析，将抛出 `HandlerError`。

!!! info "TOML 支持"
    TOML 解析需要 Python 3.11+（标准库中的 `tomllib`）。TOML 序列化仅支持扁平键值对；嵌套表将抛出 `FrontmatterError`（请使用 YAML 处理嵌套数据）。

- **Python 版本：** 需要 Python 3.10+（使用了 `X | Y` 联合类型标注语法）。
- **BOM 处理：** 检测前会自动剥离 UTF-8 BOM（`\ufeff`）。
- **Windows 换行符：** 解析和检测中均正确处理 CRLF（`\r\n`）。
- **无 frontmatter：** 如果未检测到 frontmatter，整个文本将作为 `content` 返回，`metadata` 为空字典。

## 性能测试

与 `python-frontmatter` 在三种输入大小（小、中、大）下进行解析和序列化操作的对比测试。

详见 [Frontmatter 性能测试](../benchmarks/frontmatter.md)。
