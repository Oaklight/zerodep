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

## Data Sizes Tested

| Label | Size | Description |
|-------|------|-------------|
| Small | 13 bytes | Short message (`"Hello, World!"`) |
| Medium | 1 KB | Random data (`os.urandom(1024)`) |
| Large | 64 KB | Random data (`os.urandom(65536)`) |

## Encryption (Mean)

| Data Size | Pure Python | OpenSSL ctypes | pycryptodome |
|-----------|-------------|----------------|--------------|
| 13 B (small) | 75.4 us | 2.6 us | 5.5 us |
| 1 KB (medium) | 3,722 us (3.7 ms) | 9.9 us | 13.0 us |
| 64 KB (large) | 231,908 us (232 ms) | ~10 us | ~13 us |

## Decryption (Mean)

| Data Size | Pure Python | OpenSSL ctypes | pycryptodome |
|-----------|-------------|----------------|--------------|
| 16 B (small) | 96.7 us | 2.9 us | 5.8 us |
| 1 KB (medium) | 5,043 us (5.0 ms) | 11.3 us | 13.1 us |
| 64 KB (large) | 317,441 us (317 ms) | ~11 us | ~13 us |

## Key Takeaways

- **OpenSSL ctypes** (`aes_openssl.py`) is approximately **2x faster** than pycryptodome's C extension, while requiring zero pip dependencies -- only a system-installed `libcrypto`.
- **Pure Python** (`aes.py`) is ~30x slower than OpenSSL for small data and ~23,000x slower for 64 KB payloads. It is best suited for small amounts of data or when no native library is available.
- **pycryptodome** is fast but requires installing a compiled C extension via pip.

## Run It Yourself

```bash
pip install pytest pytest-benchmark pycryptodome
pytest aes/test_aes_benchmark.py --benchmark-only -v
```
