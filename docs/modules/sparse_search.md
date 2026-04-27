# Sparse Search

Zero-dependency full-text search engine with BM25 family and TF-IDF ranking -- stdlib only, Python 3.10+.

## Overview

The `sparse_search` module provides a single-file inverted-index search engine supporting BM25/BM25+/BM25L/BM25F and TF-IDF+Cosine similarity. Designed for LLM/Agent/RAG pipelines where you need fast keyword retrieval without pulling in heavy dependencies.

| File | Description | Dependencies |
|------|-------------|--------------|
| `sparse_search.py` | Pure Python implementation | None (stdlib only: `re`, `math`, `json`, `sqlite3`, `statistics`, `collections`, `dataclasses`) |

### Key Features

- **BM25 variants** -- classic BM25, BM25+ (lower-bound correction), BM25L (long-document fix), all composable
- **BM25F** -- multi-field weighted search (e.g. boost title over body)
- **TF-IDF + Cosine** -- vector-space model as an alternative ranking
- **Dynamic CRUD** -- add / remove / update documents at any time
- **Metadata filtering** -- attach arbitrary JSON metadata, filter at search time
- **Persistence** -- save/load in JSON or SQLite format
- **Pluggable tokenizer** -- default Unicode word splitter; plug in `jieba.lcut`, NLTK, etc.
- **Bayesian BM25 calibration** -- convert raw BM25 scores to calibrated [0,1] probabilities via sigmoid likelihood, composite prior, and Bayesian posterior
- **Inverted index** -- O(matched_docs) search, 34-132x faster than rank-bm25 at query time
- **RRF (Reciprocal Rank Fusion)** -- merge multiple ranked result lists (e.g. BM25 + dense vector) into a single fused ranking
- **MMR (Maximal Marginal Relevance)** -- re-rank results for diversity with user-provided similarity function

## How to Use in Your Project

Copy the single file into your project:

```bash
cp search/sparse_search.py your_project/
```

Then import:

```python
from sparse_search import SparseIndex
```

## Usage Examples

### Basic Search

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

### BM25+ (Lower-Bound Correction)

```python
# delta > 0 enables BM25+ correction (default delta=1.0)
index = SparseIndex(delta=1.0)
```

BM25+ prevents terms that appear in many documents from getting zero contribution.

### BM25L (Long Document Fix)

```python
index = SparseIndex(variant="bm25l")
```

BM25L adjusts length normalization to avoid over-penalizing long documents.

### BM25F (Multi-Field Search)

```python
index = SparseIndex(field_weights={"title": 3.0, "body": 1.0})

index.add("doc1", {"title": "Python Guide", "body": "Learn Python programming basics"})
index.add("doc2", {"title": "Cooking Tips", "body": "How to cook python snake meat"})

results = index.search("python")
# doc1 ranks higher because "python" appears in the boosted title field
```

### TF-IDF + Cosine Similarity

```python
index = SparseIndex(variant="tfidf")
index.add("doc1", "machine learning algorithms")
index.add("doc2", "deep learning neural networks")

results = index.search("learning algorithms")
```

### Composing Variants

All BM25 options compose freely:

```python
# BM25L + BM25F + BM25+ (delta)
index = SparseIndex(
    variant="bm25l",
    field_weights={"title": 2.0, "body": 1.0},
    delta=0.5,
)
```

### Bayesian BM25 Calibration

Convert raw BM25 scores to calibrated probabilities in [0, 1]:

```python
index = SparseIndex()
index.add("doc1", "the quick brown fox jumps over the lazy dog")
index.add("doc2", "the quick brown fox")
index.add("doc3", "the lazy dog sleeps all day long")

# Auto-estimate calibration parameters from corpus
index.calibrate()

results = index.search("quick fox")
for r in results:
    print(f"{r.doc_id}: {r.score:.4f}")  # scores are now in [0, 1]
```

You can also provide parameters manually or apply a base-rate correction:

```python
# Manual parameters
index.calibrate(alpha=1.5, beta=2.0)

# With base-rate correction (shifts probabilities toward the prior)
index.calibrate(alpha=1.5, beta=2.0, base_rate=0.05)
```

Calibrated scores are useful for:

- **Threshold filtering** -- reject results below a probability cutoff
- **Multi-signal fusion** -- combine with other scoring signals on a common scale
- **Cross-query comparison** -- probabilities are comparable across different queries

### Metadata and Filtering

```python
index = SparseIndex()
index.add("doc1", "Python web framework", metadata={"year": 2024, "lang": "en"})
index.add("doc2", "Django tutorial", metadata={"year": 2023, "lang": "en"})
index.add("doc3", "Flask guide", metadata={"year": 2024, "lang": "zh"})

# Exact match filter
results = index.search("python", filters={"year": 2024})

# Custom filter with callable
results = index.search("python", filters={"year": lambda y: y >= 2024})
```

