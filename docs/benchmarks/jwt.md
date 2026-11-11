# JWT 性能测试

zerodep JWT 与 [`PyJWT[crypto]`](https://pypi.org/project/PyJWT/)（通过 `cryptography` 调用 OpenSSL）的同条件性能对比。

!!! info "测试环境"
    - **CPU:** x86_64 Linux
    - **Python:** 3.10
    - **工具:** pytest-benchmark 5.2.3（报告均值）
    - **对标库:** PyJWT 2.10.1、cryptography 46.0.6
    - **最后更新:** 2026-11-10

## 实现对比

| 实现 | 文件/包 | 说明 |
|------|---------|------|
| **zerodep（原生）** | `jwt.py` | 通过 `ctypes` 调用系统 `libcrypto` 完成 RSA/PS 模幂与 ECDSA |
| **zerodep（纯 Python）** | `jwt.py`，`ZERODEP_JWT_BACKEND=python` | `hashlib`、`hmac`、`int` 运算、Jacobian 坐标点运算 |
| **PyJWT[crypto]** | *（参考库）* | `cryptography` 调用 OpenSSL |

## 测试场景

每个用例校验（HS256 则为签名）一个含 6 个声明的令牌（`sub`、`iss`、`aud`、`iat`、`exp`、`scope`）并校验受众，因此两侧都包含令牌解析与声明校验。PyJWT 负责签发所有令牌，两个库再校验同一个 compact JWS。

| 算法 | 密钥 |
|------|------|
| RS256 | RSA 2048，`e = 65537` |
| PS256 | RSA 2048，salt 长度 = 摘要长度 |
| ES256 | P-256 |
| HS256 | 39 字节共享密钥 |

## 测试结果（均值）

| 操作 | zerodep 原生 | zerodep 纯 Python | PyJWT[crypto] | 原生 vs PyJWT |
|------|--------------|-------------------|---------------|---------------|
| RS256 校验 | 57.6 us | 164.4 us | 34.8 us | 慢 1.7 倍 |
| PS256 校验 | 77.3 us | 187.1 us | 40.3 us | 慢 1.9 倍 |
| ES256 校验 | 102.3 us | 1,716.6 us | 85.2 us | 慢 1.2 倍 |
| HS256 校验 | 16.2 us | 16.1 us | 14.5 us | 慢 1.1 倍 |
| HS256 签名 | 10.9 us | 11.2 us | 10.4 us | 慢 1.0 倍 |

所有数字为两种后端各连续三次运行、`--benchmark-min-rounds=20` 的均值，同一台机器、同一会话。纯 Python 列通过 `ZERODEP_JWT_BACKEND=python` 强制。原生后端运行间波动约 1 us，纯 Python 后端最多约 2%，因此末位数字仅供参考，不是上下界。

## 耗时构成

- **RSA / PS 原生。** `e = 65537` 的一次模幂在 `BN_mod_exp` 内完成；填充、`DigestInfo`、JSON 解析与声明校验仍在 Python 中。与 PyJWT 的剩余差距约为 RS256 23 us、PS256 37 us，主要是 Python 侧的 PSS 掩码生成（MGF1）与每次调用的密钥转换。
- **RSA / PS 纯 Python。** 同样的算法，但模幂用 `pow()`，约 150 us 落在其中。这就是纯 Python 后端在此慢 2.1--2.9 倍的原因。
- **ES256 原生。** `ECDSA_do_verify` 在 OpenSSL 中完成两次标量乘法；模块每次调用都会用 JWK 点构造一个 `EC_KEY`。比 PyJWT 多出的约 17 us 来自这次构造以及令牌解析与声明校验。
- **ES256 纯 Python。** P-256 上的两次标量乘法，用 Shamir 技巧合并为一条两位步骤的链。计数恰为 `2 * chunks + 2` 次点倍加与 `chunks + 19` 次点加法，其中 `chunks = ceil(max(bit_length(u1), bit_length(u2)) / 2)` 由两个约化后的 ECDSA 标量决定。`+ 2` 是常量：`_shamir_mult` 预计算中有两处重合——`multiples_of_p2` 把 `j2` 与自身相加，第一次 `row = _j_add(row, p1)` 把 `p1` 与自身相加——两者都走 `_j_add` 的 `h == 0` 回退到 `_j_double`。`19` 来自 16 项预计算表的构建。对 6,000 个抽样签名实测，258/147 为众数（约 94%），256/146 约 6%，254/145 约 0.4%，`chunks` 更小时依次更罕见。若分别做两次标量乘法，倍加次数会翻倍。每一步都是 Python 层的大整数运算，因此纯 Python 后端比原生慢约 17 倍。
- **HS256** 两种后端都没有大整数运算；`hmac` 与 `hashlib` 都是标准库中的 C 模块，两个库执行的是同一份哈希。差距（校验约 1.6 us、签名约 0.8 us）来自本模块自身的防护：密钥材料检查在每次 HMAC 调用上约 1 us，JSON 深度预扫描在典型令牌上约 0.4 us（仅校验）。PyJWT 没有深度预扫描。

## 要点总结

- **原生后端让非对称校验足以与 PyJWT 竞争**：RS256 慢 1.7 倍、PS256 慢 1.9 倍、ES256 慢 1.2 倍；纯 Python 后端则分别为 4.7 倍、4.7 倍与 20 倍。
- **HMAC 不变**，约为 PyJWT 的 1.1 倍，因为两者调用同一份 C 实现的 `hmac`。
- **不引入 Python 依赖。** 加速器通过 `ctypes` 使用系统 `libcrypto`，而 Python 本身为 `ssl` 与 `hashlib` 已经链接了它。当库或所需符号缺失时，模块会回退到纯 Python，结果完全一致；`BACKEND` 会说明实际运行的是哪条路径。
- **保留纯 Python 回退。** `ZERODEP_JWT_BACKEND=python` 可强制使用，适用于受限镜像或对比测量。

## 自行运行

```bash
pip install pytest pytest-benchmark "PyJWT[crypto]"
pytest jwt/test_jwt_benchmark.py --benchmark-only -v
```

---

## 最新 CI 结果

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/jwt.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> 每次发版时通过 [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml) 自动更新。
