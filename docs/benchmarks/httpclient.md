# HTTP Client Benchmark

Apple-to-apple performance comparison between zerodep HTTP client and [`httpx`](https://pypi.org/project/httpx/) (with connection pooling).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)
    - **Reference:** httpx 0.28.1
    - **Last Updated:** 2026-04-21

## Implementations

| Implementation | File/Package | Description |
|----------------|--------------|-------------|
| **zerodep** | `httpclient.py` | stdlib-only HTTP/1.1 client |
| **httpx** | *(reference)* | Popular HTTP library with connection pooling |

## Performance Comparison (Mean)

### Basic Requests

| Test | zerodep | httpx | Speedup |
|------|---------|-------|---------|
| Sync GET | 613.9 us | 20,830.0 us | **33.9x faster** |
| Sync POST JSON | 709.6 us | 21,030.0 us | **29.6x faster** |
| Sync Client GET | 637.6 us | 1,020.0 us | **1.6x faster** |
| Async GET | 1,110.0 us | 27,530.0 us | **24.8x faster** |
| Async POST JSON | 1,220.0 us | 28,130.0 us | **23.1x faster** |
| Async Client GET | 1,160.0 us | 26,590.0 us | **22.9x faster** |

### Streaming

| Test | zerodep | httpx | Speedup |
|------|---------|-------|---------|
| Sync Streaming | 627.5 us | 20,990.0 us | **33.4x faster** |
| Async Streaming | 1,150.0 us | 26,780.0 us | **23.3x faster** |

### File Upload (multipart/form-data)

| Test | zerodep | httpx | Speedup |
|------|---------|-------|---------|
| Sync File Upload | 991.3 us | 21,610.0 us | **21.8x faster** |
| Async File Upload | 1,510.0 us | 28,020.0 us | **18.5x faster** |

### Content Decompression

| Test | zerodep | httpx | Speedup |
|------|---------|-------|---------|
| Sync Gzip GET | 646.2 us | 20,710.0 us | **32.1x faster** |

## Key Takeaways

- **19--34x faster on one-off requests** -- without connection pooling, zerodep is dramatically faster than httpx because it avoids httpx's heavy client initialization and middleware stack overhead.
- **~1.6x faster with connection pooling** -- even when both libraries reuse connections, zerodep's lighter abstraction layer still provides a measurable advantage.
- **Streaming is 23--33x faster** -- zerodep's minimal stream abstraction translates directly into throughput gains.
- **File upload is 19--22x faster** -- zerodep's simple multipart encoder outperforms httpx's more featureful implementation.
- **Benchmarks use a local server** -- all tests hit `localhost`, so the numbers reflect pure library overhead without network latency.
- zerodep has **zero pip dependencies** -- it uses only `http.client` (sync) and `asyncio` streams (async) from the standard library.

## Run It Yourself

```bash
pip install pytest pytest-benchmark httpx
pytest httpclient/test_http_benchmark.py --benchmark-only -v
```

---

## Latest CI Results

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/httpclient.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> Updated automatically on each release via [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml).
