# User-Agent Generator Benchmark

Apple-to-apple performance comparison between zerodep useragent and [`ua-generator`](https://pypi.org/project/ua-generator/).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.10
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)
    - **Reference:** ua-generator 2.0+
    - **Last Updated:** 2026-04-29

## Implementations

| Implementation | File/Package | Description |
|----------------|--------------|-------------|
| **zerodep** | `useragent.py` | Single-file Chrome/Edge UA generator, stdlib only |
| **ua-generator** | *(reference)* | Multi-browser UA generator package |

## What Is Benchmarked

Both libraries generate User-Agent strings with matching Client Hints headers. The benchmark measures pure generation throughput -- no network I/O involved.

## Test Scenarios

| Scenario | Description |
|----------|-------------|
| Default | Random browser + platform (no filters) |
| Chrome Desktop | `browser="chrome", device="desktop"` |
| Edge Mobile | `browser="edge", device="mobile"` |
| Headers | Generate UA + build full Client Hints headers via `.headers.get()` |

## Generation Performance (Mean)

| Scenario | zerodep | ua-generator | Speedup |
|----------|---------|--------------|---------|
| Default | 3.1 μs | 8.6 μs | **2.7x faster** |
| Chrome Desktop | 3.9 μs | 7.9 μs | **2.0x faster** |
| Edge Mobile | 3.4 μs | 9.2 μs | **2.7x faster** |
| Headers | 5.2 μs | 11.6 μs | **2.2x faster** |

## Key Takeaways

- **zerodep is 2-3x faster** across all scenarios -- the simpler architecture (no dynamic plugin loading, no multi-browser dispatch) translates directly into throughput gains.
- **Both are extremely fast** -- at 3-12 μs per generation, UA generation is never a bottleneck in any real application (a single HTTP request takes milliseconds).
- **Headers generation adds ~2 μs** -- building the full `Sec-CH-UA-*` header set is lightweight for both libraries.
- **zerodep covers Chrome + Edge only** -- this intentional scope reduction (vs ua-generator's Chrome/Edge/Firefox/Safari) is the main source of the speed advantage.
- **Zero pip dependencies** -- zerodep uses only `random` from the standard library.

## Run It Yourself

```bash
pip install pytest pytest-benchmark ua-generator
pytest useragent/test_useragent_benchmark.py --benchmark-only -v
```

---

## Latest CI Results

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/useragent.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> Updated automatically on each release via [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml).
