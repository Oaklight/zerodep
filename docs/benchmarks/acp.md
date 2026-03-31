# ACP Benchmark

Apple-to-apple performance comparison between zerodep ACP and [`agent-client-protocol`](https://pypi.org/project/agent-client-protocol/).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.10.20
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)

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
| Small | 2.9 us | 0.7 us | 0.24x |
| Medium | 43.5 us | 6.6 us | 0.15x |
| Large | 679.4 us | 40.6 us | 0.06x |

## Deserialization Performance (Mean)

Dict → object reconstruction. zerodep uses `from_raw()`; reference uses Pydantic's `model_validate()`.

| Data Size | zerodep | agent-client-protocol | Speedup |
|-----------|---------|----------------------|---------|
| Small | 0.4 us | 0.8 us | **2.0x faster** |
| Medium | 0.7 us | 30.5 us | **40.7x faster** |
| Large | 15.0 us | 39.5 us | **2.6x faster** |

## JSON Round-Trip Performance (Mean)

Full cycle: object → dict → JSON string → dict → object.

| Data Size | zerodep | agent-client-protocol | Ratio |
|-----------|---------|----------------------|-------|
| Small | 6.0 us | 4.2 us | 0.69x |
| Medium | 56.9 us | 44.2 us | 0.78x |
| Large | 868.7 us | 238.6 us | 0.27x |

## Key Takeaways

- **Deserialization is 2-41x faster** -- zerodep's `from_raw()` uses lightweight dict-based reconstruction without deep schema validation, while Pydantic's `model_validate()` performs full type checking and coercion. This makes zerodep ideal for high-throughput message ingestion.
- **Serialization is slower** -- Pydantic v2's `model_dump()` is backed by compiled Rust code, making it significantly faster than zerodep's pure-Python `to_dict()` recursive conversion. The gap widens with data size.
- **JSON round-trip reflects the serialization gap** -- since serialization dominates the round-trip cost, the reference library's Rust-accelerated serialization gives it the edge in end-to-end scenarios.
- **Different design tradeoffs** -- zerodep prioritizes zero dependencies and simplicity; the reference library prioritizes raw throughput via compiled extensions. For most ACP use cases (stdio IPC between editor and agent), both are fast enough -- the bottleneck is the AI model, not serialization.

## Run It Yourself

```bash
pip install pytest pytest-benchmark agent-client-protocol
pytest acp/test_acp_benchmark.py --benchmark-only -v
```
