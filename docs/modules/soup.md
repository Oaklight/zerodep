# HTML 解析器（Soup）

零依赖的 HTML 解析器，提供类 BeautifulSoup 的 API —— 仅使用标准库，支持 Python 3.10+。

## 概述

Soup 模块基于 `html.parser.HTMLParser` 构建轻量级 DOM 树。支持 `find`、`find_all`、`select`、`select_one`、`get_text`、`decompose` 和 `find_parent` —— 涵盖了绝大多数实际网页抓取脚本所使用的 BeautifulSoup 子集。

| 文件 | 描述 | 依赖 |
|------|------|------|
| `soup.py` | 纯 Python 实现 | 无（仅标准库：`re`、`html.parser`） |

## 在你的项目中使用

只需将单个 `.py` 文件复制到你的项目中：

```bash
cp soup/soup.py your_project/
```

然后直接导入：

```python
from soup import Soup
```

## 使用示例

### 基本解析

```python
from soup import Soup

html = "<html><body><p class='msg'>Hello <b>world</b></p></body></html>"
soup = Soup(html)
print(soup.find("p", class_="msg").text)
# Hello world
```

### find 和 find_all

```python
html = """
<ul>
  <li class="item">Apple</li>
  <li class="item">Banana</li>
  <li class="item special">Cherry</li>
</ul>
"""
soup = Soup(html)

# 查找第一个匹配
first = soup.find("li")
print(first.text)  # Apple

# 查找所有匹配
items = soup.find_all("li", class_="item")
print([i.text for i in items])  # ['Apple', 'Banana', 'Cherry']
```

### CSS 选择器

```python
html = """
<div id="main">
  <p class="intro">Welcome</p>
  <p class="body">Content</p>
</div>
"""
soup = Soup(html)

# 按 ID 选择
main = soup.select_one("#main")

# 按类名选择
intro = soup.select_one(".intro")
print(intro.text)  # Welcome

# 按标签选择
paragraphs = soup.select("p")
print(len(paragraphs))  # 2

# 后代选择器
body_p = soup.select_one("div p.body")
print(body_p.text)  # Content

# 子选择器
children = soup.select("div > p")
print(len(children))  # 2

# 属性选择器
soup2 = Soup('<a href="/home">Home</a><a href="/about">About</a>')
links = soup2.select("a[href]")
print(len(links))  # 2
```

### get_text

```python
soup = Soup("<p>Hello <b>world</b></p>")
print(soup.get_text())          # Hello world
print(soup.get_text(separator=" | "))  # Hello  | world
print(soup.get_text(strip=True))  # Helloworld
```

### 属性访问

```python
soup = Soup('<a href="/page" class="nav active" id="link1">Click</a>')
a = soup.find("a")

# 访问属性
print(a["href"])         # /page
print(a["id"])           # link1
print(a.get("class"))    # ['nav', 'active']
print(a.get("missing", "default"))  # default
```

### decompose（移除元素）

```python
html = "<div><p>Keep</p><script>remove me</script></div>"
soup = Soup(html)
for script in soup.find_all("script"):
    script.decompose()
print(soup.get_text())  # Keep
```

### find_parent

```python
soup = Soup("<div><ul><li>Item</li></ul></div>")
li = soup.find("li")
print(li.find_parent("div").name)  # div
print(li.find_parent().name)       # ul
```

## 支持的 CSS 选择器

| 选择器 | 示例 | 描述 |
|--------|------|------|
| 标签 | `p` | 按标签名匹配 |
| 类名 | `.intro` | 按类名匹配 |
| ID | `#main` | 按 ID 匹配 |
| 属性 | `[href]` | 匹配具有某属性的元素 |
| 属性值 | `[href="/home"]` | 匹配属性值 |
| 后代 | `div p` | 匹配 `div` 内的 `p` |
| 子元素 | `div > p` | 匹配直接子元素 |
| 复合 | `p.intro` | 匹配具有 `intro` 类的 `p` |

## API 参考

### `Soup(markup, parser="html.parser")`

解析 HTML 文档并提供类 BeautifulSoup 的 API。

**参数：**

| 名称 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `markup` | `str` | -- | 要解析的 HTML 字符串。 |
| `parser` | `str` | `"html.parser"` | 忽略（仅为 BS4 API 兼容性存在）。 |

### `Tag` 方法

| 方法 | 描述 |
|------|------|
| `find(name, class_, **attrs)` | 查找第一个匹配的子元素。 |
| `find_all(name, class_, **attrs)` | 查找所有匹配的子元素。 |
| `select(selector)` | 查找所有匹配 CSS 选择器的元素。 |
| `select_one(selector)` | 查找第一个匹配 CSS 选择器的元素。 |
| `get_text(separator="", strip=False)` | 获取所有文本内容。 |
| `decompose()` | 从父元素中移除此元素。 |
| `find_parent(name=None)` | 查找最近的父元素，可按标签名过滤。 |
| `get(attr, default=None)` | 获取属性值。 |

### `Tag` 属性

| 属性 | 类型 | 描述 |
|------|------|------|
| `.text` | `str` | 所有文本内容（`get_text()` 的快捷方式）。 |
| `.name` | `str` | 标签名（如 `"div"`）。 |
| `.attrs` | `dict` | 属性字典。`class` 存储为列表。 |
| `.children` | `list` | 子节点（`Tag` 或 `str`）。 |
| `.parent` | `Tag \| None` | 父元素。 |

## 与 BeautifulSoup 的对比

| 特性 | zerodep soup | BeautifulSoup |
|------|-------------|---------------|
| 依赖 | 无（仅标准库） | `soupsieve`，可选 `lxml`/`html5lib` |
| 文件数 | 单文件 | 多文件包 |
| 解析器后端 | 仅 `html.parser` | `html.parser`、`lxml`、`html5lib` |
| find / find_all | 是 | 是 |
| CSS 选择器 | 基础（标签、类、ID、属性、后代、子元素） | 完整（通过 soupsieve） |
| prettify | 否 | 是 |
| NavigableString | 否（使用纯 `str`） | 是 |
| 解析速度（小） | 149 μs | 446 μs（慢 2.99x） |
| 解析速度（大） | 12.7 ms | 37.1 ms（慢 2.93x） |

**适用场景（zerodep）：** 需要基本的 HTML 解析（find、select、get_text），零依赖且高性能。

**适用场景（BeautifulSoup）：** 需要高级 CSS 伪选择器、多解析器后端或 NavigableString 功能。

## 性能测试

与 `beautifulsoup4` 在小、中、大 HTML 文档上进行了基准测试。

详见 [Soup 性能测试](../benchmarks/soup.md)。
