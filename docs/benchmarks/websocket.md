# WebSocket Benchmark

WebSocket round-trip performance comparison between zerodep websocket and the [websockets](https://pypi.org/project/websockets/) library.

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)
    - **Reference:** websockets 15.0.1
    - **Last Updated:** 2026-05-02

## Implementations

| Implementation | Type | Description |
|----------------|------|-------------|
| **zerodep** | sync + async | Single-file RFC 6455 client, stdlib only |
| **websockets** | sync + async | Full-featured WebSocket library |

## What Is Benchmarked

Both clients connect to a stdlib echo server (shared fixture). Benchmarks measure full send-receive round-trip latency including frame encoding, masking, and decoding.

## Benchmark Scenarios

| Scenario | Description | Payload |
|----------|-------------|---------|
| JSON-RPC Roundtrip | Send CDP-sized JSON message, receive echo | ~200B |
| Large Payload | Send SPA outerHTML-sized content, receive echo | ~50KB |
| Burst Messages | Send 100 JSON-RPC messages sequentially, then receive all | 100 x ~150B |
| Connection Setup | Connect + close handshake cycle | N/A |

## Key Takeaways

- **JSON-RPC messages** -- both implementations deliver sub-millisecond round-trips for typical CDP command sizes.
- **Large payloads** -- zerodep handles 50KB payloads with comparable latency to websockets, as the bottleneck is TCP I/O rather than frame encoding.
- **Burst messaging** -- sequential send/receive of 100 messages tests frame encoding throughput and buffer management.
- **Connection overhead** -- measures WebSocket upgrade handshake latency including TCP connect, HTTP upgrade, and key validation.
- **Zero dependencies** -- zerodep achieves comparable performance with no pip dependencies.

## Run It Yourself

```bash
pip install pytest pytest-benchmark websockets
pytest websocket/test_websocket_benchmark.py --benchmark-only -v
```

---

## Latest CI Results

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/websocket.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> Updated automatically on each release via [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml).
