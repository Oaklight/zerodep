# ACP Benchmark

Apple-to-apple performance comparison between zerodep ACP and [`agent-client-protocol`](https://pypi.org/project/agent-client-protocol/).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)
    - **Reference:** agent-client-protocol 0.9.0
    - **Last Updated:** 2026-04-21

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
| Small | 4.0 μs | 1.3 μs | 3.2x slower |
| Medium | 62.7 μs | 12.7 μs | 4.9x slower |
| Large | 526.5 μs | 73.3 μs | 7.2x slower |

## Deserialization Performance (Mean)

Dict → object reconstruction. zerodep uses `from_raw()`; reference uses Pydantic's `model_validate()`.

| Data Size | zerodep | agent-client-protocol | Ratio |
|-----------|---------|----------------------|-------|
| Small | 1.7 μs | 1.8 μs | ~same |
| Medium | 6.0 μs | 61.0 μs | **10.2x faster** |
| Large | 153.0 μs | 78.4 μs | 2.0x slower |

## JSON Round-Trip Performance (Mean)

Full cycle: object → dict → JSON string → dict → object.

| Data Size | zerodep | agent-client-protocol | Ratio |
|-----------|---------|----------------------|-------|
| Small | 10.1 μs | 7.0 μs | 1.4x slower |
| Medium | 90.4 μs | 84.6 μs | 1.1x slower |
| Large | 941.6 μs | 397.4 μs | 2.4x slower |

## Key Takeaways

- **Deserialization is mixed** -- zerodep's `from_raw()` is 10.2x faster than Pydantic at medium scale, where Pydantic's deep schema validation is most costly. At small scale the two are on par, and at large scale zerodep is 2.0x slower.
- **Serialization is 3.2-7.2x slower** -- Pydantic v2's `model_dump()` is backed by compiled Rust code, making it significantly faster than zerodep's pure-Python `to_dict()` recursive conversion. The gap widens with data size.
- **JSON round-trip is 1.1-2.4x slower** -- at medium scale zerodep is nearly on par (1.1x slower). At small scale zerodep is 1.4x slower, and at large scale 2.4x slower, reflecting the serialization overhead.
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
