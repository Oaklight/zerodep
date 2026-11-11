"""Benchmark: zerodep jwt vs PyJWT[crypto].

PyJWT signs every token and both libraries verify it, so the numbers compare
pure-Python verification against the OpenSSL-backed C extension.
"""

import base64
import os
import sys
import time

import pytest

# Every case here takes the ``benchmark`` fixture. Without the plugin
# they would be reported as errors rather than skipped, which reads as a
# broken tree for anyone who installed the module without the extras.
pytest.importorskip("pytest_benchmark")

_this_dir = os.path.dirname(__file__)

# Our jwt.py shadows the PyJWT package. Hide this directory and the project
# root for the duration of the import, clear the stale cache, then put both
# back so the repo's own modules stay importable for the rest of the session.
_saved_path = sys.path[:]
sys.path = [
    p
    for p in sys.path
    if os.path.abspath(p)
    not in (
        os.path.abspath(_this_dir),
        os.path.abspath(os.path.join(_this_dir, "..")),
    )
]
_cached_jwt = {
    key: sys.modules.pop(key)
    for key in [k for k in sys.modules if k == "jwt" or k.startswith("jwt.")]
}

try:
    import jwt as _pyjwt

    if not hasattr(_pyjwt, "PyJWK") or os.path.abspath(
        getattr(_pyjwt, "__file__", "")
    ) == os.path.abspath(os.path.join(_this_dir, "jwt.py")):
        raise ImportError("Not the real PyJWT")
except ImportError:  # pragma: no cover - depends on the environment
    pytest.skip(
        "PyJWT not installed; install the bench-jwt extra: "
        "pip install -e '.[bench-jwt]'",
        allow_module_level=True,
    )
finally:
    sys.path = _saved_path
    for key in [k for k in sys.modules if k == "jwt" or k.startswith("jwt.")]:
        del sys.modules[key]
    sys.modules.update(_cached_jwt)

crypto = pytest.importorskip("cryptography", reason="PyJWT[crypto] not installed")
from cryptography.hazmat.primitives.asymmetric import ec, rsa  # noqa: E402

sys.path.insert(0, _this_dir)

from jwt import decode, encode  # noqa: E402


def _b64uint(value: int) -> str:
    raw = value.to_bytes(max(1, (value.bit_length() + 7) // 8), "big")
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


_RSA_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_rsa_numbers = _RSA_KEY.public_key().public_numbers()
_RSA_JWK = {
    "kty": "RSA",
    "n": _b64uint(_rsa_numbers.n),
    "e": _b64uint(_rsa_numbers.e),
}
_EC_KEY = ec.generate_private_key(ec.SECP256R1())
_ec_numbers = _EC_KEY.public_key().public_numbers()
_EC_JWK = {
    "kty": "EC",
    "crv": "P-256",
    "x": _b64uint(_ec_numbers.x),
    "y": _b64uint(_ec_numbers.y),
}
_HS_SECRET = b"benchmark-secret-key-0123456789abcdef"

now = int(time.time())
_CLAIMS = {
    "sub": "user-1234",
    "iss": "https://issuer.example",
    "aud": "api://resource",
    "iat": now,
    "exp": now + 3600,
    "scope": "read write",
}

_RSA_TOKEN = _pyjwt.encode(_CLAIMS, _RSA_KEY, algorithm="RS256")
_PS_TOKEN = _pyjwt.encode(_CLAIMS, _RSA_KEY, algorithm="PS256")
_ES_TOKEN = _pyjwt.encode(_CLAIMS, _EC_KEY, algorithm="ES256")
_HS_TOKEN = _pyjwt.encode(_CLAIMS, _HS_SECRET, algorithm="HS256")


class TestRsaVerify:
    """RS256 verification."""

    def test_pyjwt(self, benchmark):
        benchmark(
            _pyjwt.decode,
            _RSA_TOKEN,
            _RSA_KEY.public_key(),
            algorithms=["RS256"],
            audience="api://resource",
        )

    def test_zerodep(self, benchmark):
        benchmark(
            decode,
            _RSA_TOKEN,
            _RSA_JWK,
            algorithms=["RS256"],
            audience="api://resource",
        )


class TestRsaPssVerify:
    """PS256 verification."""

    def test_pyjwt(self, benchmark):
        benchmark(
            _pyjwt.decode,
            _PS_TOKEN,
            _RSA_KEY.public_key(),
            algorithms=["PS256"],
            audience="api://resource",
        )

    def test_zerodep(self, benchmark):
        benchmark(
            decode,
            _PS_TOKEN,
            _RSA_JWK,
            algorithms=["PS256"],
            audience="api://resource",
        )


class TestEcdsaVerify:
    """ES256 verification."""

    def test_pyjwt(self, benchmark):
        benchmark(
            _pyjwt.decode,
            _ES_TOKEN,
            _EC_KEY.public_key(),
            algorithms=["ES256"],
            audience="api://resource",
        )

    def test_zerodep(self, benchmark):
        benchmark(
            decode,
            _ES_TOKEN,
            _EC_JWK,
            algorithms=["ES256"],
            audience="api://resource",
        )


class TestHmacVerify:
    """HS256 verification."""

    def test_pyjwt(self, benchmark):
        benchmark(
            _pyjwt.decode,
            _HS_TOKEN,
            _HS_SECRET,
            algorithms=["HS256"],
            audience="api://resource",
        )

    def test_zerodep(self, benchmark):
        benchmark(
            decode,
            _HS_TOKEN,
            _HS_SECRET,
            algorithms=["HS256"],
            audience="api://resource",
        )


class TestHmacSign:
    """HS256 signing."""

    def test_pyjwt(self, benchmark):
        benchmark(_pyjwt.encode, _CLAIMS, _HS_SECRET, algorithm="HS256")

    def test_zerodep(self, benchmark):
        benchmark(encode, _CLAIMS, _HS_SECRET, algorithm="HS256")
