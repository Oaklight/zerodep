# AES 加密

AES-128-ECB 加密与 PKCS7 填充 -- 零依赖，仅标准库，Python 3.10+。

## 概述

AES 模块提供 AES-128 在 ECB（电子密码本）模式下的加解密功能，自动进行 PKCS7 填充。提供两个可互换的实现：

| 文件 | 说明 | 依赖 |
|------|------|------|
| `aes.py` | 纯 Python 实现 | 无（仅标准库） |
| `aes_openssl.py` | 通过 `ctypes` 调用系统 OpenSSL | 运行时需要系统安装 `libcrypto` |

两个文件暴露**完全相同的公开 API**，可以直接替换，无需修改调用代码。

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
from aes import aes128_ecb_encrypt, aes128_ecb_decrypt
# 或者
from aes_openssl import aes128_ecb_encrypt, aes128_ecb_decrypt
```

## API 参考

### `aes128_ecb_encrypt(data, key)`

使用 AES-128-ECB 和 PKCS7 填充加密数据。

```python
def aes128_ecb_encrypt(data: bytes, key: bytes) -> bytes
```

**参数：**

| 名称 | 类型 | 说明 |
|------|------|------|
| `data` | `bytes` | 待加密的明文字节。可以是任意长度。 |
| `key` | `bytes` | 16 字节的 AES 密钥。必须恰好 16 字节。 |

**返回值：** `bytes` -- 密文字节。由于 PKCS7 填充，长度始终为 16 的整数倍。

**示例：**

```python
key = b"0123456789abcdef"  # 16 字节
ciphertext = aes128_ecb_encrypt(b"Hello, World!", key)
```

---

### `aes128_ecb_decrypt(data, key)`

解密 AES-128-ECB 密文并去除 PKCS7 填充。

```python
def aes128_ecb_decrypt(data: bytes, key: bytes) -> bytes
```

**参数：**

| 名称 | 类型 | 说明 |
|------|------|------|
| `data` | `bytes` | 密文字节。必须是 16 字节的整数倍。 |
| `key` | `bytes` | 16 字节的 AES 密钥。必须与加密时使用的密钥一致。 |

**返回值：** `bytes` -- 解密后的明文字节，已去除 PKCS7 填充。

**示例：**

```python
plaintext = aes128_ecb_decrypt(ciphertext, key)
assert plaintext == b"Hello, World!"
```

## 用法示例

### 基本加解密

```python
from aes import aes128_ecb_encrypt, aes128_ecb_decrypt

key = b"0123456789abcdef"
message = b"Hello, World!"

# 加密
ciphertext = aes128_ecb_encrypt(message, key)
print(f"密文 ({len(ciphertext)} 字节): {ciphertext.hex()}")

# 解密
plaintext = aes128_ecb_decrypt(ciphertext, key)
assert plaintext == message
print(f"明文: {plaintext.decode()}")
```

### 在两个实现之间切换

```python
import importlib

def get_aes_module():
    """优先使用 OpenSSL 以获得更好的性能；找不到时回退到纯 Python。"""
    try:
        return importlib.import_module("aes_openssl")
    except OSError:
        return importlib.import_module("aes")

aes = get_aes_module()
ciphertext = aes.aes128_ecb_encrypt(b"secret data", b"0123456789abcdef")
```

### 加密文件

```python
from aes_openssl import aes128_ecb_encrypt, aes128_ecb_decrypt

key = b"sixteen byte key"

# 加密
with open("input.bin", "rb") as f:
    data = f.read()
ct = aes128_ecb_encrypt(data, key)
with open("input.bin.enc", "wb") as f:
    f.write(ct)

# 解密
with open("input.bin.enc", "rb") as f:
    ct = f.read()
pt = aes128_ecb_decrypt(ct, key)
with open("input.bin.dec", "wb") as f:
    f.write(pt)
```

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
    ECB 模式独立加密每个 16 字节的数据块，这意味着相同的明文块会产生相同的密文块。因此 ECB **不适合加密结构化或重复性数据**，因为数据模式不会被隐藏。仅当你确实需要 ECB 时才使用它（例如兼容现有协议）。

!!! info "性能说明"
    纯 Python 实现（`aes.py`）设计简洁，偏重教学目的。对于大量数据，它比原生实现**慢数个数量级**。任何对性能敏感的场景，请使用 `aes_openssl.py`。

- **密钥长度：** 必须恰好 16 字节（128 位）。传入其他长度的密钥会产生错误结果或异常。
- **PKCS7 填充：** 加密时自动填充，解密时自动去除。你不需要手动处理填充。
- **Python 版本：** 需要 Python 3.10+（使用了 `list[list[int]]` 类型标注语法）。
- **无 IV：** ECB 模式不使用初始化向量。

## 性能测试

**参考库：** [`pycryptodome`](https://pypi.org/project/pycryptodome/)（C 扩展）

对比三种实现：

| 实现 | 文件 | 类型 |
|------|------|------|
| **纯 Python** | `aes.py` | 解释执行的 Python |
| **OpenSSL ctypes** | `aes_openssl.py` | 通过 ctypes 调用系统 libcrypto |
| **pycryptodome** | *（参考库）* | C 扩展 |

### 测试数据大小

| 标签 | 大小 | 说明 |
|------|------|------|
| 小 | 13 字节 | 短消息（`"Hello, World!"`） |
| 中 | 1 KB | 随机数据（`os.urandom(1024)`） |
| 大 | 64 KB | 随机数据（`os.urandom(65536)`） |

### 加密（均值）

| 数据大小 | 纯 Python | OpenSSL ctypes | pycryptodome |
|----------|-----------|----------------|--------------|
| 13 B（小） | 75.4 us | 2.6 us | 5.5 us |
| 1 KB（中） | 3,722 us (3.7 ms) | 9.9 us | 13.0 us |
| 64 KB（大） | 231,908 us (232 ms) | ~10 us | ~13 us |

### 解密（均值）

| 数据大小 | 纯 Python | OpenSSL ctypes | pycryptodome |
|----------|-----------|----------------|--------------|
| 16 B（小） | 96.7 us | 2.9 us | 5.8 us |
| 1 KB（中） | 5,043 us (5.0 ms) | 11.3 us | 13.1 us |
| 64 KB（大） | 317,441 us (317 ms) | ~11 us | ~13 us |

### 要点总结

- **OpenSSL ctypes**（`aes_openssl.py`）比 pycryptodome 的 C 扩展快约 **2 倍**，同时不需要任何 pip 依赖——只需系统安装 `libcrypto`。
- **纯 Python**（`aes.py`）小数据时比 OpenSSL 慢约 30 倍，64 KB 数据时慢约 23,000 倍。适合用于少量数据或没有原生库的环境。
- **pycryptodome** 速度很快，但需要通过 pip 安装编译的 C 扩展。

自行运行基准测试：

```bash
pytest aes/test_aes_benchmark.py --benchmark-only -v
```
