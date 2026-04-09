# Semver Benchmark

Apple-to-apple performance comparison between zerodep semver and [`packaging`](https://pypi.org/project/packaging/).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.10.20
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)

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
| Parse Simple | 10.8 us | 8.0 us | 0.74x |
| Parse Pre-release | 14.6 us | 11.0 us | 0.76x |
| Parse Complex | 16.0 us | 11.5 us | 0.72x |
| Sort | 1.2 us | 2.5 us | 2.1x faster |
| Compare | 5.0 us | 6.6 us | 1.3x faster |
| Property Access | 4.7 us | 5.8 us | 1.2x faster |

## Key Takeaways

- **Comparable overall performance** -- zerodep is within the same order of magnitude as packaging across all scenarios.
- **Faster comparison and sorting** -- once parsed, zerodep Version objects compare and sort 1.2-2.1x faster than packaging, which matters most in version-checking workflows.
- **Slightly slower parsing** -- initial parsing is ~1.3x slower due to pure Python regex vs. packaging's optimised parser, but the absolute difference is only a few microseconds.
- **Zero pip dependencies** -- zerodep uses only `re` and `functools` from the standard library.
- **Practical trade-off** -- for typical use cases (parse a version once, compare many times), zerodep performs equivalently or better than packaging.

## Run It Yourself

```bash
pip install pytest pytest-benchmark packaging
pytest semver/test_semver_benchmark.py --benchmark-only -v
```
