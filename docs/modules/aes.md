# AES 加密

AES 加密，支持 ECB、CBC、CTR 和 GCM 模式，适用于 128/192/256 位密钥——零依赖，仅标准库，Python 3.10+。

## 概述

AES 模块提供多种模式和密钥长度的 AES 加解密功能。提供两个可互换的实现：

| 文件 | 说明 | 依赖 |
|------|------|------|
| `aes.py` | 纯 Python 实现 | 无（仅标准库） |
| `aes_openssl.py` | 通过 `ctypes` 调用系统 OpenSSL | 运行时需要系统安装 `libcrypto` |

两个文件暴露**完全相同的公开 API**，可以直接替换，无需修改调用代码。

### 支持的模式

| 模式 | 填充 | IV/Nonce | 适用场景 |
|------|------|----------|----------|
| **ECB** | PKCS7 | 无 | 简单加密（不推荐用于结构化数据） |
| **CBC** | PKCS7 | 16 字节 IV | 通用分组加密 |
| **CTR** | 无 | 16 字节 nonce | 流式加密，可并行化 |
| **GCM** | 无 | 12 字节 nonce（推荐） | 认证加密（AEAD） |

### 支持的密钥长度

所有模式均支持 AES-128（16 字节）、AES-192（24 字节）和 AES-256（32 字节）密钥。

## 如何在你的项目中使用

只需将所需的 `.py` 文件复制到你的项目中：

```bash
# 纯 Python -- 到处可用
cp aes/aes.py your_project/

# OpenSSL -- 快得多，需要系统安装 libcrypto
cp aes/aes_openssl.py your_project/
```

然后直接导入：

```python
from aes import aes_ecb_encrypt, aes_cbc_encrypt, aes_ctr_encrypt, aes_gcm_encrypt
# 或者
from aes_openssl import aes_ecb_encrypt, aes_cbc_encrypt, aes_ctr_encrypt, aes_gcm_encrypt
```

## 使用示例

### ECB 模式（基本加解密）

```python
from aes import aes_ecb_encrypt, aes_ecb_decrypt

key = b"0123456789abcdef"  # 16-byte key (AES-128)
message = b"Hello, World!"

ciphertext = aes_ecb_encrypt(message, key)
plaintext = aes_ecb_decrypt(ciphertext, key)
assert plaintext == message
```

同样支持 AES-192 和 AES-256：

```python
key_256 = b"0123456789abcdef" * 2  # 32-byte key (AES-256)
ciphertext = aes_ecb_encrypt(b"secret", key_256)
```

### CBC 模式

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

### CTR 模式

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

### GCM 模式（认证加密）

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

检测数据篡改：

```python
import pytest

tampered = bytes([ciphertext[0] ^ 0xFF]) + ciphertext[1:]
with pytest.raises(ValueError, match="authentication failed"):
    aes_gcm_decrypt(tampered, key, nonce, tag, aad=header)
```

### 在两个实现之间切换

```python
import importlib

def get_aes_module():
    """Prefer OpenSSL for speed; fall back to pure Python."""
    try:
        return importlib.import_module("aes_openssl")
    except OSError:
        return importlib.import_module("aes")

aes = get_aes_module()
ciphertext = aes.aes_ecb_encrypt(b"secret data", b"0123456789abcdef")
```

### 使用 CBC 加密文件

