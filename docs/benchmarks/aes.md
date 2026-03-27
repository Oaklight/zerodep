# AES 性能测试

zerodep AES 实现与 [`pycryptodome`](https://pypi.org/project/pycryptodome/)（C 扩展）的同条件性能对比。

!!! info "测试环境"
    - **CPU:** x86_64 Linux
    - **Python:** 3.10
    - **工具:** pytest-benchmark（报告均值）

## 实现对比

| 实现 | 文件 | 类型 |
|------|------|------|
| **纯 Python** | `aes.py` | 解释执行的 Python |
| **OpenSSL ctypes** | `aes_openssl.py` | 通过 ctypes 调用系统 libcrypto |
| **pycryptodome** | *（参考库）* | C 扩展 |

## 测试数据大小

| 标签 | 大小 | 说明 |
|------|------|------|
| 小 | 13 字节 | 短消息（`"Hello, World!"`） |
| 中 | 1 KB | 随机数据（`os.urandom(1024)`） |
| 大 | 64 KB | 随机数据（`os.urandom(65536)`） |

## 加密（均值）

| 数据大小 | 纯 Python | OpenSSL ctypes | pycryptodome |
|----------|-----------|----------------|--------------|
| 13 B（小） | 75.4 us | 2.6 us | 5.5 us |
| 1 KB（中） | 3,722 us (3.7 ms) | 9.9 us | 13.0 us |
| 64 KB（大） | 231,908 us (232 ms) | ~10 us | ~13 us |

## 解密（均值）

| 数据大小 | 纯 Python | OpenSSL ctypes | pycryptodome |
|----------|-----------|----------------|--------------|
| 16 B（小） | 96.7 us | 2.9 us | 5.8 us |
| 1 KB（中） | 5,043 us (5.0 ms) | 11.3 us | 13.1 us |
| 64 KB（大） | 317,441 us (317 ms) | ~11 us | ~13 us |

## 要点总结

- **OpenSSL ctypes**（`aes_openssl.py`）比 pycryptodome 的 C 扩展快约 **2 倍**，同时不需要任何 pip 依赖——只需系统安装 `libcrypto`。
- **纯 Python**（`aes.py`）小数据时比 OpenSSL 慢约 30 倍，64 KB 数据时慢约 23,000 倍。适合用于少量数据或没有原生库的环境。
- **pycryptodome** 速度很快，但需要通过 pip 安装编译的 C 扩展。

## 自行运行

```bash
pip install pytest pytest-benchmark pycryptodome
pytest aes/test_aes_benchmark.py --benchmark-only -v
```
