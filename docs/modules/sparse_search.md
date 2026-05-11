# 稀疏搜索

零依赖的全文搜索引擎，支持 BM25 系列和 TF-IDF 排名。仅依赖标准库，要求 Python 3.10+。

> **可替代:** `rank-bm25`、`bm25s`、`whoosh`

## 概述

`sparse_search` 模块提供单文件倒排索引搜索引擎，支持 BM25/BM25+/BM25L/BM25F 和 TF-IDF+Cosine 相似度排名。专为 LLM/Agent/RAG 管道设计，无需引入重量级依赖即可实现快速关键词检索。

| 文件 | 说明 | 依赖 |
|------|------|------|
| `sparse_search.py` | 纯 Python 实现 | 无（仅标准库：`re`、`math`、`json`、`sqlite3`、`statistics`、`collections`、`dataclasses`） |

### 功能特性

- **BM25 变体** -- 经典 BM25、BM25+（下界修正）、BM25L（长文档修正），可自由组合
- **BM25F** -- 多字段加权搜索（如提升标题权重）
- **TF-IDF + Cosine** -- 向量空间模型作为替代排名方案
- **动态增删改** -- 随时添加 / 删除 / 更新文档
- **元数据过滤** -- 附加任意 JSON 元数据，搜索时按条件过滤
- **持久化** -- JSON 或 SQLite 格式保存/加载
- **可插拔分词器** -- 默认 Unicode 分词；可替换为 `jieba.lcut`、NLTK 等
- **Bayesian BM25 校准** -- 通过 sigmoid 似然、复合先验和贝叶斯后验，将原始 BM25 分数转换为校准概率 [0, 1]
- **倒排索引** -- O(matched_docs) 搜索，选择性查询时显著快于 rank-bm25；不同查询类型和语料规模的详细数据见[性能测试](../benchmarks/sparse_search.md)
- **RRF（倒数排名融合）** -- 合并多路排名结果列表（如 BM25 + 稠密向量）为统一排序
- **MMR（最大边际相关性）** -- 使用自定义相似度函数对结果进行多样性重排序

## 快速开始

将单文件复制到你的项目中：

```bash
cp search/sparse_search.py your_project/
```

然后导入：

```python
from sparse_search import SparseIndex
```

## 使用示例

### 基本搜索

```python
from sparse_search import SparseIndex

index = SparseIndex()
index.add("doc1", "the quick brown fox jumps over the lazy dog")
index.add("doc2", "a fast brown car drives past the lazy cat")
index.add("doc3", "the fox and the dog are friends")

results = index.search("quick fox")
for r in results:
    print(f"{r.doc_id}: {r.score:.4f}")
```

### BM25+（下界修正）

```python
# delta > 0 启用 BM25+ 修正（默认 delta=1.0）
index = SparseIndex(delta=1.0)
```

BM25+ 防止高文档频率的词项贡献被压缩至零。

### BM25L（长文档修正）

```python
index = SparseIndex(variant="bm25l")
```

BM25L 调整长度归一化，避免对长文档过度惩罚。

### BM25F（多字段搜索）

```python
index = SparseIndex(field_weights={"title": 3.0, "body": 1.0})

index.add("doc1", {"title": "Python 指南", "body": "学习 Python 编程基础"})
index.add("doc2", {"title": "烹饪技巧", "body": "如何烹饪蟒蛇肉"})

results = index.search("python")
# doc1 排名更高，因为 "python" 出现在权重更高的 title 字段中
```

### TF-IDF + Cosine 相似度

```python
index = SparseIndex(variant="tfidf")
index.add("doc1", "machine learning algorithms")
index.add("doc2", "deep learning neural networks")

results = index.search("learning algorithms")
```

### 组合变体

所有 BM25 选项可自由组合：

```python
# BM25L + BM25F + BM25+（delta）
index = SparseIndex(
    variant="bm25l",
    field_weights={"title": 2.0, "body": 1.0},
    delta=0.5,
)
```

### Bayesian BM25 概率校准

将原始 BM25 分数转换为校准概率 [0, 1]：

