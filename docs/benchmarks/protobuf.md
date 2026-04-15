# Protobuf Benchmark

Apple-to-apple performance comparison between zerodep protobuf (pure Python) and [`google-protobuf`](https://pypi.org/project/protobuf/) (C/upb extensions).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)
    - **Reference:** protobuf (google) 7.34.1
    - **Last Updated:** 2026-04-15

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
| Small | 5.3 μs | 0.2 μs | 22x slower |
| Medium | 49.3 μs | 0.5 μs | 106x slower |
| Large | 341.1 μs | 2.6 μs | 134x slower |

## Decode Performance (Mean)

| Message Size | zerodep | google-protobuf | Ratio |
|-------------|---------|-----------------|-------|
| Small | 5.1 μs | 0.5 μs | 11x slower |
| Medium | 59.6 μs | 1.0 μs | 58x slower |
| Large | 432.2 μs | 4.7 μs | 93x slower |

## Roundtrip Performance (Mean)

| Message Size | zerodep | google-protobuf | Ratio |
|-------------|---------|-----------------|-------|
| Small | 10.5 μs | 0.7 μs | 16x slower |
| Medium | 111.5 μs | 1.4 μs | 78x slower |
| Large | 800.1 μs | 7.2 μs | 111x slower |

## Dict Conversion (Large Message, zerodep only)

| Operation | Time |
|-----------|------|
| `to_dict()` | 138.0 μs |
| `from_dict()` | 133.9 μs |

## Key Takeaways

- **google-protobuf is 11-134x faster** -- this is expected since it uses a compiled C/upb backend while zerodep is pure Python. The gap widens with message complexity.
- **Decode is relatively closer** -- zerodep's decode gap (11-93x) is smaller than encode (22-134x), because Python's overhead is more evenly distributed across field parsing.
- **zerodep targets a different use case** -- the tradeoff is zero dependencies, no `protoc`, no `.proto` files, no C extensions, and a single-file drop-in. It is suitable for:
    - Configuration and metadata exchange (low frequency)
    - CLI tools, scripts, and prototyping
    - Environments where C extensions are unavailable
    - Projects that need proto3 wire compatibility without the build toolchain
- **Small messages at ~5 μs** -- still fast enough for per-request metadata or RPC headers at moderate throughput (200K ops/s).
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
