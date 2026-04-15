# QR Code Benchmark

Apple-to-apple performance comparison between zerodep QR implementation and the [`qrcode`](https://pypi.org/project/qrcode/) library (pure Python).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.10
    - **Tool:** pytest-benchmark (mean values reported)

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

## Encode Performance (Mean)

| Input | zerodep (`qr.py`) | `qrcode` library | Ratio |
|-------|---------------------|-------------------|-------|
| Short (5 chars) | 3.3 ms | 1.6 ms | 2.1x slower |
| URL (46 chars) | 8.7 ms | 4.5 ms | 1.9x slower |
| Long (200 chars) | 18.3 ms | 10.5 ms | 1.7x slower |

## Key Takeaways

- **zerodep** (`qr.py`) is approximately **~2x slower** than the `qrcode` library. The gap narrows with longer inputs (from 2.1x to 1.7x).
- Both are pure Python implementations. Unlike AES where system `libcrypto` can be used via ctypes, there is no universally pre-installed C library for QR code generation. zerodep prioritizes **correctness** and **zero-dependency** over raw speed.
- For most applications, both are fast enough -- QR code generation is rarely a bottleneck. Even the slowest case (200 chars) completes in under 20 ms.

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
