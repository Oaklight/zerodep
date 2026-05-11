# Markdown 渲染器

Markdown 转 HTML 渲染器 —— 零依赖，仅使用标准库，支持 Python 3.10+。

> **可替代:** `mistune`、`markdown`、`markdown-it-py`

## 概述

Markdown 模块提供了 `mistune.html()` 的直接替代品，可将常见 Markdown 渲染为 HTML。支持 CommonMark 子集和 GFM 扩展（表格、删除线、任务列表、扩展自动链接）—— 无需任何第三方依赖。

| 文件 | 说明 | 依赖 |
|------|------|------|
| `markdown.py` | 纯 Python 实现 | 无（仅标准库） |

渲染器采用两阶段架构：块级解析器（基于行的状态机）输入到行内解析器（使用占位符机制的正则处理，防止重复转义），直接生成 HTML 字符串，不产生中间 AST。

## 如何在项目中使用

只需将单个 `.py` 文件复制到你的项目中：

```bash
cp markdown/markdown.py your_project/
```

然后直接导入：

```python
from markdown import render
```

## API 参考

### `render(text)`

将 Markdown 文本转换为 HTML。

```python
def render(text: str) -> str
```

**参数：**

| 名称 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `text` | `str` | -- | Markdown 源文本。 |

**返回值：** `str` -- HTML 字符串。

**示例：**

```python
from markdown import render

html = render("# Hello\n\nThis is **bold**.")
# '<h1>Hello</h1>\n<p>This is <strong>bold</strong>.</p>\n'
```

## 使用示例

### 基本渲染

```python
from markdown import render

html = render("""
# 我的文档

这是一个包含 **粗体**、*斜体* 和 `代码` 的段落。

## 代码块

```python
def hello():
    print("world")
``\`

> 带 **强调** 的引用块。

- 项目 1
- 项目 2
  - 嵌套项目
""")
```

### 标题

```python
# ATX 标题
render("# 一级标题")         # <h1>一级标题</h1>
render("## 二级标题")        # <h2>二级标题</h2>
render("### 三级标题")       # <h3>三级标题</h3>

# Setext 标题
render("一级标题\n=========")  # <h1>一级标题</h1>
render("二级标题\n---------")  # <h2>二级标题</h2>
```

### 强调

```python
render("*斜体*")              # <em>斜体</em>
render("**粗体**")            # <strong>粗体</strong>
render("***粗斜体***")        # <em><strong>粗斜体</strong></em>
```

### 链接和图片

```python
# 行内链接
render("[点击](https://example.com)")
# <a href="https://example.com">点击</a>

# 带标题的链接
render('[点击](https://example.com "标题")')
# <a href="https://example.com" title="标题">点击</a>

# 引用链接
render("[点击][ref]\n\n[ref]: https://example.com")

# 图片
render("![替代文本](https://example.com/img.png)")
# <img src="https://example.com/img.png" alt="替代文本" />
```

### 列表

```python
# 无序列表
render("- 项目 1\n- 项目 2\n- 项目 3")

# 有序列表
render("1. 第一\n2. 第二\n3. 第三")

# 嵌套列表
render("- 父级\n  - 子级\n  - 子级\n- 同级")
```

### 表格（GFM）

```python
render("""
| 姓名  | 年龄 |
| ----- | ---- |
| Alice | 30   |
| Bob   | 25   |
""")
```

通过 `:---`（左对齐）、`:---:`（居中）和 `---:`（右对齐）语法支持列对齐。

### 删除线（GFM）

```python
render("~~删除的文本~~")
# <p><del>删除的文本</del></p>

render("~~粗体 **嵌套** 删除~~")
# <p><del>粗体 <strong>嵌套</strong> 删除</del></p>
```

### 任务列表（GFM）

```python
render("- [ ] 编写代码\n- [x] 编写测试\n- [ ] 审查 PR")
# <ul>
# <li class="task-list-item"><input class="task-list-item-checkbox" type="checkbox" disabled/>编写代码</li>
# <li class="task-list-item"><input class="task-list-item-checkbox" type="checkbox" disabled checked/>编写测试</li>
# <li class="task-list-item"><input class="task-list-item-checkbox" type="checkbox" disabled/>审查 PR</li>
# </ul>
```