### Custom Tokenizer

```python
import jieba

# Chinese text search with jieba
index = SparseIndex(tokenize=jieba.lcut)
index.add("doc1", "Python 编程语言入门教程")
results = index.search("编程语言")
```

### Document Management

```python
index = SparseIndex()
index.add("doc1", "original content")

# Update an existing document
index.update("doc1", "updated content", metadata={"version": 2})

# Remove a document
index.remove("doc1")

# Check membership
print("doc1" in index)       # False
print(len(index))            # 0
print(index.doc_count)       # 0
print(index.vocab_size)      # 0
```

### Persistence

```python
index = SparseIndex()
index.add("doc1", "hello world")

# Save as JSON (human-readable)
index.save("index.json")

# Save as SQLite (more efficient for large indices)
index.save("index.db")

# Load (auto-detects format)
loaded = SparseIndex.load("index.json")
loaded = SparseIndex.load("index.db")
```

### Reciprocal Rank Fusion (RRF)

Merge results from multiple retrieval systems (e.g. BM25 sparse + dense vector search) into a single ranked list:

```python
from sparse_search import SparseIndex, Result, rrf

# Sparse retrieval
index = SparseIndex()
index.add("d1", "quick brown fox")
index.add("d2", "lazy dog")
index.add("d3", "fast red car")
sparse_results = index.search("quick fox", top_k=20)

# Dense retrieval (from external system like FAISS, Chroma, etc.)
dense_results = [Result("d1", 0.92), Result("d3", 0.85), Result("d2", 0.71)]

# Fuse with RRF (default k=60, per Cormack et al.)
fused = rrf(sparse_results, dense_results, top_k=10)

# Weighted fusion (boost sparse results)
fused = rrf(sparse_results, dense_results, weights=[2.0, 1.0], top_k=10)
```

RRF works purely on rank positions, not raw scores, making it ideal for combining retrieval systems with incompatible score scales.

### Maximal Marginal Relevance (MMR)

Re-rank results for diversity -- useful when top results are too similar:

```python
from sparse_search import SparseIndex, mmr, jaccard_similarity

index = SparseIndex()
index.add("d1", "python web framework flask")
index.add("d2", "python web framework django")
index.add("d3", "machine learning with python")
index.add("d4", "python web development guide")

results = index.search("python web", top_k=10)

# Build a similarity function from document tokens
doc_tokens = {
    "d1": {"python", "web", "framework", "flask"},
    "d2": {"python", "web", "framework", "django"},
    "d3": {"machine", "learning", "with", "python"},
    "d4": {"python", "web", "development", "guide"},
}

def sim(a, b):
    return jaccard_similarity(doc_tokens[a.doc_id], doc_tokens[b.doc_id])

# Select top 3 diverse results (lambda_=0.7 favors relevance over diversity)
diverse = mmr(results, sim, lambda_=0.7, top_k=3)
```

The `lambda_` parameter controls the relevance-diversity trade-off:

- `lambda_=1.0` -- pure relevance (same as original ranking)
- `lambda_=0.5` -- balanced (default)
- `lambda_=0.0` -- pure diversity (most dissimilar items first)

## Design Notes

### Index vs Scoring Parameters

Only the `tokenize` function affects indexing. All other parameters (`variant`, `k1`, `b`, `delta`, `field_weights`) are scoring-time parameters that do not change what is stored in the index. This means the same index can be searched with different algorithms and tuning parameters without reindexing.

### `field_weights` is Immutable

`field_weights` is set at construction time and determines whether documents are stored as single-field or multi-field. The index does not store the original document text -- only tokenized term frequencies. This means:

- A single-field index **cannot** be converted to multi-field (the field boundaries are lost)
- To change `field_weights`, you must rebuild the index from your source data
- `update()` replaces a document's indexed data but still requires the original text

### Indexing vs Search Performance

The index uses a 3-level inverted index (`term -> doc_id -> field -> tf`) to support both single-field and multi-field (BM25F) modes uniformly. This adds overhead during indexing (~6.7x slower than rank-bm25) but enables 34-132x faster search thanks to O(matched_docs) query traversal. Since indexing is typically a one-time cost and search is the frequent operation, this trade-off favors real-world usage patterns.

Insert time is **O(tokens_in_doc)** per document and does not degrade as the index grows -- the 1st document and the 100,000th document with the same token count take the same time, since all underlying operations (dict lookup, set add) are O(1) amortized.

## API Reference

### `SparseIndex(variant, k1, b, delta, field_weights, tokenize, calibrated)`

