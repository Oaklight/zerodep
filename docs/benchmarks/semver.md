# Semver Benchmark

Apple-to-apple performance comparison between zerodep semver and [`packaging`](https://pypi.org/project/packaging/).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)
    - **Reference:** packaging 26.1
    - **Last Updated:** 2026-04-20

## Implementations

| Implementation | File/Package | Description |
|----------------|--------------|-------------|
| **zerodep** | `semver.py` | Pure Python PEP 440 parser using `re`, inlined comparison keys with integer sentinels |
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
| Parse Simple | 14.2 μs | 4.1 μs | 3.5x slower |
| Parse Pre-release | 18.8 μs | 17.5 μs | 1.1x slower |
| Parse Complex | 22.4 μs | 17.7 μs | 1.3x slower |
| Sort | 1.3 μs | 1.6 μs | **1.3x faster** |
| Compare | 3.0 μs | 3.3 μs | **1.1x faster** |
| Property Access | 1.4 μs | 7.3 μs | **5.2x faster** |

## Key Takeaways

- **Parsing is 1.1-3.5x slower** -- simple version parsing still has a gap (3.5x) because packaging uses highly optimized C regex internals. Pre-release and complex parsing gaps are much smaller (1.1-1.3x).
- **Sorting and comparison are now faster** -- integer-sentinel comparison keys and inlined `_cmpkey` make sort 1.3x faster and compare 1.1x faster than packaging.
- **Property access is 5.2x faster** -- cached `__str__`, direct `_pre`/`_post`/`_dev` attribute access instead of property dispatch make boolean checks and string conversion much faster.
- **Zero pip dependencies** -- zerodep uses only `re` and `functools` from the standard library.
- **Practical trade-off** -- for typical use cases (version comparison, sorting, property checks), zerodep is now **faster** than packaging. Only bulk parsing of simple versions is slower.

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
