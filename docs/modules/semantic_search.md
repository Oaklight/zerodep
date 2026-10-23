# Semantic Search

Zero-dependency dense vector search with Flat, IVF and LSH indexes -- stdlib only, Python 3.10+.

> **Replaces:** `faiss-cpu`, `hnswlib`, `chromadb` (for small and medium collections)

## Overview

The `semantic_search` module stores embedding vectors and answers nearest-neighbour queries without pulling in numpy or a vector database. It ships with three index types, three distance metrics, optional SQ8 quantization, JSON/SQLite persistence, and reranking helpers for hybrid retrieval.

| File | Description | Dependencies |
|------|-------------|--------------|
| `semantic_search.py` | Pure Python implementation | None (stdlib only: `array`, `base64`, `dataclasses`, `heapq`, `json`, `math`, `pathlib`, `random`, `sqlite3`, `urllib`, `typing`) |

### Key Features

- **Three index types** -- `flat` (exact brute force), `ivf` (k-means inverted lists), `lsh` (random-projection hash tables)
- **Three metrics** -- `cosine`, `euclidean`, `inner_product`
- **Text or vector queries** -- pass an embedding function once and search by text
- **Embedding helpers** -- OpenAI, Cohere, Voyage and Jina adapters built in
- **Metadata filters** -- attach arbitrary JSON metadata, filter at search time
- **SQ8 quantization** -- 4x smaller storage; search distances are computed from the quantized data after `build_index()`
- **Persistence** -- save/load in JSON or SQLite format
- **Reranking utilities** -- `rrf()` (Reciprocal Rank Fusion) and `mmr()` (Maximal Marginal Relevance)

## How to Use in Your Project

Copy the single file into your project:

```bash
cp semantic_search/semantic_search.py your_project/
```

Then import:

```python
from semantic_search import SemanticIndex
```

## Usage Examples

### Basic Search

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

### Text Queries and Embedding Helpers

```python
from semantic_search import SemanticIndex, openai_embed

embed = openai_embed(api_key="sk-...", model="text-embedding-3-small")
index = SemanticIndex(dim=1536, embed=embed)

index.add("intro", text="ToolRegistry unifies tool calling")
index.add("guide", text="Register tools from Python functions")

results = index.search(text="how do I register a tool?", top_k=5)
```

`cohere_embed()`, `voyage_embed()` and `jina_embed()` follow the same shape; any
callable with the signature `list[str] -> list[list[float]]` works as `embed=`.

### Metadata Filters

```python
index.add("a", vector=[1.0, 0.0], metadata={"year": 2023, "lang": "en"})
index.add("b", vector=[0.9, 0.1], metadata={"year": 2025, "lang": "en"})

# Exact matches and callables are both allowed
results = index.search(vector=[1.0, 0.0], filters={"year": lambda y: y > 2024})
```

With filters, `search()` asks the index for up to four times `top_k` candidates
before filtering, so a few rejected results do not shrink the answer. On IVF and
LSH, documents in unprobed clusters or buckets are never candidates; the
docstring says so.

### Approximate Indexes

```python
index = SemanticIndex(dim=768, index_type="ivf", n_clusters=64, nprobe=4)
# ... add documents ...
index.build_index()          # required before searching IVF/LSH

index = SemanticIndex(dim=768, index_type="lsh", n_tables=8, n_hash_funcs=12)
```

`search()` builds a dirty IVF or LSH index on demand; a flat index never needs a
build unless quantization is enabled.

### Quantization

```python
index = SemanticIndex(dim=768, index_type="flat", quantize=True)
# ... add documents ...
index.build_index()
```

`build_index()` compresses each coordinate to one byte (SQ8) and releases the
float32 array, so the index holds roughly a quarter of the memory. Searches then
reconstruct distances from the quantized data -- expect a small recall loss
(around 1%). `add()`, `update()` and `remove()` reconstruct the float array
first, and the next `build_index()` re-quantizes it.

### Persistence

```python
index.save("vectors.json")
index.save("vectors.db")            # SQLite, chosen by extension

loaded = SemanticIndex.load("vectors.db")
loaded.search(vector=query, top_k=5)
```

A quantized index stores only the SQ8 payload: JSON leaves `vectors_b64` empty
and SQLite writes no `vectors` rows.

### Hybrid Retrieval

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

## API Reference

See the [API reference](../api/semantic_search.md) for the full class and
function list.
