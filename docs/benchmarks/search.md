# 稀疏搜索性能测试

zerodep sparse_search 与 [`rank-bm25`](https://pypi.org/project/rank-bm25/) 的性能对比。

!!! info "测试环境"
    - **CPU:** x86_64 Linux
    - **Python:** 3.10
    - **工具:** pytest-benchmark（报告均值）

## 实现

| 实现 | 文件/包 | 说明 |
|------|---------|------|
| **zerodep** | `sparse_search.py` | 仅标准库的 BM25/TF-IDF 搜索引擎（倒排索引） |
| **rank-bm25** | *(对照)* | 基于 numpy 的流行 BM25 库 |

## 性能对比（均值）

### 搜索速度

| 语料规模 | zerodep | rank-bm25 | 加速比 |
|----------|---------|-----------|--------|
| 200 文档 | 1.79 us | 61.69 us | **34 倍更快** |
| 1000 文档 | 1.80 us | 237.30 us | **132 倍更快** |

### 索引速度

| 语料规模 | zerodep | rank-bm25 | 倍率 |
|----------|---------|-----------|------|
| 1000 文档 | 56.6 ms | 8.4 ms | 6.7 倍更慢 |

### Bayesian 校准开销

| 操作 | 耗时 | 对比原始搜索 |
|------|------|-------------|
| 原始 BM25 搜索 | 16.8 us | 基准 |
| 校准 BM25 搜索 | 42.0 us | ~2.5 倍开销 |
| `calibrate()`（20 文档） | 565 us | 一次性成本 |

## 主要结论

- **搜索快 34-132 倍**，归功于倒排索引仅遍历匹配的 posting O(matched_docs)，而 rank-bm25 每次查询扫描全量语料 O(N)。优势随语料规模增长。
- **索引较慢**，因为使用了更丰富的数据结构（反向索引支持快速删除、元数据存储、持久化支持）。这是一次性成本，换取搜索时的持续收益。
- **排名正确性** 已通过与 rank-bm25 的 BM25Okapi、BM25Plus、BM25L 三个变体各 8 组查询的排名顺序对比验证。
- zerodep **零 pip 依赖**，支持动态增删改文档，无需重建索引。
- **Bayesian 校准**每次搜索增加约 2.5 倍开销（仍快于 rank-bm25）。`calibrate()` 为一次性成本（20 文档约 565 us）。

## 自行运行

```bash
pip install pytest pytest-benchmark rank-bm25
pytest search/test_sparse_search_benchmark.py --benchmark-only -v
```

---

## 最新 CI 结果

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/search.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> 每次发版时通过 [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml) 自动更新。
