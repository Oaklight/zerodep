# HTTP Client Benchmark

Apple-to-apple performance comparison between zerodep HTTP client and [`httpx`](https://pypi.org/project/httpx/) (with connection pooling).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)
    - **Reference:** httpx 0.28.1
    - **Last Updated:** 2026-04-15

## Implementations

| Implementation | File/Package | Description |
|----------------|--------------|-------------|
| **zerodep** | `httpclient.py` | stdlib-only HTTP/1.1 client |
| **httpx** | *(reference)* | Popular HTTP library with connection pooling |

## Performance Comparison (Mean)

### Basic Requests

| Test | zerodep | httpx | Speedup |
|------|---------|-------|---------|
| Sync GET | 729.7 us | 11,970.0 us | **16.4x faster** |
| Sync POST JSON | 871.4 us | 12,279.4 us | **14.1x faster** |
| Sync Client GET | 808.4 us | 1,541.4 us | **1.9x faster** |
| Async GET | 1,328.2 us | 19,339.9 us | **14.6x faster** |
| Async POST JSON | 1,583.1 us | 19,356.7 us | **12.2x faster** |
| Async Client GET | 1,434.9 us | 20,134.9 us | **14.0x faster** |

### Streaming

| Test | zerodep | httpx | Speedup |
|------|---------|-------|---------|
| Sync Streaming | 725.4 us | 12,059.9 us | **16.6x faster** |
| Async Streaming | 1,432.7 us | 20,228.3 us | **14.1x faster** |

### File Upload (multipart/form-data)

| Test | zerodep | httpx | Speedup |
|------|---------|-------|---------|
| Sync File Upload | 1,472.0 us | 14,130.2 us | **9.6x faster** |
| Async File Upload | 1,904.0 us | 22,040.0 us | **11.6x faster** |

### Content Decompression

| Test | zerodep | httpx | Speedup |
|------|---------|-------|---------|
| Sync Gzip GET | 846.6 us | 12,454.8 us | **14.7x faster** |

## Key Takeaways

- **10--17x faster on one-off requests** -- without connection pooling, zerodep is dramatically faster than httpx because it avoids httpx's heavy client initialization and middleware stack overhead.
- **~2x faster with connection pooling** -- even when both libraries reuse connections, zerodep's lighter abstraction layer still provides a measurable advantage.
- **Streaming is 14--17x faster** -- zerodep's minimal stream abstraction translates directly into throughput gains.
- **File upload is 10--12x faster** -- zerodep's simple multipart encoder outperforms httpx's more featureful implementation.
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
