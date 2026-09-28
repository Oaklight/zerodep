# Async SQLite Benchmark

Apple-to-apple performance comparison between zerodep aiosqlite and [`aiosqlite`](https://pypi.org/project/aiosqlite/).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)
    - **Reference:** aiosqlite 0.22.0
    - **Last Updated:** 2026-09-28

## Implementations

| Implementation | File/Package | Description |
|----------------|--------------|-------------|
| **zerodep** | `aiosqlite.py` | stdlib-only async sqlite3 wrapper |
| **aiosqlite** | *(reference)* | Popular async sqlite3 library |

## Tests Performed

| Test | Description |
|------|-------------|
| Single Insert+Select | Connect, CREATE, INSERT 1 row, SELECT, close |
| Bulk Insert | `executemany` with 1000 rows |
| Bulk Select | `execute_fetchall` over 1000 rows |
| Cursor Iteration | `async for` over 1000-row cursor |
| execute_insert | 100 sequential `execute_insert` calls |
| Large Row Insert | `executemany` with 500 rows × 4KB payload |
| Large Row Select | `execute_fetchall` over 500 rows × 4KB payload |
| Large Result Fetchall | `execute_fetchall` over 10K rows |
| Large Result Iteration | `async for` over 10K-row cursor |
| Concurrent Tasks | 8 coroutines, each inserting 50 rows + reading all |
| Mixed Read/Write | 200 interleaved inserts and selects |

## Run It Yourself

```bash
pip install pytest pytest-benchmark aiosqlite
pytest aiosqlite/test_aiosqlite_benchmark.py --benchmark-only -v
```

---

## Latest CI Results

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/aiosqlite.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> Updated automatically on each release via [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml).
