"""Correctness tests: zerodep AES vs pycryptodome."""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from aes_openssl import aes128_ecb_decrypt as openssl_legacy_decrypt
from aes_openssl import aes128_ecb_encrypt as openssl_legacy_encrypt
from aes_openssl import aes_cbc_decrypt as openssl_cbc_decrypt
from aes_openssl import aes_cbc_encrypt as openssl_cbc_encrypt
from aes_openssl import aes_ctr_decrypt as openssl_ctr_decrypt
from aes_openssl import aes_ctr_encrypt as openssl_ctr_encrypt
from aes_openssl import aes_ecb_decrypt as openssl_ecb_decrypt
from aes_openssl import aes_ecb_encrypt as openssl_ecb_encrypt
from aes_openssl import aes_gcm_decrypt as openssl_gcm_decrypt
from aes_openssl import aes_gcm_encrypt as openssl_gcm_encrypt

from aes import (
    aes128_ecb_decrypt,
    aes128_ecb_encrypt,
    aes_cbc_decrypt,
    aes_cbc_encrypt,
    aes_ctr_decrypt,
    aes_ctr_encrypt,
    aes_ecb_decrypt,
    aes_ecb_encrypt,
    aes_gcm_decrypt,
    aes_gcm_encrypt,
)

Cipher = pytest.importorskip("Crypto.Cipher", reason="pycryptodome not installed")
from Crypto.Cipher import AES as PyCryptoAES
from Crypto.Util.Padding import pad, unpad


def _pycrypto_ecb_encrypt(data: bytes, key: bytes) -> bytes:
    cipher = PyCryptoAES.new(key, PyCryptoAES.MODE_ECB)
    return cipher.encrypt(pad(data, PyCryptoAES.block_size))


def _pycrypto_ecb_decrypt(ciphertext: bytes, key: bytes) -> bytes:
    cipher = PyCryptoAES.new(key, PyCryptoAES.MODE_ECB)
    return unpad(cipher.decrypt(ciphertext), PyCryptoAES.block_size)


def _pycrypto_cbc_encrypt(data: bytes, key: bytes, iv: bytes) -> bytes:
    cipher = PyCryptoAES.new(key, PyCryptoAES.MODE_CBC, iv=iv)
    return cipher.encrypt(pad(data, PyCryptoAES.block_size))


def _pycrypto_cbc_decrypt(ciphertext: bytes, key: bytes, iv: bytes) -> bytes:
    cipher = PyCryptoAES.new(key, PyCryptoAES.MODE_CBC, iv=iv)
    return unpad(cipher.decrypt(ciphertext), PyCryptoAES.block_size)


def _pycrypto_ctr_encrypt(data: bytes, key: bytes, nonce: bytes) -> bytes:
    initial_value = int.from_bytes(nonce, "big")
    cipher = PyCryptoAES.new(
        key, PyCryptoAES.MODE_CTR, nonce=b"", initial_value=initial_value
    )
    return cipher.encrypt(data)


def _pycrypto_gcm_encrypt(
    data: bytes, key: bytes, nonce: bytes, aad: bytes = b""
) -> tuple[bytes, bytes]:
    cipher = PyCryptoAES.new(key, PyCryptoAES.MODE_GCM, nonce=nonce)
    if aad:
        cipher.update(aad)
    ct, tag = cipher.encrypt_and_digest(data)
    return ct, tag


def _pycrypto_gcm_decrypt(
    data: bytes, key: bytes, nonce: bytes, tag: bytes, aad: bytes = b""
) -> bytes:
    cipher = PyCryptoAES.new(key, PyCryptoAES.MODE_GCM, nonce=nonce)
    if aad:
        cipher.update(aad)
    return cipher.decrypt_and_verify(data, tag)


# ── Test vectors ──

KEYS_128 = [
    b"0123456789abcdef",
    b"\x00" * 16,
    b"\xff" * 16,
    os.urandom(16),
]
KEYS_192 = [os.urandom(24) for _ in range(3)]
KEYS_256 = [os.urandom(32) for _ in range(3)]
ALL_KEYS = KEYS_128 + KEYS_192 + KEYS_256

IVS = [b"\x00" * 16, os.urandom(16), os.urandom(16)]

NONCES_12 = [os.urandom(12) for _ in range(3)]
NONCES_16 = [os.urandom(16) for _ in range(2)]

PLAINTEXTS = [
    b"",
    b"a",
    b"Hello, World!",
    b"A" * 16,  # exact block size
    b"B" * 32,  # two blocks
    b"C" * 31,  # just under two blocks
    b"D" * 1024,  # larger payload
    os.urandom(100),
    os.urandom(256),
]


