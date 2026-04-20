# Dotenv Benchmark

Apple-to-apple performance comparison between zerodep dotenv and [`python-dotenv`](https://pypi.org/project/python-dotenv/).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)
    - **Reference:** python-dotenv 1.2.2
    - **Last Updated:** 2026-04-21

## Implementations

| Implementation | File/Package | Description |
|----------------|--------------|-------------|
| **zerodep** | `dotenv.py` | stdlib-only `.env` parser |
| **python-dotenv** | *(reference)* | Popular dotenv library |

## Data Sizes Tested

| Label | Entries | Description |
|-------|---------|-------------|
| Small | 10 | `.env` file with 10 key-value pairs |
| Medium | 50 | `.env` file with 50 key-value pairs |
| Large | 500 | `.env` file with 500 key-value pairs |

## Performance Comparison (Mean)

| Test | zerodep | python-dotenv | Ratio |
|------|---------|---------------|-------|
| Small (10 entries) | 27.3 us | 27.1 us | ~1.0x |
| Medium (50 entries) | 191.3 us | 189.8 us | ~1.0x |
| Large (500 entries) | 1,350.0 us | 1,350.0 us | ~1.0x |

## Key Takeaways

- **Near-parity across all sizes** -- both implementations perform within measurement noise of each other across small, medium, and large files.
- **Linear scaling** -- both libraries scale linearly with the number of entries, as expected for line-by-line parsing.
- **Zero-dependency advantage** -- since performance is essentially identical for all file sizes, zerodep's benefit is in eliminating the external `python-dotenv` dependency from your project.

## Run It Yourself

```bash
pip install pytest pytest-benchmark python-dotenv
pytest dotenv/test_dotenv_benchmark.py --benchmark-only -v
```

---

## Latest CI Results

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/dotenv.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> Updated automatically on each release via [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml).
