# Readability Benchmark

Performance comparison between zerodep readability, [`readability-lxml`](https://pypi.org/project/readability-lxml/), and [Mozilla Readability.js](https://github.com/mozilla/readability).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **Node.js:** 22 (for Mozilla Readability.js)
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)
    - **Reference:** readability-lxml 0.8.4.1, @mozilla/readability + jsdom
    - **Last Updated:** 2026-04-20

## Implementations

| Implementation | File/Package | Description |
|----------------|--------------|-------------|
| **zerodep** | `readability.py` + `soup.py` | stdlib-only article extractor |
| **readability-lxml** | *(reference)* | Python readability port using lxml |
| **Mozilla Readability.js** | *(reference)* | Original JS reference implementation |

## Test Fixtures

Benchmarks use real-world HTML fixtures from Mozilla Readability.js test suite:

| Tier | Fixture | Description |
|------|---------|-------------|
| Small | 001 | Simple article page (~2 KB) |
| Medium | bbc-1 | BBC news article (~25 KB) |
| Large | wikipedia | Wikipedia article (~16 KB) |

## Python Performance (zerodep vs readability-lxml)

| Fixture | zerodep | readability-lxml | Ratio |
|---------|---------|------------------|-------|
| Small (001) | ~3 ms | ~5 ms | ~1.7x faster |
| Medium (bbc-1) | ~30 ms | ~15 ms | ~2x slower |
| Large (wikipedia) | ~25 ms | ~12 ms | ~2x slower |

## Three-Way Comparison

The `benchmark_compare.py` script provides a three-way comparison including Mozilla's JavaScript implementation:

```bash
python readability/benchmark_compare.py --rounds 10
```

This runs all three implementations on the same fixtures and reports timing with ratios.

## Key Takeaways

- **zerodep is competitive on small/medium pages** -- for typical blog posts and news articles, extraction time is in the low milliseconds
- **readability-lxml is faster on large pages** -- lxml's C-based parser gives it an advantage on complex HTML. zerodep uses pure Python parsing via `html.parser`
- **zerodep has richer metadata** -- JSON-LD extraction, RTL support, and OpenGraph metadata that readability-lxml lacks
- **Zero pip dependencies** -- zerodep needs only the stdlib, while readability-lxml requires lxml and cssselect

## Run It Yourself

```bash
# Python benchmarks (zerodep vs readability-lxml)
pip install pytest pytest-benchmark readability-lxml
pytest readability/test_readability_benchmark.py --benchmark-only -v

# Three-way comparison (requires Node.js)
cd readability && npm install
python readability/benchmark_compare.py --rounds 10
```

---

## Latest CI Results

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/readability.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> Updated automatically on each release via [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml).
