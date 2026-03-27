# AES Encryption

AES-128-ECB encryption with PKCS7 padding — zero dependencies.

## Variants

- `aes.py` — Pure Python implementation
- `aes_openssl.py` — OpenSSL via ctypes (faster, requires system libcrypto)

## Usage

```python
from aes import aes128_ecb_encrypt, aes128_ecb_decrypt

key = b"0123456789abcdef"
ciphertext = aes128_ecb_encrypt(key, b"Hello, World!")
plaintext = aes128_ecb_decrypt(key, ciphertext)
```

## Benchmark

Benchmarked against `pycryptodome`. See [Benchmarks](../benchmarks.md) for details.
