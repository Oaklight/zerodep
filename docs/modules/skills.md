# Agent Skills 运行时

Agent Skills 运行时 -- 零依赖，仅标准库，Python 3.10+。

## 概述

[Agent Skills](https://agentskills.io) 规范的轻量级运行时。以编程方式解析、发现、管理和选择 Agent Skills。专为需要将 Skills 生态集成到自定义 Agent 应用的 Agent 框架开发者设计。

| 文件 | 描述 | 依赖 |
|------|------|------|
| `skills.py` | Agent Skills 运行时 | `frontmatter`（兄弟模块）、`search`（兄弟模块，可选） |

**核心功能：**

- 按 agentskills.io 规范解析和验证 `SKILL.md` 文件
- 从目录树中发现技能
- 在注册表中注册和管理技能
- 按查询相关性预筛选技能（可插拔选择器）
- 生成系统提示词 XML（目录格式和激活格式）

## 在项目中使用

将单个 `.py` 文件（及其兄弟依赖）复制到你的项目中：

```bash
# 必需
cp skills/skills.py your_project/
cp frontmatter/frontmatter.py your_project/
cp yaml/yaml.py your_project/

# 可选（用于 BM25 选择）
cp search/sparse_search.py your_project/
```

或通过 CLI 安装：

```bash
zerodep add skills
```

然后直接导入：

```python
from skills import Skill, SkillRegistry, load, loads, validate, to_catalog
```

## 使用示例

### 解析技能

```python
from skills import load, loads

# 从目录加载
skill = load("path/to/my-skill")
print(skill.name)           # "my-skill"
print(skill.description)    # "技能描述"
print(skill.instructions)   # 完整 Markdown 正文

# 从文本解析
skill = loads("""---
name: pdf-processing
description: Extract text from PDF files
---
# PDF Processing

When the user asks about PDFs, use this skill.
""")
```

### 程序化创建技能

```python
from skills import Skill, SkillProperties

# 从字典创建
skill = Skill.from_dict({
    "name": "my-tool",
    "description": "Does something useful",
    "instructions": "# My Tool\n\nUse this when...",
})

# 序列化回 SKILL.md 格式（支持往返转换）
md_text = skill.to_markdown()
print(md_text)
# ---
# name: my-tool
# description: Does something useful
# ---
# # My Tool
#
# Use this when...
```

### 发现和注册技能

```python
from skills import SkillRegistry

registry = SkillRegistry()

# 扫描标准 Agent Skills 目录
registry.discover(
    "~/.agents/skills",       # 用户级技能
    ".agents/skills",         # 项目级技能
)

# 递归发现嵌套布局（category/skill/）
registry.discover("~/.agents/skills", recursive=True)

# 覆盖机制：项目级技能优先于用户级技能
registry.discover("~/.agents/skills")           # 用户级
registry.discover(".agents/skills", override=True)  # 项目级覆盖

print(f"发现 {len(registry)} 个技能")
for skill in registry:
    print(f"  - {skill.name}: {skill.description}")
```

### 预筛选技能（节省 Token）

```python
from skills import SkillRegistry, to_catalog

registry = SkillRegistry()
registry.discover("~/.agents/skills")

# 预筛选：100 个技能 -> 最相关的 10 个
matches = registry.select("convert this PDF to markdown", top_k=10)
shortlist = [m.skill for m in matches]

# 只将筛选后的目录注入系统提示词（节省 token）
catalog_xml = to_catalog(shortlist)

# LLM 看到缩减后的目录，自行决定激活哪个技能
```

### 质量过滤

```python
# 按最低相关性分数过滤
matches = registry.select("PDF conversion", top_k=10, min_score=0.3)

# 按工具兼容性过滤
matches = registry.select(
    "review this code",
    available_tools=["Bash", "Read", "Write"],
)

# 独立的兼容性过滤函数
from skills import filter_compatible

compatible = filter_compatible(
    registry.list(),
    available_tools=["Bash", "Read", "Write", "Glob"],
)
```

### 自定义选择器

```python
from skills import Selector, SelectionResult, Skill

class EmbeddingSelector:
    """基于句向量嵌入的自定义选择器。"""

    def __init__(self, model_name: str):
        # 初始化嵌入模型
        ...

    def select(
        self, query: str, skills: list[Skill], top_k: int
    ) -> list[SelectionResult]:
        # 你的嵌入排序逻辑
        ...

# 使用
results = registry.select("query", selector=EmbeddingSelector("bge-m3"))
```

### 验证技能

```python
from skills import validate

problems = validate("path/to/my-skill")
if problems:
    print("验证失败：")
    for p in problems:
        print(f"  - {p}")
else:
    print("技能验证通过！")
```

### 生成提示词

```python
from skills import load, to_catalog, compose

skill_a = load("skills/pdf-processing")
skill_b = load("skills/code-review")

# 第一层：目录 XML（所有技能的名称和描述）
catalog = to_catalog([skill_a, skill_b])

# 第二层：激活提示词（选中技能的完整指令）
prompt = skill_a.to_prompt()

# 第二层增强：内联资源文件内容
prompt = skill_a.to_prompt(inline_resources=True)
# 资源文件内容直接包含在 XML 输出中

# 组合多个技能
combined = compose(skill_a, skill_b)
```

## 渐进式披露

遵循 Agent Skills 规范，本模块支持三级渐进式披露：

| 层级 | 内容 | Token 开销 | 方法 |
|------|------|-----------|------|
| 1. 目录 | 名称 + 描述 | ~50-100/技能 | `to_catalog()` |
| 2. 指令 | SKILL.md 完整正文 | <5000/技能 | `skill.to_prompt()` |
| 2+. 内联 | 指令 + 资源文件内容 | 视内容而定 | `skill.to_prompt(inline_resources=True)` |
| 3. 资源 | scripts/、references/ | 按需 | `skill.scripts`、`skill.references` |

## 内置选择器

| 选择器 | 描述 | 依赖 |
|--------|------|------|
| `KeywordSelector` | 基于名称和描述的关键词匹配 | 无（仅标准库） |
| `BM25Selector` | 基于完整技能内容的 BM25 排序 | 兄弟 `search` 模块 |

实现 `Selector` 协议即可创建自定义选择器（基于嵌入、重排序、LLM 等）。

## API 参考

完整的函数签名和文档字符串请参阅 [API 参考](../api/skills.md)。

## 性能测试

本模块不提供性能测试。作为实现 Agent Skills 规范的工具模块，没有直接的第三方对标库用于性能比较 -- 详见[技能性能测试](../benchmarks/skills.md)。
