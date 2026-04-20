# AES Benchmark

Apple-to-apple performance comparison between zerodep AES implementations and [`pycryptodome`](https://pypi.org/project/pycryptodome/) (C extension).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)
    - **Reference:** pycryptodome 3.23.0
    - **Last Updated:** 2026-04-21

## Implementations

The AES module is a single file (`aes.py`) with automatic backend dispatch: **OpenSSL** (via ctypes) is used by default when `libcrypto` is available; a **pure-Python** fallback activates otherwise.

| Implementation | Backend | Type |
|----------------|---------|------|
| **OpenSSL ctypes** | `aes.py` (default) | System libcrypto via ctypes |
| **Pure Python** | `aes.py` (fallback) | Interpreted Python |
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

| Data Size | Pure Python | OpenSSL ctypes | pycryptodome | OpenSSL vs pycryptodome |
|-----------|-------------|----------------|--------------|------------------------|
| 13 B (small) | ~82 us | ~6.9 us | ~9.0 us | 1.3x faster |
| 1 KB (medium) | ~4,000 us | ~7.6 us | ~9.4 us | 1.2x faster |
| 64 KB (large) | ~250,000 us | ~20.3 us | ~21.3 us | ~1.0x (on par) |

## ECB Decryption (Mean)

| Data Size | Pure Python | OpenSSL ctypes | pycryptodome | OpenSSL vs pycryptodome |
|-----------|-------------|----------------|--------------|------------------------|
| 13 B (small) | ~109 us | ~6.9 us | ~9.5 us | 1.4x faster |
| 1 KB (medium) | ~5,500 us | ~7.5 us | ~9.5 us | 1.3x faster |
| 64 KB (large) | ~340,000 us | ~19.0 us | ~21.4 us | 1.1x faster |

## CBC Encryption (Mean)

| Data Size | Pure Python | OpenSSL ctypes | pycryptodome | OpenSSL vs pycryptodome |
|-----------|-------------|----------------|--------------|------------------------|
| 13 B (small) | ~85 us | ~6.8 us | ~10.0 us | 1.5x faster |
| 1 KB (medium) | ~4,200 us | ~7.5 us | ~11 us | 1.5x faster |
| 64 KB (large) | ~260,000 us | ~70 us | ~115 us | 1.6x faster |

## CBC Decryption (Mean)

| Data Size | Pure Python | OpenSSL ctypes | pycryptodome | OpenSSL vs pycryptodome |
|-----------|-------------|----------------|--------------|------------------------|
| 13 B (small) | ~110 us | ~7 us | ~10 us | 1.4x faster |
| 1 KB (medium) | ~5,600 us | ~7.5 us | ~12 us | 1.6x faster |
| 64 KB (large) | ~350,000 us | ~19.4 us | ~133.7 us | 6.9x faster |

## CTR Encryption (Mean)

| Data Size | Pure Python | OpenSSL ctypes | pycryptodome | OpenSSL vs pycryptodome |
|-----------|-------------|----------------|--------------|------------------------|
| 13 B (small) | ~84 us | ~7 us | ~11 us | 1.6x faster |
| 1 KB (medium) | ~4,100 us | ~7.5 us | ~13 us | 1.7x faster |
| 64 KB (large) | ~255,000 us | ~21 us | ~100 us | 4.8x faster |

## GCM Encryption (Mean)

| Data Size | Pure Python | OpenSSL ctypes | pycryptodome | OpenSSL vs pycryptodome |
|-----------|-------------|----------------|--------------|------------------------|
| 13 B (small) | ~250 us | ~9.5 us | ~56.6 us | 6.0x faster |
| 1 KB (medium) | ~5,600 us | ~10 us | ~58 us | 5.8x faster |
| 64 KB (large) | ~350,000 us | ~30 us | ~160 us | 5.3x faster |

## GCM Decryption (Mean)

| Data Size | Pure Python | OpenSSL ctypes | pycryptodome | OpenSSL vs pycryptodome |
|-----------|-------------|----------------|--------------|------------------------|
| 13 B (small) | ~248 us | ~9.5 us | ~60 us | 6.3x faster |
| 1 KB (medium) | ~5,700 us | ~10 us | ~62 us | 6.2x faster |
| 64 KB (large) | ~350,000 us | ~30.9 us | ~165.0 us | 5.3x faster |

## Key Takeaways

- **OpenSSL ctypes** is the default backend and consistently outperforms pycryptodome's C extension: **1.1--1.5x faster** in ECB/CBC for small-to-medium data, scaling up to **6.9x faster** for large CBC decryption. In **GCM mode** the advantage is most pronounced at **5.3--6.3x faster**. All of this requires zero pip dependencies -- only a system-installed `libcrypto`.
- **Pure Python** fallback is ~10x slower than pycryptodome for small messages and 300--500x slower for medium/large data. This is expected for interpreted Python vs compiled C and serves as a last-resort fallback when no native library is available.
- **GCM mode** in pure Python includes GF(2^128) multiplication, making it the slowest pure-Python mode (~250 us for 13 bytes vs ~82--85 us for ECB/CBC). The OpenSSL backend shows no such penalty.
- **pycryptodome** is fast (C extension) but requires a compiled dependency via pip. OpenSSL ctypes matches or beats it in every scenario tested.

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
