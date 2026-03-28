# HTTP Client Benchmark

Apple-to-apple performance comparison between zerodep HTTP client and [`httpx`](https://pypi.org/project/httpx/) (with connection pooling).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.10
    - **Tool:** pytest-benchmark (mean values reported)
    - **Target:** httpbin.org (network-bound tests)

## Implementations

| Implementation | File/Package | Description |
|----------------|--------------|-------------|
| **zerodep** | `httpclient.py` | stdlib-only HTTP/1.1 client |
| **httpx** | *(reference)* | Popular HTTP library with connection pooling |

## Performance Comparison (Mean)

### Basic Requests

| Test | zerodep | httpx | Notes |
|------|---------|-------|-------|
| Sync GET | ~1,288 ms | ~1,206 ms | Comparable (network-bound) |
| Sync POST JSON | ~1,436 ms | ~1,209 ms | Comparable (network-bound) |
| Sync Client GET | ~287 ms | ~264 ms | Both use connection pooling |
| Async GET | ~1,035 ms | ~1,334 ms | Comparable |
| Async POST JSON | ~1,312 ms | ~1,253 ms | Comparable |
| Async Client GET | ~1,593 ms | ~1,591 ms | Both use connection pooling |

### Streaming

| Test | zerodep | httpx | Notes |
|------|---------|-------|-------|
| Sync Streaming | ~1,378 ms | ~1,287 ms | Comparable |
| Async Streaming | ~1,129 ms | ~1,751 ms | zerodep faster |

### File Upload (multipart/form-data)

| Test | zerodep | httpx | Notes |
|------|---------|-------|-------|
| Sync File Upload | ~2,790 ms | ~2,063 ms | Comparable (network-bound) |
| Async File Upload | ~1,470 ms | ~1,643 ms | Comparable |

### Content Decompression

| Test | zerodep | httpx | Notes |
|------|---------|-------|-------|
| Sync Gzip GET | ~1,229 ms | ~1,720 ms | zerodep faster |

## Key Takeaways

- For **one-off requests**, both are comparable since performance is network-bound.
- With **session/connection pooling**, both libraries are comparable.
- **Streaming** performance is comparable or better for zerodep due to its minimal stream abstraction.
- **File upload** performance is comparable, with httpx having a slight edge.
- zerodep has **zero pip dependencies** -- it uses only `http.client` (sync) and `asyncio` streams (async) from the standard library.

## Run It Yourself

```bash
pip install pytest pytest-benchmark httpx
pytest httpclient/test_http_benchmark.py --benchmark-only -v
```
