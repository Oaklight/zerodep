# Markdown Benchmark

Apple-to-apple performance comparison between zerodep markdown and [`mistune`](https://pypi.org/project/mistune/).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.10.20
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)

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
| Small | ~25 us | ~46 us | **1.8x faster** |
| Medium | ~179 us | ~445 us | **2.5x faster** |
| Large | ~3,015 us | ~6,610 us | **2.2x faster** |

## Key Takeaways

- **Consistently faster** -- zerodep's markdown renderer is **1.8--2.6x faster** than mistune across all document sizes.
- **Linear scaling** -- both implementations scale linearly with document size, as expected.
- **Simpler architecture** -- zerodep skips building an intermediate AST and concatenates HTML directly, which contributes to the performance advantage. The tradeoff is that it only supports HTML output and is harder to extend with plugins or alternative renderers.
- **Output compatibility** -- zerodep produces identical HTML output to `mistune.html()` for all supported Markdown features (82 correctness tests pass with exact match).

## Run It Yourself

```bash
pip install pytest pytest-benchmark mistune
pytest markdown/test_markdown_benchmark.py --benchmark-only -v
```
