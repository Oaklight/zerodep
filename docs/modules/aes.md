# AES 加密

AES-128-ECB 加密与 PKCS7 填充 —— 零依赖。

## 变体

- `aes.py` —— 纯 Python 实现
- `aes_openssl.py` —— 通过 ctypes 调用 OpenSSL（更快，需要系统安装 libcrypto）

## 用法

```python
from aes import aes128_ecb_encrypt, aes128_ecb_decrypt

key = b"0123456789abcdef"
ciphertext = aes128_ecb_encrypt(key, b"Hello, World!")
plaintext = aes128_ecb_decrypt(key, ciphertext)
```

## 性能测试

与 `pycryptodome` 进行对比测试。详见[性能测试](../benchmarks.md)。
