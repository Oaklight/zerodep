# Protobuf Benchmark

Apple-to-apple performance comparison between zerodep protobuf (pure Python) and [`google-protobuf`](https://pypi.org/project/protobuf/) (C/upb extensions).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.10.20
    - **google-protobuf:** 7.34.1 (upb C backend)
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)

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
| Small | 4.86 μs | 0.094 μs | 52x slower |
| Medium | 60.7 μs | 0.169 μs | 359x slower |
| Large | 294.0 μs | 1.29 μs | 228x slower |

## Decode Performance (Mean)

| Message Size | zerodep | google-protobuf | Ratio |
|-------------|---------|-----------------|-------|
| Small | 4.60 μs | 0.263 μs | 17x slower |
| Medium | 51.7 μs | 0.565 μs | 91x slower |
| Large | 412.4 μs | 2.50 μs | 165x slower |

## Roundtrip Performance (Mean)

| Message Size | zerodep | google-protobuf | Ratio |
|-------------|---------|-----------------|-------|
| Small | 9.78 μs | 0.367 μs | 27x slower |
| Medium | 89.4 μs | 0.769 μs | 116x slower |
| Large | 722.8 μs | 3.84 μs | 188x slower |

## Dict Conversion (Large Message, zerodep only)

| Operation | Time |
|-----------|------|
| `to_dict()` | 173.2 μs |
| `from_dict()` | 126.3 μs |

## Key Takeaways

- **google-protobuf is 50-200x faster** -- this is expected since it uses a compiled C/upb backend while zerodep is pure Python. The gap widens with message complexity.
- **Decode is relatively closer** -- zerodep's decode gap (17-165x) is smaller than encode (52-359x), because Python's overhead is more evenly distributed across field parsing.
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