```python
index = SparseIndex()
index.add("doc1", "the quick brown fox jumps over the lazy dog")
index.add("doc2", "the quick brown fox")
index.add("doc3", "the lazy dog sleeps all day long")

# 从语料统计自动估计校准参数
index.calibrate()

results = index.search("quick fox")
for r in results:
    print(f"{r.doc_id}: {r.score:.4f}")  # 分数现在在 [0, 1] 范围内
```

也可以手动指定参数或应用基准率校正：

```python
# 手动参数
index.calibrate(alpha=1.5, beta=2.0)

# 带基准率校正（将概率向先验方向偏移）
index.calibrate(alpha=1.5, beta=2.0, base_rate=0.05)
```

校准分数的适用场景：

- **阈值过滤** -- 拒绝低于概率阈值的结果
- **多信号融合** -- 在统一尺度上与其他评分信号组合
- **跨查询对比** -- 概率值可在不同查询间进行比较

### 元数据与过滤

```python
index = SparseIndex()
index.add("doc1", "Python web framework", metadata={"year": 2024, "lang": "en"})
index.add("doc2", "Django tutorial", metadata={"year": 2023, "lang": "en"})
index.add("doc3", "Flask guide", metadata={"year": 2024, "lang": "zh"})

# 精确匹配过滤
results = index.search("python", filters={"year": 2024})

# 自定义过滤（callable）
results = index.search("python", filters={"year": lambda y: y >= 2024})
```

### 自定义分词器

```python
import jieba

# 使用 jieba 进行中文分词搜索
index = SparseIndex(tokenize=jieba.lcut)
index.add("doc1", "Python 编程语言入门教程")
results = index.search("编程语言")
```

### 文档管理

```python
index = SparseIndex()
index.add("doc1", "original content")

# 更新已有文档
index.update("doc1", "updated content", metadata={"version": 2})

# 删除文档
index.remove("doc1")

# 检查成员关系
print("doc1" in index)       # False
print(len(index))            # 0
print(index.doc_count)       # 0
print(index.vocab_size)      # 0
```

### 持久化

```python
index = SparseIndex()
index.add("doc1", "hello world")

# 保存为 JSON（人类可读）
index.save("index.json")

# 保存为 SQLite（大索引更高效）
index.save("index.db")

# 加载（自动检测格式）
loaded = SparseIndex.load("index.json")
loaded = SparseIndex.load("index.db")
```

### 倒数排名融合（RRF）

将多路检索系统的结果（如 BM25 稀疏搜索 + 稠密向量搜索）合并为统一排名列表：

```python
from sparse_search import SparseIndex, Result, rrf

# 稀疏检索
index = SparseIndex()
index.add("d1", "quick brown fox")
index.add("d2", "lazy dog")
index.add("d3", "fast red car")
sparse_results = index.search("quick fox", top_k=20)

# 稠密检索（来自外部系统如 FAISS、Chroma 等）
dense_results = [Result("d1", 0.92), Result("d3", 0.85), Result("d2", 0.71)]

# 使用 RRF 融合（默认 k=60，遵循 Cormack et al.）
fused = rrf(sparse_results, dense_results, top_k=10)

# 加权融合（提升稀疏结果权重）
fused = rrf(sparse_results, dense_results, weights=[2.0, 1.0], top_k=10)
```

RRF 仅基于排名位置而非原始分数进行融合，非常适合组合分数尺度不一致的检索系统。

### 最大边际相关性（MMR）

对结果进行多样性重排序——适用于顶部结果过于相似的场景：

```python
from sparse_search import SparseIndex, mmr, jaccard_similarity

index = SparseIndex()
index.add("d1", "python web framework flask")
index.add("d2", "python web framework django")
index.add("d3", "machine learning with python")
index.add("d4", "python web development guide")

results = index.search("python web", top_k=10)

# 基于文档 token 构建相似度函数
doc_tokens = {
    "d1": {"python", "web", "framework", "flask"},
    "d2": {"python", "web", "framework", "django"},
    "d3": {"machine", "learning", "with", "python"},
    "d4": {"python", "web", "development", "guide"},
}

def sim(a, b):
    return jaccard_similarity(doc_tokens[a.doc_id], doc_tokens[b.doc_id])

# 选择 top 3 多样化结果（lambda_=0.7 偏向相关性而非多样性）
diverse = mmr(results, sim, lambda_=0.7, top_k=3)
```

