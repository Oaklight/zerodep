# PNG Benchmark

Apple-to-apple performance comparison between zerodep png (pure Python) and [`Pillow`](https://pypi.org/project/Pillow/) (C extensions).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)
    - **Reference:** Pillow 12.2.0
    - **Last Updated:** 2026-04-27

## Implementations

| Implementation | File/Package | Description |
|----------------|--------------|-------------|
| **zerodep** | `png.py` | Pure-Python PNG/BMP codec using stdlib zlib |
| **Pillow** | *(reference)* | Full-featured image library with C extensions |

## Test Images

| Label | Description |
|-------|-------------|
| Small | 64x64 RGBA (16 KB pixels) |
| Medium | 256x256 RGBA (256 KB pixels) |
| Large | 1024x1024 RGBA (4 MB pixels) |

## Key Takeaways

- **Pillow is significantly faster** -- this is expected since Pillow uses compiled C extensions (libpng, zlib-ng) while zerodep is pure Python. The core bottleneck is the per-byte row filter loop.
- **PNG decode is mostly zlib** -- the `zlib.decompress` call (C code) dominates; the pure-Python unfilter loop adds overhead proportional to image size.
- **PNG encode is filter-bound** -- the minimum-sum heuristic tries all 5 filters per row, making encode ~5x more work than decode per pixel.
- **BMP is optimized** -- BMP codec uses `bytearray` slice assignment for BGR↔RGB channel swap, which runs at C level. This makes BMP encode/decode only ~4-6x slower than Pillow (vs ~20x for PNG).
- **zerodep targets different use cases** -- the tradeoff is zero dependencies and a single-file drop-in:
    - Generating QR codes, charts, or thumbnails
    - Reading image metadata or pixel data
    - Matrix data compression via PNG row filters
    - Environments where C extensions are unavailable

## Run It Yourself

```bash
pip install pytest pytest-benchmark Pillow numpy
pytest png/test_png_benchmark.py --benchmark-only -v
```

---

## Latest CI Results

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/png.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> Updated automatically on each release via [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml).
