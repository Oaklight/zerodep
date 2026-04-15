# Diff Benchmark

Apple-to-apple performance comparison between zerodep diff and [`unidiff`](https://pypi.org/project/unidiff/).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)
    - **Reference:** unidiff 0.7.5
    - **Last Updated:** 2026-04-15

## Implementations

| Implementation | File/Package | Description |
|----------------|--------------|-------------|
| **zerodep** | `diff.py` | stdlib-only unified diff parser and patch applicator |
| **unidiff** | *(reference)* | Popular unified diff parsing library |

## Data Sizes Tested

| Label | Description |
|-------|-------------|
| Small | 5-line file with 1 changed line |
| Medium | 50-line file with 3 changed lines (3 hunks) |
| Large | 1000-line file with 10 changed lines (10 hunks) |

## Parse Performance Comparison (Mean)

| Test | zerodep | unidiff | Ratio |
|------|---------|---------|-------|
| Small | 7.7 μs | 18.1 μs | **2.4x faster** |
| Medium | 24.1 μs | 49.5 μs | **2.1x faster** |
| Large | 72.2 μs | 149.3 μs | **2.1x faster** |

## Apply Performance (zerodep only)

`unidiff` does not provide patch application, so these are zerodep-only benchmarks.

| Test | zerodep |
|------|---------|
| Small | 2.0 μs |
| Medium | 6.5 μs |
| Large | 55.2 μs |

## Key Takeaways

- **Consistently faster** -- zerodep's diff parser is **2.1-2.4x faster** than unidiff across all diff sizes.
- **Linear scaling** -- both implementations scale linearly with diff size, as expected.
- **More features** -- zerodep provides patch application, reversal, and three-way merge in addition to parsing, while unidiff only parses.
- **Round-trip correctness** -- `apply_patch(a, parse_patch(make_diff(a, b))) == b` verified across 13 parametrized test cases including edge cases (Unicode, no trailing newline, Windows line endings).

## Run It Yourself

```bash
pip install pytest pytest-benchmark unidiff
pytest diff/test_diff_benchmark.py --benchmark-only -v
```

---

## Latest CI Results

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/diff.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> Updated automatically on each release via [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml).
