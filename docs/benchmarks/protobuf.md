# Protobuf Benchmark

Apple-to-apple performance comparison between zerodep protobuf (pure Python) and [`google-protobuf`](https://pypi.org/project/protobuf/) (C/upb extensions).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)
    - **Reference:** protobuf (google) 7.34.1
    - **Last Updated:** 2026-04-25

## Implementations

| Implementation | File/Package | Description |
|----------------|--------------|-------------|
| **zerodep** | `protobuf.py` | Pure-Python proto3 encoder/decoder using dataclass schemas |
| **google-protobuf** | *(reference)* | Google's official protobuf library with C/upb acceleration |

## Message Shapes

| Label | Description |
|-------|-------------|
| Small | 3 fields: string + int32 + bool |
| Medium | 5 fields: uint64 + string + double + repeated[str] (4) + repeated[int32] (100) |
| Large | 6 fields: uint64 + string + 50 nested messages + map[str,str] (20) + repeated[double] (100) + bool |

## Encode Performance (Mean)

| Message Size | zerodep | google-protobuf | Ratio |
|-------------|---------|-----------------|-------|
| Small | 6.8 μs | 0.2 μs | 31x slower |
| Medium | 47.0 μs | 0.4 μs | 113x slower |
| Large | 396.1 μs | 2.4 μs | 167x slower |

## Decode Performance (Mean)

| Message Size | zerodep | google-protobuf | Ratio |
|-------------|---------|-----------------|-------|
| Small | 8.8 μs | 0.5 μs | 18x slower |
| Medium | 64.6 μs | 1.0 μs | 62x slower |
| Large | 654.3 μs | 4.7 μs | 139x slower |

## Roundtrip Performance (Mean)

| Message Size | zerodep | google-protobuf | Ratio |
|-------------|---------|-----------------|-------|
| Small | 16.1 μs | 0.7 μs | 23x slower |
| Medium | 112.8 μs | 1.4 μs | 81x slower |
| Large | 1062.6 μs | 7.2 μs | 148x slower |

## Dict Conversion (Large Message, zerodep only)

| Operation | Time |
|-----------|------|
| `to_dict()` | 322.3 μs |
| `from_dict()` | 242.0 μs |

## Key Takeaways

- **google-protobuf is 18-167x faster** -- this is expected since it uses a compiled C/upb backend while zerodep is pure Python. The gap widens with message complexity.
- **Decode is relatively closer** -- zerodep's decode gap (18-139x) is smaller than encode (31-167x), because Python's overhead is more evenly distributed across field parsing.
- **zerodep targets a different use case** -- the tradeoff is zero dependencies, no `protoc`, no `.proto` files, no C extensions, and a single-file drop-in. It is suitable for:
    - Configuration and metadata exchange (low frequency)
    - CLI tools, scripts, and prototyping
    - Environments where C extensions are unavailable
    - Projects that need proto3 wire compatibility without the build toolchain
- **Small messages at ~7 μs** -- still fast enough for per-request metadata or RPC headers at moderate throughput (145K ops/s).
- **Dict conversion has no google equivalent** -- `to_dict()` / `from_dict()` provide JSON-friendly serialization without MessageToDict overhead.

## Run It Yourself

```bash
pip install pytest pytest-benchmark protobuf
pytest protobuf/test_protobuf_benchmark.py --benchmark-only -v
```

---

## Latest CI Results

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/protobuf.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> Updated automatically on each release via [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml).