# ── ECB: all key sizes ──


class TestEcbPurePythonVsPycryptodome:
    @pytest.mark.parametrize("key", ALL_KEYS, ids=lambda k: f"k{len(k) * 8}")
    @pytest.mark.parametrize("pt", PLAINTEXTS, ids=lambda p: f"len={len(p)}")
    def test_encrypt(self, key: bytes, pt: bytes):
        assert aes_ecb_encrypt(pt, key) == _pycrypto_ecb_encrypt(pt, key)

    @pytest.mark.parametrize("key", ALL_KEYS, ids=lambda k: f"k{len(k) * 8}")
    @pytest.mark.parametrize("pt", PLAINTEXTS, ids=lambda p: f"len={len(p)}")
    def test_decrypt(self, key: bytes, pt: bytes):
        ct = _pycrypto_ecb_encrypt(pt, key)
        assert aes_ecb_decrypt(ct, key) == pt

    @pytest.mark.parametrize("key", ALL_KEYS, ids=lambda k: f"k{len(k) * 8}")
    @pytest.mark.parametrize("pt", PLAINTEXTS, ids=lambda p: f"len={len(p)}")
    def test_roundtrip(self, key: bytes, pt: bytes):
        assert aes_ecb_decrypt(aes_ecb_encrypt(pt, key), key) == pt


class TestEcbOpenSSLVsPycryptodome:
    @pytest.mark.parametrize("key", ALL_KEYS, ids=lambda k: f"k{len(k) * 8}")
    @pytest.mark.parametrize("pt", PLAINTEXTS, ids=lambda p: f"len={len(p)}")
    def test_encrypt(self, key: bytes, pt: bytes):
        assert openssl_ecb_encrypt(pt, key) == _pycrypto_ecb_encrypt(pt, key)

    @pytest.mark.parametrize("key", ALL_KEYS, ids=lambda k: f"k{len(k) * 8}")
    @pytest.mark.parametrize("pt", PLAINTEXTS, ids=lambda p: f"len={len(p)}")
    def test_decrypt(self, key: bytes, pt: bytes):
        ct = _pycrypto_ecb_encrypt(pt, key)
        assert openssl_ecb_decrypt(ct, key) == pt


class TestEcbCrossImplementation:
    @pytest.mark.parametrize("key", ALL_KEYS, ids=lambda k: f"k{len(k) * 8}")
    @pytest.mark.parametrize("pt", PLAINTEXTS, ids=lambda p: f"len={len(p)}")
    def test_encrypt_identical(self, key: bytes, pt: bytes):
        assert aes_ecb_encrypt(pt, key) == openssl_ecb_encrypt(pt, key)

    @pytest.mark.parametrize("key", ALL_KEYS, ids=lambda k: f"k{len(k) * 8}")
    @pytest.mark.parametrize("pt", PLAINTEXTS, ids=lambda p: f"len={len(p)}")
    def test_decrypt_identical(self, key: bytes, pt: bytes):
        ct = aes_ecb_encrypt(pt, key)
        assert aes_ecb_decrypt(ct, key) == openssl_ecb_decrypt(ct, key)


# ── CBC ──


class TestCbcPurePythonVsPycryptodome:
    @pytest.mark.parametrize("key", ALL_KEYS, ids=lambda k: f"k{len(k) * 8}")
    @pytest.mark.parametrize("iv", IVS, ids=lambda v: v.hex()[:8])
    @pytest.mark.parametrize("pt", PLAINTEXTS, ids=lambda p: f"len={len(p)}")
    def test_encrypt(self, key: bytes, iv: bytes, pt: bytes):
        assert aes_cbc_encrypt(pt, key, iv) == _pycrypto_cbc_encrypt(pt, key, iv)

    @pytest.mark.parametrize("key", ALL_KEYS, ids=lambda k: f"k{len(k) * 8}")
    @pytest.mark.parametrize("iv", IVS, ids=lambda v: v.hex()[:8])
    @pytest.mark.parametrize("pt", PLAINTEXTS, ids=lambda p: f"len={len(p)}")
    def test_decrypt(self, key: bytes, iv: bytes, pt: bytes):
        ct = _pycrypto_cbc_encrypt(pt, key, iv)
        assert aes_cbc_decrypt(ct, key, iv) == pt