无序列表（`- [ ]`）和有序列表（`1. [ ]`）均支持。

### 扩展自动链接（GFM）

```python
render("访问 https://example.com 了解更多")
# <p>访问 <a href="https://example.com">https://example.com</a> 了解更多</p>

# 尾部标点自动排除在 URL 之外
render("参见 https://example.com。")
# <p>参见 <a href="https://example.com">https://example.com</a>。</p>
```

仅自动链接 `http://` 和 `https://` 协议。裸 `www.` URL 不会被匹配。

### 围栏代码块

```python
render("```python\ndef foo():\n    pass\n```")
# 生成 <pre><code class="language-python">...</code></pre>
```

## 支持的特性

| 特性 | 语法 | 示例 |
|------|------|------|
| ATX 标题 | `# ` 到 `###### ` | `# 标题` |
| Setext 标题 | `===` / `---` 下划线 | `标题\n====` |
| 段落 | 空行分隔 | 两个空行 |
| 斜体 | `*text*` 或 `_text_` | `*斜体*` |
| 粗体 | `**text**` 或 `__text__` | `**粗体**` |
| 粗斜体 | `***text***` | `***两者***` |
| 行内代码 | `` `code` `` | `` `var` `` |
| 围栏代码块 | ` ``` ` 或 `~~~` | 可带语言标签 |
| 缩进代码块 | 4 空格缩进 | `    code` |
| 块引用 | `> ` 前缀 | `> 引用`，支持嵌套 |
| 无序列表 | `- `、`* `、`+ ` | `- 项目`，支持嵌套 |
| 有序列表 | `1. ` | `1. 第一`，支持 `start` 属性 |
| 行内链接 | `[text](url)` | 可带标题 |
| 引用链接 | `[text][ref]` | `[ref]: url` 定义 |
| 图片 | `![alt](url)` | 可带标题 |
| 分隔线 | `---`、`***`、`___` | 水平线 |
| 硬换行 | 行末两空格或 `\` | 段内换行 |
| 反斜杠转义 | `\*`、`\_` 等 | 转义特殊字符 |
| 自动链接 | `<https://...>` | `<user@example.com>` |
| GFM 表格 | 管道语法 | 支持列对齐 |
| GFM 删除线 | `~~text~~` | `~~已删除~~` |
| GFM 任务列表 | `- [ ]` / `- [x]` | 带复选框的列表项 |
| GFM 扩展自动链接 | 裸 `https://` URL | 自动链接，剥离尾部标点 |
| HTML 转义 | 自动 | `<`、`>`、`&` 被转义 |

## 不支持的特性

- 原始 HTML 透传（出于安全考虑会被转义）
- 脚注、定义列表
- 数学公式 / LaTeX

## 安全性

- 所有文本内容通过 `html.escape()` 进行 HTML 转义
- 代码块内仅转义 HTML，不进行 Markdown 解析
- URL 检查有害协议（`javascript:`、`vbscript:`、`file:`、`data:`）—— 被拦截的 URL 替换为 `#harmful-link`

## 注意事项

!!! info "单函数 API"
    与 mistune 提供完整的解析器/渲染器类层次结构不同，本模块仅暴露一个 `render()` 函数。这是有意为之 —— 对于将 Markdown 转换为 HTML 的常见用例，无需额外配置。

!!! info "CommonMark 子集"
    本渲染器针对最常用的 Markdown 特性。不追求 100% CommonMark 规范合规，但覆盖了 LLM 输出和文档中常见的所有特性。

- **Python 版本：** 需要 Python 3.10+（使用 `X | Y` 联合类型语法）。
- **输出兼容性：** 对所有支持的特性，生成与 `mistune.html()`（含 GFM 插件）完全一致的 HTML 输出。
- **性能：** 在所有文档规模下（含 GFM 内容）均比 mistune 快约 2 倍。

## 性能测试

与 `mistune` 在五种测试规模下进行对比：CommonMark（小、中、大）和 GFM（中、大）。

详见 [Markdown 性能测试](../benchmarks/markdown.md)。
