# /// zerodep
# version = "0.2.0"
# deps = []
# tier = "medium"
# category = "crypto"
# note = "Install/update via: https://zerodep.readthedocs.io/en/latest/guide/cli/"
# ///
"""JWS (JWT) token verification and HMAC signing — stdlib only.

Verifies compact JWS tokens with RS256/384/512 (RSASSA-PKCS1-v1_5),
PS256/384/512 (RSASSA-PSS) and ES256/ES384 (ECDSA), and signs and verifies
HS256/384/512 (HMAC).  Asymmetric *signing* is deliberately absent: it needs
the private key, where big-int arithmetic would leak the key through timing.
Verification uses public data only.

Keys are JSON Web Keys (RFC 7517): RSA ``n``/``e``, EC P-256/P-384
``x``/``y``/``crv``, or ``oct`` shared secrets::

    >>> decode(token, {"kty": "RSA", "n": "...", "e": "AQAB"},
    ...        algorithms=["RS256"])

The caller must pass an algorithm allowlist, and the key type must match the
token's algorithm, so an RS256 token can never be checked against an HMAC
secret.  ``"none"`` is never accepted.

Signing with a shared secret::

    >>> token = encode({"sub": "alice"}, b"secret", algorithm="HS256")

A header or payload nested deeper than :data:`MAX_JSON_DEPTH` (100) levels is
rejected with :class:`DecodeError`, and so is any ``RecursionError`` the JSON
parser raises, so parsing an unauthenticated token cannot leak a
``RecursionError`` to the caller.

.. warning::

   This file is named ``jwt.py``, so a flat copy shadows the PyJWT package of
   the same name.  If the destination directory is on ``sys.path``, ``import
   jwt`` resolves to this file, and every import of a PyJWT submodule --
   ``import jwt.exceptions``, ``import jwt.algorithms`` -- fails with
   ``ModuleNotFoundError: 'jwt' is not a package``.  Copy it nested
   (``zerodep add jwt --nested``), or rename the copied file and import it
   under that name (``import my_jwt``).

The module is pure Python, with one optional accelerator: when the system
``libcrypto`` can be loaded through :mod:`ctypes`, RSA/PS modular
exponentiation and ECDSA verification run in OpenSSL instead of Python
integers.  This is the same backend strategy ``aes`` uses.  Nothing is
installed and no Python package is required; if the library or a needed symbol
is missing, every algorithm falls back to the pure-Python implementation with
identical results.  :data:`BACKEND` reports which one is active, and the
environment variable ``ZERODEP_JWT_BACKEND=python`` forces the fallback.

Part of zerodep: https://github.com/Oaklight/zerodep
Copyright (c) 2026 Peng Ding. MIT License.
"""

from __future__ import annotations

import _thread
import base64
import binascii
import hashlib
import hmac
import json
import math
import os
import re
import sys
import time
from collections.abc import Callable, Mapping, Sequence, Set
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any

__all__ = [
    # Errors
    "JWTError",
    "DecodeError",
    "InvalidSignatureError",
    "InvalidAlgorithmError",
    "UnsupportedCriticalHeaderError",
    "InvalidKeyError",
    "ExpiredSignatureError",
    "ImmatureSignatureError",
    "InvalidAudienceError",
    "InvalidIssuerError",
    "MissingRequiredClaimError",
    # Keys
    "JWKKey",
    "key_from_jwk",
    # Tokens
    "encode",
    "decode",
    "get_unverified_header",
    "get_unverified_claims",
    "ecdsa_p256_verify",
    # Encoding helpers
    "b64url_encode",
    "b64url_decode",
    "SUPPORTED_ALGORITHMS",
    "BACKEND",
]

#: ``"openssl"`` or ``"python"``, resolved on first attribute access.
BACKEND: str

# ===========================================================================
# Section 1: Errors
# ===========================================================================


class JWTError(Exception):
    """Base class for every error raised by this module."""


class DecodeError(JWTError, ValueError):
    """The token is not a well-formed compact JWS."""


class InvalidSignatureError(JWTError):
    """The signature does not verify under the supplied key."""


class InvalidAlgorithmError(DecodeError):
    """The token's ``alg`` is unsupported or outside the caller's allowlist."""


class UnsupportedCriticalHeaderError(DecodeError):
    """The token's ``crit`` names an extension this module does not implement."""


class InvalidKeyError(JWTError, ValueError):
    """The key is malformed, unusable, or does not match the algorithm."""


class ExpiredSignatureError(JWTError):
    """The ``exp`` claim is in the past."""


class ImmatureSignatureError(JWTError):
    """The ``nbf`` or ``iat`` claim is in the future."""


class InvalidAudienceError(JWTError):
    """The ``aud`` claim is missing or does not match."""


class InvalidIssuerError(JWTError):
    """The ``iss`` claim is missing or does not match."""


class MissingRequiredClaimError(JWTError):
    """A claim named in ``require`` is absent or null."""


# ===========================================================================
# Section 2: base64url helpers
# ===========================================================================

_B64URL_RE = re.compile(rb"^[A-Za-z0-9_-]*$")


def b64url_encode(data: bytes) -> str:
    """Encode bytes as unpadded base64url (RFC 4648 section 5).

    Args:
        data: Bytes to encode.

    Returns:
        The encoded text, without ``=`` padding.
    """
    if not isinstance(data, (bytes, bytearray, memoryview)):
        raise TypeError(f"expected bytes, got {type(data).__name__}")
    return base64.urlsafe_b64encode(bytes(data)).rstrip(b"=").decode("ascii")


def b64url_decode(data: str | bytes) -> bytes:
    """Decode unpadded base64url text.

    Args:
        data: Text or ASCII bytes to decode.

    Returns:
        The decoded bytes.

    Raises:
        DecodeError: The input is not ASCII base64url of a valid length, or
            carries padding.
    """
    if isinstance(data, str):
        try:
            raw = data.encode("ascii")
        except UnicodeEncodeError as exc:
            raise DecodeError("base64url segment is not ASCII") from exc
    elif isinstance(data, (bytes, bytearray, memoryview)):
        raw = bytes(data)
    else:
        raise TypeError(f"expected str or bytes, got {type(data).__name__}")
    if not _B64URL_RE.match(raw):
        raise DecodeError("base64url segment has characters outside the alphabet")
    remainder = len(raw) % 4
    if remainder == 1:
        raise DecodeError("base64url segment has an invalid length")
    try:
        return base64.urlsafe_b64decode(raw + b"=" * (-remainder % 4))
    except (binascii.Error, ValueError) as exc:
        raise DecodeError(f"base64url segment is invalid: {exc}") from exc


def _b64url_uint(value: Any, name: str) -> int:
    """Decode a base64url big-endian unsigned integer from a JWK field."""
    raw = b64url_decode(value)
    if not raw:
        raise InvalidKeyError(f"JWK {name!r} is empty")
    return int.from_bytes(raw, "big")


# ===========================================================================
# Section 3: Curve parameters (FIPS 186-4)
# ===========================================================================


@dataclass(frozen=True, slots=True)
class _Curve:
    """Short-Weierstrass curve parameters."""

    name: str
    p: int
    a: int
    b: int
    n: int
    gx: int
    gy: int
    bits: int


_SECP256R1 = _Curve(
    name="P-256",
    p=0xFFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF,
    a=-3,
    b=0x5AC635D8AA3A93E7B3EBBD55769886BC651D06B0CC53B0F63BCE3C3E27D2604B,
    n=0xFFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551,
    gx=0x6B17D1F2E12C4247F8BCE6E563A440F277037D812DEB33A0F4A13945D898C296,
    gy=0x4FE342E2FE1A7F9B8EE7EB4A7C0F9E162BCE33576B315ECECBB6406837BF51F5,
    bits=256,
)

_SECP384R1 = _Curve(
    name="P-384",
    p=int(
        "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE"
        "FFFFFFFF0000000000000000FFFFFFFF",
        16,
    ),
    a=-3,
    b=int(
        "B3312FA7E23EE7E4988E056BE3F82D19181D9C6EFE8141120314088F5013875A"
        "C656398D8A2ED19D2A85C8EDD3EC2AEF",
        16,
    ),
    n=int(
        "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFC7634D81F4372DDF"
        "581A0DB248B0A77AECEC196ACCC52973",
        16,
    ),
    gx=int(
        "AA87CA22BE8B05378EB1C71EF320AD746E1D3B628BA79B9859F741E082542A38"
        "5502F25DBF55296C3A545E3872760AB7",
        16,
    ),
    gy=int(
        "3617DE4A96262C6F5D9E98BF9292DC29F8F41DBD289A147CE9DA3113B5F0B8C0"
        "0A60B1CE1D7E819D7A431D7C90EA0E5F",
        16,
    ),
    bits=384,
)

