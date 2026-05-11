# AES Encryption

AES encryption with ECB, CBC, CTR, and GCM modes for 128/192/256-bit keys -- zero dependencies, stdlib only, Python 3.10+.

> **Replaces:** `pycryptodome` (AES), `cryptography` (AES)

## Overview

The AES module provides AES encryption and decryption across multiple modes and key sizes. Two interchangeable implementations are available:

| File | Description | Dependencies |
|------|-------------|--------------|
| `aes.py` | OpenSSL via `ctypes` (default) | System `libcrypto` at runtime |
| `aes_python.py` | Pure Python implementation | None (stdlib only) |

Both files expose the **same public API**, so you can swap one for the other with no code changes.

### Supported Modes

| Mode | Padding | IV/Nonce | Use Case |
|------|---------|----------|----------|
| **ECB** | PKCS7 | None | Simple encryption (not recommended for structured data) |
| **CBC** | PKCS7 | 16-byte IV | General-purpose block encryption |
| **CTR** | None | 16-byte nonce | Stream-like encryption, parallelizable |
| **GCM** | None | 12-byte nonce (recommended) | Authenticated encryption (AEAD) |

### Supported Key Sizes

All modes support AES-128 (16 bytes), AES-192 (24 bytes), and AES-256 (32 bytes) keys.

## How to Use in Your Project

Just copy the single `.py` file you need into your project:

```bash
# Copy the whole package (OpenSSL default, pure-Python fallback)
zerodep add aes --nested

# Or copy individual files
cp aes/aes.py your_project/          # OpenSSL (default)
cp aes/aes_python.py your_project/   # Pure Python fallback
```

Then import directly -- the package prefers OpenSSL and falls back to pure Python automatically:

```python
from aes import aes_ecb_encrypt, aes_cbc_encrypt, aes_ctr_encrypt, aes_gcm_encrypt
from aes import BACKEND  # "openssl" or "python"
```

## Usage Examples

### ECB Mode (Basic Encrypt / Decrypt)

```python
from aes import aes_ecb_encrypt, aes_ecb_decrypt

key = b"0123456789abcdef"  # 16-byte key (AES-128)
message = b"Hello, World!"

ciphertext = aes_ecb_encrypt(message, key)
plaintext = aes_ecb_decrypt(ciphertext, key)
assert plaintext == message
```

Works with AES-192 and AES-256 too:

```python
key_256 = b"0123456789abcdef" * 2  # 32-byte key (AES-256)
ciphertext = aes_ecb_encrypt(b"secret", key_256)
```

### CBC Mode

```python
import os
from aes import aes_cbc_encrypt, aes_cbc_decrypt

key = os.urandom(32)   # AES-256
iv = os.urandom(16)    # 16-byte IV
message = b"Confidential data"

ciphertext = aes_cbc_encrypt(message, key, iv)
plaintext = aes_cbc_decrypt(ciphertext, key, iv)
assert plaintext == message
```

### CTR Mode

```python
import os
from aes import aes_ctr_encrypt, aes_ctr_decrypt

key = os.urandom(16)
nonce = os.urandom(16)  # 16-byte initial counter block
data = b"Stream cipher style"

ciphertext = aes_ctr_encrypt(data, key, nonce)
assert len(ciphertext) == len(data)  # No padding needed

plaintext = aes_ctr_decrypt(ciphertext, key, nonce)
assert plaintext == data
```

### GCM Mode (Authenticated Encryption)

```python
import os
from aes import aes_gcm_encrypt, aes_gcm_decrypt

key = os.urandom(32)     # AES-256
nonce = os.urandom(12)   # 12-byte nonce (recommended)
header = b"metadata"     # Additional Authenticated Data (AAD)
message = b"Secret payload"

# Encrypt -- returns (ciphertext, authentication_tag)
ciphertext, tag = aes_gcm_encrypt(message, key, nonce, aad=header)

# Decrypt -- raises ValueError if tampered
plaintext = aes_gcm_decrypt(ciphertext, key, nonce, tag, aad=header)
assert plaintext == message
```

Detect tampering:

```python
import pytest

tampered = bytes([ciphertext[0] ^ 0xFF]) + ciphertext[1:]
with pytest.raises(ValueError, match="authentication failed"):
    aes_gcm_decrypt(tampered, key, nonce, tag, aad=header)
```

### Checking the Active Backend

The `__init__.py` automatically selects OpenSSL when available, falling back to pure Python. You can check which backend is active:

```python
from aes import BACKEND, aes_ecb_encrypt

print(BACKEND)  # "openssl" or "python"
ciphertext = aes_ecb_encrypt(b"secret data", b"0123456789abcdef")
```

### Encrypting a File with CBC

