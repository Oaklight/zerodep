# 稀疏搜索性能测试

zerodep sparse_search 与 [`rank-bm25`](https://pypi.org/project/rank-bm25/) 及 [`bm25s`](https://github.com/xhluca/bm25s) 的性能对比。

!!! info "测试环境"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **工具:** pytest-benchmark 5.2.3（报告均值）
    - **对标库:** rank-bm25 0.2.2, bm25s 0.3.8
    - **最后更新:** 2026-04-29

## 实现

| 实现 | 文件/包 | 说明 |
|------|---------|------|
| **zerodep** | `sparse_search.py` | 仅标准库的 BM25/TF-IDF 搜索引擎（倒排索引） |
| **rank-bm25** | *(对照)* | 基于 numpy 的流行 BM25 库 |
| **bm25s** | *(对照)* | 基于 numpy + scipy 的快速 BM25 库（稀疏矩阵评分） |

## 性能对比（均值）

### 选择性查询（合成语料，稀有词）

查询匹配少量文档——倒排索引 O(matched_docs) 优势最明显的场景。

| 语料规模 | zerodep | rank-bm25 | bm25s |
|----------|---------|-----------|-------|
| 200 文档 | 3.2 μs | 88.6 μs | 16.8 μs |
| 1000 文档 | 1.8 μs | 239.6 μs | 15.2 μs |

### 宽泛查询（Zipf 分布语料，高频词）

使用高频词匹配大量文档——numpy 向量化运算占优的场景。

| 语料规模 | zerodep | rank-bm25 | bm25s |
|----------|---------|-----------|-------|
| 1K 文档 | 2.48 ms | 221.9 μs | 43.6 μs |
| 10K 文档 | 56.2 ms | 2.72 ms | 59.9 μs |

### 选择性查询（Zipf 分布语料，稀有词）

在真实词频分布下使用稀有词查询。

| 语料规模 | zerodep | rank-bm25 | bm25s |
|----------|---------|-----------|-------|
| 1K 文档 | 19.0 μs | 193.9 μs | 54.3 μs |
| 10K 文档 | 87.0 μs | 2.74 ms | 185.5 μs |

### 索引速度

| 语料规模 | zerodep | rank-bm25 | bm25s |
|----------|---------|-----------|-------|
| 1000 文档 | 41.7 ms | 8.8 ms | 41.1 ms |

### Bayesian 校准开销

| 操作 | 耗时 | 对比原始搜索 |
|------|------|-------------|
| 原始 BM25 搜索 | 22.8 μs | 基准 |
| 校准 BM25 搜索 | 43.4 μs | ~1.9 倍开销 |
| `calibrate()`（20 文档） | 662.0 μs | 一次性成本 |

## 主要结论

- **搜索性能取决于查询选择性。** 对于选择性查询（匹配文档少），倒排索引提供 O(matched_docs) 遍历——显著快于 rank-bm25 的 O(N) 全量扫描。对于宽泛查询（匹配大量文档），numpy 后端库（bm25s、rank-bm25）凭借向量化数组运算更快。
- **小语料规模（< 1K 文档）下，三者均为亚毫秒级**——对于搜索结果重排或 RAG 检索等典型场景，性能差异可忽略。
- **bm25s 在大语料宽泛查询场景扩展性最好**，得益于稀疏矩阵运算，搜索耗时随语料规模增长缓慢。
- **索引速度**：zerodep 和 bm25s 相当；rank-bm25 最快（数据结构更简单）。
- **排名正确性** 已通过与 rank-bm25 的 BM25Okapi、BM25Plus、BM25L 三个变体各 8 组查询的排名顺序对比验证。
- zerodep **零 pip 依赖**，并提供 rank-bm25 和 bm25s 不具备的功能：BM25F 多字段搜索、动态增删改、元数据过滤、RRF/MMR、Bayesian 校准。

## 自行运行

```bash
pip install pytest pytest-benchmark rank-bm25 bm25s
pytest sparse_search/test_sparse_search_benchmark.py --benchmark-only -v
```

---

## 最新 CI 结果

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/search.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> 每次发版时通过 [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml) 自动更新。
