# Diff Benchmark

Apple-to-apple performance comparison between zerodep diff and [`unidiff`](https://pypi.org/project/unidiff/).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.10.20
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)

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
| Small | ~7 us | ~65 us | **~9x faster** |
| Medium | ~18 us | ~145 us | **~8x faster** |
| Large | ~130 us | ~1,200 us | **~9x faster** |

## Apply Performance (zerodep only)

`unidiff` does not provide patch application, so these are zerodep-only benchmarks.

| Test | zerodep |
|------|---------|
| Small | ~5 us |
| Medium | ~12 us |
| Large | ~80 us |

## Key Takeaways

- **Consistently faster** -- zerodep's diff parser is **~8-9x faster** than unidiff across all diff sizes.
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
