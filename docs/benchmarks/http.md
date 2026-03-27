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

| Test | zerodep | httpx | Notes |
|------|---------|-------|-------|
| Sync GET | ~1,100 ms | ~398 ms | httpx benefits from connection pooling |
| Sync POST JSON | ~1,086 ms | ~1,060 ms | Comparable (network-bound) |
| Sync Client GET | ~1,099 ms | ~1,088 ms | Comparable with session |
| Async GET | ~1,228 ms | ~1,178 ms | Comparable |
| Async POST JSON | ~1,133 ms | ~1,152 ms | Comparable |

## Key Takeaways

- For **one-off requests**, httpx is noticeably faster due to connection pooling.
- With **sessions or async**, performance is essentially identical since both implementations become network-bound.
- zerodep has **zero pip dependencies** -- it uses only `http.client` (sync) and `asyncio` streams (async) from the standard library.

## Run It Yourself

```bash
pip install pytest pytest-benchmark httpx
pytest httpclient/test_http_benchmark.py --benchmark-only -v
```
