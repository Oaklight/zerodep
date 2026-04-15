# Sparse Search Benchmark

Apple-to-apple performance comparison between zerodep sparse_search and [`rank-bm25`](https://pypi.org/project/rank-bm25/).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)
    - **Reference:** rank-bm25 0.2.2
    - **Last Updated:** 2026-04-15

## Implementations

| Implementation | File/Package | Description |
|----------------|--------------|-------------|
| **zerodep** | `sparse_search.py` | stdlib-only BM25/TF-IDF engine with inverted index |
| **rank-bm25** | *(reference)* | Popular BM25 library backed by numpy |

## Performance Comparison (Mean)

### Search Speed

| Corpus Size | zerodep | rank-bm25 | Speedup |
|-------------|---------|-----------|---------|
| 200 docs | 2.3 μs | 113.2 μs | **50x faster** |
| 1000 docs | 2.3 μs | 386.1 μs | **171x faster** |

### Indexing Speed

| Corpus Size | zerodep | rank-bm25 | Ratio |
|-------------|---------|-----------|-------|
| 1000 docs | 136.1 ms | 12.7 ms | 10.8x slower |

### Bayesian Calibration Overhead

| Operation | Time | vs Raw Search |
|-----------|------|---------------|
| Raw BM25 search | 33.9 μs | baseline |
| Calibrated BM25 search | 65.0 μs | ~1.9x overhead |
| `calibrate()` (20 docs) | 969.3 μs | one-time cost |

## Key Takeaways

- **Search is 50-171x faster** thanks to an inverted index that traverses only matching postings O(matched_docs), vs rank-bm25's full corpus scan O(N). The advantage grows with corpus size.
- **Indexing is ~11x slower** due to richer data structures (reverse index for fast deletes, metadata storage, persistence support). This is a one-time cost vs repeated search savings.
- **Ranking correctness** is validated against rank-bm25 across BM25Okapi, BM25Plus, and BM25L variants with 8 queries -- results match in ranking order.
- zerodep has **zero pip dependencies** and supports dynamic add/remove/update without rebuilding the index.
- **Bayesian calibration** adds ~1.9x overhead per search (still faster than rank-bm25). `calibrate()` is a one-time cost (~969 μs for 20 docs).

## Run It Yourself

```bash
pip install pytest pytest-benchmark rank-bm25
pytest search/test_sparse_search_benchmark.py --benchmark-only -v
```

---

## Latest CI Results

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/search.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> Updated automatically on each release via [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml).
