# AES Benchmark

Apple-to-apple performance comparison between zerodep AES implementations and [`pycryptodome`](https://pypi.org/project/pycryptodome/) (C extension).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)
    - **Reference:** pycryptodome 3.23.0
    - **Last Updated:** 2026-04-15

## Implementations

| Implementation | File | Type |
|----------------|------|------|
| **OpenSSL ctypes** | `aes.py` | System libcrypto via ctypes (default) |
| **Pure Python** | `aes_python.py` | Interpreted Python |
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
| 13 B (small) | ~71 us | ~5 us | ~7 us | 1.5x faster |
| 1 KB (medium) | ~3,546 us | ~5 us | ~8 us | 1.4x faster |
| 64 KB (large) | ~226,004 us | ~21 us | ~21 us | ~1.0x (on par) |

## ECB Decryption (Mean)

| Data Size | Pure Python | OpenSSL ctypes | pycryptodome | OpenSSL vs pycryptodome |
|-----------|-------------|----------------|--------------|------------------------|
| 13 B (small) | ~92 us | ~5 us | ~7 us | 1.5x faster |
| 1 KB (medium) | ~4,958 us | ~6 us | ~8 us | 1.5x faster |
| 64 KB (large) | ~309,896 us | ~19 us | ~22 us | 1.1x faster |

## CBC Encryption (Mean)

| Data Size | Pure Python | OpenSSL ctypes | pycryptodome | OpenSSL vs pycryptodome |
|-----------|-------------|----------------|--------------|------------------------|
| 13 B (small) | ~74 us | ~5 us | ~9 us | 1.7x faster |
| 1 KB (medium) | ~3,762 us | ~6 us | ~11 us | 1.7x faster |
| 64 KB (large) | ~232,631 us | ~68 us | ~110 us | 1.6x faster |

## CBC Decryption (Mean)

| Data Size | Pure Python | OpenSSL ctypes | pycryptodome | OpenSSL vs pycryptodome |
|-----------|-------------|----------------|--------------|------------------------|
| 13 B (small) | ~94 us | ~5 us | ~9 us | 1.7x faster |
| 1 KB (medium) | ~5,069 us | ~6 us | ~11 us | 1.9x faster |
| 64 KB (large) | ~319,752 us | ~19 us | ~111 us | 5.7x faster |

## CTR Encryption (Mean)

| Data Size | Pure Python | OpenSSL ctypes | pycryptodome | OpenSSL vs pycryptodome |
|-----------|-------------|----------------|--------------|------------------------|
| 13 B (small) | ~72 us | ~5 us | ~10 us | 1.9x faster |
| 1 KB (medium) | ~3,652 us | ~6 us | ~12 us | 2.0x faster |
| 64 KB (large) | ~234,149 us | ~21 us | ~97 us | 4.6x faster |

## GCM Encryption (Mean)

| Data Size | Pure Python | OpenSSL ctypes | pycryptodome | OpenSSL vs pycryptodome |
|-----------|-------------|----------------|--------------|------------------------|
| 13 B (small) | ~232 us | ~7 us | ~43 us | 6.4x faster |
| 1 KB (medium) | ~5,225 us | ~8 us | ~46 us | 6.1x faster |
| 64 KB (large) | ~327,032 us | ~27 us | ~142 us | 5.3x faster |

## GCM Decryption (Mean)

| Data Size | Pure Python | OpenSSL ctypes | pycryptodome | OpenSSL vs pycryptodome |
|-----------|-------------|----------------|--------------|------------------------|
| 13 B (small) | ~229 us | ~7 us | ~58 us | 8.8x faster |
| 1 KB (medium) | ~5,254 us | ~8 us | ~61 us | 8.1x faster |
| 64 KB (large) | ~326,058 us | ~26 us | ~157 us | 6.1x faster |

## Key Takeaways

- **OpenSSL ctypes** (`aes.py`) consistently outperforms pycryptodome's C extension: **1.1--1.9x faster** in ECB/CBC/CTR for small-to-medium data, scaling up to **4.6--5.7x faster** for large payloads in CBC/CTR. In **GCM mode** the advantage is most pronounced at **5.3--8.8x faster**. All of this requires zero pip dependencies -- only a system-installed `libcrypto`.
- **Pure Python** (`aes_python.py`) is 7--14,000x slower than pycryptodome depending on mode and data size. Even for 13-byte messages it takes ~71--232 us (vs ~5--7 us for OpenSSL). It is educational and serves as a fallback when no native library is available.
- **GCM mode** in pure Python includes GF(2^128) multiplication, making it the slowest pure-Python mode (~232 us for 13 bytes vs ~71--74 us for ECB/CBC). The OpenSSL variant shows no such penalty.
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
