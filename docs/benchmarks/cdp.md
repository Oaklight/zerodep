# CDP Benchmark

Chrome DevTools Protocol client performance benchmarks using a mock CDP server.

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)
    - **Last Updated:** 2026-05-02

## Implementations

| Implementation | Type | Description |
|----------------|------|-------------|
| **zerodep cdp** | sync | CDP client built on zerodep websocket, stdlib only |

## What Is Benchmarked

The CDP client connects to a stdlib mock CDP server that simulates basic Chrome DevTools Protocol interactions (Target management, Page navigation, Runtime evaluation). Benchmarks measure end-to-end CDP command latency including WebSocket frame encoding, JSON serialization, and event buffering.

## Benchmark Scenarios

| Scenario | Description | Operations |
|----------|-------------|------------|
| Full Render Pipeline | create_target → navigate → evaluate(innerText) → close_target | 6+ CDP commands |
| Render HTML | create_target → navigate → evaluate(outerHTML) → close_target | 6+ CDP commands |
| Multi-Target (5 tabs) | Create 5 targets, navigate + evaluate each, close all | 30+ CDP commands |
| JS Eval Throughput | 10 consecutive evaluate() calls on same target | 10 CDP commands |
| Command Throughput | 20 rapid-fire send_command() with mixed methods | 20 CDP commands |

## Key Takeaways

- **Full render pipeline** -- the complete create → navigate → evaluate → close cycle completes in milliseconds against the mock server, demonstrating low CDP client overhead.
- **Multi-target** -- managing 5 concurrent targets (tabs) scales linearly with minimal per-target overhead.
- **JS evaluation** -- consecutive evaluate() calls show consistent latency, confirming efficient command/response ID matching and event buffer management.
- **Command throughput** -- raw command dispatch rate measures the overhead of JSON serialization, WebSocket framing, and response correlation.

## Run It Yourself

```bash
pip install pytest pytest-benchmark
pytest cdp/test_cdp_benchmark.py --benchmark-only -v
```

---

## Latest CI Results

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/cdp.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> Updated automatically on each release via [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml).
