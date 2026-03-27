"""Correctness tests: zerodep AES vs pycryptodome."""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from aes_openssl import (
    aes128_ecb_decrypt as openssl_decrypt,
)
from aes_openssl import (
    aes128_ecb_encrypt as openssl_encrypt,
)

from aes import aes128_ecb_decrypt, aes128_ecb_encrypt

Cipher = pytest.importorskip("Crypto.Cipher", reason="pycryptodome not installed")
from Crypto.Cipher import AES as PyCryptoAES
from Crypto.Util.Padding import pad, unpad


def _pycrypto_encrypt(data: bytes, key: bytes) -> bytes:
    cipher = PyCryptoAES.new(key, PyCryptoAES.MODE_ECB)
    return cipher.encrypt(pad(data, PyCryptoAES.block_size))


def _pycrypto_decrypt(ciphertext: bytes, key: bytes) -> bytes:
    cipher = PyCryptoAES.new(key, PyCryptoAES.MODE_ECB)
    return unpad(cipher.decrypt(ciphertext), PyCryptoAES.block_size)


# ── Test vectors ──


KEYS = [
    b"0123456789abcdef",
    b"\x00" * 16,
    b"\xff" * 16,
    os.urandom(16),
]

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


class TestPurePythonVsPycryptodome:
    """Compare pure Python AES with pycryptodome output."""

    @pytest.mark.parametrize("key", KEYS, ids=lambda k: k.hex()[:8])
    @pytest.mark.parametrize("plaintext", PLAINTEXTS, ids=lambda p: f"len={len(p)}")
    def test_encrypt_matches(self, key: bytes, plaintext: bytes):
        ours = aes128_ecb_encrypt(plaintext, key)
        theirs = _pycrypto_encrypt(plaintext, key)
        assert ours == theirs

    @pytest.mark.parametrize("key", KEYS, ids=lambda k: k.hex()[:8])
    @pytest.mark.parametrize("plaintext", PLAINTEXTS, ids=lambda p: f"len={len(p)}")
    def test_decrypt_matches(self, key: bytes, plaintext: bytes):
        ciphertext = _pycrypto_encrypt(plaintext, key)
        ours = aes128_ecb_decrypt(ciphertext, key)
        assert ours == plaintext

    @pytest.mark.parametrize("key", KEYS, ids=lambda k: k.hex()[:8])
    @pytest.mark.parametrize("plaintext", PLAINTEXTS, ids=lambda p: f"len={len(p)}")
    def test_roundtrip(self, key: bytes, plaintext: bytes):
        assert aes128_ecb_decrypt(aes128_ecb_encrypt(plaintext, key), key) == plaintext


class TestOpenSSLVsPycryptodome:
    """Compare OpenSSL ctypes AES with pycryptodome output."""

    @pytest.mark.parametrize("key", KEYS, ids=lambda k: k.hex()[:8])
    @pytest.mark.parametrize("plaintext", PLAINTEXTS, ids=lambda p: f"len={len(p)}")
    def test_encrypt_matches(self, key: bytes, plaintext: bytes):
        ours = openssl_encrypt(plaintext, key)
        theirs = _pycrypto_encrypt(plaintext, key)
        assert ours == theirs

    @pytest.mark.parametrize("key", KEYS, ids=lambda k: k.hex()[:8])
    @pytest.mark.parametrize("plaintext", PLAINTEXTS, ids=lambda p: f"len={len(p)}")
    def test_decrypt_matches(self, key: bytes, plaintext: bytes):
        ciphertext = _pycrypto_encrypt(plaintext, key)
        ours = openssl_decrypt(ciphertext, key)
        assert ours == plaintext

    @pytest.mark.parametrize("key", KEYS, ids=lambda k: k.hex()[:8])
    @pytest.mark.parametrize("plaintext", PLAINTEXTS, ids=lambda p: f"len={len(p)}")
    def test_roundtrip(self, key: bytes, plaintext: bytes):
        assert openssl_decrypt(openssl_encrypt(plaintext, key), key) == plaintext


class TestCrossImplementation:
    """Verify pure Python and OpenSSL produce identical output."""

    @pytest.mark.parametrize("key", KEYS, ids=lambda k: k.hex()[:8])
    @pytest.mark.parametrize("plaintext", PLAINTEXTS, ids=lambda p: f"len={len(p)}")
    def test_encrypt_identical(self, key: bytes, plaintext: bytes):
        assert aes128_ecb_encrypt(plaintext, key) == openssl_encrypt(plaintext, key)

    @pytest.mark.parametrize("key", KEYS, ids=lambda k: k.hex()[:8])
    @pytest.mark.parametrize("plaintext", PLAINTEXTS, ids=lambda p: f"len={len(p)}")
    def test_decrypt_identical(self, key: bytes, plaintext: bytes):
        ciphertext = aes128_ecb_encrypt(plaintext, key)
        assert aes128_ecb_decrypt(ciphertext, key) == openssl_decrypt(ciphertext, key)