class TestCbcOpenSSLVsPycryptodome:
    @pytest.mark.parametrize("key", ALL_KEYS, ids=lambda k: f"k{len(k) * 8}")
    @pytest.mark.parametrize("iv", IVS, ids=lambda v: v.hex()[:8])
    @pytest.mark.parametrize("pt", PLAINTEXTS, ids=lambda p: f"len={len(p)}")
    def test_encrypt(self, key: bytes, iv: bytes, pt: bytes):
        assert openssl_cbc_encrypt(pt, key, iv) == _pycrypto_cbc_encrypt(pt, key, iv)

    @pytest.mark.parametrize("key", ALL_KEYS, ids=lambda k: f"k{len(k) * 8}")
    @pytest.mark.parametrize("iv", IVS, ids=lambda v: v.hex()[:8])
    @pytest.mark.parametrize("pt", PLAINTEXTS, ids=lambda p: f"len={len(p)}")
    def test_decrypt(self, key: bytes, iv: bytes, pt: bytes):
        ct = _pycrypto_cbc_encrypt(pt, key, iv)
        assert openssl_cbc_decrypt(ct, key, iv) == pt


class TestCbcCrossImplementation:
    @pytest.mark.parametrize("key", ALL_KEYS, ids=lambda k: f"k{len(k) * 8}")
    @pytest.mark.parametrize("iv", IVS, ids=lambda v: v.hex()[:8])
    @pytest.mark.parametrize("pt", PLAINTEXTS, ids=lambda p: f"len={len(p)}")
    def test_encrypt_identical(self, key: bytes, iv: bytes, pt: bytes):
        assert aes_cbc_encrypt(pt, key, iv) == openssl_cbc_encrypt(pt, key, iv)


# ── CTR ──


class TestCtrPurePythonVsPycryptodome:
    @pytest.mark.parametrize("key", ALL_KEYS, ids=lambda k: f"k{len(k) * 8}")
    @pytest.mark.parametrize("pt", PLAINTEXTS[1:], ids=lambda p: f"len={len(p)}")
    def test_encrypt(self, key: bytes, pt: bytes):
        nonce = os.urandom(16)
        assert aes_ctr_encrypt(pt, key, nonce) == _pycrypto_ctr_encrypt(pt, key, nonce)

    @pytest.mark.parametrize("key", ALL_KEYS, ids=lambda k: f"k{len(k) * 8}")
    @pytest.mark.parametrize("pt", PLAINTEXTS[1:], ids=lambda p: f"len={len(p)}")
    def test_roundtrip(self, key: bytes, pt: bytes):
        nonce = os.urandom(16)
        ct = aes_ctr_encrypt(pt, key, nonce)
        assert aes_ctr_decrypt(ct, key, nonce) == pt

    @pytest.mark.parametrize("key", ALL_KEYS, ids=lambda k: f"k{len(k) * 8}")
    def test_output_length(self, key: bytes):
        for size in (1, 15, 16, 17, 100):
            pt = os.urandom(size)
            nonce = os.urandom(16)
            assert len(aes_ctr_encrypt(pt, key, nonce)) == size


class TestCtrOpenSSLVsPycryptodome:
    @pytest.mark.parametrize("key", ALL_KEYS, ids=lambda k: f"k{len(k) * 8}")
    @pytest.mark.parametrize("pt", PLAINTEXTS[1:], ids=lambda p: f"len={len(p)}")
    def test_encrypt(self, key: bytes, pt: bytes):
        nonce = os.urandom(16)
        ours = openssl_ctr_encrypt(pt, key, nonce)
        theirs = _pycrypto_ctr_encrypt(pt, key, nonce)
        assert ours == theirs

    @pytest.mark.parametrize("key", ALL_KEYS, ids=lambda k: f"k{len(k) * 8}")
    @pytest.mark.parametrize("pt", PLAINTEXTS[1:], ids=lambda p: f"len={len(p)}")
    def test_roundtrip(self, key: bytes, pt: bytes):
        nonce = os.urandom(16)
        ct = openssl_ctr_encrypt(pt, key, nonce)
        assert openssl_ctr_decrypt(ct, key, nonce) == pt


class TestCtrCrossImplementation:
    @pytest.mark.parametrize("key", ALL_KEYS, ids=lambda k: f"k{len(k) * 8}")
    @pytest.mark.parametrize("pt", PLAINTEXTS[1:], ids=lambda p: f"len={len(p)}")
    def test_encrypt_identical(self, key: bytes, pt: bytes):
        nonce = os.urandom(16)
        assert aes_ctr_encrypt(pt, key, nonce) == openssl_ctr_encrypt(pt, key, nonce)


# ── GCM ──

AADS = [b"", b"additional data", os.urandom(64)]


