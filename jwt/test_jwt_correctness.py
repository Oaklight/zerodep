"""Correctness tests: zerodep jwt vs PyJWT[crypto].

Our module file ``jwt/jwt.py`` and its directory shadow the PyJWT ``jwt``
package, so the real PyJWT is imported first through a temporary sys.path and
sys.modules manipulation, sanity-checked, and put back.  Every comparison in
this file signs with PyJWT and verifies with ours (and the reverse for HMAC),
so a shadowed import fails loudly instead of comparing our module with itself.
"""

import base64
import hashlib
import hmac
import json
import os
import subprocess
import sys
import time

import pytest

_this_dir = os.path.dirname(__file__)

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

    # PyJWT has no ``eyJ``-free marker, so check for API this module lacks.
    if not hasattr(_pyjwt, "DecodeError") or not hasattr(_pyjwt, "PyJWK"):
        raise ImportError("Not the real PyJWT")
    if os.path.abspath(getattr(_pyjwt, "__file__", "")) == os.path.abspath(
        os.path.join(_this_dir, "jwt.py")
    ):
        raise ImportError("Resolved our own jwt.py instead of PyJWT")
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
from cryptography.hazmat.primitives import (
    hashes,  # noqa: E402
    serialization,  # noqa: E402
)
from cryptography.hazmat.primitives.asymmetric import (  # noqa: E402
    ec,
    padding,
    rsa,
)
from cryptography.hazmat.primitives.asymmetric.utils import (  # noqa: E402
    decode_dss_signature,
)

sys.path.insert(0, _this_dir)

from jwt import (  # noqa: E402
    DecodeError,
    ExpiredSignatureError,
    ImmatureSignatureError,
    InvalidAlgorithmError,
    InvalidAudienceError,
    InvalidIssuerError,
    InvalidKeyError,
    InvalidSignatureError,
    JWKKey,
    JWTError,
    MissingRequiredClaimError,
    UnsupportedCriticalHeaderError,
    b64url_decode,
    b64url_encode,
    decode,
    ecdsa_p256_verify,
    encode,
    get_unverified_claims,
    get_unverified_header,
    key_from_jwk,
)

# ── Helpers ──


