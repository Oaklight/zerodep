# A2A Benchmark

Apple-to-apple performance comparison between zerodep A2A and [`a2a-protocol`](https://pypi.org/project/a2a-protocol/).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)
    - **Reference:** a2a-protocol 0.1.0
    - **Last Updated:** 2026-04-21

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
| Small | 4.0 μs | 5.0 μs | **1.2x faster** |
| Medium | 85.3 μs | 103.3 μs | **1.2x faster** |
| Large | 1,570 μs | 1,920 μs | **1.2x faster** |

## Deserialization Performance (Mean)

Dict → object reconstruction. zerodep uses `from_dict()` with enum parsing and type dispatch; reference constructs dataclasses directly (no `from_dict` API).

| Data Size | zerodep | a2a-protocol | Ratio |
|-----------|---------|--------------|-------|
| Small | 1.9 μs | 1.1 μs | 1.7x slower |
| Medium | 41.0 μs | 36.1 μs | 1.1x slower |
| Large | 997.8 μs | 666.3 μs | 1.5x slower |

!!! note "Deserialization Methodology"
    The reference library (`a2a-protocol`) uses plain dataclasses without a `from_dict()` method. The benchmark constructs objects directly from known fields rather than parsing from an arbitrary dict. zerodep's `from_dict()` performs full dict → object reconstruction with enum resolution and type dispatch, which is a richer operation.

## JSON Round-Trip Performance (Mean)

Full cycle: object → dict → JSON string → dict → object.

| Data Size | zerodep | a2a-protocol | Ratio |
|-----------|---------|--------------|-------|
| Small | 11.4 μs | 12.6 μs | **1.1x faster** |
| Medium | 175.3 μs | 175.6 μs | ~same |
| Large | 3,500 μs | 3,070 μs | 1.1x slower |

!!! note "Round-Trip Methodology"
    zerodep performs full `to_dict → json.dumps → json.loads → from_dict` reconstruction. The reference does `asdict → json.dumps → json.loads` without object reconstruction (no `from_dict` exists). Despite the additional reconstruction step, zerodep's optimized serialization results in faster overall round-trip times.

## Key Takeaways

- **Serialization is consistently 1.2x faster** -- zerodep's custom `to_dict()` outperforms the reference's `dataclasses.asdict()` across all data sizes, thanks to avoiding the recursive deep-copy overhead.
- **Deserialization is 1.1-1.7x slower** -- zerodep's `from_dict()` does full dict-to-object reconstruction with enum parsing and type dispatch. The reference constructs dataclasses directly without parsing. The gap is larger on small inputs (1.7x) but narrows on medium data (1.1x).
- **JSON round-trip is mixed** -- zerodep is slightly faster on small payloads (1.1x), at parity on medium, and slightly slower on large (1.1x). The serialization advantage and deserialization overhead roughly cancel out at scale.
- **Zero dependencies** -- unlike the reference which requires installation, zerodep's A2A is a single file with no external packages.

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
