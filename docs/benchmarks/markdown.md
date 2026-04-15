# Markdown Benchmark

Apple-to-apple performance comparison between zerodep markdown and [`mistune`](https://pypi.org/project/mistune/).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)
    - **Reference:** mistune 3.2.0
    - **Last Updated:** 2026-04-15

## Implementations

| Implementation | File/Package | Description |
|----------------|--------------|-------------|
| **zerodep** | `markdown.py` | stdlib-only Markdown → HTML renderer |
| **mistune** | *(reference)* | Popular Markdown parser library |

## Data Sizes Tested

| Label | Description |
|-------|-------------|
| Small | 2 lines: one heading with bold, one paragraph with emphasis and code |
| Medium | ~15 blocks: headings, paragraphs, code block, blockquote, lists, table, thematic break |
| Large | 50 repeated sections, each with heading, paragraph, code block, quote, and list |

## Performance Comparison (Mean)

| Test | zerodep | mistune | Ratio |
|------|---------|---------|-------|
| Small | 40.2 us | 62.2 us | **1.5x faster** |
| Medium | 306.3 us | 642.4 us | **2.1x faster** |
| Large | 5,079.3 us | 9,953.1 us | **2.0x faster** |

## Key Takeaways

- **Consistently faster** -- zerodep's markdown renderer is **1.5--2.1x faster** than mistune across all document sizes.
- **Linear scaling** -- both implementations scale linearly with document size, as expected.
- **Simpler architecture** -- zerodep skips building an intermediate AST and concatenates HTML directly, which contributes to the performance advantage. The tradeoff is that it only supports HTML output and is harder to extend with plugins or alternative renderers.
- **Output compatibility** -- zerodep produces identical HTML output to `mistune.html()` for all supported Markdown features (82 correctness tests pass with exact match).

## Run It Yourself

```bash
pip install pytest pytest-benchmark mistune
pytest markdown/test_markdown_benchmark.py --benchmark-only -v
```

---

## Latest CI Results

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/markdown.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> Updated automatically on each release via [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml).
