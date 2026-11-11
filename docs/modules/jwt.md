# JWT / JWS

JWS 令牌校验（RS/PS/ES）与 HMAC 签名/校验——零 Python 依赖，仅标准库；可选使用系统 `libcrypto` 加速，Python 3.10+。

> **可替代:** `PyJWT`、`python-jose`

## 概述

JWT 模块用 Python 标准库完成 compact JWS 令牌的校验，以及 HMAC 的签名与校验。它覆盖 OAuth 资源服务器与 WebAuthn 依赖方所需的功能：

| 需求 | 使用的函数 |
|------|------------|
| `jwks` → 密钥 | `key_from_jwk()` |
| 校验访问令牌 | `decode()` + RS256 / ES256 |
| 读取 `kid` 以选择密钥 | `get_unverified_header()` |
| 签发内部令牌 | `encode()` + HS256 |
| 校验 passkey 断言 | `ecdsa_p256_verify()` |

非对称**签名**有意不在范围内。校验只用公开数据，纯 Python 大整数运算不会泄漏任何秘密；签名要用私钥，同样的运算会通过时序泄漏私钥。这一部分应交由有 C 后端支撑的库完成。

| 文件 | 说明 | 依赖 |
|------|------|------|
| `jwt.py` | JWS 校验、HMAC 签名、P-256 校验器 | 无（仅标准库）；可选通过 `ctypes` 使用系统 `libcrypto` |

## 在项目中使用

把单个 `.py` 文件复制到项目中即可：

```bash
cp jwt/jwt.py your_project/
```

然后直接导入：

```python
from jwt import decode, encode, get_unverified_header, key_from_jwk
```

!!! warning "包名冲突"
    文件名为 `jwt.py`，会遮蔽同名的 PyJWT 包。若项目同时需要两者，请重命名其中一个。正确性测试中给出了用于比对两者的 `sys.path` 处理方式。

## 后端

RSA/PS 模幂与 ECDSA 校验各有两种实现。`BACKEND` 报告当前使用哪一种；HMAC、base64 与 JSON 在两种实现下相同。

| 后端 | `BACKEND` | 实现方式 |
|------|-----------|----------|
| 原生 | `"openssl"` | 通过 `ctypes` 调用系统 `libcrypto`，与 `aes` 采用相同策略 |
| 纯 Python | `"python"` | Python 整数运算；参考实现，也是回退路径 |

`BACKEND` 在首次访问时才解析，因此只用 HMAC 的进程不会付出加载库的代价。当 `libcrypto` 能加载并导出所需符号时使用原生后端。以下情况会静默回退，校验结果完全一致：

- 找不到候选库——distroless 或精简镜像、SONAME 不同的 BoringSSL/LibreSSL，或不在加载器搜索路径中的 Windows `libcrypto-*.dll`；
- 该构建缺少 `BN_mod_exp`、`EC_KEY_*` 或 `ECDSA_*`，例如 OpenSSL 以 `no-deprecated` 配置构建；
- 原生调用在运行时失败。

用环境变量强制纯 Python 实现，测试套件也用它覆盖两条路径：

```bash
ZERODEP_JWT_BACKEND=python
```

只有公开密钥材料会跨过 `ctypes` 边界。HMAC 密钥不会：HMAC 本来就在 `hmac` 与 `hashlib` 的 C 实现中完成。

| 操作 | 原生 | 纯 Python |
|------|------|-----------|
| RSA / PSS 校验 | `BN_mod_exp` | `pow()` |
| ECDSA 校验 | `ECDSA_do_verify` | Jacobian 坐标点运算 |
| HMAC、base64、JSON | 不变 | 不变 |

## 支持的算法

| 算法族 | 算法 | 密钥类型 |
|--------|------|----------|
| HMAC | `HS256`、`HS384`、`HS512` | `bytes`、`str` 或 `oct` JWK |
| RSASSA-PKCS1-v1_5 | `RS256`、`RS384`、`RS512` | RSA JWK（`n`、`e`） |
| RSASSA-PSS | `PS256`、`PS384`、`PS512` | RSA JWK（`n`、`e`） |
| ECDSA | `ES256`、`ES384` | P-256 / P-384 上的 EC JWK（`crv`、`x`、`y`） |

`SUPPORTED_ALGORITHMS` 以 frozenset 形式给出全部算法。

## 安全模型

以下三条规则由 API 结构保证，而不是依赖调用方自觉：