def _b64uint(value: int) -> str:
    raw = value.to_bytes(max(1, (value.bit_length() + 7) // 8), "big")
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _rsa_jwk(pub) -> dict:
    nums = pub.public_numbers()
    return {"kty": "RSA", "n": _b64uint(nums.n), "e": _b64uint(nums.e)}


def _ec_jwk(pub) -> dict:
    nums = pub.public_numbers()
    crv = "P-256" if isinstance(pub.curve, ec.SECP256R1) else "P-384"
    return {"kty": "EC", "crv": crv, "x": _b64uint(nums.x), "y": _b64uint(nums.y)}


def _oct_jwk(secret: bytes) -> dict:
    return {"kty": "oct", "k": base64.urlsafe_b64encode(secret).rstrip(b"=").decode()}


_RSA_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_RSA_JWK = _rsa_jwk(_RSA_KEY.public_key())
_EC_P256 = ec.generate_private_key(ec.SECP256R1())
_EC_P384 = ec.generate_private_key(ec.SECP384R1())
_EC_P256_JWK = _ec_jwk(_EC_P256.public_key())
_EC_P384_JWK = _ec_jwk(_EC_P384.public_key())

_HS_SECRET = b"a-secret-that-is-long-enough-for-hmac"

_RSA_ALGS = ["RS256", "RS384", "RS512", "PS256", "PS384", "PS512"]
_EC_ALGS = ["ES256", "ES384"]
_HS_ALGS = ["HS256", "HS384", "HS512"]


def _rsa_token(alg: str, claims: dict | None = None) -> str:
    return _pyjwt.encode(claims or {"sub": "alice"}, _RSA_KEY, algorithm=alg)


def _ec_token(alg: str, claims: dict | None = None) -> str:
    key = _EC_P256 if alg == "ES256" else _EC_P384
    return _pyjwt.encode(claims or {"sub": "alice"}, key, algorithm=alg)


def _forge_hs256(secret: bytes) -> str:
    """Build an HS256 token by hand, as an attacker holding a public key would.

    Neither library will sign with an asymmetric key, so the attack token is
    assembled from stdlib primitives: that is exactly what an attacker has.
    """
    header = b64url_encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload = b64url_encode(json.dumps({"sub": "attacker"}).encode())
    signing_input = f"{header}.{payload}".encode()
    signature = hmac.new(secret, signing_input, hashlib.sha256).digest()
    return f"{header}.{payload}.{b64url_encode(signature)}"


def _ec_jwk_for(alg: str) -> dict:
    return _EC_P256_JWK if alg == "ES256" else _EC_P384_JWK


# ── base64url ──


class TestBase64Url:
    """The encoding helpers follow RFC 4648 section 5 without padding."""

    @pytest.mark.parametrize(
        "data",
        [b"", b"f", b"fo", b"foo", b"foob", b"fooba", b"foobar", bytes(range(256))],
    )
    def test_round_trip(self, data):
        assert b64url_decode(b64url_encode(data)) == data

    def test_matches_stdlib(self):
        data = b"\xfb\xff\xfe any bytes?"
        expected = base64.urlsafe_b64encode(data).rstrip(b"=").decode()
        assert b64url_encode(data) == expected

    def test_encode_has_no_padding(self):
        assert "=" not in b64url_encode(b"\x00\x00")

    @pytest.mark.parametrize("bad", ["a", "ab=", "a+b/", "ab cd", "é"])
    def test_decode_rejects_bad_input(self, bad):
        with pytest.raises(DecodeError):
            b64url_decode(bad)

    def test_decode_accepts_bytes(self):
        assert b64url_decode(b"Zm9v") == b"foo"

    def test_encode_rejects_str(self):
        with pytest.raises(TypeError):
            b64url_encode("foo")  # type: ignore[arg-type]


# ── get_unverified_header / parse ──


class TestUnverifiedAccess:
    """Header and claim access works without a key and never verifies."""

    def test_header(self):
        token = _rsa_token("RS256", {"sub": "alice"})
        header = get_unverified_header(token)
        assert header["alg"] == "RS256"
        assert header["typ"] == "JWT"

    def test_claims(self):
        token = _rsa_token("RS256", {"sub": "alice", "n": 1})
        assert get_unverified_claims(token) == {"sub": "alice", "n": 1}

    def test_returns_a_copy(self):
        token = _rsa_token("RS256", {"sub": "alice"})
        get_unverified_header(token)["alg"] = "none"
        assert get_unverified_header(token)["alg"] == "RS256"

    @pytest.mark.parametrize(
        "token",
        [
            "",
            "abc",
            "a.b",
            "a.b.c.d",
            "!!!.e30.abc",
            "eyJhbGciOiJSUzI1NiJ9.e30",  # two parts
        ],
    )
    def test_malformed(self, token):
        with pytest.raises(DecodeError):
            get_unverified_header(token)

    def test_payload_must_be_object(self):
        header = b64url_encode(b'{"alg":"HS256"}')
        payload = b64url_encode(b"[1,2]")
        with pytest.raises(DecodeError):
            get_unverified_header(f"{header}.{payload}.")

    def test_missing_alg(self):
        header = b64url_encode(b'{"typ":"JWT"}')
        payload = b64url_encode(b"{}")
        with pytest.raises(DecodeError):
            get_unverified_header(f"{header}.{payload}.")

    def test_accepts_bytes(self):
        token = _rsa_token("RS256")
        assert get_unverified_header(token.encode())["alg"] == "RS256"


# ── Signature verification, PyJWT signs and we verify ──


class TestVerifyRsa:
    """RS* and PS* verification matches PyJWT."""

    @pytest.mark.parametrize("alg", _RSA_ALGS)
    def test_round_trip(self, alg):
        token = _rsa_token(alg, {"sub": "alice", "iss": "https://issuer"})
        claims = decode(token, _RSA_JWK, algorithms=[alg])
        assert claims == {"sub": "alice", "iss": "https://issuer"}

    @pytest.mark.parametrize("alg", _RSA_ALGS)
    def test_accepts_jwkkey(self, alg):
        token = _rsa_token(alg)
        claims = decode(token, key_from_jwk(_RSA_JWK), algorithms=[alg])
        assert claims["sub"] == "alice"

    @pytest.mark.parametrize("alg", _RSA_ALGS)
    def test_tampered_signature(self, alg):
        token = _rsa_token(alg)
        head, payload, sig = token.split(".")
        flipped = bytearray(b64url_decode(sig))
        flipped[0] ^= 0x01
        tampered = f"{head}.{payload}.{b64url_encode(bytes(flipped))}"
        with pytest.raises(InvalidSignatureError):
            decode(tampered, _RSA_JWK, algorithms=[alg])

    def test_tampered_payload(self):
        token = _rsa_token("RS256", {"sub": "alice"})
        head, _payload, sig = token.split(".")
        forged = b64url_encode(json.dumps({"sub": "root"}).encode())
        with pytest.raises(InvalidSignatureError):
            decode(f"{head}.{forged}.{sig}", _RSA_JWK, algorithms=["RS256"])

    def test_wrong_key(self):
        other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        token = _rsa_token("RS256")
        with pytest.raises(InvalidSignatureError):
            decode(token, _rsa_jwk(other.public_key()), algorithms=["RS256"])

    def test_truncated_signature(self):
        token = _rsa_token("RS256")
        head, payload, sig = token.split(".")
        short = b64url_encode(b64url_decode(sig)[:-8])
        with pytest.raises(InvalidSignatureError):
            decode(f"{head}.{payload}.{short}", _RSA_JWK, algorithms=["RS256"])

    def test_pkcs1_signature_rejected_by_pss(self):
        """A PKCS1-v1_5 signature over the same input is not a valid PSS one."""
        token = _rsa_token("PS256")
        head, payload, _sig = token.split(".")
        signing_input = f"{head}.{payload}".encode()
        pkcs1 = _RSA_KEY.sign(signing_input, padding.PKCS1v15(), hashes.SHA256())
        with pytest.raises(InvalidSignatureError):
            decode(
                f"{head}.{payload}.{b64url_encode(pkcs1)}",
                _RSA_JWK,
                algorithms=["PS256"],
            )

    def test_pss_signature_rejected_by_pkcs1(self):
        """A PSS signature is not a valid PKCS1-v1_5 one."""
        token = _rsa_token("RS256")
        head, payload, _sig = token.split(".")
        signing_input = f"{head}.{payload}".encode()
        pss = _RSA_KEY.sign(
            signing_input,
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=32),
            hashes.SHA256(),
        )
        with pytest.raises(InvalidSignatureError):
            decode(
                f"{head}.{payload}.{b64url_encode(pss)}", _RSA_JWK, algorithms=["RS256"]
            )

    def test_weak_modulus_rejected(self):
        weak = rsa.generate_private_key(public_exponent=65537, key_size=1024)
        token = _pyjwt.encode({"sub": "a"}, weak, algorithm="RS256")
        with pytest.raises(InvalidKeyError):
            decode(token, _rsa_jwk(weak.public_key()), algorithms=["RS256"])


class TestVerifyEc:
    """ES* verification matches PyJWT."""

    @pytest.mark.parametrize("alg", _EC_ALGS)
    def test_round_trip(self, alg):
        token = _ec_token(alg, {"sub": "alice"})
        assert decode(token, _ec_jwk_for(alg), algorithms=[alg]) == {"sub": "alice"}

    @pytest.mark.parametrize("alg", _EC_ALGS)
    def test_tampered_signature(self, alg):
        token = _ec_token(alg)
        head, payload, sig = token.split(".")
        flipped = bytearray(b64url_decode(sig))
        flipped[-1] ^= 0x01
        with pytest.raises(InvalidSignatureError):
            decode(
                f"{head}.{payload}.{b64url_encode(bytes(flipped))}",
                _ec_jwk_for(alg),
                algorithms=[alg],
            )

    def test_wrong_curve(self):
        token = _ec_token("ES256")
        with pytest.raises(InvalidKeyError):
            decode(token, _EC_P384_JWK, algorithms=["ES256"])

    def test_out_of_range_r_s(self):
        token = _ec_token("ES256")
        head, payload, _sig = token.split(".")
        zero_sig = b"\x00" * 64
        with pytest.raises(InvalidSignatureError):
            decode(
                f"{head}.{payload}.{b64url_encode(zero_sig)}",
                _EC_P256_JWK,
                algorithms=["ES256"],
            )


class TestVerifyHmac:
    """HS* signing and verification work in both directions."""

    @pytest.mark.parametrize("alg", _HS_ALGS)
    def test_ours_accepted_by_pyjwt(self, alg):
        token = encode({"sub": "alice"}, _HS_SECRET, algorithm=alg)
        assert _pyjwt.decode(token, _HS_SECRET, algorithms=[alg]) == {"sub": "alice"}

    @pytest.mark.parametrize("alg", _HS_ALGS)
    def test_pyjwt_accepted_by_ours(self, alg):
        token = _pyjwt.encode({"sub": "alice"}, _HS_SECRET, algorithm=alg)
        assert decode(token, _HS_SECRET, algorithms=[alg]) == {"sub": "alice"}

    @pytest.mark.parametrize("alg", _HS_ALGS)
    def test_str_secret(self, alg):
        token = encode({"sub": "alice"}, "secret", algorithm=alg)
        assert decode(token, "secret", algorithms=[alg]) == {"sub": "alice"}

    def test_oct_jwk(self, alg="HS256"):
        token = encode({"sub": "alice"}, _oct_jwk(_HS_SECRET), algorithm=alg)
        assert decode(token, _oct_jwk(_HS_SECRET), algorithms=[alg]) == {"sub": "alice"}

    def test_wrong_secret(self):
        token = encode({"sub": "alice"}, _HS_SECRET)
        with pytest.raises(InvalidSignatureError):
            decode(token, b"other-secret", algorithms=["HS256"])

    def test_pem_public_key_rejected_as_secret(self):
        """A PEM public key is public data and must not sign or verify HS*."""
        pem = _RSA_KEY.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        with pytest.raises(InvalidKeyError):
            encode({"sub": "attacker"}, pem, algorithm="HS256")
        forged = _forge_hs256(pem)
        with pytest.raises(InvalidKeyError):
            decode(forged, pem, algorithms=["HS256"])

    @pytest.mark.parametrize("open_ssh", [True, False], ids=["ssh-rsa", "ecdsa"])
    def test_openssh_public_key_rejected_as_secret(self, open_ssh):
        key = _RSA_KEY if open_ssh else _EC_P256
        openssh = key.public_key().public_bytes(
            serialization.Encoding.OpenSSH, serialization.PublicFormat.OpenSSH
        )
        with pytest.raises(InvalidKeyError):
            encode({"sub": "attacker"}, openssh, algorithm="HS256")
        with pytest.raises(InvalidKeyError):
            decode(_forge_hs256(openssh), openssh, algorithms=["HS256"])

    def test_str_secret_with_leading_space_still_works(self):
        """The prefix guard only rejects key material, not an odd secret."""
        token = encode({"sub": "a"}, b"  padded secret", algorithm="HS256")
        assert decode(token, b"  padded secret", algorithms=["HS256"])["sub"] == "a"

    def test_extra_headers(self):
        token = encode({"sub": "a"}, _HS_SECRET, headers={"kid": "key-1"})
        assert get_unverified_header(token)["kid"] == "key-1"

    def test_alg_header_cannot_override(self):
        token = encode({"sub": "a"}, _HS_SECRET, headers={"alg": "none"})
        assert get_unverified_header(token)["alg"] == "HS256"

    @pytest.mark.parametrize("alg", ["RS256", "ES256", "PS512", "none", "HS999"])
    def test_encode_rejects_non_hmac(self, alg):
        with pytest.raises(InvalidAlgorithmError):
            encode({"sub": "a"}, _HS_SECRET, algorithm=alg)

    def test_encode_rejects_mapping_claims(self):
        with pytest.raises(TypeError):
            encode(["not", "a", "mapping"], _HS_SECRET)  # type: ignore[arg-type]


# ── Algorithm allowlist and confusion ──


def _force_alg(token: str, alg: str) -> str:
    """Rewrite a token header's alg, keeping the original signature."""
    head, payload, sig = token.split(".")
    header = json.loads(b64url_decode(head))
    header["alg"] = alg
    new_header = b64url_encode(json.dumps(header, separators=(",", ":")).encode())
    return f"{new_header}.{payload}.{sig}"


class TestAlgorithms:
    """The allowlist is required and key type must match the algorithm."""

    def test_algorithms_required(self):
        token = _rsa_token("RS256")
        with pytest.raises(TypeError):
            decode(token, _RSA_JWK)  # type: ignore[call-arg]

    def test_empty_allowlist(self):
        token = _rsa_token("RS256")
        with pytest.raises(TypeError):
            decode(token, _RSA_JWK, algorithms=[])

    def test_alg_outside_allowlist(self):
        token = _rsa_token("RS256")
        with pytest.raises(InvalidAlgorithmError):
            decode(token, _RSA_JWK, algorithms=["RS512"])

    def test_unknown_alg(self):
        token = _rsa_token("RS256")
        with pytest.raises(InvalidAlgorithmError):
            decode(token, _RSA_JWK, algorithms=["XY256"])

    def test_none_never_accepted(self):
        token = _rsa_token("RS256")
        unsigned = _force_alg(token, "none")
        with pytest.raises(InvalidAlgorithmError):
            decode(unsigned, _RSA_JWK, algorithms=["none"])

    def test_none_case_insensitive(self):
        token = _rsa_token("RS256")
        unsigned = _force_alg(token, "NoNe")
        with pytest.raises(InvalidAlgorithmError):
            decode(unsigned, _RSA_JWK, algorithms=["NoNe"])

    def test_rs_token_with_hmac_secret(self):
        token = _rsa_token("RS256")
        with pytest.raises(InvalidKeyError):
            decode(token, _HS_SECRET, algorithms=["RS256"])

    def test_hs_token_with_rsa_jwk(self):
        token = _pyjwt.encode({"sub": "a"}, _HS_SECRET, algorithm="HS256")
        with pytest.raises(InvalidKeyError):
            decode(token, _RSA_JWK, algorithms=["HS256"])

    def test_es_token_with_rsa_jwk(self):
        token = _ec_token("ES256")
        with pytest.raises(InvalidKeyError):
            decode(token, _RSA_JWK, algorithms=["ES256"])

    def test_jwk_alg_mismatch(self):
        jwk = dict(_RSA_JWK, alg="RS512")
        token = _rsa_token("RS256")
        with pytest.raises(InvalidKeyError):
            decode(token, jwk, algorithms=["RS256"])

    def test_jwk_alg_match(self):
        jwk = dict(_RSA_JWK, alg="RS256")
        token = _rsa_token("RS256")
        assert decode(token, jwk, algorithms=["RS256"])["sub"] == "alice"

    def test_crit_extension_rejected(self):
        """RFC 7515 4.1.11: an unimplemented critical extension invalidates."""
        token = encode({"sub": "a"}, _HS_SECRET, headers={"crit": ["exp"]})
        with pytest.raises(UnsupportedCriticalHeaderError):
            decode(token, _HS_SECRET, algorithms=["HS256"])

    @pytest.mark.parametrize(
        "crit", [[], "exp", [1]], ids=["empty", "string", "non-string-entry"]
    )
    def test_malformed_crit_rejected(self, crit):
        token = encode({"sub": "a"}, _HS_SECRET, headers={"crit": crit})
        with pytest.raises(DecodeError):
            decode(token, _HS_SECRET, algorithms=["HS256"])

    def test_absent_crit_is_fine(self):
        token = encode({"sub": "a"}, _HS_SECRET)
        assert decode(token, _HS_SECRET, algorithms=["HS256"])["sub"] == "a"

    @pytest.mark.parametrize(
        ("alg", "key"),
        [
            ("HS256", lambda: JWKKey(kty="oct")),
            ("RS256", lambda: JWKKey(kty="RSA")),
            ("ES256", lambda: JWKKey(kty="EC")),
        ],
    )
    def test_incomplete_jwkkey_raises_key_error(self, alg, key):
        """A hand-built JWKKey with missing members is a key error, not an assert."""
        signer = _HS_SECRET if alg == "HS256" else None
        if alg == "RS256":
            token = _rsa_token(alg)
        elif alg == "ES256":
            token = _ec_token(alg)
        else:
            token = _pyjwt.encode({"sub": "a"}, signer, algorithm=alg)
        with pytest.raises(InvalidKeyError):
            decode(token, key(), algorithms=[alg])

    def test_incomplete_jwkkey_under_python_optimized(self):
        """The same error must survive ``python -O``, where asserts vanish."""
        code = (
            "import sys; sys.path.insert(0, {path!r})\n"
            "import jwt\n"
            "token = jwt.encode({{'sub': 'a'}}, b'secret')\n"
            "try:\n"
            "    jwt.decode(token, jwt.JWKKey(kty='oct'), algorithms=['HS256'])\n"
            "except jwt.InvalidKeyError:\n"
            "    raise SystemExit(0)\n"
            "raise SystemExit(1)\n"
        ).format(path=_this_dir)
        result = subprocess.run(
            [sys.executable, "-O", "-c", code], capture_output=True, text=True
        )
        assert result.returncode == 0, result.stderr

    def test_supported_algorithms_constant(self):
        from jwt import SUPPORTED_ALGORITHMS

        assert SUPPORTED_ALGORITHMS == frozenset(_RSA_ALGS + _EC_ALGS + _HS_ALGS)


# ── JWK parsing ──


class TestJwk:
    """Bad keys raise InvalidKeyError rather than an obscure error."""

    def test_rsa(self):
        key = key_from_jwk(_RSA_JWK)
        assert key.kty == "RSA"
        assert key.n == _RSA_KEY.public_key().public_numbers().n

    def test_ec(self):
        key = key_from_jwk(_EC_P256_JWK)
        assert key.kty == "EC"
        assert key.crv == "P-256"

    def test_kid_and_alg(self):
        key = key_from_jwk(dict(_RSA_JWK, kid="k1", alg="RS256"))
        assert key.kid == "k1"
        assert key.alg == "RS256"

    def test_oct_secret_hidden_in_repr(self):
        key = key_from_jwk(_oct_jwk(b"super-secret"))
        assert "super-secret" not in repr(key)
        assert key.secret == b"super-secret"

    @pytest.mark.parametrize(
        "jwk",
        [
            {},
            {"kty": "OKP"},
            {"kty": "RSA"},
            {"kty": "RSA", "n": "AQAB"},
            {"kty": "RSA", "n": "", "e": "AQAB"},
            {"kty": "RSA", "n": "AQAB", "e": "AQAB"},
            {"kty": "oct", "k": ""},
            {"kty": "EC", "crv": "P-521", "x": "AQ", "y": "AQ"},
            {"kty": "EC", "crv": "P-256", "x": "AQ", "y": "AQ"},
            {"kty": "EC", "crv": "P-256"},
            {"kty": "EC", "crv": 256, "x": "AQ", "y": "AQ"},
            {"kty": "RSA", "n": "AQAB", "e": "AQAB", "kid": 7},
        ],
    )
    def test_invalid(self, jwk):
        with pytest.raises(InvalidKeyError):
            key_from_jwk(jwk)

    def test_not_a_mapping(self):
        with pytest.raises(InvalidKeyError):
            key_from_jwk([1, 2, 3])  # type: ignore[arg-type]

    def test_point_not_on_curve_rejected(self):
        jwk = {"kty": "EC", "crv": "P-256", "x": _b64uint(1), "y": _b64uint(1)}
        with pytest.raises(InvalidKeyError):
            key_from_jwk(jwk)

    def test_invalid_base64_in_field(self):
        with pytest.raises(InvalidKeyError):
            key_from_jwk({"kty": "RSA", "n": "!!!", "e": "AQAB"})

    @pytest.mark.parametrize(
        "jwk",
        [
            {"kty": "RSA", "n": 5, "e": "AQAB"},
            {"kty": "RSA", "n": "AQAB", "e": None},
            {"kty": "EC", "crv": "P-256", "x": 1, "y": "AQ"},
            {"kty": "oct", "k": 7},
        ],
        ids=["int-n", "null-e", "int-x", "int-k"],
    )
    def test_non_string_field_is_a_key_error(self, jwk):
        """A non-string member is a key error, not a bare TypeError."""
        with pytest.raises(InvalidKeyError):
            key_from_jwk(jwk)

    def test_short_rsa_modulus_refused_at_key_load(self):
        """The 2048-bit floor is enforced by key_from_jwk, not only by decode."""
        weak = rsa.generate_private_key(public_exponent=65537, key_size=1024)
        with pytest.raises(InvalidKeyError, match=r"1024 bits"):
            key_from_jwk(_rsa_jwk(weak.public_key()))

    def test_hand_built_rsa_jwkkey_below_floor_refused(self):
        """A JWKKey built by hand bypasses key_from_jwk; decode still refuses."""
        weak = rsa.generate_private_key(public_exponent=65537, key_size=1024)
        numbers = weak.public_key().public_numbers()
        token = _pyjwt.encode({"sub": "a"}, weak, algorithm="RS256")
        hand = JWKKey(kty="RSA", n=numbers.n, e=numbers.e)
        with pytest.raises(InvalidKeyError, match=r"1024 bits"):
            decode(token, hand, algorithms=["RS256"])


# ── Claims ──


# ── Claims ──


class TestClaims:
    """Time, issuer, audience and required-claim checks match PyJWT semantics."""

    def _token(self, claims, alg="HS256"):
        return encode(claims, _HS_SECRET, algorithm=alg)

    def test_expired(self):
        token = self._token({"exp": time.time() - 10})
        with pytest.raises(ExpiredSignatureError):
            decode(token, _HS_SECRET, algorithms=["HS256"])

    def test_exp_leeway(self):
        token = self._token({"exp": time.time() - 10})
        assert decode(token, _HS_SECRET, algorithms=["HS256"], leeway=30)["exp"]

    def test_exp_leeway_timedelta(self):
        from datetime import timedelta

        token = self._token({"exp": time.time() - 10})
        claims = decode(
            token, _HS_SECRET, algorithms=["HS256"], leeway=timedelta(seconds=30)
        )
        assert "exp" in claims

    def test_exp_exact_boundary(self):
        token = self._token({"exp": 1000})
        with pytest.raises(ExpiredSignatureError):
            decode(token, _HS_SECRET, algorithms=["HS256"], now=1000)

    def test_verify_expiry_false(self):
        token = self._token({"exp": time.time() - 10})
        assert decode(token, _HS_SECRET, algorithms=["HS256"], verify_expiry=False)[
            "exp"
        ]

    def test_nbf_in_future(self):
        token = self._token({"nbf": time.time() + 60})
        with pytest.raises(ImmatureSignatureError):
            decode(token, _HS_SECRET, algorithms=["HS256"])

    def test_nbf_leeway(self):
        token = self._token({"nbf": time.time() + 60})
        assert decode(token, _HS_SECRET, algorithms=["HS256"], leeway=120)["nbf"]

    def test_nbf_still_enforced_with_verify_expiry_false(self):
        token = self._token({"nbf": time.time() + 60})
        with pytest.raises(ImmatureSignatureError):
            decode(token, _HS_SECRET, algorithms=["HS256"], verify_expiry=False)

    def test_iat_in_future(self):
        token = self._token({"iat": time.time() + 60})
        with pytest.raises(ImmatureSignatureError):
            decode(token, _HS_SECRET, algorithms=["HS256"])

    @pytest.mark.parametrize("claim", ["exp", "nbf", "iat"])
    def test_non_numeric_time_claim(self, claim):
        token = self._token({claim: "tomorrow"})
        with pytest.raises(DecodeError):
            decode(token, _HS_SECRET, algorithms=["HS256"])

    def test_issuer(self):
        token = self._token({"iss": "https://issuer.example"})
        assert decode(
            token, _HS_SECRET, algorithms=["HS256"], issuer="https://issuer.example"
        )["iss"]

    def test_issuer_list(self):
        token = self._token({"iss": "b"})
        claims = decode(token, _HS_SECRET, algorithms=["HS256"], issuer=["a", "b"])
        assert claims["iss"] == "b"

    def test_wrong_issuer(self):
        token = self._token({"iss": "https://evil.example"})
        with pytest.raises(InvalidIssuerError):
            decode(token, _HS_SECRET, algorithms=["HS256"], issuer="https://issuer")

    def test_missing_issuer(self):
        token = self._token({"sub": "a"})
        with pytest.raises(MissingRequiredClaimError):
            decode(token, _HS_SECRET, algorithms=["HS256"], issuer="https://issuer")

    def test_issuer_unchecked_without_argument(self):
        token = self._token({"iss": "anything"})
        assert decode(token, _HS_SECRET, algorithms=["HS256"])["iss"] == "anything"

    def test_audience(self):
        token = self._token({"aud": "api://mine"})
        assert decode(token, _HS_SECRET, algorithms=["HS256"], audience="api://mine")[
            "aud"
        ]

    def test_audience_list_claim(self):
        token = self._token({"aud": ["a", "b"]})
        assert decode(token, _HS_SECRET, algorithms=["HS256"], audience="b")["aud"]

    def test_audience_any_of(self):
        token = self._token({"aud": "b"})
        claims = decode(token, _HS_SECRET, algorithms=["HS256"], audience=["a", "b"])
        assert claims["aud"] == "b"

    def test_wrong_audience(self):
        token = self._token({"aud": "api://other"})
        with pytest.raises(InvalidAudienceError):
            decode(token, _HS_SECRET, algorithms=["HS256"], audience="api://mine")

    def test_missing_audience(self):
        token = self._token({"sub": "a"})
        with pytest.raises(MissingRequiredClaimError):
            decode(token, _HS_SECRET, algorithms=["HS256"], audience="api://mine")

    def test_audience_disabled(self):
        token = self._token({"aud": "api://other"})
        claims = decode(
            token,
            _HS_SECRET,
            algorithms=["HS256"],
            audience="api://mine",
            verify_audience=False,
        )
        assert claims["aud"] == "api://other"

    def test_audience_unchecked_without_argument(self):
        token = self._token({"aud": "anything"})
        assert decode(token, _HS_SECRET, algorithms=["HS256"])["aud"] == "anything"

    def test_require_present(self):
        token = self._token({"sub": "a", "scope": "read"})
        claims = decode(
            token, _HS_SECRET, algorithms=["HS256"], require=["sub", "scope"]
        )
        assert claims["scope"] == "read"

    def test_require_missing(self):
        token = self._token({"sub": "a"})
        with pytest.raises(MissingRequiredClaimError):
            decode(token, _HS_SECRET, algorithms=["HS256"], require=["scope"])

    def test_require_null(self):
        token = self._token({"sub": None})
        with pytest.raises(MissingRequiredClaimError):
            decode(token, _HS_SECRET, algorithms=["HS256"], require=["sub"])

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (float("nan"), "finite"),
            (float("inf"), "finite"),
            (float("-inf"), "finite"),
            (float("1e400"), "finite"),
            (10**400, "out of range"),
        ],
        ids=["nan", "inf", "neg-inf", "1e400", "huge-int"],
    )
    def test_non_finite_time_claim_rejected(self, value, expected):
        """``exp: NaN`` must not pass, and a huge int must not escape as

        OverflowError.  Both would otherwise leave a token that never expires.
        """
        token = self._token({"exp": value})
        with pytest.raises(DecodeError, match=expected):
            decode(token, _HS_SECRET, algorithms=["HS256"])

    @pytest.mark.parametrize("claim", ["nbf", "iat"])
    def test_non_finite_other_time_claims_rejected(self, claim):
        token = self._token({claim: float("nan")})
        with pytest.raises(DecodeError):
            decode(token, _HS_SECRET, algorithms=["HS256"])

    def test_empty_audience_claim_is_missing(self):
        """``aud: ""`` is absent, matching PyJWT."""
        token = self._token({"aud": ""})
        with pytest.raises(MissingRequiredClaimError):
            decode(token, _HS_SECRET, algorithms=["HS256"], audience="api://mine")
        pyjwt_token = _pyjwt.encode({"aud": ""}, _HS_SECRET, algorithm="HS256")
        with pytest.raises(_pyjwt.exceptions.MissingRequiredClaimError):
            _pyjwt.decode(
                pyjwt_token, _HS_SECRET, algorithms=["HS256"], audience="api://mine"
            )

    def test_require_not_iterable(self):
        token = self._token({"sub": "a"})
        with pytest.raises(TypeError, match="require"):
            decode(token, _HS_SECRET, algorithms=["HS256"], require=5)

    def test_require_non_string_entry(self):
        token = self._token({"sub": "a"})
        with pytest.raises(TypeError, match="claim names"):
            decode(token, _HS_SECRET, algorithms=["HS256"], require=[5])

    def test_now_override(self):
        token = self._token({"exp": 5000})
        assert decode(token, _HS_SECRET, algorithms=["HS256"], now=4000)["exp"]
        with pytest.raises(ExpiredSignatureError):
            decode(token, _HS_SECRET, algorithms=["HS256"], now=6000)

    def test_negative_leeway_rejected(self):
        token = self._token({"sub": "a"})
        with pytest.raises(ValueError):
            decode(token, _HS_SECRET, algorithms=["HS256"], leeway=-1)

    def test_negative_timedelta_leeway_rejected(self):
        """The timedelta path applies the same negative check as the float one."""
        from datetime import timedelta

        token = self._token({"sub": "a"})
        with pytest.raises(ValueError):
            decode(
                token,
                _HS_SECRET,
                algorithms=["HS256"],
                leeway=timedelta(seconds=-5),
            )

    def test_bad_leeway_type(self):
        token = self._token({"sub": "a"})
        with pytest.raises(TypeError):
            decode(token, _HS_SECRET, algorithms=["HS256"], leeway="30")  # type: ignore[arg-type]

    @pytest.mark.parametrize(
        ("claims", "kwargs"),
        [
            ({"exp": time.time() - 60}, {}),
            ({"exp": time.time() + 3600}, {}),
            ({"nbf": time.time() - 60}, {}),
            ({"nbf": time.time() + 3600}, {}),
            ({"iat": time.time() - 60}, {}),
            ({"iat": time.time() + 3600}, {}),
            ({"exp": time.time() - 60}, {"leeway": 3600}),
            ({"iss": "x"}, {"issuer": "y"}),
            ({"iss": "y"}, {"issuer": "y"}),
            ({"aud": "z"}, {"audience": "y"}),
            ({"aud": "y"}, {"audience": "y"}),
            ({"aud": ["y", "w"]}, {"audience": "w"}),
            ({}, {"require": ["sub"]}),
            ({"sub": "a"}, {"require": ["sub"]}),
        ],
    )
    def test_matches_pyjwt_verdict(self, claims, kwargs):
        """Both libraries accept or reject the same claim case."""
        token = _pyjwt.encode(claims, _HS_SECRET, algorithm="HS256")
        pyjwt_kwargs = {
            key: value
            for key, value in kwargs.items()
            if key in ("issuer", "audience", "leeway")
        }
        if "require" in kwargs:
            pyjwt_kwargs["options"] = {"require": kwargs["require"]}
        try:
            theirs = _pyjwt.decode(
                token, _HS_SECRET, algorithms=["HS256"], **pyjwt_kwargs
            )
        except _pyjwt.exceptions.PyJWTError:
            theirs = None
        try:
            ours = decode(token, _HS_SECRET, algorithms=["HS256"], **kwargs)
        except JWTError:
            ours = None
        assert (theirs is None) == (ours is None)