```python
import os
from aes_openssl import aes_cbc_encrypt, aes_cbc_decrypt

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

## API 参考

### ECB 模式

```python
aes_ecb_encrypt(data: bytes, key: bytes) -> bytes
aes_ecb_decrypt(data: bytes, key: bytes) -> bytes
aes_ecb_padded_size(plaintext_size: int) -> int
```

- **key**：16、24 或 32 字节
- PKCS7 填充自动应用
- `aes_ecb_padded_size()` 计算 PKCS7 填充后的密文大小，无需实际执行加密——适用于预分配缓冲区
- `aes128_ecb_encrypt` / `aes128_ecb_decrypt` 作为向后兼容的别名可用

### CBC 模式

```python
aes_cbc_encrypt(data: bytes, key: bytes, iv: bytes) -> bytes
aes_cbc_decrypt(data: bytes, key: bytes, iv: bytes) -> bytes
```

- **key**：16、24 或 32 字节
- **iv**：必须恰好 16 字节
- PKCS7 填充自动应用

### CTR 模式

```python
aes_ctr_encrypt(data: bytes, key: bytes, nonce: bytes) -> bytes
aes_ctr_decrypt(data: bytes, key: bytes, nonce: bytes) -> bytes
```

- **key**：16、24 或 32 字节
- **nonce**：16 字节初始计数器块
- 无填充——输出长度等于输入长度
- `aes_ctr_encrypt` 和 `aes_ctr_decrypt` 是同一个函数（CTR 模式加解密对称）

### GCM 模式

```python
aes_gcm_encrypt(data: bytes, key: bytes, nonce: bytes,
                aad: bytes = b"", tag_length: int = 16) -> tuple[bytes, bytes]
aes_gcm_decrypt(data: bytes, key: bytes, nonce: bytes,
                tag: bytes, aad: bytes = b"") -> bytes
```

- **key**：16、24 或 32 字节
- **nonce**：推荐 12 字节（支持任意长度）
- **aad**：附加认证数据（受完整性保护但不加密）
- **tag_length**：4-16 字节（默认 16）
- 加密时返回 `(ciphertext, tag)`
- 解密时若认证标签验证失败，抛出 `ValueError("authentication failed")`

## OpenSSL 变体细节

`aes_openssl.py` 使用 Python 内置的 `ctypes` 模块调用系统的 OpenSSL `libcrypto` 库。由于 Python 自身就依赖 OpenSSL（`ssl` 和 `hashlib` 模块都链接到 `libcrypto`），任何标准的 Python 3.10+ 安装都已经包含 `libcrypto`——无需额外安装任何软件。

运行时按以下顺序查找库文件：

1. `ctypes.util.find_library("crypto")` -- 跨平台标准方式。
2. 平台特定的回退路径：
    - **Linux:** `libcrypto.so.3`, `libcrypto.so.1.1`, `libcrypto.so`
    - **macOS:** `/opt/homebrew/lib/libcrypto.dylib`, `/usr/local/lib/libcrypto.dylib`, `libcrypto.dylib`
    - **Windows:** `libcrypto-3-x64.dll`, `libcrypto-3.dll`, `libcrypto-1_1-x64.dll`, `libcrypto-1_1.dll`

如果找不到 `libcrypto`，将在**导入时**抛出 `OSError`。

## 注意事项

!!! warning "ECB 模式的安全性"
    ECB 模式独立加密每个 16 字节的数据块，这意味着相同的明文块会产生相同的密文块。因此 ECB **不适合加密结构化或重复性数据**。请改用 CBC、CTR 或 GCM。

!!! tip "推荐模式"
    对于大多数应用场景，推荐使用 **GCM 模式**——它同时提供加密和认证（AEAD），能够防止窃听和篡改。GCM 也是 TLS 1.3 的默认加密模式。

!!! info "性能说明"
    纯 Python 实现（`aes.py`）设计简洁，偏重教学目的。对于大量数据，它比原生实现**慢数个数量级**。任何对性能敏感的场景，请使用 `aes_openssl.py`。

- **密钥长度：** 必须为 16、24 或 32 字节。传入无效长度的密钥会抛出 `ValueError`。
- **PKCS7 填充：** 在 ECB 和 CBC 模式下自动应用。CTR 和 GCM 不使用填充。
- **Python 版本：** 需要 Python 3.10+。
- **IV/nonce 管理：** IV 和 nonce 不会自动生成。请使用 `os.urandom()` 生成，并将其与密文一起存储或传输。

## 性能测试

与 `pycryptodome` 在 ECB、CBC、CTR 和 GCM 模式下进行对比。OpenSSL ctypes 比 pycryptodome 快约 2 倍；纯 Python 仅适合小数据量。

详见 [AES 性能测试](../benchmarks/aes.md)。
