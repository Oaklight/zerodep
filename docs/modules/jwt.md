# JWT / JWS

JWS token verification (RS/PS/ES) and HMAC sign/verify -- zero dependencies, stdlib only, Python 3.10+.

> **Replaces:** `PyJWT`, `python-jose`

## Overview

The JWT module verifies compact JSON Web Signature tokens and signs/verifies with HMAC, using only the Python standard library. It covers what an OAuth resource server or a WebAuthn relying party needs:

| Need | Covered by |
|------|------------|
| `jwks` -> key | `key_from_jwk()` |
| Verify an access token | `decode()` with RS256 / ES256 |
| Read `kid` to pick a key | `get_unverified_header()` |
| Issue an internal token | `encode()` with HS256 |
| Verify a passkey assertion | `ecdsa_p256_verify()` |

Asymmetric **signing** is out of scope on purpose. Verification works on public data, so pure-Python big-integer arithmetic leaks nothing; signing works on a private key, where the same arithmetic leaks it through timing. Keep that on a C-backed library.

| File | Description | Dependencies |
|------|-------------|--------------|
| `jwt.py` | JWS verification, HMAC signing, P-256 verifier | None (stdlib only) |

## How to Use in Your Project

Just copy the single `.py` file into your project:

```bash
cp jwt/jwt.py your_project/
```

Then import directly:

```python
from jwt import decode, encode, get_unverified_header, key_from_jwk
```

!!! warning "Package name collision"
    The file is named `jwt.py`, so it shadows the PyJWT package of the same name. If a project needs both, rename one of them. The correctness tests show the `sys.path` workaround used to compare the two.

## Supported Algorithms

| Family | Algorithms | Key type |
|--------|------------|----------|
| HMAC | `HS256`, `HS384`, `HS512` | `bytes`, `str`, or an `oct` JWK |
| RSASSA-PKCS1-v1_5 | `RS256`, `RS384`, `RS512` | RSA JWK (`n`, `e`) |
| RSASSA-PSS | `PS256`, `PS384`, `PS512` | RSA JWK (`n`, `e`) |
| ECDSA | `ES256`, `ES384` | EC JWK (`crv`, `x`, `y`) on P-256 / P-384 |

`SUPPORTED_ALGORITHMS` holds the full set as a frozenset.

## Safety Model

Three rules are enforced by the API shape, not by the caller:

- **An algorithm allowlist is required.** `decode()` has no default for `algorithms`; omitting it raises `TypeError`. A token cannot choose its own verification algorithm.
- **`alg: "none"` is never accepted**, even when it appears in the allowlist. The check is case-insensitive.
- **The key type must match the algorithm.** An `RS256` token with a `bytes` key raises `InvalidKeyError`, and an `HS256` token with an RSA JWK does too. This closes the RS/HS confusion class where a public key is replayed as an HMAC secret.
- **PEM and OpenSSH keys are never HMAC secrets.** `-----BEGIN `, `ssh-rsa `, `ssh-ed25519 ` and `ecdsa-sha2-` prefixes raise `InvalidKeyError` on the raw `bytes`/`str` path, so a mixed `algorithms=["RS256", "HS256"]` deployment cannot be tricked into verifying an `HS256` token signed with the RSA public key. PyJWT applies the same guard.

RSA moduli below 2048 bits are refused by `key_from_jwk()`, so a rejected key never reaches `decode()`; `decode()` repeats the check for a hand-built `JWKKey`. EC points are checked against the curve equation before use.

A `crit` header naming any extension is rejected with `UnsupportedCriticalHeaderError`: RFC 7515 section 4.1.11 requires that, and this module implements no extensions.

Parsing is unauthenticated, so a malformed or hostile token produces only `JWTError`: a header or payload nested deeper than `MAX_JSON_DEPTH` (100) is rejected with `DecodeError`, a `RecursionError` from the JSON parser is converted to `DecodeError`, and a DER integer wider than the P-256 field is an invalid signature (`False`), not an `OverflowError`.

## API Reference

### `decode(token, key, *, algorithms, ...)`

Verify a compact JWS and return its claims.

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