`lambda_` 参数控制相关性-多样性的权衡：

- `lambda_=1.0` -- 纯相关性（与原始排名相同）
- `lambda_=0.5` -- 均衡（默认值）
- `lambda_=0.0` -- 纯多样性（最不相似的项优先）

## 设计说明

### 索引参数 vs 评分参数

只有 `tokenize` 分词函数影响索引内容。其他参数（`variant`、`k1`、`b`、`delta`、`field_weights`）仅在评分时使用，不改变索引中存储的数据。这意味着同一个索引可以使用不同的算法和调参进行搜索，无需重新索引。

### `field_weights` 不可变

`field_weights` 在构造时设定，决定文档以单字段还是多字段方式存储。索引不保存原始文档文本，只保存分词后的词频数据。因此：

- 单字段索引**无法**转换为多字段索引（字段边界已丢失）
- 要更改 `field_weights`，必须从源数据重建索引
- `update()` 替换文档的索引数据，但仍需要原始文本

### 索引速度 vs 搜索速度

索引使用三层倒排索引（`term → doc_id → field → tf`）以统一支持单字段和多字段（BM25F）模式。索引构建相比 numpy 后端库有额外开销，但搜索性能取决于查询的选择性：

- **选择性查询**（匹配文档少）：倒排索引仅遍历匹配的 posting O(matched_docs)，显著快于 rank-bm25 和 bm25s 的 O(N) 全量扫描。
- **宽泛查询**（高频词匹配大量文档）：numpy 后端库（bm25s、rank-bm25）凭借向量化数组运算可能更快。
- **小语料**（< 1K 文档）：三者均为亚毫秒级，差异可忽略。

详细数据见[性能测试](../benchmarks/sparse_search.md)。

单次插入的时间复杂度为 **O(tokens_in_doc)**，不会随索引规模增长而退化——第 1 个文档和第 100,000 个文档在相同 token 数量下耗时相同，因为所有底层操作（dict 查找、set 添加）均为 O(1) 均摊。

## API 参考

### `SparseIndex(variant, k1, b, delta, field_weights, tokenize, calibrated)`

主搜索索引类。

**参数：**

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `variant` | `str` | `"bm25"` | 排名算法：`"bm25"`、`"bm25l"` 或 `"tfidf"` |
| `k1` | `float` | `1.5` | BM25 词频饱和参数（tfidf 时忽略） |
| `b` | `float` | `0.75` | BM25 文档长度归一化因子（tfidf 时忽略） |
| `delta` | `float` | `1.0` | BM25+ 下界修正值。设为 `0` 则为经典 BM25 |
| `field_weights` | `dict[str, float] \| None` | `None` | BM25F 各字段权重 |
| `tokenize` | `Callable[[str], list[str]] \| None` | `None` | 自定义分词函数。默认为 Unicode 分词 + 小写化 |
| `calibrated` | `bool` | `False` | 若为 `True`，BM25 分数将通过 Bayesian BM25 转换为校准概率 |

**方法：**

| 方法 | 说明 |
|------|------|
| `add(doc_id, content, metadata=None)` | 添加新文档。`doc_id` 已存在时抛出 `ValueError` |
| `remove(doc_id)` | 删除文档。未找到时抛出 `KeyError` |
| `update(doc_id, content, metadata=None)` | 替换文档。未找到时抛出 `KeyError` |
| `search(query, top_k=10, filters=None)` | 搜索并返回排名结果 |
| `calibrate(*, alpha=None, beta=None, base_rate=None, n_samples=50)` | 估计或设置贝叶斯校准参数。启用校准模式 |
| `save(path, format=None)` | 保存索引到磁盘（JSON 或 SQLite） |
| `load(path)` | *(类方法)* 从磁盘加载索引（自动检测格式） |

**属性：**

| 属性 | 类型 | 说明 |
|------|------|------|
| `doc_count` | `int` | 索引中的文档数量 |
| `vocab_size` | `int` | 唯一词项数量 |

