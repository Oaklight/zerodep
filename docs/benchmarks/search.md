# Sparse Search Benchmark

Apple-to-apple performance comparison between zerodep sparse_search and [`rank-bm25`](https://pypi.org/project/rank-bm25/).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.10
    - **Tool:** pytest-benchmark (mean values reported)

## Implementations

| Implementation | File/Package | Description |
|----------------|--------------|-------------|
| **zerodep** | `sparse_search.py` | stdlib-only BM25/TF-IDF engine with inverted index |
| **rank-bm25** | *(reference)* | Popular BM25 library backed by numpy |

## Performance Comparison (Mean)

### Search Speed

| Corpus Size | zerodep | rank-bm25 | Speedup |
|-------------|---------|-----------|---------|
| 200 docs | 1.79 us | 61.69 us | **34x faster** |
| 1000 docs | 1.80 us | 237.30 us | **132x faster** |

### Indexing Speed

| Corpus Size | zerodep | rank-bm25 | Ratio |
|-------------|---------|-----------|-------|
| 1000 docs | 56.6 ms | 8.4 ms | 6.7x slower |

## Key Takeaways

- **Search is 34-132x faster** thanks to an inverted index that traverses only matching postings O(matched_docs), vs rank-bm25's full corpus scan O(N). The advantage grows with corpus size.
- **Indexing is slower** due to richer data structures (reverse index for fast deletes, metadata storage, persistence support). This is a one-time cost vs repeated search savings.
- **Ranking correctness** is validated against rank-bm25 across BM25Okapi, BM25Plus, and BM25L variants with 8 queries -- results match in ranking order.
- zerodep has **zero pip dependencies** and supports dynamic add/remove/update without rebuilding the index.

## Run It Yourself

```bash
pip install pytest pytest-benchmark rank-bm25
pytest search/test_sparse_search_benchmark.py --benchmark-only -v
```