_CURVES: dict[str, _Curve] = {"P-256": _SECP256R1, "P-384": _SECP384R1}


def _curve_a(curve: _Curve) -> int:
    """Return the curve coefficient ``a`` reduced into the field."""
    return curve.a % curve.p


def _field_size(curve: _Curve) -> int:
    """Return the byte width of a field element or a signature half."""
    return (curve.bits + 7) // 8


def _on_curve(curve: _Curve, x: int, y: int) -> bool:
    """Report whether ``(x, y)`` is a finite point on *curve*."""
    if not (0 <= x < curve.p and 0 <= y < curve.p):
        return False
    return (y * y - (x * x * x + _curve_a(curve) * x + curve.b)) % curve.p == 0


# ===========================================================================
# Section 4: JWK parsing
# ===========================================================================


@dataclass(frozen=True, slots=True)
class JWKKey:
    """A JSON Web Key parsed and validated from its JWK fields.

    Attributes:
        kty: Key type: ``"RSA"``, ``"EC"`` or ``"oct"``.
        n: RSA modulus.
        e: RSA public exponent.
        crv: EC curve name, ``"P-256"`` or ``"P-384"``.
        x: EC public point x coordinate.
        y: EC public point y coordinate.
        secret: Shared secret of an ``oct`` key.
        kid: Key ID from the JWK, when present.
        alg: Algorithm the JWK declares, when present.
    """

    kty: str
    n: int | None = None
    e: int | None = None
    crv: str | None = None
    x: int | None = None
    y: int | None = None
    secret: bytes | None = field(default=None, repr=False)
    kid: str | None = None
    alg: str | None = None


def _jwk_field(jwk: Mapping[str, Any], name: str) -> Any:
    """Return a required JWK field or raise InvalidKeyError."""
    if name not in jwk:
        raise InvalidKeyError(f"JWK is missing the required field {name!r}")
    return jwk[name]


def _jwk_optional_str(jwk: Mapping[str, Any], name: str) -> str | None:
    """Return an optional string JWK field, rejecting non-string values."""
    value = jwk.get(name)
    if value is None:
        return None
    if not isinstance(value, str):
        raise InvalidKeyError(f"JWK field {name!r} must be a string")
    return value


#: Smallest RSA modulus accepted, in bits.  A shorter modulus is forgeable
#: with modest effort, so it is rejected as a bad key rather than used.  The
#: floor is enforced here, in :func:`key_from_jwk`, so a rejected modulus never
#: reaches ``decode()``; :func:`_rsa_public` repeats the check as defence in
#: depth for a directly constructed :class:`JWKKey`.
MIN_RSA_BITS = 2048


def _parse_rsa_jwk(jwk: Mapping[str, Any]) -> JWKKey:
    """Build and validate an RSA JWKKey."""
    n = _b64url_uint(_jwk_field(jwk, "n"), "n")
    e = _b64url_uint(_jwk_field(jwk, "e"), "e")
    if n < 3 or n % 2 == 0:
        raise InvalidKeyError("JWK 'n' must be an odd positive integer")
    if e < 3 or e % 2 == 0:
        raise InvalidKeyError("JWK 'e' must be an odd integer >= 3")
    if e >= n:
        raise InvalidKeyError("JWK 'e' must be smaller than 'n'")
    if n.bit_length() < MIN_RSA_BITS:
        raise InvalidKeyError(
            f"RSA modulus is {n.bit_length()} bits; "
            f"at least {MIN_RSA_BITS} are required"
        )
    return JWKKey(
        kty="RSA",
        n=n,
        e=e,
        kid=_jwk_optional_str(jwk, "kid"),
        alg=_jwk_optional_str(jwk, "alg"),
    )


def _parse_ec_jwk(jwk: Mapping[str, Any]) -> JWKKey:
    """Build and validate an EC JWKKey."""
    crv = _jwk_field(jwk, "crv")
    if not isinstance(crv, str):
        raise InvalidKeyError("JWK 'crv' must be a string")
    curve = _CURVES.get(crv)
    if curve is None:
        raise InvalidKeyError(
            f"unsupported curve {crv!r}; only P-256 and P-384 are supported"
        )
    size = _field_size(curve)
    x_raw = b64url_decode(_jwk_field(jwk, "x"))
    y_raw = b64url_decode(_jwk_field(jwk, "y"))
    for name, raw in (("x", x_raw), ("y", y_raw)):
        if not 0 < len(raw) <= size:
            raise InvalidKeyError(f"JWK {name!r} must be 1..{size} bytes")
    x = int.from_bytes(x_raw, "big")
    y = int.from_bytes(y_raw, "big")
    if not _on_curve(curve, x, y):
        raise InvalidKeyError(f"JWK point is not on curve {crv}")
    return JWKKey(
        kty="EC",
        crv=crv,
        x=x,
        y=y,
        kid=_jwk_optional_str(jwk, "kid"),
        alg=_jwk_optional_str(jwk, "alg"),
    )


def _parse_oct_jwk(jwk: Mapping[str, Any]) -> JWKKey:
    """Build a symmetric JWKKey."""
    secret = b64url_decode(_jwk_field(jwk, "k"))
    if not secret:
        raise InvalidKeyError("JWK 'k' is empty")
    return JWKKey(
        kty="oct",
        secret=secret,
        kid=_jwk_optional_str(jwk, "kid"),
        alg=_jwk_optional_str(jwk, "alg"),
    )


_JWK_PARSERS: dict[str, Callable[[Mapping[str, Any]], JWKKey]] = {
    "RSA": _parse_rsa_jwk,
    "EC": _parse_ec_jwk,
    "oct": _parse_oct_jwk,
}


def key_from_jwk(jwk: Mapping[str, Any]) -> JWKKey:
    """Parse and validate a JSON Web Key.

    Args:
        jwk: JWK members.  RSA needs ``kty``, ``n``, ``e``; EC needs ``kty``,
            ``crv``, ``x``, ``y``; symmetric keys need ``kty`` and ``k``.

    Returns:
        The parsed key, ready for :func:`decode`.

    Raises:
        InvalidKeyError: The JWK is malformed in any way: missing or non-string
            members, invalid base64url, an unsupported key type or curve, an
            EC point off the curve, or an RSA modulus below
            :data:`MIN_RSA_BITS`.  No other exception type escapes, so
            ``except InvalidKeyError`` covers the whole key-loading path.
    """
    if not isinstance(jwk, Mapping):
        raise InvalidKeyError(f"expected a JWK mapping, got {type(jwk).__name__}")
    kty = _jwk_field(jwk, "kty")
    parser = _JWK_PARSERS.get(kty) if isinstance(kty, str) else None
    if parser is None:
        raise InvalidKeyError(f"unsupported JWK key type {kty!r}")
    try:
        return parser(jwk)
    except InvalidKeyError:
        raise
    except (DecodeError, TypeError, ValueError) as exc:
        # b64url_decode raises DecodeError for bad base64 and TypeError for a
        # non-str member; both are key errors from the caller's point of view.
        raise InvalidKeyError(f"malformed JWK: {exc}") from exc


def _as_jwk(key: Any) -> JWKKey:
    """Coerce a JWK mapping or JWKKey into a JWKKey."""
    if isinstance(key, JWKKey):
        return key
    if isinstance(key, Mapping):
        return key_from_jwk(key)
    raise InvalidKeyError(f"expected a JWK mapping or JWKKey, got {type(key).__name__}")


# ===========================================================================
# Section 5: Signature primitives
# ===========================================================================

_SHA256 = hashlib.sha256
_SHA384 = hashlib.sha384
_SHA512 = hashlib.sha512

_HMAC_ALGS: dict[str, str] = {
    "HS256": "sha256",
    "HS384": "sha384",
    "HS512": "sha512",
}

