# 正文提取器（Readability）

零依赖的网页正文提取模块，移植自 Mozilla Readability.js —— 仅使用标准库，支持 Python 3.10+。

> **可替代:** `readability-lxml`、`newspaper3k`、`trafilatura`

## 概述

`readability` 模块从网页中提取主要文章内容，移除导航栏、广告、侧边栏等无关元素。其核心算法移植自 [Mozilla Readability.js](https://github.com/mozilla/readability)，基于 zerodep 的 [`soup`](soup.md) 模块进行 HTML 解析和操作。

| 文件 | 描述 | 依赖 |
|------|------|------|
| `readability.py` | 纯 Python 实现 | `soup` 模块（仅标准库） |

### 主要特性

- **正文提取** —— 从杂乱的网页中识别并提取主要文章内容
- **元数据提取** —— 标题、作者、摘要、发布时间、站点名称、语言、文本方向
- **JSON-LD 支持** —— 从 Schema.org JSON-LD 结构化数据中提取元数据
- **OpenGraph / meta 标签** —— 回退到 og:title、og:description、article:author 等
- **智能标题精炼** —— 从 `<title>` 标签中去除站点名后缀（如 "文章标题 | 站点名" → "文章标题"）
- **两级重试** —— 首次激进过滤候选元素；如果结果过短，放宽过滤条件重试
- **可读性检测** —— 快速启发式判断页面是否可能包含文章

## 在你的项目中使用

将两个必需文件复制到你的项目中：

```bash
cp soup/soup.py your_project/
cp readability/readability.py your_project/
```

然后导入：

```python
from readability import extract, is_probably_readable
```

## 使用示例

### 基本文章提取

```python
from readability import extract

html = """
<html><head><title>我的博客文章 - 我的网站</title></head>
<body>
  <nav>导航链接...</nav>
  <article>
    <h1>我的博客文章</h1>
    <p>这是文章的主要内容，包含足够的文本以便被可读性算法识别为有意义的内容。</p>
    <p>更多具有实质内容的段落...</p>
  </article>
  <aside>侧边栏广告...</aside>
  <footer>版权信息...</footer>
</body></html>
"""

result = extract(html)
print(result.title)    # "我的博客文章"
print(result.text)     # 文章的纯文本内容
print(result.content)  # 文章的清洁 HTML
print(result.length)   # 提取文本的字符数
```

### 检查页面是否可读

```python
from readability import is_probably_readable

# 在完整提取前快速检查
if is_probably_readable(html):
    result = extract(html)
else:
    print("此页面似乎不包含文章内容")
```

### 带 URL 提取以获取元数据

```python
result = extract(html, url="https://example.com/article/123")
print(result.title)
print(result.author)
print(result.excerpt)
print(result.site_name)
print(result.published_time)
print(result.lang)
print(result.dir)   # "ltr" 或 "rtl"
```

### 处理 JSON-LD 元数据

包含 Schema.org JSON-LD 的页面可获取更丰富的元数据：

```python
html = """
<html><head>
<script type="application/ld+json">
{
  "@type": "Article",
  "headline": "突发新闻报道",
  "author": {"name": "张三"},
  "datePublished": "2026-01-15T10:30:00Z",
  "description": "突发新闻摘要。"
}
</script>
</head><body>
<article><p>详细的文章内容...</p></article>
</body></html>
"""

result = extract(html)
print(result.title)           # "突发新闻报道"
print(result.author)          # "张三"
print(result.published_time)  # "2026-01-15T10:30:00Z"
print(result.excerpt)         # "突发新闻摘要。"
```

## 算法概述

Readability 算法遵循 Mozilla Readability.js 的方法：

1. **预清理** —— 移除 `<script>`、`<style>`、`<link>`、`<noscript>` 标签
2. **移除不太可能的候选者** —— class/id 匹配 "sidebar"、"comment"、"footer"、"nav" 等模式的元素
3. **将 div 转换为段落** —— 没有块级子元素的 div 转为 `<p>` 标签以参与评分
4. **段落评分** —— 基于文本长度、逗号数量和 class/id 启发式规则分配内容分数；将分数传播到父节点和祖父节点
5. **选择最佳候选** —— 选取得分最高的节点
6. **组装文章** —— 将高分兄弟节点合并到文章容器中
7. **清理** —— 移除低质量元素（表单、空节点、高链接密度区域）
8. **必要时重试** —— 如果提取内容过短（< 250 字符），在不进行激进候选过滤的情况下重试

## API 参考

### `extract(html, url=None)`

从 HTML 字符串中提取主要文章内容。

**参数：**

| 名称 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `html` | `str` | -- | 要提取的 HTML 字符串。 |
| `url` | `str \| None` | `None` | 可选的 URL，用于元数据解析。 |

**返回：** `ReadabilityResult` 数据类。

### `is_probably_readable(html, min_score=20, min_content_length=140)`

快速启发式检查 HTML 是否可能包含文章。

**参数：**

| 名称 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `html` | `str` | -- | 要检查的 HTML 字符串。 |
| `min_score` | `float` | `20` | 最低分数阈值。 |
| `min_content_length` | `int` | `140` | 每个节点的最小文本长度。 |

**返回：** `bool`

### `ReadabilityResult`

| 字段 | 类型 | 描述 |
|------|------|------|
| `title` | `str` | 文章标题（从 `<title>` 或元数据中精炼） |
| `content` | `str` | 清理后的文章正文 HTML |
| `text` | `str` | 文章正文的纯文本 |
| `author` | `str \| None` | 作者名称 |
| `excerpt` | `str \| None` | 文章摘要/描述 |
| `site_name` | `str \| None` | 站点名称 |
| `published_time` | `str \| None` | 发布时间戳 |
| `lang` | `str \| None` | 语言代码（如 `"en"`） |
| `dir` | `str \| None` | 文本方向（`"ltr"` 或 `"rtl"`） |
| `length` | `int` | 纯文本字符数 |

## 与替代方案对比

| 特性 | zerodep readability | readability-lxml | Mozilla Readability.js |
|------|-------------------|------------------|----------------------|
| 语言 | Python | Python | JavaScript |
| 依赖 | 无（标准库 + soup） | lxml、cssselect | jsdom（Node.js） |
| 文件数 | 单文件 + soup | 多文件包 | 多文件包 |
| JSON-LD 元数据 | 是 | 否 | 是 |
| OpenGraph 元数据 | 是 | 部分 | 是 |
| 标题精炼 | 是 | 是 | 是 |
| RTL 支持 | 是 | 否 | 是 |

**适用场景（zerodep）：** 需要在 Python 中进行正文提取且不想引入任何 pip 依赖。

**适用场景（readability-lxml）：** 已有 lxml 依赖且需要最大兼容性。

**适用场景（Mozilla Readability.js）：** 在 Node.js 环境下工作或需要参考实现。

## 性能测试

与 `readability-lxml` 和 Mozilla Readability.js 的性能对比。

详见 [Readability 性能测试](../benchmarks/readability.md)。
