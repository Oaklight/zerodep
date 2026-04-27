# llms.txt Benchmark

Baseline performance measurements for the zerodep llms.txt parser. No competing zero-dependency Python library exists for comparison, so this benchmark establishes a baseline for future optimization.

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)
    - **Reference:** N/A (no competing library)
    - **Last Updated:** 2026-04-27

## Implementation

| Implementation | File/Package | Description |
|----------------|--------------|-------------|
| **zerodep** | `llmstxt.py` | Regex-split parser + `urllib.parse` for URL handling |

## Data Sizes Tested

| Label | Description |
|-------|-------------|
| Small | H1, blockquote, 1 section with 3 entries (~10 lines) |
| Medium | H1, blockquote, details, 4 sections with 6-10 entries each, Optional section (~50 lines) |
| Large | H1, blockquote, details, 10 sections × 50 entries each + Optional (~600 lines) |

## Parse Performance (Mean)

| Data Size | zerodep |
|-----------|---------|
| Small | ~7 us |
| Medium | ~12 us |
| Large | ~1,050 us |

## Key Takeaways

- **Microsecond-level parsing** — small and medium files parse in under 15 us.
- **Linear scaling** — performance scales linearly with entry count.
- **Regex-split approach** — splitting on H2 headers gives O(n) parsing with minimal overhead.
- **Zero pip dependencies** — uses only `re`, `dataclasses`, and `urllib.parse` from the standard library.

## Run It Yourself

```bash
pip install pytest pytest-benchmark
pytest llmstxt/test_llmstxt_benchmark.py --benchmark-only -v
```

---

## Latest CI Results

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/llmstxt.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> Updated automatically on each release via [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml).