_RSA_PKCS1_ALGS: dict[str, tuple[Callable[[bytes], Any], bytes]] = {
    "RS256": (
        _SHA256,
        bytes.fromhex("3031300d060960864801650304020105000420"),
    ),
    "RS384": (
        _SHA384,
        bytes.fromhex("3041300d060960864801650304020205000430"),
    ),
    "RS512": (
        _SHA512,
        bytes.fromhex("3051300d060960864801650304020305000440"),
    ),
}

_RSA_PSS_ALGS: dict[str, Callable[[bytes], Any]] = {
    "PS256": _SHA256,
    "PS384": _SHA384,
    "PS512": _SHA512,
}

_ECDSA_ALGS: dict[str, tuple[str, Callable[[bytes], Any]]] = {
    "ES256": ("P-256", _SHA256),
    "ES384": ("P-384", _SHA384),
}

SUPPORTED_ALGORITHMS: frozenset[str] = frozenset(
    (*_HMAC_ALGS, *_RSA_PKCS1_ALGS, *_RSA_PSS_ALGS, *_ECDSA_ALGS)
)


def _hmac_sign(alg: str, key: bytes, msg: bytes) -> bytes:
    """Return the HMAC tag for *msg*."""
    return hmac.new(key, msg, _HMAC_ALGS[alg]).digest()


def _hmac_verify(alg: str, key: bytes, msg: bytes, sig: bytes) -> bool:
    """Compare an HMAC tag in constant time."""
    return hmac.compare_digest(_hmac_sign(alg, key, msg), sig)


def _mgf1(hash_ctor: Callable[[bytes], Any], seed: bytes, length: int) -> bytes:
    """MGF1 mask generation (RFC 8017 appendix B.2.1)."""
    out = bytearray()
    counter = 0
    while len(out) < length:
        out += hash_ctor(seed + counter.to_bytes(4, "big")).digest()
        counter += 1
    return bytes(out[:length])


def _rsa_pkcs1_v15_verify(
    n: int,
    e: int,
    sig: bytes,
    msg: bytes,
    hash_ctor: Callable[[bytes], Any],
    digest_info_prefix: bytes,
) -> bool:
    """Verify RSASSA-PKCS1-v1_5 (RFC 8017 section 8.2.2)."""
    k = (n.bit_length() + 7) // 8
    if len(sig) != k:
        return False
    s = int.from_bytes(sig, "big")
    if s >= n:
        return False
    em = _modexp(s, e, n).to_bytes(k, "big")
    t = digest_info_prefix + hash_ctor(msg).digest()
    if k < len(t) + 11:
        return False
    expected = b"\x00\x01" + b"\xff" * (k - len(t) - 3) + b"\x00" + t
    return hmac.compare_digest(em, expected)


def _rsa_pss_verify(
    n: int,
    e: int,
    sig: bytes,
    msg: bytes,
    hash_ctor: Callable[[bytes], Any],
    salt_len: int,
) -> bool:
    """Verify RSASSA-PSS (RFC 8017 section 9.1.2) with MGF1 and salt=hLen."""
    mod_bits = n.bit_length()
    em_bits = mod_bits - 1
    em_len = (em_bits + 7) // 8
    k = (mod_bits + 7) // 8
    h_len = hash_ctor(b"").digest_size
    if len(sig) != k:
        return False
    s = int.from_bytes(sig, "big")
    if s >= n:
        return False
    m = _modexp(s, e, n)
    if m.bit_length() > em_bits:
        return False
    if em_len < h_len + salt_len + 2:
        return False
    em = m.to_bytes(em_len, "big")
    if em[-1] != 0xBC:
        return False
    db_len = em_len - h_len - 1
    masked_db = em[:db_len]
    h = em[db_len:-1]
    unused_bits = 8 * em_len - em_bits
    if unused_bits and masked_db[0] >> (8 - unused_bits):
        return False
    db = bytes(a ^ b for a, b in zip(masked_db, _mgf1(hash_ctor, h, db_len)))
    if unused_bits:
        db = bytes([db[0] & (0xFF >> unused_bits)]) + db[1:]
    ps_len = em_len - h_len - salt_len - 2
    if any(db[:ps_len]) or db[ps_len] != 0x01:
        return False
    salt = db[ps_len + 1 :]
    h2 = hash_ctor(b"\x00" * 8 + hash_ctor(msg).digest() + salt).digest()
    return hmac.compare_digest(h, h2)


# ── Elliptic-curve point arithmetic (Jacobian coordinates) ──

_Affine = tuple[int, int]
_Jacobian = tuple[int, int, int]


def _j_double(curve: _Curve, p: _Jacobian) -> _Jacobian:
    """Double a Jacobian point; ``Z == 0`` is the point at infinity."""
    x1, y1, z1 = p
    mod = curve.p
    if z1 == 0 or y1 == 0:
        return (0, 0, 0)
    a = _curve_a(curve)
    a1 = x1 * x1 % mod
    b1 = y1 * y1 % mod
    c1 = b1 * b1 % mod
    d1 = 2 * ((x1 + b1) * (x1 + b1) - a1 - c1) % mod
    z2 = z1 * z1 % mod
    e1 = (3 * a1 + a * z2 * z2) % mod
    f1 = e1 * e1 % mod
    x3 = (f1 - 2 * d1) % mod
    y3 = (e1 * (d1 - x3) - 8 * c1) % mod
    z3 = 2 * y1 * z1 % mod
    return (x3, y3, z3)


def _j_add(curve: _Curve, p: _Jacobian, q: _Jacobian) -> _Jacobian:
    """Add two Jacobian points."""
    x1, y1, z1 = p
    x2, y2, z2 = q
    mod = curve.p
    if z1 == 0:
        return q
    if z2 == 0:
        return p
    z1z1 = z1 * z1 % mod
    z2z2 = z2 * z2 % mod
    u1 = x1 * z2z2 % mod
    u2 = x2 * z1z1 % mod
    s1 = y1 * z2 * z2z2 % mod
    s2 = y2 * z1 * z1z1 % mod
    h = (u2 - u1) % mod
    r = 2 * (s2 - s1) % mod
    if h == 0:
        return _j_double(curve, p) if r == 0 else (0, 0, 0)
    i = 4 * h * h % mod
    j = h * i % mod
    v = u1 * i % mod
    x3 = (r * r - j - 2 * v) % mod
    y3 = (r * (v - x3) - 2 * s1 * j) % mod
    z3 = ((z1 + z2) * (z1 + z2) - z1z1 - z2z2) * h % mod
    return (x3, y3, z3)


def _j_to_affine(curve: _Curve, p: _Jacobian) -> _Affine | None:
    """Convert a Jacobian point to affine, or ``None`` for infinity."""
    x, y, z = p
    if z == 0:
        return None
    z_inv = pow(z, -1, curve.p)
    z_inv2 = z_inv * z_inv % curve.p
    return (x * z_inv2 % curve.p, y * z_inv2 * z_inv % curve.p)


def _shamir_mult(
    curve: _Curve,
    k1: int,
    p1: _Affine,
    k2: int,
    p2: _Affine,
) -> _Jacobian:
    """Compute ``k1 * p1 + k2 * p2`` with Shamir's trick, two bits at a time.

    One doubling chain serves both scalars, which halves the doublings of two
    separate multiplications.  Each two-bit chunk of both scalars selects one
    of 16 precomputed points and costs two doublings and one addition.
    """
    infinity: _Jacobian = (0, 0, 0)
    j2: _Jacobian = (p2[0], p2[1], 1)
    multiples_of_p2: list[_Jacobian] = [infinity]
    for _ in range(3):
        multiples_of_p2.append(_j_add(curve, multiples_of_p2[-1], j2))
    table: dict[int, _Jacobian] = {}
    row = infinity
    for i in range(4):
        for j, multiple in enumerate(multiples_of_p2):
            table[(i << 2) | j] = multiple if i == 0 else _j_add(curve, row, multiple)
        row = _j_add(curve, row, (p1[0], p1[1], 1))
    result = infinity
    chunks = (max(k1.bit_length(), k2.bit_length()) + 1) // 2
    for index in range(chunks - 1, -1, -1):
        result = _j_double(curve, _j_double(curve, result))
        shift = 2 * index
        result = _j_add(
            curve, result, table[((k1 >> shift) & 0b11) << 2 | ((k2 >> shift) & 0b11)]
        )
    return result