The main search index class.

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `variant` | `str` | `"bm25"` | Ranking algorithm: `"bm25"`, `"bm25l"`, or `"tfidf"` |
| `k1` | `float` | `1.5` | BM25 term-frequency saturation (ignored for tfidf) |
| `b` | `float` | `0.75` | BM25 length normalization factor (ignored for tfidf) |
| `delta` | `float` | `1.0` | BM25+ lower-bound correction. `0` for classic BM25 |
| `field_weights` | `dict[str, float] \| None` | `None` | Per-field boost weights for BM25F |
| `tokenize` | `Callable[[str], list[str]] \| None` | `None` | Custom tokenizer. Defaults to Unicode word split + lowercase |
| `calibrated` | `bool` | `False` | If `True`, BM25 scores are converted to calibrated probabilities via Bayesian BM25 |

**Methods:**

| Method | Description |
|--------|-------------|
| `add(doc_id, content, metadata=None)` | Add a new document. Raises `ValueError` if `doc_id` exists. |
| `remove(doc_id)` | Remove a document. Raises `KeyError` if not found. |
| `update(doc_id, content, metadata=None)` | Replace a document. Raises `KeyError` if not found. |
| `search(query, top_k=10, filters=None)` | Search and return ranked results. |
| `calibrate(*, alpha=None, beta=None, base_rate=None, n_samples=50)` | Estimate or set Bayesian calibration parameters. Enables calibrated mode. |
| `save(path, format=None)` | Save index to disk (JSON or SQLite). |
| `load(path)` | *(classmethod)* Load index from disk (auto-detects format). |

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `doc_count` | `int` | Number of documents in the index |
| `vocab_size` | `int` | Number of unique terms |

---

### `Result`

Dataclass representing a single search result.

| Field | Type | Description |
|-------|------|-------------|
| `doc_id` | `str` | Document identifier |
| `score` | `float` | Relevance score |
| `metadata` | `dict[str, Any] \| None` | Document metadata |

---

### Default Tokenizer

The built-in tokenizer splits on Unicode word boundaries and lowercases all tokens:

```python
"Hello, World! 42" -> ["hello", "world", "42"]
```

For production use, consider passing a custom tokenizer with stemming, stop-word removal, or CJK segmentation.

---

### `rrf(*result_lists, k=60, top_k=None, weights=None)`

Reciprocal Rank Fusion -- merge multiple ranked result lists into one.

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `*result_lists` | `list[Result]` | *(required)* | One or more ranked result lists |
| `k` | `int` | `60` | RRF constant controlling rank sensitivity |
| `top_k` | `int \| None` | `None` | Max results to return. `None` returns all |
| `weights` | `list[float] \| None` | `None` | Per-list weights. `None` = equal weights |

**Returns:** `list[Result]` sorted by descending RRF score. Metadata from the highest-scoring original occurrence is preserved.

---

### `mmr(results, similarity_fn, *, lambda_=0.5, top_k=None)`

Maximal Marginal Relevance -- re-rank results for diversity.

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `results` | `list[Result]` | *(required)* | Candidate results to re-rank |
| `similarity_fn` | `Callable[[Result, Result], float]` | *(required)* | Similarity function returning [0, 1] |
| `lambda_` | `float` | `0.5` | Trade-off: 1.0 = pure relevance, 0.0 = pure diversity |
| `top_k` | `int \| None` | `None` | Number of results to select. `None` = all |

**Returns:** `list[Result]` with scores set to MMR values.

---

### `jaccard_similarity(set_a, set_b)`

Jaccard similarity coefficient: `|A ∩ B| / |A ∪ B|`. Returns 0.0 when both sets are empty.

## Comparison with rank-bm25

| Feature | zerodep sparse_search | rank-bm25 |
|---------|----------------------|-----------|
| Dependencies | None (stdlib only) | numpy |
| BM25 variants | BM25/BM25+/BM25L/BM25F/TF-IDF | BM25Okapi/BM25Plus/BM25L |
| Multi-field (BM25F) | Yes | No |
| Search complexity | O(matched_docs) | O(N) full corpus scan |
| Dynamic add/remove | Yes | No (rebuild required) |
| Metadata filtering | Yes | No |
| Persistence | JSON + SQLite | No |
| Custom tokenizer | Yes | Yes |
| Search speed (1000 docs) | **132x faster** | baseline |
| Indexing speed (1000 docs) | 6.7x slower | baseline |

**When to use zerodep:** You need dynamic document management, multi-field search, metadata filtering, or zero-dependency deployment.

**When to use rank-bm25:** You only need static BM25 scoring with numpy already in your stack.

## Benchmark

Performance comparison against rank-bm25, tested with pytest-benchmark.

See [Sparse Search Benchmark](../benchmarks/sparse_search.md) for detailed results.
