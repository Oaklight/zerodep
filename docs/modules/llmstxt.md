# llms.txt 解析器

零依赖的 [llms.txt 规范](https://llmstxt.org/) 解析器 — 将 llms.txt 文件解析为结构化数据，并提供页面级 Markdown URL 发现功能。

## 特性

- **规范兼容解析**：H1 标题、引用描述、详情段落、H2 分节及链接条目
- **Optional 分节处理**：`## Optional` 条目按规范语义自动分离
- **统一 URL 发现**：`find_candidates()` 优先搜索 llms.txt 条目，无匹配时回退到启发式规则
- **宽容解析**：仅 H1 标题为必填，其余缺失项优雅降级
- **不可变结果**：冻结 dataclass 作为解析输出
- **零依赖**：仅使用标准库（`re`、`urllib.parse`、`dataclasses`）

## 快速开始

```python
from llmstxt import parse, find_candidates

# 解析 llms.txt 文件
doc = parse("""# My Project

> A brief description of the project.

Some extra detail here.

## Docs

- [Guide](https://example.com/guide.md): The main guide
- [API](https://example.com/api.md): API reference

## Optional

- [Advanced](https://example.com/advanced.md): Advanced topics
""")

print(doc.title)        # 'My Project'
print(doc.description)  # 'A brief description of the project.'
print(doc.details)      # 'Some extra detail here.'
print(doc.sections)     # {'Docs': [FileEntry(name='Guide', ...), ...]}
print(doc.optional)     # [FileEntry(name='Advanced', ...)]
```

## API

### `parse(text)`

将 llms.txt 内容解析为结构化的 `LlmsTxt` 对象。

| 参数 | 类型 | 说明 |
|------|------|------|
| `text` | `str` | llms.txt 文件的原始文本内容 |

**返回值：** `LlmsTxt` — 解析结果。

**异常：** `LlmsTxtError` — 缺少必需的 H1 标题或输入为空时抛出。

### `find_candidates(url, doc=None)`

为给定 URL 查找候选 Markdown 资源。

提供 `doc` 时，搜索所有分节和 Optional 条目进行 URL 匹配（精确 > 扩展名变体 > 路径前缀）。未找到匹配项或 `doc` 为 `None` 时，回退到启发式 URL 生成。

| 参数 | 类型 | 说明 |
|------|------|------|
| `url` | `str` | 要查找的页面 URL |
| `doc` | `LlmsTxt \| None` | 可选的已解析 llms.txt 对象 |

**返回值：** `list[FileEntry]` — 按匹配质量排序的候选列表。

### `LlmsTxt`

表示已解析 llms.txt 文件的冻结 dataclass。

| 字段 | 类型 | 说明 |
|------|------|------|
| `title` | `str` | H1 标题（项目/站点名称） |
| `description` | `str` | 引用摘要，缺失时为 `""` |
| `details` | `str` | 引用与首个 H2 之间的段落，缺失时为 `""` |
| `sections` | `dict[str, list[FileEntry]]` | H2 分节名 → 条目列表（不含 "Optional"） |
| `optional` | `list[FileEntry]` | `## Optional` 分节中的条目 |

### `FileEntry`

表示单个链接条目的冻结 dataclass。

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | `str` | 链接的显示名称 |
| `url` | `str` | 链接资源的 URL |
| `notes` | `str` | `: ` 分隔符后的描述文本，缺失时为 `""` |

### `LlmsTxtError`

解析失败时抛出的异常（缺少 H1 标题或输入为空）。

## 使用示例

### 从已解析的 llms.txt 中查找 URL

```python
from llmstxt import parse, find_candidates

doc = parse(llms_txt_content)

# 精确匹配和扩展名匹配
results = find_candidates(
    "https://docs.example.com/guide.html", doc=doc
)
# 可找到 guide.html.md、guide.md 等条目

# 前缀匹配 — 查找路径下的所有条目
results = find_candidates(
    "https://docs.example.com/tutorials", doc=doc
)
# 返回 URL 以 /tutorials/ 开头的所有条目
```

### 启发式回退（无 llms.txt）

```python
from llmstxt import find_candidates

# 未提供 doc — 按约定生成候选 .md URL
results = find_candidates("https://example.com/docs/guide")
for entry in results:
    print(entry.url)
# https://example.com/docs/guide.md
# https://example.com/docs/guide/index.md
# https://example.com/docs/guide/index.html.md
```

### 典型发现流程

```python
import urllib.request
from llmstxt import parse, find_candidates, LlmsTxtError

page_url = "https://example.com/docs/guide"
site_root = "https://example.com"

# 尝试获取并解析站点的 llms.txt
try:
    llms_txt = urllib.request.urlopen(f"{site_root}/llms.txt").read().decode()
    doc = parse(llms_txt)
except (Exception, LlmsTxtError):
    doc = None

# 统一查找 — 有 llms.txt 则使用，否则启发式推导
candidates = find_candidates(page_url, doc=doc)
for entry in candidates:
    print(f"尝试: {entry.url}")
```

## 匹配策略

`find_candidates()` 按匹配质量排序返回结果：

1. **精确匹配** — 条目 URL 与输入 URL 完全相等（去除 query/fragment 后）
2. **扩展名变体** — `guide.html` ↔ `guide.html.md`，`guide` ↔ `guide.md`
3. **路径前缀** — 输入路径是条目路径的前缀或反之
4. **启发式回退** — 无 llms.txt 匹配时，生成 `{url}.md`、`{url}/index.md`、`{url}/index.html.md`

## 注意事项

- 解析器采用**宽容模式**：仅 H1 标题为必填。缺少引用、详情或分节时返回空字符串/空列表。
- `## Optional` 按规范特殊处理 — 其条目进入 `LlmsTxt.optional`，不在 `sections` 中。
- 大小写敏感：仅精确的 `## Optional`（大写 O）触发特殊处理。
- Windows 换行符（`\r\n`）会自动规范化。
- `find_candidates()` 匹配前会去除 URL 中的查询字符串和片段标识符。
