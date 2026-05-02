# HTTP Server Benchmark

End-to-end serving performance comparison between zerodep httpserver, [Flask](https://pypi.org/project/Flask/), [microdot](https://pypi.org/project/microdot/), and [bottle](https://pypi.org/project/bottle/).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)
    - **Reference:** Flask 3.1.3, microdot 2.6.1, bottle 0.13.4
    - **Last Updated:** 2026-05-02

## Implementations

| Implementation | Type | Description |
|----------------|------|-------------|
| **zerodep** | async (`asyncio`) | Single-file HTTP server, stdlib only |
| **Flask** | sync (WSGI) | Full-featured web framework (werkzeug) |
| **microdot** | async (`asyncio`) | Minimal Flask-like async framework |
| **bottle** | sync (WSGI) | Single-file WSGI framework (wsgiref) |

## What Is Benchmarked

Each framework starts an HTTP server in a background thread. Benchmarks measure full request-response round-trip latency using the zerodep `httpclient` module.

## Benchmark Scenarios

| Scenario | Description | Client |
|----------|-------------|--------|
| Serial GET JSON | Single GET returning `{"pong": true}` | Sync `get()` |
| Serial POST JSON | Single POST echoing a small JSON payload | Sync `post()` |
| Serial GET Text | Single GET returning `"Hello, World!"` | Sync `get()` |
| Sync vs Async Handler | Compare `async def` vs `def` (zerodep only) | Sync `get()` |
| Concurrent GET (x10) | 10 simultaneous GET requests | `asyncio.gather` + `async_get()` |
| Concurrent POST (x10) | 10 simultaneous POST requests with JSON | `asyncio.gather` + `async_post()` |
| Large Payload POST | POST with ~30KB JSON body | Sync `post()` |

## Key Takeaways

- **Serial latency** -- all four frameworks deliver similar single-request latency (~250-400 us). No framework has a major edge for serial workloads.
- **Concurrent handling** -- async frameworks (zerodep, microdot) handle 10 concurrent requests in ~5 ms. WSGI frameworks (Flask, bottle) serialize requests and take ~1 second (200x slower).
- **Sync handler overhead** -- `asyncio.to_thread()` adds ~20% overhead vs native async handlers, but still outperforms WSGI frameworks under concurrent load.
- **Large payloads** -- JSON parsing/serialization throughput is comparable across all frameworks; the bottleneck is `json.dumps()`/`json.loads()`, not the HTTP layer.
- **Zero dependencies** -- zerodep achieves Flask/microdot-level performance with no pip dependencies.

## Run It Yourself

```bash
pip install pytest pytest-benchmark flask microdot bottle
pytest httpserver/test_httpserver_benchmark.py --benchmark-only -v
```

---

## Latest CI Results

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/httpserver.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> Updated automatically on each release via [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml).
