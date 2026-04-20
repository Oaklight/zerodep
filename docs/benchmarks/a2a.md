# A2A Benchmark

Apple-to-apple performance comparison between zerodep A2A and [`a2a-protocol`](https://pypi.org/project/a2a-protocol/).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)
    - **Reference:** a2a-protocol 0.1.0
    - **Last Updated:** 2026-04-20

## Implementations

| Implementation | File/Package | Description |
|----------------|--------------|-------------|
| **zerodep** | `a2a.py` | stdlib-only A2A protocol with custom `to_dict()` / `from_dict()` |
| **a2a-protocol** | *(reference)* | Official A2A Python SDK using plain dataclasses |

## Data Sizes Tested

| Label | Description |
|-------|-------------|
| Small | Single `Message` with 1 text part |
| Medium | `Task` with 10 artifacts (3 parts each) and 5 history messages |
| Large | 50 `Task` objects, each with 3 artifacts and 4 history messages |

## Serialization Performance (Mean)

Object → dict conversion. zerodep uses custom `to_dict()`; reference uses `dataclasses.asdict()`.

| Data Size | zerodep | a2a-protocol | Ratio |
|-----------|---------|--------------|-------|
| Small | 1.9 μs | 4.2 μs | **2.2x faster** |
| Medium | 36.3 μs | 93.0 μs | **2.6x faster** |
| Large | 917.0 μs | 2,236.7 μs | **2.4x faster** |

## Deserialization Performance (Mean)

Dict → object reconstruction. zerodep uses `from_dict()` with enum parsing and type dispatch; reference constructs dataclasses directly (no `from_dict` API).

| Data Size | zerodep | a2a-protocol | Ratio |
|-----------|---------|--------------|-------|
| Small | 1.5 μs | 0.9 μs | 1.7x slower |
| Medium | 27.7 μs | 25.9 μs | 1.1x slower |
| Large | 795.2 μs | 685.5 μs | 1.2x slower |

!!! note "Deserialization Methodology"
    The reference library (`a2a-protocol`) uses plain dataclasses without a `from_dict()` method. The benchmark constructs objects directly from known fields rather than parsing from an arbitrary dict. zerodep's `from_dict()` performs full dict → object reconstruction with enum resolution and type dispatch, which is a richer operation.

## JSON Round-Trip Performance (Mean)

Full cycle: object → dict → JSON string → dict → object.

| Data Size | zerodep | a2a-protocol | Ratio |
|-----------|---------|--------------|-------|
| Small | 7.9 μs | 10.9 μs | **1.4x faster** |
| Medium | 114.0 μs | 167.4 μs | **1.5x faster** |
| Large | 2,912.0 μs | 4,085.4 μs | **1.4x faster** |

!!! note "Round-Trip Methodology"
    zerodep performs full `to_dict → json.dumps → json.loads → from_dict` reconstruction. The reference does `asdict → json.dumps → json.loads` without object reconstruction (no `from_dict` exists). Despite the additional reconstruction step, zerodep's optimized serialization results in faster overall round-trip times.

## Key Takeaways

- **Serialization is 2.2-2.6x faster** -- zerodep's optimized `to_dict()` now significantly outperforms the reference's `dataclasses.asdict()`. The improvement comes from avoiding the overhead of `dataclasses.asdict()`'s recursive deep-copy behavior. Previously 1.4-2.1x slower, now **2.2-2.6x faster**.
- **Deserialization is 1.1-1.7x slower** -- zerodep's `from_dict()` does full dict-to-object reconstruction with enum parsing and type dispatch. The reference constructs dataclasses directly without parsing. The gap has narrowed dramatically (previously 1.8-4.1x slower) thanks to optimized enum resolution and type dispatch paths.
- **JSON round-trip is now 1.4-1.5x faster** -- the serialization gains more than compensate for the deserialization overhead, resulting in zerodep being faster end-to-end. Previously 1.6-1.8x slower.
- **Zero dependencies** -- unlike the reference which requires installation, zerodep's A2A is a single file with no external packages. Performance is now a strength rather than a tradeoff.

## Run It Yourself

```bash
pip install pytest pytest-benchmark a2a-protocol
pytest a2a/test_a2a_benchmark.py --benchmark-only -v
```

---

## Latest CI Results

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/a2a.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> Updated automatically on each release via [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml).
