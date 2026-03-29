# XML

XML 与 dict 双向转换器，支持容错 LLM 标签提取 -- 零依赖，仅标准库，Python 3.10+。

## 概述

XML 模块提供了一个与 xmltodict 兼容的双向 XML ↔ dict 转换器，以及一个专为 LLM 输出解析设计的容错标签提取器。它可以在绝大多数场景下直接替换 [`xmltodict`](https://pypi.org/project/xmltodict/) -- 包括解析 sitemap、RSS/Atom 订阅源、企业 API 响应和 LLM 结构化输出。

| 文件 | 说明 | 依赖 |
|------|------|------|
| `xml.py` | 纯 Python XML 转换器与 LLM 标签提取 | 无（仅标准库） |

提供两层功能：

- **标准层：** `parse()` / `unparse()` 用于 xmltodict 兼容的 dict ↔ XML 转换
- **容错层：** `extract_tags()` 用于从 LLM 输出中容错提取 XML 风格标签

## 如何在你的项目中使用

只需将 `.py` 文件复制到你的项目中：

```bash
cp xml/xml.py your_project/
```

然后直接导入：

```python
from xml import parse, unparse, extract_tags
```

!!! warning "模块名冲突"
    文件名 `xml.py` 会覆盖 Python 标准库的 `xml` 包。模块内部通过 `sys.path` / `sys.modules` 操作来处理此问题。如果你需要同时使用标准库 `xml`，请考虑重命名文件。

## API 参考

### `parse(xml_input, **kwargs)`

将 XML 文档解析为 Python dict。兼容 `xmltodict.parse()`。

```python
def parse(
    xml_input: str | bytes | IO[bytes],
    *,
    encoding: str | None = None,
    process_namespaces: bool = False,
    namespace_separator: str = ":",
    disable_entities: bool = True,
    process_comments: bool = False,
    xml_attribs: bool = True,
    attr_prefix: str = "@",
    cdata_key: str = "#text",
    force_cdata: bool = False,
    cdata_separator: str = "",
    postprocessor: Callable | None = None,
    dict_constructor: type = dict,
    strip_whitespace: bool = True,
    force_list: bool | tuple[str, ...] | Callable | None = None,
    comment_key: str = "#comment",
) -> dict | None
```

**主要参数：**

| 名称 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `xml_input` | `str \| bytes \| IO[bytes]` | *（必填）* | XML 字符串、字节或类文件对象。 |
| `attr_prefix` | `str` | `"@"` | 输出 dict 中属性键的前缀。 |
| `cdata_key` | `str` | `"#text"` | 输出 dict 中文本内容的键。 |
| `force_list` | `bool \| tuple \| Callable \| None` | `None` | 强制指定元素始终创建列表。 |
| `strip_whitespace` | `bool` | `True` | 去除文本节点的空白字符。 |
| `disable_entities` | `bool` | `True` | 阻止实体声明以防 XXE 攻击。 |
| `postprocessor` | `Callable \| None` | `None` | `(path, key, value) -> (key, value)` 或返回 `None` 跳过。 |

**返回值：** `dict | None` -- 解析后的 dict，空文档返回 `None`。

**异常：** XML 格式错误时抛出 `XMLError`。

**示例：**

```python
d = parse('<root><name>Alice</name><age>30</age></root>')
# {'root': {'name': 'Alice', 'age': '30'}}
```

---

### `unparse(input_dict, **kwargs)`

将 Python dict 转换为 XML 字符串。兼容 `xmltodict.unparse()`。

```python
def unparse(
    input_dict: dict,
    *,
    output: IO[str] | None = None,
    encoding: str = "utf-8",
    full_document: bool = True,
    short_empty_elements: bool = False,
    pretty: bool = False,
    indent: str = "\t",
    newl: str = "\n",
    attr_prefix: str = "@",
    cdata_key: str = "#text",
    preprocessor: Callable | None = None,
    namespace_separator: str = ":",
    namespaces: dict[str, str] | None = None,
    comment_key: str = "#comment",
) -> str | None
```

**主要参数：**

| 名称 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `input_dict` | `dict` | *（必填）* | 包含单个根键的字典。 |
| `output` | `IO[str] \| None` | `None` | 如果提供，写入流并返回 `None`。 |
| `full_document` | `bool` | `True` | 包含 `<?xml ...?>` 声明。 |
| `pretty` | `bool` | `False` | 格式化输出，带缩进。 |
| `indent` | `str` | `"\t"` | 缩进字符串（`pretty` 为 True 时使用）。 |

**返回值：** `output` 为 `None` 时返回 `str`，否则返回 `None`。

**异常：** dict 无法序列化时抛出 `XMLError`。

**示例：**

```python
xml_str = unparse({'root': {'name': 'Alice'}}, full_document=False)
# '<root><name>Alice</name></root>'
```

---

### `extract_tags(text, tag, *, first_only)`

从文本中提取 XML 风格标签，容忍格式错误的 XML。专为 LLM 输出设计。

```python
def extract_tags(
    text: str,
    tag: str | None = None,
    *,
    first_only: bool = False,
) -> list[ExtractedTag]
```

**参数：**

| 名称 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `text` | `str` | *（必填）* | 包含 XML 风格标签的原始文本。 |
| `tag` | `str \| None` | `None` | 仅提取指定名称的标签，`None` 提取全部。 |
| `first_only` | `bool` | `False` | 找到第一个匹配后即返回。 |

**返回值：** `list[ExtractedTag]`

**示例：**

```python
tags = extract_tags('<answer>42</answer>', 'answer')
# [ExtractedTag(tag='answer', content='42', attrs={}, is_closed=True)]
```

---

### `class ExtractedTag`

表示提取的标签的数据类。

| 字段 | 类型 | 说明 |
|------|------|------|
| `tag` | `str` | 标签名（如 `"answer"`）。 |
| `content` | `str` | 开闭标签之间的文本内容。 |
| `attrs` | `dict[str, str]` | 开始标签上的属性。 |
| `is_closed` | `bool` | 找到匹配的闭合标签时为 `True`。 |

---

### `class XMLError(Exception)`

XML 解析或序列化失败时抛出。

---

### 别名

| 别名 | 目标 | 约定 |
|------|------|------|
| `loads` | `parse` | zerodep 约定 |
| `dumps` | `unparse` | zerodep 约定 |

## 用法示例

### 解析 Sitemap

```python
from xml import parse

sitemap_xml = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://example.com/</loc>
    <lastmod>2024-01-01</lastmod>
  </url>
  <url>
    <loc>https://example.com/about</loc>
    <lastmod>2024-01-02</lastmod>
  </url>
</urlset>"""

d = parse(sitemap_xml)
for url in d["urlset"]["url"]:
    print(url["loc"], url["lastmod"])
```

### 解析 RSS 订阅源

```python
from xml import parse

rss_xml = """<?xml version="1.0"?>
<rss version="2.0">
  <channel>
    <title>My Blog</title>
    <item>
      <title>First Post</title>
      <link>https://example.com/first</link>
    </item>
    <item>
      <title>Second Post</title>
      <link>https://example.com/second</link>
    </item>
  </channel>
</rss>"""

d = parse(rss_xml)
for item in d["rss"]["channel"]["item"]:
    print(item["title"], item["link"])
```

### 往返转换

```python
from xml import parse, unparse

original = {'catalog': {'book': [
    {'@id': '1', 'title': 'Python', 'price': '29.99'},
    {'@id': '2', 'title': 'Rust', 'price': '39.99'},
]}}

xml_str = unparse(original, pretty=True, full_document=False)
print(xml_str)

restored = parse(xml_str)
assert restored == original
```

### 提取 LLM 输出标签

```python
from xml import extract_tags

llm_output = """Let me think about this.

<thinking>
The user wants to know the capital of France.
This is a straightforward factual question.
</thinking>

<answer>
The capital of France is Paris.
</answer>"""

thinking = extract_tags(llm_output, "thinking")
answer = extract_tags(llm_output, "answer")
print(thinking[0].content.strip())
print(answer[0].content.strip())
```

### 处理流式截断

```python
from xml import extract_tags

# LLM 输出在流式传输中被截断
partial_output = "<response>The answer is 42 and the reason is"

tags = extract_tags(partial_output, "response")
print(tags[0].content)    # "The answer is 42 and the reason is"
print(tags[0].is_closed)  # False -- 标签未闭合
```

### 强制列表

```python
from xml import parse

# 不使用 force_list 时，单个 <item> 是标量
d = parse('<root><item>only one</item></root>')
print(type(d['root']['item']))  # str

# 使用 force_list 后，始终是列表
d = parse('<root><item>only one</item></root>', force_list=('item',))
print(type(d['root']['item']))  # list
```

## 约定

### 属性处理

XML 属性以 `@` 为前缀（可通过 `attr_prefix` 配置）：

```python
parse('<item id="1" type="book">hello</item>')
# {'item': {'@id': '1', '@type': 'book', '#text': 'hello'}}
```

### 文本内容

文本内容存储在 `#text` 键下（可通过 `cdata_key` 配置）：

```python
parse('<tag attr="val">content</tag>')
# {'tag': {'@attr': 'val', '#text': 'content'}}
```

### 列表合并

同名兄弟元素自动合并为列表：

```python
parse('<root><item>a</item><item>b</item></root>')
# {'root': {'item': ['a', 'b']}}
```

### 空元素

空元素产生 `None`：

```python
parse('<root><empty/></root>')
# {'root': {'empty': None}}
```

## 注意事项

!!! warning "安全：实体扩展"
    默认情况下，`disable_entities=True` 会阻止 XML 实体声明，以防止 XXE（XML 外部实体）攻击。仅在信任 XML 来源时才设置 `disable_entities=False`。

!!! info "模块名冲突"
    模块文件名为 `xml.py`，与 Python 标准库的 `xml` 包冲突。模块在导入时会透明地处理此问题。但如果你的项目还需要直接访问 `xml.etree.ElementTree` 或其他标准库 `xml` 子模块，可能需要重命名文件。

- **Python 版本：** 需要 Python 3.10+（使用了 `X | Y` 联合类型标注语法）。
- **流式处理：** `item_depth` / `item_callback` 流式模式尚未支持，但基于 SAX 的架构允许在未来添加。
- **命名空间处理：** 设置 `process_namespaces=True` 以展开命名空间 URI。默认保留命名空间前缀原样。

## 性能测试

与 `xmltodict` 在三种输入大小（小、中、大）下进行 parse 和 unparse 操作的对比测试，以及独立的 `extract_tags` 性能测试。

详见 [XML 性能测试](../benchmarks/xml.md)。