---

### `Result`

表示单个搜索结果的数据类。

| 属性 | 类型 | 说明 |
|------|------|------|
| `doc_id` | `str` | 文档标识符 |
| `score` | `float` | 相关性分数 |
| `metadata` | `dict[str, Any] \| None` | 文档元数据 |

---

### 默认分词器

内置分词器按 Unicode 词边界分割，并将所有 token 小写化：

```python
"Hello, World! 42" -> ["hello", "world", "42"]
```

生产环境中建议传入自定义分词器，支持词干提取、停用词移除或 CJK 分词。

---

### `rrf(*result_lists, k=60, top_k=None, weights=None)`

倒数排名融合——将多路排名结果列表合并为统一排名。

**参数：**

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `*result_lists` | `list[Result]` | *(必需)* | 一个或多个排名结果列表 |
| `k` | `int` | `60` | RRF 常数，控制排名位置的敏感度 |
| `top_k` | `int \| None` | `None` | 最大返回数量。`None` 返回全部 |
| `weights` | `list[float] \| None` | `None` | 各列表权重。`None` = 等权重 |

**返回值：** `list[Result]`，按 RRF 分数降序排列。元数据取自原始分数最高的出现。

---

### `mmr(results, similarity_fn, *, lambda_=0.5, top_k=None)`

最大边际相关性——对结果进行多样性重排序。

**参数：**

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `results` | `list[Result]` | *(必需)* | 待重排序的候选结果 |
| `similarity_fn` | `Callable[[Result, Result], float]` | *(必需)* | 相似度函数，返回 [0, 1] |
| `lambda_` | `float` | `0.5` | 权衡参数：1.0 = 纯相关性，0.0 = 纯多样性 |
| `top_k` | `int \| None` | `None` | 选择的结果数量。`None` = 全部 |

**返回值：** `list[Result]`，分数为 MMR 值。

---

### `jaccard_similarity(set_a, set_b)`

Jaccard 相似度系数：`|A ∩ B| / |A ∪ B|`。两个集合均为空时返回 0.0。

## 与 rank-bm25 和 bm25s 的对比

| 特性 | zerodep sparse_search | rank-bm25 | bm25s |
|------|----------------------|-----------|-------|
| 依赖 | 无（仅标准库） | numpy | numpy, scipy |
| BM25 变体 | BM25/BM25+/BM25L/BM25F/TF-IDF | BM25Okapi/BM25Plus/BM25L | BM25（Lucene 默认） |
| 多字段（BM25F） | 支持 | 不支持 | 不支持 |
| 搜索复杂度 | O(matched_docs) | O(N) 全量扫描 | O(N) 稀疏矩阵 |
| 动态增删改 | 支持 | 不支持（需重建） | 不支持（需重建） |
| 元数据过滤 | 支持 | 不支持 | 不支持 |
| 持久化 | JSON + SQLite | 不支持 | 支持 |
| 自定义分词器 | 支持 | 支持 | 支持 |
| RRF / MMR | 内置 | 不支持 | 不支持 |
| Bayesian 校准 | 支持 | 不支持 | 不支持 |

### 性能特征

搜索性能取决于**查询选择性**——有多少文档匹配查询词：

- **选择性查询**（稀有词，匹配文档少）：zerodep 最快（倒排索引优势）
- **宽泛查询**（高频词，匹配大量文档）：bm25s 最快（numpy 向量化）
- **小语料**（< 1K 文档）：三者均为亚毫秒级，差异可忽略

详细数据见[性能测试](../benchmarks/sparse_search.md)。

**何时使用 zerodep：** 中小规模语料、动态文档管理、多字段搜索（BM25F）、元数据过滤、RRF/MMR 融合、零依赖部署，或大语料上的选择性查询。

**何时使用 rank-bm25：** 简单的静态 BM25 评分，且项目已依赖 numpy。

**何时使用 bm25s：** 大规模静态语料配合宽泛查询，numpy 向量化提供更高吞吐。

## 性能测试

与 rank-bm25 的性能对比，使用 pytest-benchmark 测试。

详见 [稀疏搜索性能测试](../benchmarks/sparse_search.md)。
