# 性能测试

zerodep 实现与常用参考库之间的同条件性能对比。

所有基准测试使用 [`pytest-benchmark`](https://pytest-benchmark.readthedocs.io/)。以下结果在如下环境中测得：

!!! info "测试环境"
    - **CPU:** x86_64 Linux
    - **Python:** 3.10
    - **工具:** pytest-benchmark（报告均值）

建议在你自己的机器上运行测试以获得准确数据：

```bash
# AES 基准测试（需要 pycryptodome）
cd aes && pytest test_benchmark.py --benchmark-only

# QR 基准测试（需要 qrcode）
cd qr && pytest test_benchmark.py --benchmark-only

# HTTP 基准测试（需要 httpx）
cd httpclient && pytest test_benchmark.py --benchmark-only
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

### 编码性能（均值）

| 输入 | zerodep（`qr.py`） | `qrcode` 库 | 倍率 |
|------|---------------------|-------------|------|
| 短文本（5 字符） | 3.3 ms | 1.6 ms | 慢 2.1 倍 |
| URL（46 字符） | 8.7 ms | 4.5 ms | 慢 1.9 倍 |
| 长文本（200 字符） | 18.3 ms | 10.5 ms | 慢 1.7 倍 |

### 要点总结

- **zerodep**（`qr.py`）比 `qrcode` 库**慢约 2 倍**。随着输入变长，差距逐渐缩小（从 2.1 倍到 1.7 倍）。
- 两者都是纯 Python 实现。zerodep 优先保证**正确性**和**零依赖**，而非追求极致速度。
- 对于大多数应用场景，两者都足够快——QR Code 生成很少成为性能瓶颈。即使最慢的情况（200 字符）也在 20 ms 内完成。

---

## HTTP 客户端

**参考库：** [`httpx`](https://pypi.org/project/httpx/)（带连接池）

| 实现 | 文件/包 | 说明 |
|------|---------|------|
| **zerodep** | `httpclient.py` | 仅依赖标准库的 HTTP/1.1 客户端 |
| **httpx** | *（参考库）* | 带连接池的流行 HTTP 库 |

### 性能对比（均值）

| 测试项 | zerodep | httpx | 备注 |
|--------|---------|-------|------|
| 同步 GET | ~1,100 ms | ~398 ms | httpx 受益于连接池 |
| 同步 POST JSON | ~1,086 ms | ~1,060 ms | 基本持平（网络受限） |
| 同步 Client GET | ~1,099 ms | ~1,088 ms | 使用会话时基本持平 |
| 异步 GET | ~1,228 ms | ~1,178 ms | 基本持平 |
| 异步 POST JSON | ~1,133 ms | ~1,152 ms | 基本持平 |

### 要点总结

- **一次性请求**时，httpx 由于连接池明显更快。
- 使用**会话或异步**模式时，两者性能几乎一致，因为此时都受限于网络延迟。
- zerodep **无需任何 pip 依赖**——同步模式使用标准库 `http.client`，异步模式使用 `asyncio` 流。

---

## 自行运行基准测试

前置依赖：

```bash
pip install pytest pytest-benchmark pycryptodome qrcode httpx
```

运行所有基准测试：

```bash
# AES
cd aes
pytest test_benchmark.py --benchmark-only -v

# QR
cd qr
pytest test_benchmark.py --benchmark-only -v

# HTTP 客户端
cd httpclient
pytest test_benchmark.py --benchmark-only -v
```

输出详细统计信息：

```bash
pytest test_benchmark.py --benchmark-only --benchmark-columns=mean,stddev,rounds
```
