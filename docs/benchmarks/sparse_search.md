# Sparse Search Benchmark

Performance comparison between zerodep sparse_search, [`rank-bm25`](https://pypi.org/project/rank-bm25/), and [`bm25s`](https://github.com/xhluca/bm25s).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)
    - **References:** rank-bm25 0.2.2, bm25s 0.3.8
    - **Last Updated:** 2026-04-29

## Implementations

| Implementation | File/Package | Description |
|----------------|--------------|-------------|
| **zerodep** | `sparse_search.py` | stdlib-only BM25/TF-IDF engine with inverted index |
| **rank-bm25** | *(reference)* | Popular BM25 library backed by numpy |
| **bm25s** | *(reference)* | Fast BM25 library with eager sparse scoring (numpy + scipy) |

## Performance Comparison (Mean)

### Selective Queries (synthetic corpus, rare terms)

Queries matching few documents — the inverted index's O(matched_docs) advantage is strongest here.

| Corpus Size | zerodep | rank-bm25 | bm25s |
|-------------|---------|-----------|-------|
| 200 docs | 3.2 μs | 88.6 μs | 16.8 μs |
| 1000 docs | 1.8 μs | 239.6 μs | 15.2 μs |

### Broad Queries (Zipf-distributed corpus, common terms)

Queries using high-frequency words that match most documents — numpy vectorization dominates.

| Corpus Size | zerodep | rank-bm25 | bm25s |
|-------------|---------|-----------|-------|
| 1K docs | 2.48 ms | 221.9 μs | 43.6 μs |
| 10K docs | 56.2 ms | 2.72 ms | 59.9 μs |

### Selective Queries (Zipf-distributed corpus, rare terms)

Queries using rare words on a realistic vocabulary distribution.

| Corpus Size | zerodep | rank-bm25 | bm25s |
|-------------|---------|-----------|-------|
| 1K docs | 19.0 μs | 193.9 μs | 54.3 μs |
| 10K docs | 87.0 μs | 2.74 ms | 185.5 μs |

### Indexing Speed

| Corpus Size | zerodep | rank-bm25 | bm25s |
|-------------|---------|-----------|-------|
| 1000 docs | 41.7 ms | 8.8 ms | 41.1 ms |

### Bayesian Calibration Overhead

| Operation | Time | vs Raw Search |
|-----------|------|---------------|
| Raw BM25 search | 22.8 μs | baseline |
| Calibrated BM25 search | 43.4 μs | ~1.9x overhead |
| `calibrate()` (20 docs) | 662.0 μs | one-time cost |

## Key Takeaways

- **Search performance depends on query selectivity.** For selective queries (few matching documents), the inverted index provides O(matched_docs) traversal — significantly faster than the O(N) full corpus scan used by rank-bm25. For broad queries matching most documents, numpy-backed libraries (bm25s, rank-bm25) are faster due to vectorized array operations.
- **At small corpus sizes (< 1K docs), all implementations are sub-millisecond** — performance differences are negligible for typical use cases like search result reranking or RAG retrieval.
- **bm25s scales best for large corpora with broad queries** thanks to sparse matrix operations. Its search time grows slowly with corpus size.
- **Indexing speed** is comparable between zerodep and bm25s; rank-bm25 is fastest due to simpler data structures.
- **Ranking correctness** is validated against rank-bm25 across BM25Okapi, BM25Plus, and BM25L variants with 8 queries — results match in ranking order.
- zerodep has **zero pip dependencies** and provides features not available in rank-bm25 or bm25s: BM25F multi-field search, dynamic add/remove/update, metadata filtering, RRF/MMR, and Bayesian calibration.

## Run It Yourself

```bash
pip install pytest pytest-benchmark rank-bm25 bm25s
pytest sparse_search/test_sparse_search_benchmark.py --benchmark-only -v
```

---

## Latest CI Results

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/search.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> Updated automatically on each release via [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml).
