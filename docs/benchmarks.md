# 性能测试

zerodep 实现与常用参考库之间的同条件性能对比。

所有基准测试使用 [`pytest-benchmark`](https://pytest-benchmark.readthedocs.io/)。以下结果为参考值，实际数据会因硬件、Python 版本和系统负载而异。建议在你自己的机器上运行测试以获得准确数据：

```bash
# AES 基准测试（需要 pycryptodome）
cd aes && pytest test_benchmark.py --benchmark-only

# QR 基准测试（需要 qrcode）
cd qr && pytest test_benchmark.py --benchmark-only
```

---

## AES 加密

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

### 加密

| 数据大小 | 纯 Python | OpenSSL ctypes | pycryptodome |
|----------|-----------|----------------|--------------|
| 13 B | ~0.1 ms | ~0.005 ms | ~0.002 ms |
| 1 KB | ~7 ms | ~0.01 ms | ~0.003 ms |
| 64 KB | ~450 ms | ~0.15 ms | ~0.05 ms |

### 解密

| 数据大小 | 纯 Python | OpenSSL ctypes | pycryptodome |
|----------|-----------|----------------|--------------|
| 16 B | ~0.1 ms | ~0.005 ms | ~0.002 ms |
| 1 KB | ~7 ms | ~0.01 ms | ~0.003 ms |
| 64 KB | ~450 ms | ~0.15 ms | ~0.05 ms |

!!! note "估算值说明"
    以上数字是在典型 x86_64 机器、Python 3.12 环境下的数量级估算。请自行运行基准测试以获得你的硬件上的精确数据。

### 要点总结

- **纯 Python**（`aes.py`）处理大数据时比原生 C 慢约 1000 倍。适合用于少量数据或没有原生库的环境。
- **OpenSSL ctypes**（`aes_openssl.py`）性能在 pycryptodome C 扩展的 2--3 倍以内，同时不需要任何 pip 依赖 -- 只需系统安装 `libcrypto`。
- **pycryptodome** 是最快的选项，但需要安装编译的 C 扩展。

---

## QR Code 生成

**参考库：** [`qrcode`](https://pypi.org/project/qrcode/)（纯 Python）

两个实现都是纯 Python，因此对比的是两个解释执行的代码库之间的效率差异。

| 实现 | 文件/包 | 说明 |
|------|---------|------|
| **zerodep** | `qr.py` | 基于 Nayuki，单文件 |
| **qrcode** | *（参考库）* | 流行的 `qrcode` PyPI 包 |

### 测试输入

| 标签 | 内容 | 长度 |
|------|------|------|
| 短文本 | `"Hello"` | 5 字符 |
| URL | `"https://example.com/path?query=value&foo=bar"` | 46 字符 |
| 长文本 | `"A" * 200` | 200 字符 |

### 编码性能

| 输入 | zerodep（`qr.py`） | `qrcode` 库 |
|------|---------------------|-------------|
| 短文本（5 字符） | ~1.5 ms | ~3 ms |
| URL（46 字符） | ~3 ms | ~5 ms |
| 长文本（200 字符） | ~8 ms | ~12 ms |

!!! note "估算值说明"
    以上数字为数量级估算。两个库都是纯 Python 实现。实际比率可能因输入内容和选择的 QR 版本而异。

### 要点总结

- **zerodep**（`qr.py`）通常比 `qrcode` 库**更快**，一般快约 1.5--2 倍。
- 两者都是纯 Python 实现，性能差异来自算法效率而非原生代码。
- 对于大多数应用场景，两者都足够快 -- QR Code 生成很少成为性能瓶颈。

---

## 自行运行基准测试

前置依赖：

```bash
pip install pytest pytest-benchmark pycryptodome qrcode
```

运行所有基准测试：

```bash
# AES
cd aes
pytest test_benchmark.py --benchmark-only -v

# QR
cd qr
pytest test_benchmark.py --benchmark-only -v
```

输出详细统计信息：

```bash
pytest test_benchmark.py --benchmark-only --benchmark-columns=mean,stddev,rounds
```
