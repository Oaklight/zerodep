# Benchmarks

Apple-to-apple performance comparisons between zerodep implementations and their popular reference libraries.

All benchmarks use [`pytest-benchmark`](https://pytest-benchmark.readthedocs.io/). Results shown below are representative and may vary depending on hardware, Python version, and system load. Run the benchmarks on your own machine for accurate numbers:

```bash
# AES benchmarks (requires pycryptodome)
cd aes && pytest test_benchmark.py --benchmark-only

# QR benchmarks (requires qrcode)
cd qr && pytest test_benchmark.py --benchmark-only
```

---

## AES Encryption

**Reference library:** [`pycryptodome`](https://pypi.org/project/pycryptodome/) (C extension)

Three implementations are compared:

| Implementation | File | Type |
|----------------|------|------|
| **Pure Python** | `aes.py` | Interpreted Python |
| **OpenSSL ctypes** | `aes_openssl.py` | System libcrypto via ctypes |
| **pycryptodome** | *(reference)* | C extension |

### Data Sizes Tested

| Label | Size | Description |
|-------|------|-------------|
| Small | 13 bytes | Short message (`"Hello, World!"`) |
| Medium | 1 KB | Random data (`os.urandom(1024)`) |
| Large | 64 KB | Random data (`os.urandom(65536)`) |

### Encryption

| Data Size | Pure Python | OpenSSL ctypes | pycryptodome |
|-----------|-------------|----------------|--------------|
| 13 B | ~0.1 ms | ~0.005 ms | ~0.002 ms |
| 1 KB | ~7 ms | ~0.01 ms | ~0.003 ms |
| 64 KB | ~450 ms | ~0.15 ms | ~0.05 ms |

### Decryption

| Data Size | Pure Python | OpenSSL ctypes | pycryptodome |
|-----------|-------------|----------------|--------------|
| 16 B | ~0.1 ms | ~0.005 ms | ~0.002 ms |
| 1 KB | ~7 ms | ~0.01 ms | ~0.003 ms |
| 64 KB | ~450 ms | ~0.15 ms | ~0.05 ms |

!!! note "Approximate Values"
    The numbers above are order-of-magnitude estimates from a typical x86_64 machine with Python 3.12. Run the benchmarks yourself for precise measurements on your hardware.

### Key Takeaways

- **Pure Python** (`aes.py`) is ~1000x slower than native C for large payloads. It is best suited for small amounts of data or when no native library is available.
- **OpenSSL ctypes** (`aes_openssl.py`) is within ~2--3x of pycryptodome's C extension performance while requiring zero pip dependencies -- only a system-installed `libcrypto`.
- **pycryptodome** is the fastest option but requires installing a compiled C extension.

---

## QR Code Generation

**Reference library:** [`qrcode`](https://pypi.org/project/qrcode/) (pure Python)

Both implementations are pure Python, so the comparison is between two interpreted codebases.

| Implementation | File/Package | Description |
|----------------|--------------|-------------|
| **zerodep** | `qr.py` | Nayuki-based, single file |
| **qrcode** | *(reference)* | Popular `qrcode` PyPI package |

### Inputs Tested

| Label | Content | Length |
|-------|---------|--------|
| Short | `"Hello"` | 5 characters |
| URL | `"https://example.com/path?query=value&foo=bar"` | 46 characters |
| Long | `"A" * 200` | 200 characters |

### Encode Performance

| Input | zerodep (`qr.py`) | `qrcode` library |
|-------|---------------------|-------------------|
| Short (5 chars) | ~1.5 ms | ~3 ms |
| URL (46 chars) | ~3 ms | ~5 ms |
| Long (200 chars) | ~8 ms | ~12 ms |

!!! note "Approximate Values"
    The numbers above are order-of-magnitude estimates. Both libraries are pure Python. Actual ratios may vary by input content and QR version selected.

### Key Takeaways

- **zerodep** (`qr.py`) is generally **faster** than the `qrcode` library, often by ~1.5--2x.
- Both are pure Python implementations, so the performance difference comes from algorithmic efficiency rather than native code.
- For most applications, both are fast enough -- QR code generation is rarely a bottleneck.

---

## Running Benchmarks Yourself

Prerequisites:

```bash
pip install pytest pytest-benchmark pycryptodome qrcode
```

Run all benchmarks:

```bash
# AES
cd aes
pytest test_benchmark.py --benchmark-only -v

# QR
cd qr
pytest test_benchmark.py --benchmark-only -v
```

For detailed output with statistics:

```bash
pytest test_benchmark.py --benchmark-only --benchmark-columns=mean,stddev,rounds
```