- **算法白名单是必填项。** `decode()` 的 `algorithms` 没有默认值，省略会抛出 `TypeError`。令牌无法自行决定校验算法。
- **永不接受 `alg: "none"`**，即使它出现在白名单中；判断不区分大小写。
- **密钥类型必须与算法匹配。** `RS256` 令牌配 `bytes` 密钥会抛出 `InvalidKeyError`，`HS256` 令牌配 RSA JWK 同样如此。这封堵了把公钥当作 HMAC 密钥重放的 RS/HS 混淆攻击。
- **PEM 与 OpenSSH 密钥不能作为 HMAC 密钥。** 在裸 `bytes`/`str` 路径上，PEM 装甲、RFC 4716 装甲（`---- BEGIN SSH2 PUBLIC KEY ----`）以及 `ssh-rsa`、`ssh-ed25519`、`ssh-dss`、`ecdsa-sha2-` 前缀都会抛出 `InvalidKeyError`，因此 `algorithms=["RS256", "HS256"]` 的混合部署无法被"用 RSA 公钥签名的 HS256 令牌"骗过。PyJWT 采用同样的防护。这是一份尽力而为的黑名单：未装甲的 DER 密钥材料没有可辨识的前缀，本模块与 PyJWT 都会接受，持有此类材料的调用方不得把它当作 `oct` 密钥传入。

小于 2048 位的 RSA 模数由 `key_from_jwk()` 拒绝，因此被拒绝的密钥不会进入 `decode()`；对手工构造的 `JWKKey`，`decode()` 会重复该检查。使用前还会校验 EC 点是否满足曲线方程。

带有 `crit` 头（列出任何扩展）的令牌会抛出 `UnsupportedCriticalHeaderError`：RFC 7515 第 4.1.11 节有此要求，而本模块未实现任何扩展。

解析发生在认证之前，因此格式错误或恶意的令牌只会产生 `JWTError`：头部或载荷的嵌套深度超过 `MAX_JSON_DEPTH`（100）时抛出 `DecodeError`，JSON 解析器抛出的 `RecursionError` 会转换为 `DecodeError`，宽于 P-256 域的 DER 整数按无效签名处理（返回 `False`），而不是抛出 `OverflowError`。

## API 参考

### `decode(token, key, *, algorithms, ...)`

校验 compact JWS 并返回其中的声明。

```python
def decode(
    token: str | bytes,
    key: Any,
    *,
    algorithms: Sequence[str] | Set[str] | str,
    audience: str | Sequence[str] | None = None,
    issuer: str | Sequence[str] | None = None,
    leeway: float | timedelta = 0.0,
    require: Sequence[str] | str | None = None,
    verify_audience: bool = True,
    verify_expiry: bool = True,
    now: float | None = None,
) -> dict[str, Any]
```

| 参数 | 说明 |
|------|------|
| `algorithms` | 允许的 `alg` 值。必填且不能为空。 |
| `audience` | 期望的 `aud`。令牌缺少 `aud` 时抛出 `MissingRequiredClaimError`。 |
| `issuer` | 期望的 `iss`，可为单个字符串或多个值。 |
| `leeway` | `exp`、`nbf`、`iat` 的时钟偏差容忍度，单位为秒或 `timedelta`。负值或非有限值抛出 `ValueError`。 |
| `require` | 必须存在且不为 null 的声明。 |
| `verify_audience` | 传 `False` 跳过受众检查。只有在传入 `audience` 时才检查 `aud`。 |
| `verify_expiry` | 传 `False` 时接受已过期令牌；`nbf` 与 `iat` 仍会校验。 |
| `now` | 覆盖当前时间，单位为自 epoch 起的秒数。 |

**示例：**

```python
from jwt import decode

jwks = {"keys": [{"kty": "RSA", "kid": "k1", "n": "...", "e": "AQAB"}]}
header = get_unverified_header(token)
key = next(k for k in jwks["keys"] if k["kid"] == header.get("kid"))

claims = decode(
    token,
    key,
    algorithms=["RS256"],
    audience="api://resource",
    issuer="https://issuer.example",
    leeway=30,
)
```

### `encode(claims, key, *, algorithm="HS256", headers=None)`

用 HMAC 算法为声明签名，返回 compact JWS。

```python
token = encode({"sub": "alice", "exp": 1767225600}, b"shared-secret", algorithm="HS256")
```

