# JSON-RPC Benchmark

Apple-to-apple performance comparison between zerodep JSON-RPC and [`jsonrpcserver`](https://pypi.org/project/jsonrpcserver/).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.10.20
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)

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
| Success | 4.5 μs | 69.0 μs | **15.4x faster** |
| Error | 5.4 μs | 68.9 μs | **12.8x faster** |
| Method not found | 4.7 μs | 54.3 μs | **11.5x faster** |
| Batch (20 requests) | 85.2 μs | 1,436.8 μs | **16.9x faster** |

## Serialization Performance (Mean, zerodep only)

`jsonrpcserver` does not expose model objects, so serialization is zerodep-only.

| Operation | Time |
|-----------|------|
| Request `to_dict()` | 187 ns |
| Response `to_dict()` | 143 ns |
| Request `from_dict()` | 360 ns |
| Response `from_dict()` | 414 ns |
| Full JSON round-trip | 3.8 μs |

## ID Generation (Mean)

| Operation | Time |
|-----------|------|
| `next_id()` | 55 ns |

## Key Takeaways

- **Dispatch is ~12-17x faster** -- zerodep dramatically outperforms jsonrpcserver across all dispatch scenarios because it avoids jsonrpcserver's schema validation overhead and function introspection machinery.
- **Batch scaling is linear** -- 20-request batch shows the same ~17x speedup, confirming zero per-request overhead beyond the handler itself.
- **Serialization is sub-microsecond** -- dataclass `to_dict()` / `from_dict()` is extremely lightweight compared to full dispatch.
- **ID generation is ~55 ns** -- `itertools.count` is essentially free.

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
