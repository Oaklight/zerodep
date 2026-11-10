"""Correctness tests: zerodep jwt vs PyJWT[crypto].

Our module file ``jwt/jwt.py`` and its directory shadow the PyJWT ``jwt``
package, so the real PyJWT is imported first through a temporary sys.path and
sys.modules manipulation, sanity-checked, and put back.  Every comparison in
this file signs with PyJWT and verifies with ours (and the reverse for HMAC),
so a shadowed import fails loudly instead of comparing our module with itself.
"""

import base64
import json
import os
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
    pytest.skip("PyJWT not installed", allow_module_level=True)
finally:
    sys.path = _saved_path
    for key in [k for k in sys.modules if k == "jwt" or k.startswith("jwt.")]:
        del sys.modules[key]
    sys.modules.update(_cached_jwt)

crypto = pytest.importorskip("cryptography", reason="PyJWT[crypto] not installed")
from cryptography.hazmat.primitives import hashes  # noqa: E402
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
    JWTError,
    MissingRequiredClaimError,
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

    def test_low_order_point_rejected(self):
        # (0, 0) satisfies no curve equation; a real off-curve point is used.
        jwk = {"kty": "EC", "crv": "P-256", "x": _b64uint(1), "y": _b64uint(1)}
        with pytest.raises(InvalidKeyError):
            key_from_jwk(jwk)

    def test_invalid_base64_in_field(self):
        with pytest.raises(DecodeError):
            key_from_jwk({"kty": "RSA", "n": "!!!", "e": "AQAB"})


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

    def test_now_override(self):
        token = self._token({"exp": 5000})
        assert decode(token, _HS_SECRET, algorithms=["HS256"], now=4000)["exp"]
        with pytest.raises(ExpiredSignatureError):
            decode(token, _HS_SECRET, algorithms=["HS256"], now=6000)

    def test_negative_leeway_rejected(self):
        token = self._token({"sub": "a"})
        with pytest.raises(ValueError):
            decode(token, _HS_SECRET, algorithms=["HS256"], leeway=-1)

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


# ── Error hierarchy ──


class TestErrors:
    """One exception tree rooted at JWTError."""

    @pytest.mark.parametrize(
        "exc",
        [
            DecodeError,
            InvalidSignatureError,
            InvalidAlgorithmError,
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
