# Persistent Dictionary Benchmark

Performance comparison between zerodep persistdict (JSON and SQLite backends), stdlib [`shelve`](https://docs.python.org/3/library/shelve.html), and [`sqlitedict`](https://pypi.org/project/sqlitedict/).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.10.20
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)

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
| Small (50) | 210.3 μs | 675.6 μs | 644.3 μs | 14,849.8 μs |
| Large (2,000) | 12,825.1 μs | 20,957.7 μs | 26,082.2 μs | 685,824.9 μs |

### Write Speedup vs Competitors

| Data Size | vs shelve | vs sqlitedict |
|-----------|-----------|---------------|
| Small (JSON) | **3.1x faster** | **70.6x faster** |
| Large (JSON) | **2.0x faster** | **53.5x faster** |
| Large (SQLite) | **1.2x faster** | **32.7x faster** |

## Read Performance — Small (50 items, Mean)

| Implementation | Time |
|----------------|------|
| zerodep JSON | 302.7 μs |
| zerodep SQLite | 347.9 μs |
| shelve | 521.7 μs |
| sqlitedict | 9,785.8 μs |

### Read Speedup

| vs | zerodep JSON | zerodep SQLite |
|----|-------------|---------------|
| shelve | **1.7x faster** | **1.5x faster** |
| sqlitedict | **32.3x faster** | **28.1x faster** |

## Iterate Performance — Small (50 items, Mean)

| Implementation | Time |
|----------------|------|
| zerodep JSON | 308.7 μs |
| zerodep SQLite | 370.7 μs |
| shelve | 534.5 μs |
| sqlitedict | 1,841.4 μs |

### Iterate Speedup

| vs | zerodep JSON | zerodep SQLite |
|----|-------------|---------------|
| shelve | **1.7x faster** | **1.4x faster** |
| sqlitedict | **6.0x faster** | **5.0x faster** |

## Key Takeaways

- **JSON backend is fastest overall** -- buffered writes + atomic flush makes it the best choice for small-to-medium datasets.
- **SQLite backend trades write speed for durability** -- write-through commits are slower than JSON's buffered approach, but each write is immediately persistent.
- **Both backends massively outperform sqlitedict** -- 30-70x faster writes, 28-32x faster reads. This is because sqlitedict uses pickle serialization and per-operation commit overhead.
- **Competitive with shelve, often faster** -- zerodep JSON is 1.7-3.1x faster than shelve across all operations, with the added benefit of human-readable storage and no pickle vulnerabilities.
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
