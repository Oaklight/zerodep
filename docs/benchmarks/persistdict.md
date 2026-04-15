# Persistent Dictionary Benchmark

Performance comparison between zerodep persistdict (JSON and SQLite backends), stdlib [`shelve`](https://docs.python.org/3/library/shelve.html), and [`sqlitedict`](https://pypi.org/project/sqlitedict/).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)
    - **Reference:** sqlitedict 2.1.0
    - **Last Updated:** 2026-04-15

## Implementations

| Implementation | Backend | Description |
|----------------|---------|-------------|
| **zerodep (JSON)** | `persistdict.py` | JSON file backend, buffered writes, atomic flush |
| **zerodep (SQLite)** | `persistdict.py` | SQLite WAL backend, write-through |
| **shelve** | *(stdlib)* | dbm-backed persistent dict with pickle serialization |
| **sqlitedict** | *(reference)* | SQLite-backed dict with pickle serialization |

## Data Sizes

| Label | Items | Value Shape |
|-------|-------|-------------|
| Small | 50 | `{"index": int, "name": str}` |
| Large | 2,000 | `{"index": int, "name": str, "tags": [5 strings], "active": bool}` |

## Write Performance (Mean)

| Data Size | zerodep JSON | zerodep SQLite | shelve | sqlitedict |
|-----------|-------------|---------------|--------|------------|
| Small (50) | 307.4 μs | 1,279.4 μs | 1,446.4 μs | 13,415.6 μs |
| Large (2,000) | 12,236.1 μs | 36,017.8 μs | 47,169.7 μs | 526,946.9 μs |

### Write Speedup vs Competitors

| Data Size | vs shelve | vs sqlitedict |
|-----------|-----------|---------------|
| Small (JSON) | **4.7x faster** | **43.6x faster** |
| Small (SQLite) | **1.1x faster** | **10.5x faster** |
| Large (JSON) | **3.9x faster** | **43.1x faster** |
| Large (SQLite) | **1.3x faster** | **14.6x faster** |

## Read Performance — Small (50 items, Mean)

| Implementation | Time |
|----------------|------|
| zerodep JSON | 252.9 μs |
| zerodep SQLite | 532.3 μs |
| shelve | 1,006.2 μs |
| sqlitedict | 7,824.1 μs |

### Read Speedup

| vs | zerodep JSON | zerodep SQLite |
|----|-------------|---------------|
| shelve | **4.0x faster** | **1.9x faster** |
| sqlitedict | **30.9x faster** | **14.7x faster** |

## Iterate Performance — Small (50 items, Mean)

| Implementation | Time |
|----------------|------|
| zerodep JSON | 264.5 μs |
| zerodep SQLite | 591.7 μs |
| shelve | 1,032.6 μs |
| sqlitedict | 1,523.3 μs |

### Iterate Speedup

| vs | zerodep JSON | zerodep SQLite |
|----|-------------|---------------|
| shelve | **3.9x faster** | **1.7x faster** |
| sqlitedict | **5.8x faster** | **2.6x faster** |

## Key Takeaways

- **JSON backend is fastest overall** -- buffered writes + atomic flush makes it the best choice for small-to-medium datasets.
- **SQLite backend trades write speed for durability** -- write-through commits are slower than JSON's buffered approach, but each write is immediately persistent.
- **Both backends massively outperform sqlitedict** -- 10-43x faster writes, 15-31x faster reads. This is because sqlitedict uses pickle serialization and per-operation commit overhead.
- **Competitive with shelve, often faster** -- zerodep JSON is 3.9-4.7x faster than shelve for writes and 4.0x faster for reads. The SQLite backend is also 1.1-1.9x faster than shelve across operations.
- **No pickle** -- unlike shelve and sqlitedict, zerodep uses JSON serialization by default, avoiding deserialization vulnerabilities.

## Run It Yourself

```bash
pip install pytest pytest-benchmark sqlitedict
pytest persistdict/test_persistdict_benchmark.py --benchmark-only -v
```

---

## Latest CI Results

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/persistdict.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> Updated automatically on each release via [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml).