def _ecdsa_verify(
    curve: _Curve,
    qx: int,
    qy: int,
    msg: bytes,
    sig_raw: bytes,
    hash_ctor: Callable[[bytes], Any],
) -> bool:
    """Verify an ECDSA signature in raw ``r || s`` form (FIPS 186-4)."""
    size = _field_size(curve)
    if len(sig_raw) != 2 * size:
        return False
    r = int.from_bytes(sig_raw[:size], "big")
    s = int.from_bytes(sig_raw[size:], "big")
    if not (1 <= r < curve.n and 1 <= s < curve.n):
        return False
    if not _on_curve(curve, qx, qy):
        return False
    native = _native_backend()
    if native is not None:
        try:
            verdict = native.ecdsa_verify(curve, qx, qy, msg, sig_raw, hash_ctor)
        except (MemoryError, OSError, RuntimeError, ValueError):
            # The pure implementation below is the reference; a native failure
            # must not change the verdict or escape as a non-JWTError.
            verdict = None
        if verdict is not None:
            return verdict
    digest = hash_ctor(msg).digest()
    e = int.from_bytes(digest, "big")
    excess = len(digest) * 8 - curve.n.bit_length()
    if excess > 0:
        e >>= excess
    w = pow(s, -1, curve.n)
    u1 = e * w % curve.n
    u2 = r * w % curve.n
    point = _j_to_affine(
        curve,
        _shamir_mult(curve, u1, (curve.gx, curve.gy), u2, (qx, qy)),
    )
    if point is None:
        return False
    return point[0] % curve.n == r


# ── DER <-> raw ECDSA signature conversion ──


def _der_to_raw(sig: bytes, size: int) -> bytes:
    """Convert a DER-encoded ECDSA signature to fixed-size ``r || s``."""
    if len(sig) < 8 or sig[0] != 0x30:
        raise DecodeError("DER signature does not start with a SEQUENCE")
    if sig[1] & 0x80:
        raise DecodeError("DER signature uses a long-form length")
    if sig[1] != len(sig) - 2:
        raise DecodeError("DER signature length does not match its contents")
    values = []
    offset = 2
    for _ in range(2):
        if offset + 2 > len(sig) or sig[offset] != 0x02:
            raise DecodeError("DER signature is missing an INTEGER")
        length = sig[offset + 1]
        start = offset + 2
        end = start + length
        if length == 0 or end > len(sig):
            raise DecodeError("DER signature INTEGER is truncated")
        raw = sig[start:end]
        if raw[0] & 0x80:
            raise DecodeError("DER signature INTEGER is negative")
        if length > 1 and raw[0] == 0 and not raw[1] & 0x80:
            raise DecodeError("DER signature INTEGER is not minimally encoded")
        value = int.from_bytes(raw, "big")
        # A barely-wider-than-field integer is a legal DER encoding of an
        # invalid signature, not a malformed one: report it as DecodeError so
        # ecdsa_p256_verify() turns it into False instead of OverflowError.
        if value.bit_length() > 8 * size:
            raise DecodeError("DER signature INTEGER is wider than the field")
        values.append(value)
        offset = end
    if offset != len(sig):
        raise DecodeError("DER signature has trailing bytes")
    return b"".join(v.to_bytes(size, "big") for v in values)


# ===========================================================================
# Section 6: Key selection
# ===========================================================================


#: Armor labels a PEM or RFC 4716 block can carry.  The list matches PyJWT's,
#: including the bare ``CERTIFICATE`` an OIDC resource server holds as ``x5c``.
_ARMOR_LABELS = (
    b"TRUSTED CERTIFICATE",
    b"CERTIFICATE",
    b"PRIVATE KEY",
    b"PUBLIC KEY",
    b"ENCRYPTED PRIVATE KEY",
    b"OPENSSH PRIVATE KEY",
    b"DSA PRIVATE KEY",
    b"RSA PRIVATE KEY",
    b"RSA PUBLIC KEY",
    b"EC PRIVATE KEY",
    b"DH PARAMETERS",
    b"NEW CERTIFICATE REQUEST",
    b"CERTIFICATE REQUEST",
    b"SSH2 PUBLIC KEY",
    b"SSH2 ENCRYPTED PRIVATE KEY",
    b"X509 CRL",
)

#: A PEM (five dashes) or RFC 4716 (four dashes and a space) ``BEGIN`` marker,
#: searched anywhere in the material: a caller may prepend a comment or a
#: banner.  PyJWT's PEM regex also searches the whole value.
_ARMOR_RE = re.compile(
    rb"-{4,5}[ -]BEGIN (?:"
    # Longest first so ``CERTIFICATE REQUEST`` is not shadowed by ``CERTIFICATE``
    # when the alternation is evaluated; a bare ``CERTIFICATE`` still matches.
    + b"|".join(
        re.escape(label) for label in sorted(_ARMOR_LABELS, key=len, reverse=True)
    )
    + rb")"
)

#: OpenSSH public key type prefixes, as PyJWT lists them.
_SSH_KEY_MARKERS = (
    b"ssh-rsa",
    b"ssh-ed25519",
    b"ssh-dss",
    b"ecdsa-sha2-",
)


def _looks_like_public_key(secret: bytes) -> bool:
    """Report whether *secret* looks like PEM, RFC 4716 or OpenSSH key material."""
    stripped = secret.lstrip()
    if any(stripped.startswith(marker) for marker in _SSH_KEY_MARKERS):
        return True
    # Every armor label follows the word BEGIN, so this C-level substring test
    # spares the regex on the common path.
    if b"BEGIN" not in secret:
        return False
    return _ARMOR_RE.search(secret) is not None


def _secret_bytes(key: Any) -> bytes:
    """Return the shared secret carried by *key*.

    A PEM, RFC 4716 or OpenSSH public key is rejected: it is public data, so
    anyone holding it could sign an ``HS*`` token that verifies against it.
    Without this check the RS/HS confusion class is only closed for keys that
    arrive as a JWK.

    The check is a best-effort denylist keyed on armor and on OpenSSH type
    prefixes, the same approach PyJWT takes.  Unarmored DER SubjectPublicKeyInfo
    carries no distinguishing prefix, so this module -- like PyJWT -- accepts it
    as a secret; a caller holding DER key material must not pass it as an
    ``oct`` key.
    """
    if isinstance(key, (bytes, bytearray, memoryview)):
        secret = bytes(key)
    elif isinstance(key, str):
        secret = key.encode("utf-8")
    else:
        raise InvalidKeyError(
            f"an HMAC algorithm needs a bytes or str secret, got {type(key).__name__}"
        )
    if _looks_like_public_key(secret):
        raise InvalidKeyError(
            "an asymmetric public key or certificate cannot be used as an "
            "HMAC secret: it is public data, so anyone holding it could "
            "forge a token"
        )
    return secret


def _rsa_public(key: Any, alg: str) -> tuple[int, int]:
    """Return ``(n, e)`` for an RSA key, rejecting any other key type."""
    if not isinstance(key, (JWKKey, Mapping)):
        raise InvalidKeyError(
            f"{alg} needs a JWK mapping or JWKKey, got {type(key).__name__}; "
            "a bytes or str key is only valid for HS* algorithms"
        )
    parsed = _as_jwk(key)
    if parsed.kty != "RSA":
        raise InvalidKeyError(f"{alg} needs an RSA key, got kty={parsed.kty!r}")
    if parsed.n is None or parsed.e is None:
        raise InvalidKeyError(f"{alg} needs an RSA key with 'n' and 'e'")
    if parsed.n.bit_length() < MIN_RSA_BITS:
        raise InvalidKeyError(
            f"RSA modulus is {parsed.n.bit_length()} bits; "
            f"at least {MIN_RSA_BITS} are required"
        )
    if parsed.alg is not None and parsed.alg != alg:
        raise InvalidKeyError(
            f"JWK declares alg={parsed.alg!r} but the token uses {alg!r}"
        )
    return parsed.n, parsed.e


