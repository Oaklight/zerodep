# A2A Benchmark

Apple-to-apple performance comparison between zerodep A2A and [`a2a-protocol`](https://pypi.org/project/a2a-protocol/).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)
    - **Reference:** a2a-protocol 0.1.0
    - **Last Updated:** 2026-04-15

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
| Small | 9.1 μs | 4.2 μs | 2.1x slower |
| Medium | 188.0 μs | 93.0 μs | 2.0x slower |
| Large | 3,205.7 μs | 2,236.7 μs | 1.4x slower |

## Deserialization Performance (Mean)

Dict → object reconstruction. zerodep uses `from_dict()` with enum parsing and type dispatch; reference constructs dataclasses directly (no `from_dict` API).

| Data Size | zerodep | a2a-protocol | Ratio |
|-----------|---------|--------------|-------|
| Small | 3.6 μs | 0.9 μs | 4.1x slower |
| Medium | 59.5 μs | 25.9 μs | 2.3x slower |
| Large | 1,256.4 μs | 685.5 μs | 1.8x slower |

!!! note "Deserialization Methodology"
    The reference library (`a2a-protocol`) uses plain dataclasses without a `from_dict()` method. The benchmark constructs objects directly from known fields rather than parsing from an arbitrary dict. zerodep's `from_dict()` performs full dict → object reconstruction with enum resolution and type dispatch, which is a richer operation.

## JSON Round-Trip Performance (Mean)

Full cycle: object → dict → JSON string → dict → object.

| Data Size | zerodep | a2a-protocol | Ratio |
|-----------|---------|--------------|-------|
| Small | 17.2 μs | 10.9 μs | 1.6x slower |
| Medium | 297.0 μs | 167.4 μs | 1.8x slower |
| Large | 6,881.9 μs | 4,085.4 μs | 1.7x slower |

!!! note "Round-Trip Methodology"
    zerodep performs full `to_dict → json.dumps → json.loads → from_dict` reconstruction. The reference does `asdict → json.dumps → json.loads` without object reconstruction (no `from_dict` exists). zerodep's additional reconstruction step contributes to the slower round-trip times.

## Key Takeaways

- **Serialization is 1.4-2.1x slower** -- zerodep's pure-Python `to_dict()` is slower than the reference's `dataclasses.asdict()`. The gap narrows at larger data sizes (1.4x at large vs 2.1x at small).
- **Deserialization is 1.8-4.1x slower** -- zerodep's `from_dict()` does full dict-to-object reconstruction with enum parsing and type dispatch. The reference library constructs dataclasses directly without parsing, which is inherently faster. The gap narrows with data size as per-object overhead becomes less dominant.
- **JSON round-trip is 1.6-1.8x slower** -- the overhead is consistent across all data sizes. Note that zerodep performs full object reconstruction on the deserialization side while the reference does not.
- **Zero dependencies** -- unlike the reference which requires installation, zerodep's A2A is a single file with no external packages. The performance tradeoff is the cost of a pure-Python, zero-dependency implementation.

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
