# ACP Benchmark

Apple-to-apple performance comparison between zerodep ACP and [`agent-client-protocol`](https://pypi.org/project/agent-client-protocol/).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)
    - **Reference:** agent-client-protocol 0.9.0
    - **Last Updated:** 2026-04-15

## Implementations

| Implementation | File/Package | Description |
|----------------|--------------|-------------|
| **zerodep** | `acp.py` | stdlib-only ACP protocol with plain dataclasses |
| **agent-client-protocol** | *(reference)* | Official ACP SDK using Pydantic v2 (Rust-accelerated) |

## Data Sizes Tested

| Label | Description |
|-------|-------------|
| Small | Single `TextContent` block |
| Medium | `PromptParams` with 10 content blocks + `InitializeResult` with capabilities |
| Large | 20 `ToolCallUpdate` objects with nested locations, raw input/output |

## Serialization Performance (Mean)

Object → dict conversion. zerodep uses `to_dict()`; reference uses Pydantic's `model_dump()`.

| Data Size | zerodep | agent-client-protocol | Ratio |
|-----------|---------|----------------------|-------|
| Small | 3.0 μs | 1.1 μs | 2.7x slower |
| Medium | 46.5 μs | 12.6 μs | 3.7x slower |
| Large | 399.8 μs | 76.8 μs | 5.2x slower |

## Deserialization Performance (Mean)

Dict → object reconstruction. zerodep uses `from_raw()`; reference uses Pydantic's `model_validate()`.

| Data Size | zerodep | agent-client-protocol | Ratio |
|-----------|---------|----------------------|-------|
| Small | 1.4 μs | 1.3 μs | ~same |
| Medium | 5.0 μs | 49.9 μs | **10.0x faster** |
| Large | 128.9 μs | 68.4 μs | 1.9x slower |

## JSON Round-Trip Performance (Mean)

Full cycle: object → dict → JSON string → dict → object.

| Data Size | zerodep | agent-client-protocol | Ratio |
|-----------|---------|----------------------|-------|
| Small | 8.3 μs | 5.9 μs | 1.4x slower |
| Medium | 72.4 μs | 72.4 μs | ~same |
| Large | 793.6 μs | 385.5 μs | 2.1x slower |

## Key Takeaways

- **Deserialization is mixed** -- zerodep's `from_raw()` is 10.0x faster than Pydantic at medium scale, where Pydantic's deep schema validation is most costly. At small scale the two are on par, and at large scale zerodep is 1.9x slower.
- **Serialization is 2.7-5.2x slower** -- Pydantic v2's `model_dump()` is backed by compiled Rust code, making it significantly faster than zerodep's pure-Python `to_dict()` recursive conversion. The gap widens with data size.
- **JSON round-trip is mixed** -- at medium scale the two are on par. At small scale zerodep is 1.4x slower, and at large scale 2.1x slower, reflecting the serialization overhead.
- **Different design tradeoffs** -- zerodep prioritizes zero dependencies and simplicity; the reference library prioritizes raw throughput via compiled extensions. For most ACP use cases (stdio IPC between editor and agent), both are fast enough -- the bottleneck is the AI model, not serialization.

## Run It Yourself

```bash
pip install pytest pytest-benchmark agent-client-protocol
pytest acp/test_acp_benchmark.py --benchmark-only -v
```

---

## Latest CI Results

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/acp.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> Updated automatically on each release via [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml).
