# Frontmatter Benchmark

Apple-to-apple performance comparison between zerodep frontmatter and [`python-frontmatter`](https://pypi.org/project/python-frontmatter/).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)
    - **Reference:** python-frontmatter 1.1.0
    - **Last Updated:** 2026-04-15

## Implementations

| Implementation | File/Package | Description |
|----------------|--------------|-------------|
| **zerodep** | `frontmatter.py` | stdlib-only frontmatter parser (uses sibling `yaml` module) |
| **python-frontmatter** | *(reference)* | Popular frontmatter library (depends on PyYAML) |

## Data Sizes Tested

| Label | Description |
|-------|-------------|
| Small | Simple YAML frontmatter with title and short body (~3 lines) |
| Medium | YAML frontmatter with 7 metadata fields and multi-section body (~20 lines) |
| Large | YAML frontmatter with 50+ metadata fields and 50 paragraphs of body text |

## Parse Performance (Mean)

| Data Size | zerodep | python-frontmatter | Ratio |
|-----------|---------|---------------------|-------|
| Small | 12.3 us | 12.4 us | ~1.0x (parity) |
| Medium | 82.4 us | 84.0 us | ~1.0x (parity) |
| Large | 383.0 us | 386.2 us | ~1.0x (parity) |

## Serialize Performance (Mean)

| Data Size | zerodep | python-frontmatter | Ratio |
|-----------|---------|---------------------|-------|
| Small | 20.6 us | 19.7 us | ~1.0x (parity) |
| Medium | 136.7 us | 132.3 us | ~1.0x (parity) |
| Large | 688.7 us | 683.9 us | ~1.0x (parity) |

## Key Takeaways

- **Performance parity** -- zerodep frontmatter matches `python-frontmatter` speed across all data sizes for both parsing and serialization. This is expected since both use the same underlying YAML library (zerodep's own `yaml` module vs PyYAML) and the frontmatter splitting logic is lightweight string operations.
- **Zero pip dependencies** -- unlike `python-frontmatter` which requires `PyYAML`, zerodep uses only the sibling `yaml` module and the standard library.
- **Additional format support** -- zerodep frontmatter also supports TOML (`+++`) and JSON (`{}`) frontmatter out of the box, while `python-frontmatter` only supports YAML by default.

## Run It Yourself

```bash
pip install pytest pytest-benchmark python-frontmatter
pytest frontmatter/test_frontmatter_benchmark.py --benchmark-only -v
```

---

## Latest CI Results

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/frontmatter.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> Updated automatically on each release via [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml).