# ── ecdsa_p256_verify ──


def _raw_signature(key, msg: bytes):
    der = key.sign(msg, ec.ECDSA(hashes.SHA256()))
    r, s = decode_dss_signature(der)
    return r.to_bytes(32, "big") + s.to_bytes(32, "big"), der


class TestEcdsaP256Verify:
    """The standalone P-256 verifier accepts raw and DER signatures."""

    def test_raw_signature(self):
        msg = b"webauthn-signing-input"
        raw, _der = _raw_signature(_EC_P256, msg)
        nums = _EC_P256.public_key().public_numbers()
        assert ecdsa_p256_verify((nums.x, nums.y), msg, raw)

    def test_der_signature(self):
        msg = b"webauthn-signing-input"
        _raw, der = _raw_signature(_EC_P256, msg)
        nums = _EC_P256.public_key().public_numbers()
        assert ecdsa_p256_verify((nums.x, nums.y), msg, der, der=True)

    def test_jwk_key(self):
        msg = b"message"
        raw, der = _raw_signature(_EC_P256, msg)
        assert ecdsa_p256_verify(_EC_P256_JWK, msg, raw)
        assert ecdsa_p256_verify(_EC_P256_JWK, msg, der, der=True)
        assert ecdsa_p256_verify(key_from_jwk(_EC_P256_JWK), msg, raw)

    def test_wrong_message(self):
        raw, _der = _raw_signature(_EC_P256, b"one")
        assert not ecdsa_p256_verify(_EC_P256_JWK, b"two", raw)

    def test_der_flag_mismatch(self):
        msg = b"message"
        raw, der = _raw_signature(_EC_P256, msg)
        assert not ecdsa_p256_verify(_EC_P256_JWK, msg, der)
        assert not ecdsa_p256_verify(_EC_P256_JWK, msg, raw, der=True)

    def test_empty_signature(self):
        assert not ecdsa_p256_verify(_EC_P256_JWK, b"msg", b"")

    def test_wrong_length(self):
        assert not ecdsa_p256_verify(_EC_P256_JWK, b"msg", b"\x01" * 63)

    def test_off_curve_point(self):
        with pytest.raises(InvalidKeyError):
            ecdsa_p256_verify((1, 1), b"msg", b"\x01" * 64)

    def test_p384_key_rejected(self):
        with pytest.raises(InvalidKeyError):
            ecdsa_p256_verify(_EC_P384_JWK, b"msg", b"\x01" * 64)

    def test_rsa_key_rejected(self):
        with pytest.raises(InvalidKeyError):
            ecdsa_p256_verify(_RSA_JWK, b"msg", b"\x01" * 64)

    def test_bad_key_type(self):
        with pytest.raises(InvalidKeyError):
            ecdsa_p256_verify("nope", b"msg", b"\x01" * 64)

    def test_signature_must_be_bytes(self):
        with pytest.raises(TypeError):
            ecdsa_p256_verify(_EC_P256_JWK, b"msg", "abc")  # type: ignore[arg-type]

    @pytest.mark.parametrize(
        "der",
        [
            b"\x30",
            b"\x31\x06\x02\x01\x01\x02\x01\x01",
            b"\x30\x06\x02\x01\x01\x02\x01",
            b"\x30\x06\x02\x01\x81\x02\x01\x01",
            b"\x30\x06\x02\x01\x01\x02\x01\x01\x30",
            b"\x30\x81\x06\x02\x01\x01\x02\x01\x01",
        ],
        ids=["short", "not-seq", "truncated-int", "negative", "trailing", "long-form"],
    )
    def test_malformed_der_is_invalid(self, der):
        assert not ecdsa_p256_verify(_EC_P256_JWK, b"msg", der, der=True)

    def test_wide_der_integer_is_invalid_not_an_error(self):
        """A DER integer at or above the field is an invalid signature.

        V1-V3 have a value of or above 2**256 -- the encoding is legal DER, the
        value cannot fit the field, and the call must return False rather than
        raise.  V4 sits one below the bound and must also stay False.  V5 is a
        genuine signature whose r and s both have the top bit set, encoded with
        a leading zero: it is valid and must stay True, so a bound that rejects
        a 33-byte integer rather than a wide value fails here.
        """
        jwk = {
            "kty": "EC",
            "crv": "P-256",
            "x": "Rxw-dYxJBChbun5TEY7Q9SSt6wdX0lvS-Oew1236cUw",
            "y": "3VIPesqKi5F6zDf1HejwybvjrYWDgucC3CWhLQn3qFg",
        }
        msg = b"top-bit-probe-0"
        v1 = bytes.fromhex("3026022101") + b"\x00" * 32 + bytes.fromhex("020101")
        v2 = bytes.fromhex("3026020101") + bytes.fromhex("022101") + b"\x00" * 32
        v3 = bytes.fromhex("30760271") + b"\x10" + b"\x00" * 112
        v3 += bytes.fromhex("020101")
        v4 = bytes.fromhex("3026022100") + b"\xff" * 32 + bytes.fromhex("020101")
        v5 = bytes.fromhex(
            "3046022100a55cf842158d258610f4abcf3e8e8735036ca02bd53df288"
            "4949126aebbf0a8502210082676849650e19aff49422ce105b44a9951174"
            "7e4df101d9115d06653baeae8b"
        )

        assert not ecdsa_p256_verify(jwk, msg, v1, der=True)
        assert not ecdsa_p256_verify(jwk, msg, v2, der=True)
        assert not ecdsa_p256_verify(jwk, msg, v3, der=True)
        assert not ecdsa_p256_verify(jwk, msg, v4, der=True)
        assert ecdsa_p256_verify(jwk, msg, v5, der=True)


