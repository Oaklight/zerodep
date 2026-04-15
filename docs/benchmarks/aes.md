# AES 性能测试

zerodep AES 实现与 [`pycryptodome`](https://pypi.org/project/pycryptodome/)（C 扩展）的同条件性能对比。

!!! info "测试环境"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **工具:** pytest-benchmark 5.2.3（报告均值）
    - **对标库:** pycryptodome 3.23.0
    - **最后更新:** 2026-04-15

## 实现对比

| 实现 | 文件 | 类型 |
|------|------|------|
| **OpenSSL ctypes** | `aes.py` | 通过 ctypes 调用系统 libcrypto（默认） |
| **纯 Python** | `aes_python.py` | 解释执行的 Python |
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

| 数据大小 | 纯 Python | OpenSSL ctypes | pycryptodome | OpenSSL vs pycryptodome |
|----------|-----------|----------------|--------------|------------------------|
| 13 B（小） | ~71 us | ~5 us | ~7 us | 1.5x 更快 |
| 1 KB（中） | ~3,546 us | ~5 us | ~8 us | 1.4x 更快 |
| 64 KB（大） | ~226,004 us | ~21 us | ~21 us | ~1.0x（持平） |

## ECB 解密（均值）

| 数据大小 | 纯 Python | OpenSSL ctypes | pycryptodome | OpenSSL vs pycryptodome |
|----------|-----------|----------------|--------------|------------------------|
| 13 B（小） | ~92 us | ~5 us | ~7 us | 1.5x 更快 |
| 1 KB（中） | ~4,958 us | ~6 us | ~8 us | 1.5x 更快 |
| 64 KB（大） | ~309,896 us | ~19 us | ~22 us | 1.1x 更快 |

## CBC 加密（均值）

| 数据大小 | 纯 Python | OpenSSL ctypes | pycryptodome | OpenSSL vs pycryptodome |
|----------|-----------|----------------|--------------|------------------------|
| 13 B（小） | ~74 us | ~5 us | ~9 us | 1.7x 更快 |
| 1 KB（中） | ~3,762 us | ~6 us | ~11 us | 1.7x 更快 |
| 64 KB（大） | ~232,631 us | ~68 us | ~110 us | 1.6x 更快 |

## CBC 解密（均值）

| 数据大小 | 纯 Python | OpenSSL ctypes | pycryptodome | OpenSSL vs pycryptodome |
|----------|-----------|----------------|--------------|------------------------|
| 13 B（小） | ~94 us | ~5 us | ~9 us | 1.7x 更快 |
| 1 KB（中） | ~5,069 us | ~6 us | ~11 us | 1.9x 更快 |
| 64 KB（大） | ~319,752 us | ~19 us | ~111 us | 5.7x 更快 |

## CTR 加密（均值）

| 数据大小 | 纯 Python | OpenSSL ctypes | pycryptodome | OpenSSL vs pycryptodome |
|----------|-----------|----------------|--------------|------------------------|
| 13 B（小） | ~72 us | ~5 us | ~10 us | 1.9x 更快 |
| 1 KB（中） | ~3,652 us | ~6 us | ~12 us | 2.0x 更快 |
| 64 KB（大） | ~234,149 us | ~21 us | ~97 us | 4.6x 更快 |

## GCM 加密（均值）

| 数据大小 | 纯 Python | OpenSSL ctypes | pycryptodome | OpenSSL vs pycryptodome |
|----------|-----------|----------------|--------------|------------------------|
| 13 B（小） | ~232 us | ~7 us | ~43 us | 6.4x 更快 |
| 1 KB（中） | ~5,225 us | ~8 us | ~46 us | 6.1x 更快 |
| 64 KB（大） | ~327,032 us | ~27 us | ~142 us | 5.3x 更快 |

## GCM 解密（均值）

| 数据大小 | 纯 Python | OpenSSL ctypes | pycryptodome | OpenSSL vs pycryptodome |
|----------|-----------|----------------|--------------|------------------------|
| 13 B（小） | ~229 us | ~7 us | ~58 us | 8.8x 更快 |
| 1 KB（中） | ~5,254 us | ~8 us | ~61 us | 8.1x 更快 |
| 64 KB（大） | ~326,058 us | ~26 us | ~157 us | 6.1x 更快 |

## 要点总结

- **OpenSSL ctypes**（`aes.py`）稳定优于 pycryptodome 的 C 扩展：ECB/CBC/CTR 模式中小数据快 **1.1--1.9 倍**，大数据在 CBC/CTR 下快 **4.6--5.7 倍**。在 **GCM 模式** 下优势最为显著，达到 **5.3--8.8 倍**。且不需要任何 pip 依赖——只需系统安装 `libcrypto`。
- **纯 Python**（`aes_python.py`）比 pycryptodome 慢 7--14,000 倍，取决于模式和数据大小。即使对于 13 字节消息也需要 ~71--232 us（OpenSSL 仅需 ~5--7 us）。仅适合教学用途或在无原生库环境下作为后备方案。
- **GCM 模式** 的纯 Python 实现包含 GF(2^128) 乘法运算，是最慢的纯 Python 模式（13 字节需 ~232 us，而 ECB/CBC 仅需 ~71--74 us）。OpenSSL 变体则没有此开销。
- **pycryptodome** 速度较快（C 扩展），但需要通过 pip 安装编译依赖。在所有测试场景中 OpenSSL ctypes 均持平或更快。

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