```python
import os
from aes import aes_cbc_encrypt, aes_cbc_decrypt

key = os.urandom(32)
iv = os.urandom(16)

# Encrypt
with open("input.bin", "rb") as f:
    data = f.read()
ct = aes_cbc_encrypt(data, key, iv)
with open("input.bin.enc", "wb") as f:
    f.write(iv + ct)  # Prepend IV for later retrieval

# Decrypt
with open("input.bin.enc", "rb") as f:
    raw = f.read()
iv_read, ct_read = raw[:16], raw[16:]
pt = aes_cbc_decrypt(ct_read, key, iv_read)
```

## API Reference

### ECB Mode

```python
aes_ecb_encrypt(data: bytes, key: bytes) -> bytes
aes_ecb_decrypt(data: bytes, key: bytes) -> bytes
aes_ecb_padded_size(plaintext_size: int) -> int
```

- **key**: 16, 24, or 32 bytes
- PKCS7 padding applied automatically
- `aes_ecb_padded_size()` calculates the ciphertext size after PKCS7 padding without performing encryption -- useful for pre-allocating buffers
- `aes128_ecb_encrypt` / `aes128_ecb_decrypt` are available as backward-compatible aliases

### CBC Mode

```python
aes_cbc_encrypt(data: bytes, key: bytes, iv: bytes) -> bytes
aes_cbc_decrypt(data: bytes, key: bytes, iv: bytes) -> bytes
```

- **key**: 16, 24, or 32 bytes
- **iv**: Must be exactly 16 bytes
- PKCS7 padding applied automatically

### CTR Mode

```python
aes_ctr_encrypt(data: bytes, key: bytes, nonce: bytes) -> bytes
aes_ctr_decrypt(data: bytes, key: bytes, nonce: bytes) -> bytes
```

- **key**: 16, 24, or 32 bytes
- **nonce**: 16-byte initial counter block
- No padding -- output length equals input length
- `aes_ctr_encrypt` and `aes_ctr_decrypt` are the same function (CTR is symmetric)

### GCM Mode

```python
aes_gcm_encrypt(data: bytes, key: bytes, nonce: bytes,
                aad: bytes = b"", tag_length: int = 16) -> tuple[bytes, bytes]
aes_gcm_decrypt(data: bytes, key: bytes, nonce: bytes,
                tag: bytes, aad: bytes = b"") -> bytes
```

- **key**: 16, 24, or 32 bytes
- **nonce**: 12 bytes recommended (arbitrary length supported)
- **aad**: Additional Authenticated Data (integrity-protected but not encrypted)
- **tag_length**: 4-16 bytes (default 16)
- Returns `(ciphertext, tag)` on encrypt
- Raises `ValueError("authentication failed")` on decrypt if tag verification fails

## OpenSSL Variant Details

`aes.py` (the OpenSSL variant) uses Python's built-in `ctypes` module to call the system's OpenSSL `libcrypto` library. Since Python itself depends on OpenSSL (`ssl` and `hashlib` modules link against `libcrypto`), any standard Python 3.10+ installation already has `libcrypto` available -- no additional software needs to be installed.

The library is located at runtime in this order:

1. `ctypes.util.find_library("crypto")` -- the canonical cross-platform method.
2. Platform-specific fallback paths:
    - **Linux:** `libcrypto.so.3`, `libcrypto.so.1.1`, `libcrypto.so`
    - **macOS:** `/opt/homebrew/lib/libcrypto.dylib`, `/usr/local/lib/libcrypto.dylib`, `libcrypto.dylib`
    - **Windows:** `libcrypto-3-x64.dll`, `libcrypto-3.dll`, `libcrypto-1_1-x64.dll`, `libcrypto-1_1.dll`

If `libcrypto` cannot be found, an `OSError` is raised at **import time**.

## Notes and Caveats

!!! warning "ECB Mode Security"
    ECB mode encrypts each 16-byte block independently, which means identical plaintext blocks produce identical ciphertext blocks. This makes ECB **unsuitable for encrypting structured or repetitive data**. Use CBC, CTR, or GCM instead.

!!! tip "Recommended Mode"
    For most applications, use **GCM mode** -- it provides both encryption and authentication (AEAD), preventing both eavesdropping and tampering. It is the default in TLS 1.3.

!!! info "Performance"
    The pure Python implementation (`aes_python.py`) is intentionally simple and educational. It is **orders of magnitude slower** than native implementations for large data. For any performance-sensitive workload, use the default `aes.py` (OpenSSL) instead.

- **Key length:** Must be 16, 24, or 32 bytes. Invalid lengths raise `ValueError`.
- **PKCS7 padding:** Applied automatically in ECB and CBC modes. CTR and GCM do not use padding.
- **Python version:** Requires Python 3.10+.
- **IV/nonce management:** IVs and nonces are never auto-generated. Use `os.urandom()` to generate them and store/transmit them alongside the ciphertext.

## Benchmark

Benchmarked against `pycryptodome` across ECB, CBC, CTR, and GCM modes. OpenSSL ctypes is ~2x faster than pycryptodome; pure Python is suited for small data only.

See [AES Benchmark](../benchmarks/aes.md) for detailed results.
