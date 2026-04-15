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

## 测试模式

| 模式 | 说明 |
|------|------|
| ECB | 电子密码本模式（PKCS7 填充） |
| CBC | 密码块链接模式（PKCS7 填充） |
| CTR | 计数器模式（无填充） |
| GCM | Galois/Counter 模式（认证加密） |

## 测试数据大小

| 标签 | 大小 | 说明 |
|------|------|------|
| 小 | 13 字节 | 短消息（`"Hello, World!"`） |
| 中 | 1 KB | 随机数据（`os.urandom(1024)`） |
| 大 | 64 KB | 随机数据（`os.urandom(64 * 1024)`） |

## ECB 加密（均值）

| 数据大小 | 纯 Python | OpenSSL ctypes | pycryptodome |
|----------|-----------|----------------|--------------|
| 13 B（小） | ~75 us | ~3 us | ~6 us |
| 1 KB（中） | ~3,700 us | ~3 us | ~6 us |
| 64 KB（大） | ~233,000 us | ~11 us | ~13 us |

## CBC 加密（均值）

| 数据大小 | 纯 Python | OpenSSL ctypes | pycryptodome |
|----------|-----------|----------------|--------------|
| 13 B（小） | ~100 us | ~3 us | ~6 us |
| 1 KB（中） | ~3,800 us | ~4 us | ~8 us |
| 64 KB（大） | ~237,000 us | ~36 us | ~62 us |

## CTR 加密（均值）

| 数据大小 | 纯 Python | OpenSSL ctypes | pycryptodome |
|----------|-----------|----------------|--------------|
| 13 B（小） | ~75 us | ~3 us | ~8 us |
| 1 KB（中） | ~3,800 us | ~3 us | ~8 us |
| 64 KB（大） | ~240,000 us | ~11 us | ~54 us |

## GCM 加密（均值）

| 数据大小 | 纯 Python | OpenSSL ctypes | pycryptodome |
|----------|-----------|----------------|--------------|
| 13 B（小） | ~220 us | ~4 us | ~35 us |
| 1 KB（中） | ~4,800 us | ~4 us | ~35 us |
| 64 KB（大） | ~292,000 us | ~15 us | ~88 us |

## 要点总结

- **OpenSSL ctypes**（`aes_openssl.py`）在所有模式下均比 pycryptodome 的 C 扩展快约 **2 倍**，同时不需要任何 pip 依赖——只需系统安装 `libcrypto`。
- **纯 Python**（`aes.py`）小数据时比 OpenSSL 慢约 30 倍，大数据时差距更大。适合用于少量数据或没有原生库的环境。
- **GCM 模式** 的纯 Python 实现包含 GF(2^128) 乘法运算，是最慢的纯 Python 模式。OpenSSL 变体则没有此开销。
- **pycryptodome** 速度很快，但需要通过 pip 安装编译的 C 扩展。

## 自行运行

```bash
pip install pytest pytest-benchmark pycryptodome
pytest aes/test_aes_benchmark.py --benchmark-only -v
```

---

## 最新 CI 结果

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/aes.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> 每次发版时通过 [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml) 自动更新。