class TestGcmPurePythonVsPycryptodome:
    @pytest.mark.parametrize("key", ALL_KEYS, ids=lambda k: f"k{len(k) * 8}")
    @pytest.mark.parametrize("pt", PLAINTEXTS, ids=lambda p: f"len={len(p)}")
    @pytest.mark.parametrize("aad", AADS, ids=lambda a: f"aad={len(a)}")
    def test_encrypt(self, key: bytes, pt: bytes, aad: bytes):
        nonce = os.urandom(12)
        our_ct, our_tag = aes_gcm_encrypt(pt, key, nonce, aad=aad)
        ref_ct, ref_tag = _pycrypto_gcm_encrypt(pt, key, nonce, aad=aad)
        assert our_ct == ref_ct
        assert our_tag == ref_tag

    @pytest.mark.parametrize("key", ALL_KEYS, ids=lambda k: f"k{len(k) * 8}")
    @pytest.mark.parametrize("pt", PLAINTEXTS, ids=lambda p: f"len={len(p)}")
    def test_roundtrip(self, key: bytes, pt: bytes):
        nonce = os.urandom(12)
        ct, tag = aes_gcm_encrypt(pt, key, nonce)
        assert aes_gcm_decrypt(ct, key, nonce, tag) == pt


class TestGcmOpenSSLVsPycryptodome:
    @pytest.mark.parametrize("key", ALL_KEYS, ids=lambda k: f"k{len(k) * 8}")
    @pytest.mark.parametrize("pt", PLAINTEXTS, ids=lambda p: f"len={len(p)}")
    @pytest.mark.parametrize("aad", AADS, ids=lambda a: f"aad={len(a)}")
    def test_encrypt(self, key: bytes, pt: bytes, aad: bytes):
        nonce = os.urandom(12)
        our_ct, our_tag = openssl_gcm_encrypt(pt, key, nonce, aad=aad)
        ref_ct, ref_tag = _pycrypto_gcm_encrypt(pt, key, nonce, aad=aad)
        assert our_ct == ref_ct
        assert our_tag == ref_tag

    @pytest.mark.parametrize("key", ALL_KEYS, ids=lambda k: f"k{len(k) * 8}")
    @pytest.mark.parametrize("pt", PLAINTEXTS, ids=lambda p: f"len={len(p)}")
    def test_roundtrip(self, key: bytes, pt: bytes):
        nonce = os.urandom(12)
        ct, tag = openssl_gcm_encrypt(pt, key, nonce)
        assert openssl_gcm_decrypt(ct, key, nonce, tag) == pt


class TestGcmCrossImplementation:
    @pytest.mark.parametrize("key", ALL_KEYS, ids=lambda k: f"k{len(k) * 8}")
    @pytest.mark.parametrize("pt", PLAINTEXTS, ids=lambda p: f"len={len(p)}")
    def test_encrypt_identical(self, key: bytes, pt: bytes):
        nonce = os.urandom(12)
        aad = b"cross-check"
        our_ct, our_tag = aes_gcm_encrypt(pt, key, nonce, aad=aad)
        ossl_ct, ossl_tag = openssl_gcm_encrypt(pt, key, nonce, aad=aad)
        assert our_ct == ossl_ct
        assert our_tag == ossl_tag

    @pytest.mark.parametrize("key", ALL_KEYS, ids=lambda k: f"k{len(k) * 8}")
    @pytest.mark.parametrize("pt", PLAINTEXTS, ids=lambda p: f"len={len(p)}")
    def test_decrypt_cross(self, key: bytes, pt: bytes):
        nonce = os.urandom(12)
        ct, tag = aes_gcm_encrypt(pt, key, nonce)
        assert openssl_gcm_decrypt(ct, key, nonce, tag) == pt

        ct2, tag2 = openssl_gcm_encrypt(pt, key, nonce)
        assert aes_gcm_decrypt(ct2, key, nonce, tag2) == pt