def _ec_public(key: Any, alg: str) -> tuple[_Curve, int, int]:
    """Return ``(curve, x, y)`` for an EC key, rejecting any other key type."""
    if not isinstance(key, (JWKKey, Mapping)):
        raise InvalidKeyError(
            f"{alg} needs a JWK mapping or JWKKey, got {type(key).__name__}; "
            "a bytes or str key is only valid for HS* algorithms"
        )
    parsed = _as_jwk(key)
    if parsed.kty != "EC":
        raise InvalidKeyError(f"{alg} needs an EC key, got kty={parsed.kty!r}")
    curve_name, _hash = _ECDSA_ALGS[alg]
    if parsed.crv != curve_name:
        raise InvalidKeyError(f"{alg} needs curve {curve_name}, got {parsed.crv!r}")
    if parsed.x is None or parsed.y is None:
        raise InvalidKeyError(f"{alg} needs an EC key with 'x' and 'y'")
    if parsed.alg is not None and parsed.alg != alg:
        raise InvalidKeyError(
            f"JWK declares alg={parsed.alg!r} but the token uses {alg!r}"
        )
    return _CURVES[curve_name], parsed.x, parsed.y


def _hmac_secret(key: Any, alg: str) -> bytes:
    """Return the HMAC secret, rejecting asymmetric keys."""
    if isinstance(key, (JWKKey, Mapping)):
        parsed = _as_jwk(key)
        if parsed.kty != "oct":
            raise InvalidKeyError(
                f"{alg} needs an oct key, got kty={parsed.kty!r}; "
                "asymmetric keys cannot be used as an HMAC secret"
            )
        if parsed.alg is not None and parsed.alg != alg:
            raise InvalidKeyError(
                f"JWK declares alg={parsed.alg!r} but the token uses {alg!r}"
            )
        if parsed.secret is None:
            raise InvalidKeyError("oct key has no 'k' secret")
        return parsed.secret
    return _secret_bytes(key)


def _verify_signature(alg: str, key: Any, signing_input: bytes, sig: bytes) -> bool:
    """Verify *sig* over *signing_input* with *alg* and *key*."""
    if alg in _HMAC_ALGS:
        return _hmac_verify(alg, _hmac_secret(key, alg), signing_input, sig)
    if alg in _RSA_PKCS1_ALGS:
        hash_ctor, prefix = _RSA_PKCS1_ALGS[alg]
        n, e = _rsa_public(key, alg)
        return _rsa_pkcs1_v15_verify(n, e, sig, signing_input, hash_ctor, prefix)
    if alg in _RSA_PSS_ALGS:
        hash_ctor = _RSA_PSS_ALGS[alg]
        n, e = _rsa_public(key, alg)
        salt_len = hash_ctor(b"").digest_size
        return _rsa_pss_verify(n, e, sig, signing_input, hash_ctor, salt_len)
    curve, x, y = _ec_public(key, alg)
    return _ecdsa_verify(curve, x, y, signing_input, sig, _ECDSA_ALGS[alg][1])


# ===========================================================================
# Section 7: Compact serialization
# ===========================================================================


@dataclass(frozen=True, slots=True)
class _JWS:
    """A parsed, unverified compact JWS."""

    header: dict[str, Any]
    claims: dict[str, Any]
    signing_input: bytes
    signature: bytes


#: Deepest JSON nesting accepted in a header or payload.  JWT headers and
#: claims nest a handful of levels, so 100 is far above any legitimate token.
#: The cap is enforced by a scan, not by the parser, because CPython changed
#: where ``json`` gives up: 3.10 raises at roughly 1,000 levels, while 3.12
#: parses 2,000 and 3.14 parses 50,000.  A scan makes the answer the same on
#: every supported version.
MAX_JSON_DEPTH = 100


def _check_json_depth(raw: bytes, what: str) -> None:
    """Reject JSON nested deeper than :data:`MAX_JSON_DEPTH`.

    Bracket characters inside string literals do not count, and backslash
    escapes inside a string are skipped, so a claim holding ``"[[[["`` is not
    mistaken for nesting.  The segment is scanned, not parsed.

    The scan is skipped when the segment cannot be too deep: nesting is bounded
    by the number of opening brackets, so a segment with at most
    :data:`MAX_JSON_DEPTH` of them is accepted after two C-level ``count``
    calls.  Brackets inside strings are counted too, which only makes the
    estimate more conservative.
    """
    if raw.count(b"[") + raw.count(b"{") <= MAX_JSON_DEPTH:
        return
    depth = 0
    in_string = False
    escaped = False
    for byte in raw:
        if in_string:
            if escaped:
                escaped = False
            elif byte == 0x5C:  # backslash
                escaped = True
            elif byte == 0x22:  # double quote
                in_string = False
            continue
        if byte == 0x22:
            in_string = True
        elif byte in (0x7B, 0x5B):  # { or [
            depth += 1
            if depth > MAX_JSON_DEPTH:
                raise DecodeError(f"{what} is nested too deeply")
        elif byte in (0x7D, 0x5D):  # } or ]
            depth -= 1


