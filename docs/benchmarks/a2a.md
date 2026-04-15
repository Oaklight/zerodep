# A2A Benchmark

Apple-to-apple performance comparison between zerodep A2A and [`a2a-protocol`](https://pypi.org/project/a2a-protocol/).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.10.20
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)

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

| Data Size | zerodep | a2a-protocol | Speedup |
|-----------|---------|--------------|---------|
| Small | 5.5 us | 7.2 us | **1.3x faster** |
| Medium | 118.6 us | 171.8 us | **1.4x faster** |
| Large | 2,131.6 us | 3,178.0 us | **1.5x faster** |

## Deserialization Performance (Mean)

Dict → object reconstruction. zerodep uses `from_dict()` with enum parsing and type dispatch; reference constructs dataclasses directly (no `from_dict` API).

| Data Size | zerodep | a2a-protocol | Ratio |
|-----------|---------|--------------|-------|
| Small | 2.5 us | 0.6 us | 0.24x |
| Medium | 39.3 us | 20.5 us | 0.52x |
| Large | 988.6 us | 424.7 us | 0.43x |

!!! note "Deserialization Methodology"
    The reference library (`a2a-protocol`) uses plain dataclasses without a `from_dict()` method. The benchmark constructs objects directly from known fields rather than parsing from an arbitrary dict. zerodep's `from_dict()` performs full dict → object reconstruction with enum resolution and type dispatch, which is a richer operation.

## JSON Round-Trip Performance (Mean)

Full cycle: object → dict → JSON string → dict → object.

| Data Size | zerodep | a2a-protocol | Speedup |
|-----------|---------|--------------|---------|
| Small | 11.7 us | 12.1 us | 1.0x (on par) |
| Medium | 192.1 us | 220.7 us | **1.1x faster** |
| Large | 3,914.0 us | 4,006.5 us | 1.0x (on par) |

!!! note "Round-Trip Methodology"
    zerodep performs full `to_dict → json.dumps → json.loads → from_dict` reconstruction. The reference does `asdict → json.dumps → json.loads` without object reconstruction (no `from_dict` exists). Despite this extra work, zerodep is on par or faster.

## Key Takeaways

- **Serialization is 1.3-1.5x faster** -- zerodep's custom `to_dict()` avoids the expensive deep copy that `dataclasses.asdict()` performs, giving a consistent advantage across all scales.
- **Deserialization is slower but more capable** -- zerodep's `from_dict()` does full dict-to-object reconstruction with enum parsing and type dispatch. The reference library has no equivalent -- it only supports direct construction.
- **JSON round-trip is on par** -- the serialization advantage compensates for the richer deserialization, resulting in comparable end-to-end performance.
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
