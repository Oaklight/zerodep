# Persistent Dictionary Benchmark

Performance comparison between zerodep persistdict (JSON and SQLite backends), stdlib [`shelve`](https://docs.python.org/3/library/shelve.html), and [`sqlitedict`](https://pypi.org/project/sqlitedict/).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)
    - **Reference:** sqlitedict 2.1.0
    - **Last Updated:** 2026-04-21

## Implementations

| Implementation | Backend | Description |
|----------------|---------|-------------|
| **zerodep (JSON)** | `persistdict.py` | JSON file backend, buffered writes, atomic flush |
| **zerodep (SQLite)** | `persistdict.py` | SQLite WAL backend, deferred commits with `PRAGMA synchronous=NORMAL` |
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
| Small (50) | 422.7 μs | 2,970.0 μs | 449.1 μs | -- |
| Large (2,000) | 16,110.0 μs | 24,510.0 μs | 12,450.0 μs | -- |

### Write Comparison vs shelve

| Data Size | zerodep JSON vs shelve | zerodep SQLite vs shelve |
|-----------|------------------------|--------------------------|
| Small | ~same | 6.6x slower |
| Large | 1.3x slower | 2.0x slower |

## Read Performance — Small (50 items, Mean)

| Implementation | Time |
|----------------|------|
| zerodep JSON | 403.6 μs |
| zerodep SQLite | 811.2 μs |
| shelve | 184.5 μs |

### Read Comparison vs shelve

| zerodep JSON | zerodep SQLite |
|-------------|---------------|
| 2.2x slower | 4.4x slower |

## Iterate Performance — Small (50 items, Mean)

| Implementation | Time |
|----------------|------|
| zerodep JSON | 427.4 μs |
| zerodep SQLite | 847.1 μs |
| shelve | 204.0 μs |

### Iterate Comparison vs shelve

| zerodep JSON | zerodep SQLite |
|-------------|---------------|
| 2.1x slower | 4.2x slower |

## Key Takeaways

- **JSON backend is competitive for small writes** -- for 50-item datasets, zerodep JSON write performance is on par with shelve (~same speed).
- **SQLite backend trades speed for durability** -- deferred commits with `PRAGMA synchronous=NORMAL` balance durability and performance. Batch writes via `commit_every` parameter further reduce per-write overhead, but shelve's dbm backend remains faster for raw throughput.
- **shelve is faster for reads and iteration** -- shelve's dbm-based key-value lookup is 2-4x faster than zerodep for read and iterate operations on small datasets.
- **No pickle** -- unlike shelve, zerodep uses JSON serialization by default, avoiding deserialization vulnerabilities. This is the primary advantage when security matters.
- **Portability and transparency** -- zerodep's JSON backend produces human-readable files, and the SQLite backend uses a standard database format, both of which are more portable and inspectable than dbm files.

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