def _loads_object(raw: bytes, what: str) -> dict[str, Any]:
    """Decode a JSON object from *raw*, or raise DecodeError.

    Depth is capped before parsing, and ``RecursionError`` is caught as defence
    in depth: the token is unauthenticated at this point, so deeply nested JSON
    must not escape as anything but a :class:`DecodeError`.
    """
    _check_json_depth(raw, what)
    try:
        value = json.loads(raw)
    except RecursionError as exc:
        raise DecodeError(f"{what} is nested too deeply") from exc
    except (ValueError, UnicodeDecodeError) as exc:
        raise DecodeError(f"{what} is not valid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise DecodeError(f"{what} is not a JSON object")
    return value


def _parse(token: str | bytes) -> _JWS:
    """Parse a compact JWS without verifying it."""
    if isinstance(token, (bytes, bytearray, memoryview)):
        try:
            text = bytes(token).decode("ascii")
        except UnicodeDecodeError as exc:
            raise DecodeError("token is not ASCII") from exc
    elif isinstance(token, str):
        text = token
    else:
        raise DecodeError(f"expected a str or bytes token, got {type(token).__name__}")
    parts = text.split(".")
    if len(parts) != 3:
        raise DecodeError(
            f"compact JWS must have 3 dot-separated parts, found {len(parts)}"
        )
    header_b64, claims_b64, sig_b64 = parts
    header = _loads_object(b64url_decode(header_b64), "JWS header")
    alg = header.get("alg")
    if not isinstance(alg, str):
        raise DecodeError("JWS header has no string 'alg' member")
    claims = _loads_object(b64url_decode(claims_b64), "JWS payload")
    signing_input = f"{header_b64}.{claims_b64}".encode("ascii")
    return _JWS(
        header=header,
        claims=claims,
        signing_input=signing_input,
        signature=b64url_decode(sig_b64),
    )


def get_unverified_header(token: str | bytes) -> dict[str, Any]:
    """Return a token's header without verifying the signature.

    Use this only to pick a key (for example by ``kid``).  Any decision that
    depends on the token must be made after :func:`decode` has verified it.

    Args:
        token: Compact JWS text or ASCII bytes.

    Returns:
        The decoded header.

    Raises:
        DecodeError: The token is not a well-formed compact JWS.
    """
    return dict(_parse(token).header)


def get_unverified_claims(token: str | bytes) -> dict[str, Any]:
    """Return a token's claims without verifying the signature.

    Args:
        token: Compact JWS text or ASCII bytes.

    Returns:
        The decoded payload.

    Raises:
        DecodeError: The token is not a well-formed compact JWS.
    """
    return dict(_parse(token).claims)


# ===========================================================================
# Section 8: Signing (HMAC only)
# ===========================================================================


def encode(
    claims: Mapping[str, Any],
    key: str | bytes | Mapping[str, Any] | JWKKey,
    *,
    algorithm: str = "HS256",
    headers: Mapping[str, Any] | None = None,
) -> str:
    """Sign *claims* with an HMAC algorithm and return a compact JWS.

    Only HS256, HS384 and HS512 are supported.  Asymmetric signing is out of
    scope because big-int arithmetic over a private key leaks it through
    timing.

    Args:
        claims: JWT claims.  Must be JSON-serializable.
        key: The shared secret (bytes or str), or an ``oct`` JWK.
        algorithm: ``HS256`` (default), ``HS384`` or ``HS512``.
        headers: Extra JWS header members, such as ``kid``.

    Returns:
        The compact JWS text.

    Raises:
        InvalidAlgorithmError: *algorithm* is not an HMAC algorithm.
        InvalidKeyError: The key is not a usable shared secret.
        TypeError: *claims* is not a mapping.
    """
    if algorithm not in _HMAC_ALGS:
        raise InvalidAlgorithmError(
            f"{algorithm!r} cannot be signed by this module; "
            f"supported signing algorithms: {', '.join(sorted(_HMAC_ALGS))}"
        )
    if not isinstance(claims, Mapping):
        raise TypeError(f"claims must be a mapping, got {type(claims).__name__}")
    secret = _hmac_secret(key, algorithm)
    header: dict[str, Any] = {"alg": algorithm, "typ": "JWT"}
    if headers:
        header.update(headers)
    header["alg"] = algorithm
    header_b64 = b64url_encode(
        json.dumps(header, separators=(",", ":"), sort_keys=True).encode("utf-8")
    )
    claims_b64 = b64url_encode(
        json.dumps(dict(claims), separators=(",", ":")).encode("utf-8")
    )
    signing_input = f"{header_b64}.{claims_b64}".encode("ascii")
    sig = _hmac_sign(algorithm, secret, signing_input)
    return f"{header_b64}.{claims_b64}.{b64url_encode(sig)}"


# ===========================================================================
# Section 9: Claims validation
# ===========================================================================


def _leeway_seconds(leeway: float | timedelta) -> float:
    """Normalize *leeway* to seconds, rejecting a negative tolerance."""
    if isinstance(leeway, timedelta):
        seconds = leeway.total_seconds()
    elif isinstance(leeway, bool) or not isinstance(leeway, (int, float)):
        raise TypeError(
            f"leeway must be a number or timedelta, got {type(leeway).__name__}"
        )
    else:
        try:
            seconds = float(leeway)
        except OverflowError as exc:
            raise ValueError("leeway must be finite") from exc
    if not math.isfinite(seconds):
        # exp <= now - nan is False, so a NaN tolerance would let an expired
        # token through: reject it like a negative one.
        raise ValueError("leeway must be finite")
    if seconds < 0:
        raise ValueError("leeway must not be negative")
    return seconds


def _numeric_claim(claims: Mapping[str, Any], name: str) -> float:
    """Return a finite NumericDate claim as a number of seconds.

    RFC 7519 defines NumericDate as a number, and RFC 8259 has no ``NaN`` or
    ``Infinity``, so a non-finite value is malformed.  Rejecting it also
    closes a fail-open case: every comparison against ``NaN`` is false, so an
    ``exp`` of ``NaN`` would never expire.
    """
    value = claims[name]
    if isinstance(value, bool):
        raise DecodeError(f"{name!r} claim must be a number, got a bool")
    if not isinstance(value, (int, float)):
        raise DecodeError(
            f"{name!r} claim must be a number, got {type(value).__name__}"
        )
    try:
        seconds = float(value)
    except OverflowError as exc:
        raise DecodeError(f"{name!r} claim is out of range") from exc
    if not math.isfinite(seconds):
        raise DecodeError(f"{name!r} claim must be a finite number")
    return seconds


def _check_time_claims(
    claims: Mapping[str, Any], now: float, leeway: float, allow_expiry: bool
) -> None:
    """Validate ``exp``, ``nbf`` and ``iat`` against *now*."""
    if allow_expiry and "exp" in claims:
        if _numeric_claim(claims, "exp") <= now - leeway:
            raise ExpiredSignatureError("the token has expired")
    if "nbf" in claims:
        if _numeric_claim(claims, "nbf") > now + leeway:
            raise ImmatureSignatureError("the token is not valid yet (nbf)")
    if "iat" in claims:
        if _numeric_claim(claims, "iat") > now + leeway:
            raise ImmatureSignatureError("the token was issued in the future (iat)")


def _check_audience(claims: Mapping[str, Any], audience: Any) -> None:
    """Validate the ``aud`` claim against the expected audience values."""
    if audience is None:
        return
    expected = [audience] if isinstance(audience, str) else list(audience)
    if not expected or any(not isinstance(a, str) for a in expected):
        raise InvalidAudienceError(
            "audience must be a string or a non-empty iterable of strings"
        )
    value = claims.get("aud")
    if not value:
        # An empty string or empty list is treated as absent, matching PyJWT.
        raise MissingRequiredClaimError("aud")
    if isinstance(value, str):
        actual = [value]
    elif isinstance(value, list) and all(isinstance(a, str) for a in value):
        actual = value
    else:
        raise InvalidAudienceError("the 'aud' claim is not a string or list of strings")
    if not any(a in actual for a in expected):
        raise InvalidAudienceError("the audience does not match")


def _check_issuer(claims: Mapping[str, Any], issuer: Any) -> None:
    """Validate the ``iss`` claim against the expected issuer values."""
    if issuer is None:
        return
    expected = [issuer] if isinstance(issuer, str) else list(issuer)
    if not expected or any(not isinstance(i, str) for i in expected):
        raise InvalidIssuerError(
            "issuer must be a string or a non-empty iterable of strings"
        )
    if "iss" not in claims or claims["iss"] is None:
        raise MissingRequiredClaimError("iss")
    if claims["iss"] not in expected:
        raise InvalidIssuerError("the issuer does not match")


def _check_required(claims: Mapping[str, Any], required: Any) -> None:
    """Validate that every claim in *required* is present and not null."""
    if not required:
        return
    if isinstance(required, str):
        names = [required]
    else:
        try:
            names = list(required)
        except TypeError as exc:
            raise TypeError(
                "'require' must be a claim name or an iterable of claim names, "
                f"got {type(required).__name__}"
            ) from exc
    for name in names:
        if not isinstance(name, str):
            raise TypeError(
                f"'require' entries must be claim names, got {type(name).__name__}"
            )
        if claims.get(name) is None:
            raise MissingRequiredClaimError(name)


def _check_critical_header(header: Mapping[str, Any]) -> None:
    """Reject a JWS whose ``crit`` names an extension this module ignores.

    RFC 7515 section 4.1.11 requires the recipient to reject a JWS that lists
    a critical extension it does not implement.  This module implements none,
    so any well-formed non-empty ``crit`` is unsupported.
    """
    if "crit" not in header:
        return
    crit = header["crit"]
    if (
        not isinstance(crit, list)
        or not crit
        or any(not isinstance(name, str) for name in crit)
    ):
        raise DecodeError("'crit' must be a non-empty array of strings")
    raise UnsupportedCriticalHeaderError(
        "the token requires critical header extensions this module does not "
        f"implement: {', '.join(crit)}"
    )


def _validate_claims(
    claims: Mapping[str, Any],
    *,
    now: float,
    leeway: float,
    audience: str | Sequence[str] | None,
    issuer: str | Sequence[str] | None,
    require: Sequence[str] | str | None,
    allow_expired: bool,
) -> None:
    """Run every enabled claim check."""
    _check_required(claims, require)
    _check_time_claims(claims, now, leeway, not allow_expired)
    _check_audience(claims, audience)
    _check_issuer(claims, issuer)


# ===========================================================================
# Section 10: decode
# ===========================================================================


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
) -> dict[str, Any]:
    """Verify a compact JWS and return its claims.

    The algorithm comes from the token header, so *algorithms* is required:
    it is the allowlist the caller accepts.  ``"none"`` is never accepted, and
    the key type must match the algorithm, so an ``RS256`` token cannot be
    checked against an HMAC secret or the reverse.

    Args:
        token: Compact JWS text or ASCII bytes.
        key: The verification key.  HMAC algorithms take ``bytes``, ``str`` or
            an ``oct`` JWK; RSA and EC algorithms take a JWK mapping or
            :class:`JWKKey`.
        algorithms: Allowed ``alg`` values, for example ``["RS256"]``.
        audience: Expected ``aud`` value or values.  When given, a token with
            no ``aud`` claim raises :class:`MissingRequiredClaimError`.
        issuer: Expected ``iss`` value or values.
        leeway: Clock skew tolerance for ``exp``, ``nbf`` and ``iat``, in
            seconds or as a :class:`~datetime.timedelta`.  A negative or
            non-finite value raises ``ValueError``.
        require: Claims that must be present and non-null.
        verify_audience: Set to ``False`` to skip the ``aud`` check even when
            *audience* is given.  The ``aud`` claim is never checked unless
            *audience* is supplied.
        verify_expiry: Set to ``False`` to accept an expired token.  ``nbf``
            and ``iat`` are still enforced.
        now: Override the current time, in seconds since the epoch.

    Returns:
        The verified claims.

    Raises:
        DecodeError: The token is not a well-formed compact JWS.
        InvalidAlgorithmError: ``alg`` is absent, unsupported, not in
            *algorithms*, or is ``"none"``.
        UnsupportedCriticalHeaderError: The header's ``crit`` lists an
            extension this module does not implement.
        InvalidKeyError: The key is unusable or does not match the algorithm.
        InvalidSignatureError: The signature does not verify.
        ExpiredSignatureError: ``exp`` has passed.
        ImmatureSignatureError: ``nbf`` or ``iat`` is in the future.
        InvalidAudienceError: The ``aud`` claim does not match.
        InvalidIssuerError: The ``iss`` claim does not match.
        MissingRequiredClaimError: A required claim is absent or null.
        TypeError: *algorithms* is missing or empty, or *leeway* is invalid.
    """
    allowed = _normalize_algorithms(algorithms)
    jws = _parse(token)
    alg = jws.header["alg"]
    if alg.lower() == "none":
        raise InvalidAlgorithmError("unsigned tokens ('none') are never accepted")
    if alg not in allowed:
        raise InvalidAlgorithmError(
            f"algorithm {alg!r} is not in the accepted list "
            f"({', '.join(sorted(allowed))})"
        )
    if alg not in SUPPORTED_ALGORITHMS:
        raise InvalidAlgorithmError(f"algorithm {alg!r} is not supported")
    _check_critical_header(jws.header)
    if not _verify_signature(alg, key, jws.signing_input, jws.signature):
        raise InvalidSignatureError("the signature does not verify")
    _validate_claims(
        jws.claims,
        now=time.time() if now is None else float(now),
        leeway=_leeway_seconds(leeway),
        audience=audience if verify_audience else None,
        issuer=issuer,
        require=require,
        allow_expired=not verify_expiry,
    )
    return jws.claims


