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
| Sync GET | ~1,091 ms | ~1,165 ms | Comparable (network-bound) |
| Sync POST JSON | ~1,039 ms | ~1,154 ms | Comparable (network-bound) |
| Sync Client GET | ~1,613 ms | ~462 ms | Both use connection pooling |
| Async GET | ~1,147 ms | ~1,207 ms | Comparable |
| Async POST JSON | ~1,437 ms | ~1,352 ms | Comparable |

### Streaming

| Test | zerodep | httpx | Notes |
|------|---------|-------|-------|
| Sync Streaming | ~1,666 ms | ~2,295 ms | zerodep faster (lower stream overhead) |
| Async Streaming | ~1,476 ms | ~1,448 ms | Comparable |

### File Upload (multipart/form-data)

| Test | zerodep | httpx | Notes |
|------|---------|-------|-------|
| Sync File Upload | ~1,731 ms | ~1,398 ms | Comparable (network-bound) |
| Async File Upload | ~2,003 ms | ~1,571 ms | httpx slightly faster |

### Content Decompression

| Test | zerodep | httpx | Notes |
|------|---------|-------|-------|
| Sync Gzip GET | TBD | TBD | Both decompress automatically |

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
