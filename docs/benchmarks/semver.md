# Semver Benchmark

Apple-to-apple performance comparison between zerodep semver and [`packaging`](https://pypi.org/project/packaging/).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)
    - **Reference:** packaging 26.1
    - **Last Updated:** 2026-04-15

## Implementations

| Implementation | File/Package | Description |
|----------------|--------------|-------------|
| **zerodep** | `semver.py` | Pure Python PEP 440 parser using `re` + `functools.total_ordering` |
| **packaging** | *(reference)* | The standard Python packaging library |

## Test Scenarios

| Scenario | Description |
|----------|-------------|
| Parse Simple | 5 basic version strings (`1.0`, `2.3.4`, etc.) |
| Parse Pre-release | 6 pre/post/dev versions (`1.0a1`, `2.0.dev3`, etc.) |
| Parse Complex | 5 versions with epoch, local, combined suffixes |
| Sort | Sort a list of 10 mixed versions |
| Compare | Pairwise `<` and `==` on 10 parsed versions |
| Property Access | `is_prerelease`, `is_devrelease`, `str()` on 6 versions |

## Performance Comparison (Mean)

| Scenario | zerodep | packaging | Ratio |
|----------|---------|-----------|-------|
| Parse Simple | 18.5 μs | 4.1 μs | 4.5x slower |
| Parse Pre-release | 24.4 μs | 17.5 μs | 1.4x slower |
| Parse Complex | 29.1 μs | 17.7 μs | 1.6x slower |
| Sort | 1.8 μs | 1.6 μs | 1.2x slower |
| Compare | 4.1 μs | 3.3 μs | 1.2x slower |
| Property Access | 6.2 μs | 7.3 μs | 1.2x faster |

## Key Takeaways

- **zerodep is generally slower than packaging** -- parsing is 1.4-4.5x slower, and comparison/sorting is ~1.2x slower. The absolute differences are small (a few microseconds).
- **Property access is slightly faster** -- `is_prerelease`, `is_devrelease`, and `str()` are 1.2x faster in zerodep.
- **Parsing simple versions has the largest gap** (4.5x) because packaging's parser is highly optimized for common version strings, while zerodep uses pure Python regex.
- **Zero pip dependencies** -- zerodep uses only `re` and `functools` from the standard library.
- **Practical trade-off** -- for typical use cases where version parsing is not on the hot path, the microsecond-level difference is negligible. zerodep's value is in eliminating the packaging dependency.

## Run It Yourself

```bash
pip install pytest pytest-benchmark packaging
pytest semver/test_semver_benchmark.py --benchmark-only -v
```

---

## Latest CI Results

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/semver.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> Updated automatically on each release via [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml).
