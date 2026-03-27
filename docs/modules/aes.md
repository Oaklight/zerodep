# AES Encryption

AES-128-ECB encryption with PKCS7 padding -- zero dependencies, stdlib only, Python 3.10+.

## Overview

The AES module provides AES-128 encryption and decryption in ECB (Electronic Codebook) mode with automatic PKCS7 padding. Two interchangeable implementations are available:

| File | Description | Dependencies |
|------|-------------|--------------|
| `aes.py` | Pure Python implementation | None (stdlib only) |
| `aes_openssl.py` | Delegates to system OpenSSL via `ctypes` | System `libcrypto` at runtime |

Both files expose the **same public API**, so you can swap one for the other with no code changes.

## How to Use in Your Project

Just copy the single `.py` file you need into your project:

```bash
# Pure Python -- works everywhere
cp aes/aes.py your_project/

# OpenSSL -- much faster, requires system libcrypto
cp aes/aes_openssl.py your_project/
```

Then import directly:

```python
from aes import aes128_ecb_encrypt, aes128_ecb_decrypt
# or
from aes_openssl import aes128_ecb_encrypt, aes128_ecb_decrypt
```

## API Reference

### `aes128_ecb_encrypt(data, key)`

Encrypt data with AES-128-ECB and PKCS7 padding.

```python
def aes128_ecb_encrypt(data: bytes, key: bytes) -> bytes
```

**Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `data` | `bytes` | Plaintext bytes to encrypt. Can be any length. |
| `key` | `bytes` | 16-byte AES key. Must be exactly 16 bytes. |

**Returns:** `bytes` -- Ciphertext bytes. The length is always a multiple of 16 due to PKCS7 padding.

**Example:**

```python
key = b"0123456789abcdef"  # 16 bytes
ciphertext = aes128_ecb_encrypt(b"Hello, World!", key)
```

---

### `aes128_ecb_decrypt(data, key)`

Decrypt AES-128-ECB ciphertext and remove PKCS7 padding.

```python
def aes128_ecb_decrypt(data: bytes, key: bytes) -> bytes
```

**Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `data` | `bytes` | Ciphertext bytes. Must be a multiple of 16 bytes. |
| `key` | `bytes` | 16-byte AES key. Must match the key used for encryption. |

**Returns:** `bytes` -- Decrypted plaintext bytes with PKCS7 padding removed.

**Example:**

```python
plaintext = aes128_ecb_decrypt(ciphertext, key)
assert plaintext == b"Hello, World!"
```

## Usage Examples

### Basic Encrypt / Decrypt

```python
from aes import aes128_ecb_encrypt, aes128_ecb_decrypt

key = b"0123456789abcdef"
message = b"Hello, World!"

# Encrypt
ciphertext = aes128_ecb_encrypt(message, key)
print(f"Ciphertext ({len(ciphertext)} bytes): {ciphertext.hex()}")

# Decrypt
plaintext = aes128_ecb_decrypt(ciphertext, key)
assert plaintext == message
print(f"Plaintext: {plaintext.decode()}")
```

### Switching Between Implementations

```python
import importlib

def get_aes_module():
    """Prefer OpenSSL for speed; fall back to pure Python."""
    try:
        return importlib.import_module("aes_openssl")
    except OSError:
        return importlib.import_module("aes")

aes = get_aes_module()
ciphertext = aes.aes128_ecb_encrypt(b"secret data", b"0123456789abcdef")
```

### Encrypting a File

```python
from aes_openssl import aes128_ecb_encrypt, aes128_ecb_decrypt

key = b"sixteen byte key"

# Encrypt
with open("input.bin", "rb") as f:
    data = f.read()
ct = aes128_ecb_encrypt(data, key)
with open("input.bin.enc", "wb") as f:
    f.write(ct)

# Decrypt
with open("input.bin.enc", "rb") as f:
    ct = f.read()
pt = aes128_ecb_decrypt(ct, key)
with open("input.bin.dec", "wb") as f:
    f.write(pt)
```

## OpenSSL Variant Details

`aes_openssl.py` uses Python's built-in `ctypes` module to call the system's OpenSSL `libcrypto` library. It searches for the library in this order:

1. `ctypes.util.find_library("crypto")` -- the canonical cross-platform method.
2. Platform-specific fallback paths:
    - **Linux:** `libcrypto.so.3`, `libcrypto.so.1.1`, `libcrypto.so`
    - **macOS:** `/opt/homebrew/lib/libcrypto.dylib`, `/usr/local/lib/libcrypto.dylib`, `libcrypto.dylib`
    - **Windows:** `libcrypto-3-x64.dll`, `libcrypto-3.dll`, `libcrypto-1_1-x64.dll`, `libcrypto-1_1.dll`

If `libcrypto` cannot be found, an `OSError` is raised at **import time**.

## Notes and Caveats

!!! warning "ECB Mode Security"
    ECB mode encrypts each 16-byte block independently, which means identical plaintext blocks produce identical ciphertext blocks. This makes ECB **unsuitable for encrypting structured or repetitive data** where patterns should be hidden. Use ECB only when you specifically need it (e.g., compatibility with an existing protocol).

!!! info "Performance"
    The pure Python implementation (`aes.py`) is intentionally simple and educational. It is **orders of magnitude slower** than native implementations for large data. For any performance-sensitive workload, use `aes_openssl.py` instead.

- **Key length:** Must be exactly 16 bytes (128 bits). Passing a key of a different length will produce incorrect results or errors.
- **PKCS7 padding:** Applied automatically during encryption and stripped during decryption. You do not need to pad your data manually.
- **Python version:** Requires Python 3.10+ (uses `list[list[int]]` type hint syntax).
- **No IV:** ECB mode does not use an initialization vector.

## Benchmark

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

Run the benchmark yourself:

```bash
pytest aes/test_aes_benchmark.py --benchmark-only -v
```
