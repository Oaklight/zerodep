# JSON-RPC Benchmark

Apple-to-apple performance comparison between zerodep JSON-RPC and [`jsonrpcserver`](https://pypi.org/project/jsonrpcserver/).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)
    - **Reference:** jsonrpcserver 5.0.9
    - **Last Updated:** 2026-04-15

## Implementations

| Implementation | File/Package | Description |
|----------------|--------------|-------------|
| **zerodep** | `jsonrpc.py` | stdlib-only JSON-RPC 2.0 with dispatcher, transport, and streaming |
| **jsonrpcserver** | *(reference)* | Popular JSON-RPC server library |

## Test Methodology

End-to-end dispatch comparison: JSON string → parse → dispatch → serialize → JSON string. This is the fairest comparison since `jsonrpcserver` operates on serialized JSON strings.

## Dispatch Performance (Mean)

| Scenario | zerodep | jsonrpcserver | Speedup |
|----------|---------|---------------|---------|
| Success | 6.3 μs | 118.5 μs | **18.8x faster** |
| Error | 8.1 μs | 112.0 μs | **13.8x faster** |
| Method not found | 7.0 μs | 92.4 μs | **13.2x faster** |
| Batch (20 requests) | 124.9 μs | 2,400.5 μs | **19.2x faster** |

## Serialization Performance (Mean, zerodep only)

`jsonrpcserver` does not expose model objects, so serialization is zerodep-only.

| Operation | Time |
|-----------|------|
| Request `to_dict()` | 300 ns |
| Response `to_dict()` | 300 ns |
| Request `from_dict()` | 700 ns |
| Response `from_dict()` | 700 ns |
| Full JSON round-trip | 6.4 μs |

## ID Generation (Mean)

| Operation | Time |
|-----------|------|
| `next_id()` | 93 ns |

## Key Takeaways

- **Dispatch is ~13-19x faster** -- zerodep dramatically outperforms jsonrpcserver across all dispatch scenarios because it avoids jsonrpcserver's schema validation overhead and function introspection machinery.
- **Batch scaling is linear** -- 20-request batch shows the same ~19x speedup, confirming zero per-request overhead beyond the handler itself.
- **Serialization is sub-microsecond** -- dataclass `to_dict()` / `from_dict()` is extremely lightweight compared to full dispatch.
- **ID generation is ~93 ns** -- `itertools.count` is essentially free.

## Run It Yourself

```bash
pip install pytest pytest-benchmark jsonrpcserver
pytest jsonrpc/test_jsonrpc_benchmark.py --benchmark-only -v
```

---

## Latest CI Results

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/jsonrpc.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> Updated automatically on each release via [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml).
