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
| **zerodep** | `jwt.py` | 纯 Python：`hashlib`、`hmac`、`int` 运算、Jacobian 坐标点运算 |
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

| 操作 | zerodep | PyJWT[crypto] | 比值 |
|------|---------|---------------|------|
| RS256 校验 | 167 us | 35.4 us | 慢 4.7 倍 |
| PS256 校验 | 188 us | 40.8 us | 慢 4.6 倍 |
| ES256 校验 | 1,715 us | 86.2 us | 慢 19.9 倍 |
| HS256 校验 | 15.0 us | 14.4 us | 约 1.0 倍 |
| HS256 签名 | 10.8 us | 10.5 us | 约 1.0 倍 |

所有数字均为连续三次运行、`--benchmark-min-rounds=20` 的均值。三次运行的实测区间：HS256 校验 14.7--15.4 us、HS256 签名 10.6--11.2 us、RS256 164.7--170.0 us、PS256 184.9--190.9 us、ES256 1,704--1,736 us。

## 耗时构成

- **RS256 / PS256** 本质上是一次 `e = 65537` 的模幂运算，约 147 us 落在其中，总量约 167 us。OpenSSL 在 C 中用同样的平方-乘序列，差距来自 2048 位乘法的解释器开销；这是固定成本，不随令牌长度增长。
- **ES256** 是 P-256 上的两次标量乘法，用 Shamir 技巧合并为一条两位步骤的链。对六个抽样签名插桩统计点运算辅助函数，每次校验为 **254--258 次点倍加与 145--147 次点加法**（ES384：384--386 次倍加、210--211 次加法）。两位一组的循环每步贡献 2 次倍加、1 次加法，再加上 16 项预计算表的构建；小幅波动来自标量本身，因为 `_j_add` 在无穷远点会提前返回，两操作数重合时还会回退为 `_j_double`。若分别做两次标量乘法，倍加次数会翻倍。每一步都是 Python 层的大整数运算，因此差距比 RSA 更大。
- **HS256** 没有大整数运算；`hmac` 与 `hashlib` 都是标准库中的 C 模块，两个库测到的是同一份代码，差异落在运行间噪声之内。

## 要点总结

- **HMAC 校验与签名与 PyJWT 持平**，因为两者调用同一份 `hmac` 实现。
- **非对称校验比 OpenSSL 慢 4.6--20 倍。** 对 OAuth 资源服务器而言，JWKS 查找之后每个请求多花几百微秒，通常远低于该请求自身的数据库或网络开销——但它并非免费，令牌密集型的高并发路径应先测量再采用。
- **不引入编译依赖。** 模块不安装任何东西，因此适用于无法获取或不希望依赖 `cryptography` 轮子的环境。

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
