# SSE Client Benchmark

Apple-to-apple parsing performance comparison between zerodep SSE and [`httpx-sse`](https://pypi.org/project/httpx-sse/).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.10.20
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)

## Implementations

| Implementation | File/Package | Description |
|----------------|--------------|-------------|
| **zerodep** | `sse.py` | Single-file SSE parser + client, stdlib only |
| **httpx-sse** | *(reference)* | SSE extension for httpx |

## What Is Benchmarked

Both libraries implement the same W3C SSE line-parsing algorithm. The benchmark feeds identical pre-built line arrays to each parser and measures pure parsing throughput -- no network I/O involved.

## Data Sizes Tested

| Label | Events | Data lines/event | Chars/line | Description |
|-------|--------|-------------------|------------|-------------|
| Small | 10 | 1 | 20 | Simple notification stream |
| Medium | 100 | 3 | 50 | Typical LLM token stream |
| Large | 1,000 | 1 | 200 | Bulk data stream |

## Parsing Performance (Mean)

| Data Size | zerodep | httpx-sse | Ratio |
|-----------|---------|-----------|-------|
| Small | 14.9 us | 13.2 us | ~1.13x slower |
| Medium | 200.9 us | 186.9 us | ~1.07x slower |
| Large | 1,526.4 us | 1,379.9 us | ~1.11x slower |

## Key Takeaways

- **Parsing performance is nearly identical** -- both libraries implement the same W3C SSE parsing algorithm, so the ~10% difference is expected noise from implementation details.
- **Throughput is excellent for both** -- parsing 1,000 events with 200-char payloads takes ~1.5 ms, meaning parsing is never the bottleneck in real SSE workloads (network latency dominates).
- **zerodep provides more functionality** -- unlike httpx-sse (which is an httpx extension), zerodep SSE includes a standalone parser (no HTTP dependency), auto-reconnection, sync+async clients, and Last-Event-ID tracking.
- **Zero pip dependencies** -- zerodep uses only `dataclasses`, `asyncio`, `time`, and `os` from the standard library (plus the optional sibling `httpclient` module for the high-level client).

## Run It Yourself

```bash
pip install pytest pytest-benchmark httpx-sse httpx
pytest sse/test_sse_benchmark.py --benchmark-only -v
```

---

## Latest CI Results

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/sse.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> Updated automatically on each release via [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml).
