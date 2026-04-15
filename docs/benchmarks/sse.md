# SSE Client Benchmark

Apple-to-apple parsing performance comparison between zerodep SSE and [`httpx-sse`](https://pypi.org/project/httpx-sse/).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)
    - **Reference:** httpx-sse 0.4.3
    - **Last Updated:** 2026-04-15

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
| Small | 22.0 us | 17.0 us | ~1.3x slower |
| Medium | 300.3 us | 240.9 us | ~1.2x slower |
| Large | 2,153.1 us | 1,813.2 us | ~1.2x slower |

## Key Takeaways

- **zerodep is ~20-30% slower** -- both libraries implement the same W3C SSE parsing algorithm. The difference comes from zerodep's additional per-event processing (field normalization, event type dispatch) compared to httpx-sse's minimal parser.
- **Throughput is excellent for both** -- parsing 1,000 events with 200-char payloads takes ~2.2 ms, meaning parsing is never the bottleneck in real SSE workloads (network latency dominates).
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
