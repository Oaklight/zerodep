# AES 性能测试

zerodep AES 实现与 [`pycryptodome`](https://pypi.org/project/pycryptodome/)（C 扩展）的同条件性能对比。

!!! info "测试环境"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **工具:** pytest-benchmark 5.2.3（报告均值）
    - **对标库:** pycryptodome 3.23.0
    - **最后更新:** 2026-04-21

## 实现对比

AES 模块已整合为单文件（`aes.py`），自动选择后端：当 `libcrypto` 可用时默认使用 **OpenSSL**（通过 ctypes）；否则自动切换到**纯 Python** 后备方案。

| 实现 | 后端 | 类型 |
|------|------|------|
| **OpenSSL ctypes** | `aes.py`（默认） | 通过 ctypes 调用系统 libcrypto |
| **纯 Python** | `aes.py`（后备） | 解释执行的 Python |
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
| 13 B（小） | ~82 us | ~6.9 us | ~9.0 us | 1.3x 更快 |
| 1 KB（中） | ~4,000 us | ~7.6 us | ~9.4 us | 1.2x 更快 |
| 64 KB（大） | ~250,000 us | ~20.3 us | ~21.3 us | ~1.0x（持平） |

## ECB 解密（均值）

| 数据大小 | 纯 Python | OpenSSL ctypes | pycryptodome | OpenSSL vs pycryptodome |
|----------|-----------|----------------|--------------|------------------------|
| 13 B（小） | ~109 us | ~6.9 us | ~9.5 us | 1.4x 更快 |
| 1 KB（中） | ~5,500 us | ~7.5 us | ~9.5 us | 1.3x 更快 |
| 64 KB（大） | ~340,000 us | ~19.0 us | ~21.4 us | 1.1x 更快 |

## CBC 加密（均值）

| 数据大小 | 纯 Python | OpenSSL ctypes | pycryptodome | OpenSSL vs pycryptodome |
|----------|-----------|----------------|--------------|------------------------|
| 13 B（小） | ~85 us | ~6.8 us | ~10.0 us | 1.5x 更快 |
| 1 KB（中） | ~4,200 us | ~7.5 us | ~11 us | 1.5x 更快 |
| 64 KB（大） | ~260,000 us | ~70 us | ~115 us | 1.6x 更快 |

## CBC 解密（均值）

| 数据大小 | 纯 Python | OpenSSL ctypes | pycryptodome | OpenSSL vs pycryptodome |
|----------|-----------|----------------|--------------|------------------------|
| 13 B（小） | ~110 us | ~7 us | ~10 us | 1.4x 更快 |
| 1 KB（中） | ~5,600 us | ~7.5 us | ~12 us | 1.6x 更快 |
| 64 KB（大） | ~350,000 us | ~19.4 us | ~133.7 us | 6.9x 更快 |

## CTR 加密（均值）

| 数据大小 | 纯 Python | OpenSSL ctypes | pycryptodome | OpenSSL vs pycryptodome |
|----------|-----------|----------------|--------------|------------------------|
| 13 B（小） | ~84 us | ~7 us | ~11 us | 1.6x 更快 |
| 1 KB（中） | ~4,100 us | ~7.5 us | ~13 us | 1.7x 更快 |
| 64 KB（大） | ~255,000 us | ~21 us | ~100 us | 4.8x 更快 |

## GCM 加密（均值）

| 数据大小 | 纯 Python | OpenSSL ctypes | pycryptodome | OpenSSL vs pycryptodome |
|----------|-----------|----------------|--------------|------------------------|
| 13 B（小） | ~250 us | ~9.5 us | ~56.6 us | 6.0x 更快 |
| 1 KB（中） | ~5,600 us | ~10 us | ~58 us | 5.8x 更快 |
| 64 KB（大） | ~350,000 us | ~30 us | ~160 us | 5.3x 更快 |

## GCM 解密（均值）

| 数据大小 | 纯 Python | OpenSSL ctypes | pycryptodome | OpenSSL vs pycryptodome |
|----------|-----------|----------------|--------------|------------------------|
| 13 B（小） | ~248 us | ~9.5 us | ~60 us | 6.3x 更快 |
| 1 KB（中） | ~5,700 us | ~10 us | ~62 us | 6.2x 更快 |
| 64 KB（大） | ~350,000 us | ~30.9 us | ~165.0 us | 5.3x 更快 |

## 要点总结

- **OpenSSL ctypes** 是默认后端，稳定优于 pycryptodome 的 C 扩展：ECB/CBC 模式中小数据快 **1.1--1.5 倍**，大型 CBC 解密可达 **6.9 倍**。在 **GCM 模式** 下优势最为显著，达到 **5.3--6.3 倍**。且不需要任何 pip 依赖——只需系统安装 `libcrypto`。
- **纯 Python** 后备方案对于小消息比 pycryptodome 慢约 10 倍，中大型数据慢 300--500 倍。这是解释执行 Python 与编译 C 之间的预期差距，仅在无原生库环境下作为最后手段。
- **GCM 模式** 的纯 Python 实现包含 GF(2^128) 乘法运算，是最慢的纯 Python 模式（13 字节需 ~250 us，而 ECB/CBC 仅需 ~82--85 us）。OpenSSL 后端则没有此开销。
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
