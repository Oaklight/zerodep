# AES Benchmark

Apple-to-apple performance comparison between zerodep AES implementations and [`pycryptodome`](https://pypi.org/project/pycryptodome/) (C extension).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.10
    - **Tool:** pytest-benchmark (mean values reported)

## Implementations

| Implementation | File | Type |
|----------------|------|------|
| **Pure Python** | `aes.py` | Interpreted Python |
| **OpenSSL ctypes** | `aes_openssl.py` | System libcrypto via ctypes |
| **pycryptodome** | *(reference)* | C extension |

## Modes Tested

| Mode | Description |
|------|-------------|
| ECB | Electronic Codebook (PKCS7 padding) |
| CBC | Cipher Block Chaining (PKCS7 padding) |
| CTR | Counter mode (no padding) |
| GCM | Galois/Counter Mode (authenticated encryption) |

## Data Sizes

| Label | Size | Description |
|-------|------|-------------|
| Small | 13 bytes | Short message (`"Hello, World!"`) |
| Medium | 1 KB | Random data (`os.urandom(1024)`) |
| Large | 64 KB | Random data (`os.urandom(64 * 1024)`) |

## ECB Encryption (Mean)

| Data Size | Pure Python | OpenSSL ctypes | pycryptodome |
|-----------|-------------|----------------|--------------|
| 13 B (small) | ~75 us | ~3 us | ~6 us |
| 1 KB (medium) | ~3,700 us | ~3 us | ~6 us |
| 64 KB (large) | ~233,000 us | ~11 us | ~13 us |

## CBC Encryption (Mean)

| Data Size | Pure Python | OpenSSL ctypes | pycryptodome |
|-----------|-------------|----------------|--------------|
| 13 B (small) | ~100 us | ~3 us | ~6 us |
| 1 KB (medium) | ~3,800 us | ~4 us | ~8 us |
| 64 KB (large) | ~237,000 us | ~36 us | ~62 us |

## CTR Encryption (Mean)

| Data Size | Pure Python | OpenSSL ctypes | pycryptodome |
|-----------|-------------|----------------|--------------|
| 13 B (small) | ~75 us | ~3 us | ~8 us |
| 1 KB (medium) | ~3,800 us | ~3 us | ~8 us |
| 64 KB (large) | ~240,000 us | ~11 us | ~54 us |

## GCM Encryption (Mean)

| Data Size | Pure Python | OpenSSL ctypes | pycryptodome |
|-----------|-------------|----------------|--------------|
| 13 B (small) | ~220 us | ~4 us | ~35 us |
| 1 KB (medium) | ~4,800 us | ~4 us | ~35 us |
| 64 KB (large) | ~292,000 us | ~15 us | ~88 us |

## Key Takeaways

- **OpenSSL ctypes** (`aes_openssl.py`) is approximately **2x faster** than pycryptodome's C extension across all modes, while requiring zero pip dependencies -- only a system-installed `libcrypto`.
- **Pure Python** (`aes.py`) is ~30x slower than OpenSSL for small data and orders of magnitude slower for larger payloads. It is best suited for small amounts of data or when no native library is available.
- **GCM mode** in pure Python includes GF(2^128) multiplication, making it the slowest pure-Python mode. The OpenSSL variant shows no such penalty.
- **pycryptodome** is fast but requires installing a compiled C extension via pip.

## Run It Yourself

```bash
pip install pytest pytest-benchmark pycryptodome
pytest aes/test_aes_benchmark.py --benchmark-only -v
```

---

## Latest CI Results

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/aes.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> Updated automatically on each release via [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml).
