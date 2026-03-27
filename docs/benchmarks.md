# Benchmarks

Apple-to-apple performance comparisons between zerodep implementations and their popular reference libraries.

All benchmarks use [`pytest-benchmark`](https://pytest-benchmark.readthedocs.io/). Results shown below were measured on the following environment:

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.10
    - **Tool:** pytest-benchmark (mean values reported)

Run the benchmarks on your own machine for accurate numbers:

```bash
# AES benchmarks (requires pycryptodome)
cd aes && pytest test_benchmark.py --benchmark-only

# QR benchmarks (requires qrcode)
cd qr && pytest test_benchmark.py --benchmark-only

# HTTP benchmarks (requires httpx)
cd httpclient && pytest test_benchmark.py --benchmark-only
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

### Encryption (Mean)

| Data Size | Pure Python | OpenSSL ctypes | pycryptodome |
|-----------|-------------|----------------|--------------|
| 13 B (small) | 75.4 us | 2.6 us | 5.5 us |
| 1 KB (medium) | 3,722 us (3.7 ms) | 9.9 us | 13.0 us |
| 64 KB (large) | 231,908 us (232 ms) | ~10 us | ~13 us |

### Decryption (Mean)

| Data Size | Pure Python | OpenSSL ctypes | pycryptodome |
|-----------|-------------|----------------|--------------|
| 16 B (small) | 96.7 us | 2.9 us | 5.8 us |
| 1 KB (medium) | 5,043 us (5.0 ms) | 11.3 us | 13.1 us |
| 64 KB (large) | 317,441 us (317 ms) | ~11 us | ~13 us |

### Key Takeaways

- **OpenSSL ctypes** (`aes_openssl.py`) is approximately **2x faster** than pycryptodome's C extension, while requiring zero pip dependencies -- only a system-installed `libcrypto`.
- **Pure Python** (`aes.py`) is ~30x slower than OpenSSL for small data and ~23,000x slower for 64 KB payloads. It is best suited for small amounts of data or when no native library is available.
- **pycryptodome** is fast but requires installing a compiled C extension via pip.

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

### Encode Performance (Mean)

| Input | zerodep (`qr.py`) | `qrcode` library | Ratio |
|-------|---------------------|-------------------|-------|
| Short (5 chars) | 3.3 ms | 1.6 ms | 2.1x slower |
| URL (46 chars) | 8.7 ms | 4.5 ms | 1.9x slower |
| Long (200 chars) | 18.3 ms | 10.5 ms | 1.7x slower |

### Key Takeaways

- **zerodep** (`qr.py`) is approximately **~2x slower** than the `qrcode` library. The gap narrows with longer inputs (from 2.1x to 1.7x).
- Both are pure Python implementations. zerodep prioritizes **correctness** and **zero-dependency** over raw speed.
- For most applications, both are fast enough -- QR code generation is rarely a bottleneck. Even the slowest case (200 chars) completes in under 20 ms.

---

## HTTP Client

**Reference library:** [`httpx`](https://pypi.org/project/httpx/) (with connection pooling)

| Implementation | File/Package | Description |
|----------------|--------------|-------------|
| **zerodep** | `httpclient.py` | stdlib-only HTTP/1.1 client |
| **httpx** | *(reference)* | Popular HTTP library with connection pooling |

### Performance Comparison (Mean)

| Test | zerodep | httpx | Notes |
|------|---------|-------|-------|
| Sync GET | ~1,100 ms | ~398 ms | httpx benefits from connection pooling |
| Sync POST JSON | ~1,086 ms | ~1,060 ms | Comparable (network-bound) |
| Sync Client GET | ~1,099 ms | ~1,088 ms | Comparable with session |
| Async GET | ~1,228 ms | ~1,178 ms | Comparable |
| Async POST JSON | ~1,133 ms | ~1,152 ms | Comparable |

### Key Takeaways

- For **one-off requests**, httpx is noticeably faster due to connection pooling.
- With **sessions or async**, performance is essentially identical since both implementations become network-bound.
- zerodep has **zero pip dependencies** -- it uses only `http.client` (sync) and `asyncio` streams (async) from the standard library.

---

## Running Benchmarks Yourself

Prerequisites:

```bash
pip install pytest pytest-benchmark pycryptodome qrcode httpx
```

Run all benchmarks:

```bash
# AES
cd aes
pytest test_benchmark.py --benchmark-only -v

# QR
cd qr
pytest test_benchmark.py --benchmark-only -v

# HTTP Client
cd httpclient
pytest test_benchmark.py --benchmark-only -v
```

For detailed output with statistics:

```bash
pytest test_benchmark.py --benchmark-only --benchmark-columns=mean,stddev,rounds
```