只接受 `HS256`、`HS384`、`HS512`。`headers` 可添加 `kid` 等成员；`headers` 中的 `alg` 无法改变算法。

### `get_unverified_header(token)` / `get_unverified_claims(token)`

不校验签名，直接解码头部或载荷。用 `get_unverified_header()` 按 `kid` 选择密钥；其余判断必须在 `decode()` 之后进行。

### `key_from_jwk(jwk)`

解析并校验 JWK，返回 `JWKKey`。

```python
def key_from_jwk(jwk: Mapping[str, Any]) -> JWKKey
```

| 密钥类型 | 必需成员 |
|----------|----------|
| RSA | `kty="RSA"`、`n`、`e` |
| EC | `kty="EC"`、`crv`（`P-256` / `P-384`）、`x`、`y` |
| oct | `kty="oct"`、`k` |

可选的 `kid` 与 `alg` 会保留。当 JWK 声明了 `alg` 时，`decode()` 会拒绝算法不同的令牌。

### `ecdsa_p256_verify(pub, msg, sig, *, der=False)`

无需 JWT 封装，直接校验 ECDSA P-256 / SHA-256 签名。JWS 使用裸 `r || s`，WebAuthn 使用 DER。

```python
def ecdsa_p256_verify(
    pub: tuple[int, int] | JWKKey | Mapping[str, Any],
    msg: bytes,
    sig: bytes,
    *,
    der: bool = False,
) -> bool
```

**示例：**

```python
from jwt import ecdsa_p256_verify

ok = ecdsa_p256_verify((x, y), auth_data + sha256(client_data_json), der_signature, der=True)
```

签名格式错误或点不在曲线上时返回 `False`；密钥不是 P-256 密钥时抛出 `InvalidKeyError`。

### 编码工具

`b64url_encode(data) -> str` 与 `b64url_decode(data) -> bytes` 是整个模块使用的无填充 base64url 编解码器。之所以公开，是因为调用方在拼装 JWKS 或 COSE 密钥时通常也要用到。

### `BACKEND`

原生后端启用时为 `"openssl"`，纯 Python 实现启用或被强制时为 `"python"`。导入后读取一次即可记录或断言部署使用的是哪条路径：

```python
from jwt import BACKEND

if BACKEND != "openssl":
    log.warning("jwt 正在使用纯 Python 后端")
```

首次读取 `BACKEND` 会加载 `libcrypto`；只用 HMAC 且从不读取它的进程不会付出该代价。

## 声明校验

| 声明 | 检查 | 默认 |
|------|------|------|
| `exp` | `exp <= now - leeway` 时抛出 `ExpiredSignatureError` | 开启 |
| `nbf` | `nbf > now + leeway` 时抛出 `ImmatureSignatureError` | 开启 |
| `iat` | `iat > now + leeway` 时抛出 `ImmatureSignatureError` | 开启 |
| `iss` | 传入 `issuer` 时必须匹配 | 未传 `issuer` 时关闭 |
| `aud` | 传入 `audience` 时必须匹配；列表声明命中任一即可；空声明视为缺失 | 未传 `audience` 时关闭 |
| `require` | 每个指定声明必须存在且不为 null | 关闭 |

`exp`、`nbf`、`iat` 不是数值、不是有限数（`NaN`、`Infinity`）或超出范围时抛出 `DecodeError`，因此 `exp: NaN` 无法产生永不过期的令牌。

## 异常

所有异常都继承 `JWTError`。

```
JWTError
├── DecodeError            (同时是 ValueError)
│   ├── InvalidAlgorithmError
│   └── UnsupportedCriticalHeaderError
├── InvalidSignatureError
├── InvalidKeyError        (同时是 ValueError)
├── ExpiredSignatureError
├── ImmatureSignatureError
├── InvalidAudienceError
├── InvalidIssuerError
└── MissingRequiredClaimError
```

## 不在范围内

- RS / ES / PS 签名（Python 中的私钥大数运算会泄漏密钥）
- JWE、X.509 证书、加密 PEM
- 分离载荷（`b64: false`），compact 解析器会拒绝此类令牌
- `crit` 中列出的任何 JWS 扩展（本模块未实现）
- JWKS 拉取与缓存——这部分策略由调用方负责

## 运行测试

```bash
make test-jwt        # 与 PyJWT[crypto] 的正确性比对
make benchmark-jwt   # 与 PyJWT[crypto] 的性能对比
```