class TestGcmAuthFailure:
    def test_tampered_ciphertext(self):
        key, nonce = os.urandom(16), os.urandom(12)
        ct, tag = aes_gcm_encrypt(b"secret", key, nonce)
        tampered = bytes([ct[0] ^ 0xFF]) + ct[1:]
        with pytest.raises(ValueError, match="authentication failed"):
            aes_gcm_decrypt(tampered, key, nonce, tag)

    def test_tampered_tag(self):
        key, nonce = os.urandom(16), os.urandom(12)
        ct, tag = aes_gcm_encrypt(b"secret", key, nonce)
        bad_tag = bytes([tag[0] ^ 0xFF]) + tag[1:]
        with pytest.raises(ValueError, match="authentication failed"):
            aes_gcm_decrypt(ct, key, nonce, bad_tag)

    def test_tampered_aad(self):
        key, nonce = os.urandom(16), os.urandom(12)
        ct, tag = aes_gcm_encrypt(b"secret", key, nonce, aad=b"header")
        with pytest.raises(ValueError, match="authentication failed"):
            aes_gcm_decrypt(ct, key, nonce, tag, aad=b"tampered")

    def test_openssl_tampered_ciphertext(self):
        key, nonce = os.urandom(16), os.urandom(12)
        ct, tag = openssl_gcm_encrypt(b"secret", key, nonce)
        tampered = bytes([ct[0] ^ 0xFF]) + ct[1:]
        with pytest.raises(ValueError, match="authentication failed"):
            openssl_gcm_decrypt(tampered, key, nonce, tag)


class TestGcmTagLengths:
    @pytest.mark.parametrize("tag_len", [4, 8, 12, 16])
    def test_pure_python(self, tag_len: int):
        key, nonce = os.urandom(32), os.urandom(12)
        pt = b"test data"
        ct, tag = aes_gcm_encrypt(pt, key, nonce, tag_length=tag_len)
        assert len(tag) == tag_len
        assert aes_gcm_decrypt(ct, key, nonce, tag) == pt

    @pytest.mark.parametrize("tag_len", [4, 8, 12, 16])
    def test_openssl(self, tag_len: int):
        key, nonce = os.urandom(32), os.urandom(12)
        pt = b"test data"
        ct, tag = openssl_gcm_encrypt(pt, key, nonce, tag_length=tag_len)
        assert len(tag) == tag_len
        assert openssl_gcm_decrypt(ct, key, nonce, tag) == pt


class TestGcmEmptyPlaintext:
    def test_authenticate_only(self):
        key, nonce = os.urandom(16), os.urandom(12)
        aad = b"only authenticate this"
        ct, tag = aes_gcm_encrypt(b"", key, nonce, aad=aad)
        assert ct == b""
        assert len(tag) == 16
        assert aes_gcm_decrypt(ct, key, nonce, tag, aad=aad) == b""


# ── Backward compatibility ──


class TestBackwardCompatibility:
    @pytest.mark.parametrize("key", KEYS_128, ids=lambda k: k.hex()[:8])
    @pytest.mark.parametrize("pt", PLAINTEXTS, ids=lambda p: f"len={len(p)}")
    def test_legacy_pure_python(self, key: bytes, pt: bytes):
        assert aes128_ecb_encrypt(pt, key) == aes_ecb_encrypt(pt, key)
        ct = aes128_ecb_encrypt(pt, key)
        assert aes128_ecb_decrypt(ct, key) == pt

    @pytest.mark.parametrize("key", KEYS_128, ids=lambda k: k.hex()[:8])
    @pytest.mark.parametrize("pt", PLAINTEXTS, ids=lambda p: f"len={len(p)}")
    def test_legacy_openssl(self, key: bytes, pt: bytes):
        assert openssl_legacy_encrypt(pt, key) == openssl_ecb_encrypt(pt, key)
        ct = openssl_legacy_encrypt(pt, key)
        assert openssl_legacy_decrypt(ct, key) == pt


# ── Validation ──


class TestKeyValidation:
    @pytest.mark.parametrize("bad_len", [0, 1, 15, 17, 20, 33])
    def test_ecb(self, bad_len: int):
        with pytest.raises(ValueError, match="key must be"):
            aes_ecb_encrypt(b"data", b"\x00" * bad_len)

    @pytest.mark.parametrize("bad_len", [0, 1, 15, 17, 20, 33])
    def test_cbc(self, bad_len: int):
        with pytest.raises(ValueError, match="key must be"):
            aes_cbc_encrypt(b"data", b"\x00" * bad_len, b"\x00" * 16)


class TestIvValidation:
    @pytest.mark.parametrize("bad_len", [0, 1, 15, 17, 32])
    def test_cbc(self, bad_len: int):
        with pytest.raises(ValueError, match="IV must be"):
            aes_cbc_encrypt(b"data", b"\x00" * 16, b"\x00" * bad_len)

    @pytest.mark.parametrize("bad_len", [0, 1, 15, 17, 32])
    def test_ctr(self, bad_len: int):
        with pytest.raises(ValueError, match="nonce must be"):
            aes_ctr_encrypt(b"data", b"\x00" * 16, b"\x00" * bad_len)
