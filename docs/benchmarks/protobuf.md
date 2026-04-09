# Protobuf Benchmark

Encode/decode throughput for the zerodep protobuf module across small, medium, and large message shapes. Pure-Python proto3 with no C extensions.

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.10.20
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)

## Message Shapes

| Label | Description |
|-------|-------------|
| Small | 3 fields: string + int32 + bool |
| Medium | 5 fields: uint64 + string + double + repeated[str] (4) + repeated[int32] (100) |
| Large | 6 fields: uint64 + string + 50 nested messages + map[str,str] (20) + repeated[double] (100) + bool |

## Encode Performance (Mean)

| Message Size | Time | OPS (Kops/s) |
|-------------|------|--------------|
| Small | 4.6 μs | 215.4 |
| Medium | 36.3 μs | 27.5 |
| Large | 294.2 μs | 3.4 |

## Decode Performance (Mean)

| Message Size | Time | OPS (Kops/s) |
|-------------|------|--------------|
| Small | 4.5 μs | 221.0 |
| Medium | 50.7 μs | 19.7 |
| Large | 405.5 μs | 2.5 |

## Roundtrip Performance (Mean)

| Message Size | Time | OPS (Kops/s) |
|-------------|------|--------------|
| Small | 9.5 μs | 105.0 |
| Medium | 119.5 μs | 8.4 |
| Large | 712.3 μs | 1.4 |

## Dict Conversion (Large Message)

| Operation | Time | OPS (Kops/s) |
|-----------|------|--------------|
| `to_dict()` | 173.2 μs | 5.8 |
| `from_dict()` | 126.3 μs | 7.9 |

## Key Takeaways

- **Small messages encode/decode in ~4.5 μs** -- fast enough for per-request metadata, RPC headers, and config objects.
- **Medium messages (~100 repeated ints) stay under 120 μs roundtrip** -- suitable for batch payloads and streaming records.
- **Large messages (~50 nested + map + repeated) roundtrip in ~712 μs** -- acceptable for configuration blobs and moderate-throughput pipelines.
- **Dict conversion is competitive with wire format** -- `from_dict()` at 126 μs vs `parse()` at 405 μs for the same large message, since dict conversion skips varint/wire encoding.
- **Pure Python** -- no C extensions, no `protoc`, no build step. For high-throughput scenarios (>10K msg/s), consider google-protobuf with C acceleration.

## Run It Yourself

```bash
pip install pytest pytest-benchmark
pytest protobuf/test_protobuf_benchmark.py --benchmark-only -v
```
