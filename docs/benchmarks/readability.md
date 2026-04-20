# Readability Benchmark

Performance comparison between zerodep readability, [`readability-lxml`](https://pypi.org/project/readability-lxml/), and [Mozilla Readability.js](https://github.com/mozilla/readability).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **Node.js:** 22 (for Mozilla Readability.js)
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)
    - **Reference:** readability-lxml 0.8.4.1, @mozilla/readability + jsdom
    - **Last Updated:** 2026-04-21

## Implementations

| Implementation | File/Package | Description |
|----------------|--------------|-------------|
| **zerodep** | `readability.py` + `soup.py` | stdlib-only article extractor |
| **readability-lxml** | *(reference)* | Python readability port using lxml |
| **Mozilla Readability.js** | *(reference)* | Original JS reference implementation |

## Test Fixtures

Benchmarks use real-world HTML fixtures from Mozilla Readability.js test suite, plus synthetic fixtures for controlled scaling:

| Tier | Fixture | Description |
|------|---------|-------------|
| Small | 001 | Simple article page (~2 KB) |
| Medium | bbc-1 | BBC news article (~25 KB) |
| Large | wikipedia | Wikipedia article (~16 KB) |
| Synthetic Small | generated | Synthetic article (~1 KB, controlled structure) |
| Synthetic Medium | generated | Synthetic article (~5 KB, controlled structure) |
| Synthetic Large | generated | Synthetic article (~20 KB, controlled structure) |

## Performance: zerodep vs readability-lxml

| Fixture | zerodep | readability-lxml | Ratio |
|---------|---------|------------------|-------|
| Small (001) | 276.1 μs | 680.3 μs | **2.5x faster** |
| Medium (bbc-1) | 2.59 ms | 3.19 ms | **1.2x faster** |
| Large (wikipedia) | 33.85 ms | 28.52 ms | 1.2x slower |
| Synthetic Small | 458.7 μs | 757.7 μs | **1.7x faster** |
| Synthetic Medium | 1.16 ms | 2.40 ms | **2.1x faster** |
| Synthetic Large | 5.69 ms | 13.08 ms | **2.3x faster** |

## Performance: zerodep vs Mozilla Readability.js

All three implementations are now benchmarked via pytest-benchmark in the same CI run. Mozilla Readability.js is invoked through a Node.js subprocess.

| Fixture | zerodep | Mozilla JS | Ratio |
|---------|---------|------------|-------|
| Small (001) | 276.1 μs | 5.59 ms | **20x faster** |
| Medium (bbc-1) | 2.59 ms | 8.21 ms | **3.2x faster** |
| Large (wikipedia) | 33.85 ms | 423 ms | **12.5x faster** |
| Synthetic Small | 458.7 μs | 8.10 ms | **17.7x faster** |
| Synthetic Medium | 1.16 ms | 13.50 ms | **11.6x faster** |
| Synthetic Large | 5.69 ms | 28.95 ms | **5.1x faster** |

## Key Takeaways

- **zerodep dominates on small and synthetic pages** -- **2.5x faster** on the small real-world fixture and **1.7-2.3x faster** across all synthetic sizes vs readability-lxml. The optimized scoring and tree-walking algorithms shine on cleaner HTML.
- **readability-lxml retains an edge on large complex pages** -- lxml's C-based parser still provides an advantage on complex HTML like Wikipedia articles (1.2x slower).
- **Massively faster than Mozilla Readability.js** -- zerodep is **3.2-20x faster** than the original JS reference across all fixtures. The JS implementation pays heavy overhead from jsdom's DOM construction.
- **zerodep has richer metadata** -- JSON-LD extraction, RTL support, and OpenGraph metadata that readability-lxml lacks
- **Zero pip dependencies** -- zerodep needs only the stdlib, while readability-lxml requires lxml and cssselect

## Run It Yourself

```bash
# All benchmarks (zerodep vs readability-lxml vs Mozilla JS, requires Node.js)
pip install pytest pytest-benchmark readability-lxml
cd readability && npm install
pytest readability/test_readability_benchmark.py --benchmark-only -v
```

---

## Latest CI Results

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/readability.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> Updated automatically on each release via [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml).
