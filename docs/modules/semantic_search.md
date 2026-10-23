# 语义搜索

零依赖的稠密向量检索，支持 Flat、IVF 与 LSH 三种索引——仅使用标准库，Python 3.10+。

> **替代：** `faiss-cpu`、`hnswlib`、`chromadb`（适用于中小规模集合）

## 概述

`semantic_search` 模块负责存储嵌入向量并回答最近邻查询，无需引入 numpy 或向量数据库。它内置三种索引类型、三种距离度量、可选的 SQ8 量化、JSON/SQLite 持久化，以及用于混合检索的重排工具。

| 文件 | 说明 | 依赖 |
|------|------|------|
| `semantic_search.py` | 纯 Python 实现 | 无（仅标准库：`array`、`base64`、`dataclasses`、`heapq`、`json`、`math`、`pathlib`、`random`、`sqlite3`、`urllib`、`typing`） |

### 主要特性

- **三种索引类型**——`flat`（精确暴力搜索）、`ivf`（k-means 倒排列表）、`lsh`（随机投影哈希表）
- **三种度量**——`cosine`、`euclidean`、`inner_product`
- **文本或向量查询**——配置一次嵌入函数后即可按文本检索
- **嵌入辅助函数**——内置 OpenAI、Cohere、Voyage 与 Jina 适配器
- **元数据过滤**——附加任意 JSON 元数据，并在检索时过滤
- **SQ8 量化**——存储缩小到约四分之一；调用 `build_index()` 后，检索距离直接由量化数据计算
- **持久化**——支持 JSON 或 SQLite 格式
- **重排工具**——`rrf()`（倒数排名融合）与 `mmr()`（最大边际相关性）

## 在项目中使用

将单文件复制到你的项目中：

```bash
cp semantic_search/semantic_search.py your_project/
```

然后导入：

```python
from semantic_search import SemanticIndex
```

## 使用示例

### 基本检索

```python
from semantic_search import SemanticIndex

index = SemanticIndex(dim=3)
index.add("doc1", vector=[1.0, 0.0, 0.0])
index.add("doc2", vector=[0.0, 1.0, 0.0])
index.add("doc3", vector=[0.0, 0.0, 1.0])

results = index.search(vector=[0.9, 0.1, 0.0], top_k=2)
for r in results:
    print(r.doc_id, r.score)   # doc1, doc2
```

### 文本查询与嵌入辅助函数

```python
from semantic_search import SemanticIndex, openai_embed

embed = openai_embed(api_key="sk-...", model="text-embedding-3-small")
index = SemanticIndex(dim=1536, embed=embed)

index.add("intro", text="ToolRegistry 统一了工具调用")
index.add("guide", text="从 Python 函数注册工具")

results = index.search(text="如何注册工具？", top_k=5)
```

`cohere_embed()`、`voyage_embed()` 与 `jina_embed()` 的用法相同；任何签名为
`list[str] -> list[list[float]]` 的可调用对象都可以作为 `embed=` 传入。

### 元数据过滤

```python
index.add("a", vector=[1.0, 0.0], metadata={"year": 2023, "lang": "en"})
index.add("b", vector=[0.9, 0.1], metadata={"year": 2025, "lang": "en"})

# 既支持精确匹配，也支持可调用对象
results = index.search(vector=[1.0, 0.0], filters={"year": lambda y: y > 2024})
```

带过滤条件时，`search()` 会先向索引索取最多 `top_k` 四倍的候选再过滤，因此少量被
拒绝的结果不会让返回数量缩水。在 IVF 与 LSH 上，未被探测的簇或桶中的文档不会成
为候选；docstring 中对此有说明。

### 近似索引

```python
index = SemanticIndex(dim=768, index_type="ivf", n_clusters=64, nprobe=4)
# ... 添加文档 ...
index.build_index()          # 检索 IVF/LSH 前必须构建

index = SemanticIndex(dim=768, index_type="lsh", n_tables=8, n_hash_funcs=12)
```

`search()` 会在 IVF 或 LSH 索引变脏时按需构建；除非启用量化，flat 索引从不需要
构建。

### 量化

```python
index = SemanticIndex(dim=768, index_type="flat", quantize=True)
# ... 添加文档 ...
index.build_index()
```

`build_index()` 将每个维度压缩为一个字节（SQ8），并释放 float32 数组，因此索引
占用约为原来的四分之一。此后检索距离由量化数据重建——预计召回率会有少量下降
（约 1%）。`add()`、`update()` 与 `remove()` 会先重建浮点数组，下一次
`build_index()` 再重新量化。

### 持久化

```python
index.save("vectors.json")
index.save("vectors.db")            # SQLite，按扩展名选择

loaded = SemanticIndex.load("vectors.db")
loaded.search(vector=query, top_k=5)
```

量化索引只保存 SQ8 数据：JSON 中 `vectors_b64` 为空，SQLite 不写入 `vectors`
行。

### 混合检索

```python
from semantic_search import mmr, rrf

fused = rrf([keyword_results, vector_results], k=60)

diverse = mmr(
    query_vector,
    candidate_vectors,
    candidate_ids,
    lambda_score=0.7,
)
```

## API 参考

完整的类与函数清单见 [API 参考](../api/semantic_search.md)。
