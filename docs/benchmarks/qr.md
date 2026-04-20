# QR Code Benchmark

Apple-to-apple performance comparison between zerodep QR implementation and the [`qrcode`](https://pypi.org/project/qrcode/) library (pure Python).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)
    - **Reference:** qrcode 8.2, Pillow 12.2.0
    - **Last Updated:** 2026-04-21

## Implementations

Both implementations are pure Python, so the comparison is between two interpreted codebases.

| Implementation | File/Package | Description |
|----------------|--------------|-------------|
| **zerodep** | `qr.py` | Nayuki-based, single file |
| **qrcode** | *(reference)* | Popular `qrcode` PyPI package |

## Inputs Tested

| Label | Content | Length |
|-------|---------|--------|
| Short | `"Hello"` | 5 characters |
| URL | `"https://example.com/path?query=value&foo=bar"` | 46 characters |
| Long | `"A" * 200` | 200 characters |
| Numeric | `"0123456789" * 10` | 100 characters |
| Binary | 512 random bytes | 512 bytes |
| High ECC | URL with `ERROR_CORRECT_H` | 46 characters |
| Large Data | `"A" * 1000` with `ERROR_CORRECT_L` | 1000 characters |

## Encode Performance (Mean)

| Input | zerodep (`qr.py`) | `qrcode` library | Ratio |
|-------|---------------------|-------------------|-------|
| Short (5 chars) | 2.34 ms | 1.84 ms | 1.3x slower |
| URL (46 chars) | 5.40 ms | 5.22 ms | ~same |
| Long (200 chars) | 11.06 ms | 11.69 ms | ~same |
| Numeric (100 chars) | 4.30 ms | 4.02 ms | 1.1x slower |
| Binary (512 bytes) | 34.33 ms | 41.75 ms | **1.2x faster** |
| High ECC (URL, HIGH) | 6.43 ms | 6.36 ms | ~same |
| Large Data (1000 chars, LOW) | 34.87 ms | 44.88 ms | **1.3x faster** |

## Key Takeaways

- **zerodep excels on large payloads** -- for binary data (512 bytes) and large text (1000 chars), zerodep is **1.2-1.3x faster** than `qrcode`, showing superior scaling on data-heavy inputs.
- **Competitive on medium inputs** -- URL, long text (200 chars), and high ECC scenarios are at parity (~same) between both implementations.
- **Slightly slower on short/numeric inputs** -- zerodep is 1.1-1.3x slower on the shortest inputs (5 chars, numeric), where `qrcode`'s encoding path has less overhead.
- Both are pure Python implementations. Unlike AES where system `libcrypto` can be used via ctypes, there is no universally pre-installed C library for QR code generation.
- For most applications, both are fast enough -- QR code generation is rarely a bottleneck. Even the largest case (1000 chars) completes in under 45 ms.

## Run It Yourself

```bash
pip install pytest pytest-benchmark qrcode
pytest qr/test_qr_benchmark.py --benchmark-only -v
```

---

## Latest CI Results

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/qr.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> Updated automatically on each release via [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml).