def _normalize_algorithms(algorithms: Sequence[str] | Set[str] | str) -> frozenset[str]:
    """Validate the caller's algorithm allowlist."""
    if algorithms is None:
        raise TypeError("decode() requires an explicit algorithms allowlist")
    if isinstance(algorithms, str):
        values = [algorithms]
    else:
        try:
            values = list(algorithms)
        except TypeError as exc:
            raise TypeError(
                "algorithms must be a string or an iterable of strings"
            ) from exc
    if not values:
        raise TypeError("algorithms must not be empty")
    for value in values:
        if not isinstance(value, str):
            raise TypeError(
                f"algorithms entries must be strings, got {type(value).__name__}"
            )
    return frozenset(values)


# ===========================================================================
# Section 11: Standalone ECDSA P-256 verification
# ===========================================================================


def ecdsa_p256_verify(
    pub: Any,
    msg: bytes,
    sig: bytes,
    *,
    der: bool = False,
) -> bool:
    """Verify an ECDSA P-256 (SHA-256) signature over *msg*.

    JWS carries signatures as fixed-width ``r || s``, and WebAuthn carries
    them as DER, so both forms are accepted.  The public key may be a JWK
    mapping, a :class:`JWKKey`, or an affine point ``(x, y)``.

    Args:
        pub: Public key: ``(x, y)`` integers, an EC ``JWKKey``, or a JWK
            mapping with ``kty="EC"`` and ``crv="P-256"``.
        msg: The signed message.
        sig: The signature: 64 bytes of raw ``r || s`` unless *der* is true.
        der: Read *sig* as a DER-encoded ``SEQUENCE`` of two integers.

    Returns:
        ``True`` when the signature is valid, ``False`` otherwise.  A malformed
        signature or an off-curve point is invalid, not an error.

    Raises:
        InvalidKeyError: *pub* is not a P-256 public key of a supported form.

    Examples:
        >>> generator = (_SECP256R1.gx, _SECP256R1.gy)
        >>> ecdsa_p256_verify(generator, b"msg", b"")  # empty is not a signature
        False
    """
    curve, qx, qy = _p256_point(pub)
    if not isinstance(sig, (bytes, bytearray, memoryview)):
        raise TypeError(f"sig must be bytes, got {type(sig).__name__}")
    raw = bytes(sig)
    if der:
        try:
            raw = _der_to_raw(raw, _field_size(curve))
        except DecodeError:
            return False
    return _ecdsa_verify(curve, qx, qy, bytes(msg), raw, _SHA256)


def _p256_point(pub: Any) -> tuple[_Curve, int, int]:
    """Coerce *pub* into a validated P-256 affine point."""
    if isinstance(pub, tuple) and len(pub) == 2:
        x, y = pub
        if not isinstance(x, int) or not isinstance(y, int):
            raise InvalidKeyError("an EC point must be a tuple of two integers")
        if not _on_curve(_SECP256R1, x, y):
            raise InvalidKeyError("the public key point is not on P-256")
        return _SECP256R1, x, y
    if isinstance(pub, (JWKKey, Mapping)):
        parsed = _as_jwk(pub)
        if parsed.kty != "EC":
            raise InvalidKeyError(f"expected an EC key, got kty={parsed.kty!r}")
        if parsed.crv != "P-256":
            raise InvalidKeyError(f"expected curve P-256, got {parsed.crv!r}")
        if parsed.x is None or parsed.y is None:
            raise InvalidKeyError("EC key is missing 'x' or 'y'")
        return _SECP256R1, parsed.x, parsed.y
    raise InvalidKeyError(
        f"expected (x, y), a JWK mapping or a JWKKey, got {type(pub).__name__}"
    )


# ===========================================================================
# Section 12: Optional libcrypto acceleration
# ===========================================================================

#: Sentinel meaning "the native load has not been attempted yet".
_NATIVE_UNSET = object()

#: ``_NATIVE_UNSET`` until a load is attempted; ``None`` when unavailable.
_native: Any = _NATIVE_UNSET
#: Guards the one-time load.  Created eagerly: lazy creation races, and two
#: racers can disagree about whether the accelerator loaded.
_native_lock = _thread.allocate_lock()
_load_error: str | None = None


def _native_libraries() -> list[str]:
    """Return candidate ``libcrypto`` names for this platform.

    Names are tried directly with :class:`ctypes.CDLL`, which lets the
    platform loader resolve them.  ``ctypes.util.find_library`` is avoided on
    purpose: it can shell out to ``ldconfig`` and cost hundreds of
    milliseconds.
    """
    if sys.platform == "win32":
        names = [
            "libcrypto-3-x64.dll",
            "libcrypto-3.dll",
            "libcrypto-1_1-x64.dll",
            "libcrypto-1_1.dll",
        ]
        # A CPython build from python.org keeps its OpenSSL DLLs here.  Only
        # absolute paths are used on Windows: the bare-name loader search order
        # includes the current directory, which is a DLL-hijack surface.
        dll_dir = os.path.join(sys.base_prefix, "DLLs")
        return [os.path.join(dll_dir, name) for name in names]
    if sys.platform == "darwin":
        return [
            "libcrypto.3.dylib",
            "/opt/homebrew/lib/libcrypto.dylib",
            "/usr/local/lib/libcrypto.dylib",
            "libcrypto.dylib",
        ]
    return ["libcrypto.so.3", "libcrypto.so.1.1", "libcrypto.so"]


def _try_load_libcrypto() -> _LibCrypto | None:
    """Load ``libcrypto`` and bind the primitives, or return ``None``."""
    global _load_error
    try:
        import ctypes
    except ImportError as exc:  # pragma: no cover - ctypes is always present
        _load_error = f"ctypes unavailable: {exc}"
        return None

    last_error: Exception | None = None
    for candidate in _native_libraries():
        try:
            library = ctypes.CDLL(candidate)
        except OSError as exc:
            last_error = exc
            continue
        try:
            return _LibCrypto(library, ctypes)
        except (AttributeError, OSError, TypeError) as exc:
            # A build without the symbols, for example OpenSSL configured with
            # ``no-deprecated``, which drops the EC_KEY_* and ECDSA_* family.
            last_error = exc
            continue
    _load_error = str(last_error) if last_error is not None else "not found"
    return None