# ── Hostile input ──


class TestHostileInput:
    """Unauthenticated parsing must never raise anything but JWTError."""

    @staticmethod
    def _token(header: bytes, payload: bytes) -> str:
        return f"{b64url_encode(header)}.{b64url_encode(payload)}."

    def test_deeply_nested_payload_is_a_decode_error(self):
        nested = b"[" * 2000 + b"]" * 2000
        token = self._token(b'{"alg":"HS256"}', nested)
        with pytest.raises(DecodeError):
            get_unverified_header(token)
        with pytest.raises(DecodeError):
            decode(token, _HS_SECRET, algorithms=["HS256"])

    def test_deeply_nested_header_is_a_decode_error(self):
        nested = b"[" * 2000 + b"]" * 2000
        header = b'{"alg":"HS256","x":' + nested + b"}"
        token = self._token(header, b'{"sub":"a"}')
        with pytest.raises(DecodeError):
            get_unverified_header(token)

    def test_deeply_nested_claims_are_a_decode_error(self):
        payload = b'{"sub":"a","x":' + b"[" * 2000 + b"]" * 2000 + b"}"
        token = self._token(b'{"alg":"HS256"}', payload)
        with pytest.raises(DecodeError):
            get_unverified_claims(token)


# ── Error hierarchy ──


class TestErrors:
    """One exception tree rooted at JWTError."""

    @pytest.mark.parametrize(
        "exc",
        [
            DecodeError,
            InvalidSignatureError,
            InvalidAlgorithmError,
            UnsupportedCriticalHeaderError,
            InvalidKeyError,
            ExpiredSignatureError,
            ImmatureSignatureError,
            InvalidAudienceError,
            InvalidIssuerError,
            MissingRequiredClaimError,
        ],
    )
    def test_subclasses(self, exc):
        assert issubclass(exc, JWTError)

    def test_decode_error_is_value_error(self):
        assert issubclass(DecodeError, ValueError)

    def test_invalid_key_is_value_error(self):
        assert issubclass(InvalidKeyError, ValueError)