| Parameter | Description |
|-----------|-------------|
| `algorithms` | Allowed `alg` values. Required, and must be non-empty. |
| `audience` | Expected `aud`. A token without an `aud` claim raises `MissingRequiredClaimError`. |
| `issuer` | Expected `iss`, as one string or several. |
| `leeway` | Clock-skew tolerance for `exp`, `nbf` and `iat`, in seconds or as a `timedelta`. |
| `require` | Claims that must be present and not null. |
| `verify_audience` | Set `False` to skip the audience check. `aud` is only checked when `audience` is given. |
| `verify_expiry` | Set `False` to accept an expired token. `nbf` and `iat` stay enforced. |
| `now` | Override the clock, in seconds since the epoch. |

**Example:**

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

Sign claims with an HMAC algorithm and return a compact JWS.

```python
token = encode({"sub": "alice", "exp": 1767225600}, b"shared-secret", algorithm="HS256")
```

Only `HS256`, `HS384` and `HS512` are accepted. A `headers` mapping adds members such as `kid`; `alg` in `headers` cannot change the algorithm.

### `get_unverified_header(token)` / `get_unverified_claims(token)`

Decode the header or payload without checking the signature. Use `get_unverified_header()` to pick a key by `kid`; make every other decision after `decode()`.

### `key_from_jwk(jwk)`

Parse and validate a JWK into a `JWKKey`.

```python
def key_from_jwk(jwk: Mapping[str, Any]) -> JWKKey
```

| Key type | Required members |
|----------|------------------|
| RSA | `kty="RSA"`, `n`, `e` |
| EC | `kty="EC"`, `crv` (`P-256` / `P-384`), `x`, `y` |
| oct | `kty="oct"`, `k` |

Optional `kid` and `alg` members are kept. When a JWK declares `alg`, `decode()` refuses a token whose algorithm differs.

### `ecdsa_p256_verify(pub, msg, sig, *, der=False)`

Verify an ECDSA P-256 / SHA-256 signature without a JWT around it. JWS carries raw `r || s`; WebAuthn carries DER.

```python
def ecdsa_p256_verify(
    pub: tuple[int, int] | JWKKey | Mapping[str, Any],
    msg: bytes,
    sig: bytes,
    *,
    der: bool = False,
) -> bool
```

**Example:**

```python
from jwt import ecdsa_p256_verify

ok = ecdsa_p256_verify((x, y), auth_data + sha256(client_data_json), der_signature, der=True)
```

A malformed signature or an off-curve point returns `False`. A key that is not a P-256 key raises `InvalidKeyError`.

### Encoding helpers

`b64url_encode(data) -> str` and `b64url_decode(data) -> bytes` are the unpadded base64url codec used throughout, exported because callers assembling a JWKS or a COSE key usually need it.

## Claims

| Claim | Check | Default |
|-------|-------|---------|
| `exp` | `exp <= now - leeway` raises `ExpiredSignatureError` | on |
| `nbf` | `nbf > now + leeway` raises `ImmatureSignatureError` | on |
| `iat` | `iat > now + leeway` raises `ImmatureSignatureError` | on |
| `iss` | must match `issuer` when given | off unless `issuer` is passed |
| `aud` | must match `audience` when given; a list claim matches any entry; an empty claim counts as absent | off unless `audience` is passed |
| `require` | each named claim must be present and not null | off |

A non-numeric, non-finite (`NaN`, `Infinity`) or out-of-range `exp`, `nbf` or `iat` raises `DecodeError`, so `exp: NaN` cannot produce a token that never expires.

## Errors

Every error derives from `JWTError`.

```
JWTError
├── DecodeError            (also ValueError)
│   ├── InvalidAlgorithmError
│   └── UnsupportedCriticalHeaderError
├── InvalidSignatureError
├── InvalidKeyError        (also ValueError)
├── ExpiredSignatureError
├── ImmatureSignatureError
├── InvalidAudienceError
├── InvalidIssuerError
└── MissingRequiredClaimError
```

## Out of Scope

- RS / ES / PS signing (private-key arithmetic in Python leaks the key)
- JWE, X.509 certificates, encrypted PEM
- Detached payloads (`b64: false`), which the compact parser rejects
- Any JWS extension listed in `crit` (none are implemented)
- JWKS fetching and caching -- the caller owns that policy

## Run the Tests

```bash
make test-jwt        # correctness against PyJWT[crypto]
make benchmark-jwt   # performance against PyJWT[crypto]
```