def _native_backend() -> _LibCrypto | None:
    """Return the loaded backend, loading it once, or ``None``."""
    global _native
    if _native is not _NATIVE_UNSET:
        return _native
    with _native_lock:
        if _native is not _NATIVE_UNSET:
            return _native
        if os.environ.get("ZERODEP_JWT_BACKEND", "").strip().lower() == "python":
            _native = None
        else:
            try:
                _native = _try_load_libcrypto()
            except Exception:  # pragma: no cover - defensive: never break verify
                _native = None
        return _native


def _modexp(base: int, exponent: int, modulus: int) -> int:
    """Return ``base ** exponent % modulus``, natively when available."""
    backend = _native_backend()
    if backend is not None:
        try:
            return backend.modexp(base, exponent, modulus)
        except (MemoryError, RuntimeError, ValueError):
            # The pure implementation is the reference and stays correct, so a
            # native failure must not change a verification verdict.
            pass
    return pow(base, exponent, modulus)


def __getattr__(name: str) -> Any:
    """Resolve :data:`BACKEND` lazily so an HMAC-only import stays cheap."""
    if name == "BACKEND":
        return "openssl" if _native_backend() is not None else "python"
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


class _LibCrypto:
    """The two OpenSSL primitives this module needs, through :mod:`ctypes`.

    Only public key material crosses this boundary.  HMAC secrets never do:
    HMAC already runs in C inside :mod:`hmac` and :mod:`hashlib`.

    Every call owns its BIGNUMs, BN_CTX and EC_KEY objects and frees them in a
    ``finally`` block.  A shared BN_CTX is not thread-safe, so one is created
    per call.  Inputs are public and short-lived, so no zeroisation is needed.
    """

    #: Curve parameter sets to OpenSSL NIDs: prime256v1 and secp384r1.
    _CURVE_NIDS = {_SECP256R1.p: 415, _SECP384R1.p: 715}

    def __init__(self, library: Any, ctypes: Any) -> None:
        self._c = ctypes
        self._lib = library
        pointer = ctypes.c_void_p
        integer = ctypes.c_int
        size_t = ctypes.c_size_t

        def declare(name: str, argtypes: list[Any], restype: Any) -> Any:
            function = getattr(library, name)
            function.argtypes = argtypes
            function.restype = restype
            return function

        self._BN_new = declare("BN_new", [], pointer)
        self._BN_free = declare("BN_free", [pointer], None)
        self._BN_bin2bn = declare("BN_bin2bn", [pointer, integer, pointer], pointer)
        self._BN_bn2bin = declare("BN_bn2bin", [pointer, pointer], integer)
        self._BN_num_bits = declare("BN_num_bits", [pointer], integer)
        self._BN_CTX_new = declare("BN_CTX_new", [], pointer)
        self._BN_CTX_free = declare("BN_CTX_free", [pointer], None)
        self._BN_mod_exp = declare(
            "BN_mod_exp", [pointer, pointer, pointer, pointer, pointer], integer
        )

        self._EC_KEY_new_by_curve_name = declare(
            "EC_KEY_new_by_curve_name", [integer], pointer
        )
        self._EC_KEY_free = declare("EC_KEY_free", [pointer], None)
        self._EC_KEY_get0_group = declare("EC_KEY_get0_group", [pointer], pointer)
        self._EC_KEY_set_public_key = declare(
            "EC_KEY_set_public_key", [pointer, pointer], integer
        )
        self._EC_POINT_new = declare("EC_POINT_new", [pointer], pointer)
        self._EC_POINT_free = declare("EC_POINT_free", [pointer], None)
        self._EC_POINT_oct2point = declare(
            "EC_POINT_oct2point",
            [pointer, pointer, pointer, size_t, pointer],
            integer,
        )
        self._ECDSA_SIG_new = declare("ECDSA_SIG_new", [], pointer)
        self._ECDSA_SIG_free = declare("ECDSA_SIG_free", [pointer], None)
        self._ECDSA_SIG_set0 = declare(
            "ECDSA_SIG_set0", [pointer, pointer, pointer], integer
        )
        self._ECDSA_do_verify = declare(
            "ECDSA_do_verify", [pointer, integer, pointer, pointer], integer
        )
        self._ERR_clear_error = declare("ERR_clear_error", [], None)

    def _int_to_bn(self, value: int) -> Any:
        """Copy a non-negative integer into a new BIGNUM."""
        raw = value.to_bytes((value.bit_length() + 7) // 8 or 1, "big")
        buffer = self._c.create_string_buffer(raw, len(raw))
        bignum = self._BN_bin2bn(buffer, len(raw), None)
        if not bignum:
            self._ERR_clear_error()
            raise MemoryError("libcrypto could not allocate a BIGNUM")
        return bignum

    def modexp(self, base: int, exponent: int, modulus: int) -> int:
        """Return ``base ** exponent % modulus`` through ``BN_mod_exp``."""
        ctypes = self._c
        bn_base = bn_exponent = bn_modulus = result = context = None
        try:
            bn_base = self._int_to_bn(base)
            bn_exponent = self._int_to_bn(exponent)
            bn_modulus = self._int_to_bn(modulus)
            result = self._BN_new()
            context = self._BN_CTX_new()
            if not result or not context:
                self._ERR_clear_error()
                raise MemoryError("libcrypto could not allocate a BIGNUM context")
            if self._BN_mod_exp(result, bn_base, bn_exponent, bn_modulus, context) != 1:
                self._ERR_clear_error()
                raise RuntimeError("BN_mod_exp failed")
            size = (self._BN_num_bits(result) + 7) // 8
            buffer = ctypes.create_string_buffer(size or 1)
            self._BN_bn2bin(result, buffer)
            return int.from_bytes(buffer.raw[:size], "big")
        finally:
            for bignum in (bn_base, bn_exponent, bn_modulus, result):
                if bignum:
                    self._BN_free(bignum)
            if context:
                self._BN_CTX_free(context)

    def ecdsa_verify(
        self,
        curve: _Curve,
        qx: int,
        qy: int,
        msg: bytes,
        sig_raw: bytes,
        hash_ctor: Callable[[bytes], Any],
    ) -> bool | None:
        """Verify raw ``r || s`` with ``ECDSA_do_verify``.

        Returns ``True`` or ``False`` for a verdict, and ``None`` when OpenSSL
        reports an error, so the caller can fall back to the pure path.
        """
        ctypes = self._c
        size = _field_size(curve)
        nid = self._CURVE_NIDS.get(curve.p)
        if nid is None:
            return None
        key = self._EC_KEY_new_by_curve_name(nid)
        if not key:
            self._ERR_clear_error()
            return None
        point = None
        signature = None
        try:
            group = self._EC_KEY_get0_group(key)
            point = self._EC_POINT_new(group)
            if not point:
                self._ERR_clear_error()
                return None
            raw = b"\x04" + qx.to_bytes(size, "big") + qy.to_bytes(size, "big")
            buffer = ctypes.create_string_buffer(raw, len(raw))
            if self._EC_POINT_oct2point(group, point, buffer, len(raw), None) != 1:
                # The point passed the curve check, so this is an internal
                # error; let the pure path decide rather than reject a valid
                # signature.
                self._ERR_clear_error()
                return None
            if self._EC_KEY_set_public_key(key, point) != 1:
                self._ERR_clear_error()
                return None
            signature = self._ECDSA_SIG_new()
            if not signature:
                self._ERR_clear_error()
                return None
            bn_r = bn_s = None
            try:
                bn_r = self._int_to_bn(int.from_bytes(sig_raw[:size], "big"))
                bn_s = self._int_to_bn(int.from_bytes(sig_raw[size:], "big"))
                if self._ECDSA_SIG_set0(signature, bn_r, bn_s) != 1:
                    self._ERR_clear_error()
                    return None
                # ECDSA_SIG_set0 took ownership of both BIGNUMs.
                bn_r = bn_s = None
                digest = hash_ctor(msg).digest()
                digest_buffer = ctypes.create_string_buffer(digest, len(digest))
                verdict = self._ECDSA_do_verify(
                    digest_buffer, len(digest), signature, key
                )
                if verdict < 0:
                    self._ERR_clear_error()
                    return None
                return verdict == 1
            finally:
                if bn_r:
                    self._BN_free(bn_r)
                if bn_s:
                    self._BN_free(bn_s)
        finally:
            if signature:
                self._ECDSA_SIG_free(signature)
            if point:
                self._EC_POINT_free(point)
            self._EC_KEY_free(key)
