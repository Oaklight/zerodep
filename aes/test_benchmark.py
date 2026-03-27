"""Benchmark: zerodep AES vs pycryptodome."""

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

from aes import aes128_ecb_decrypt as pure_decrypt
from aes import aes128_ecb_encrypt as pure_encrypt

Cipher = pytest.importorskip("Crypto.Cipher", reason="pycryptodome not installed")
from Crypto.Cipher import AES as PyCryptoAES
from Crypto.Util.Padding import pad, unpad

KEY = b"0123456789abcdef"
SMALL = b"Hello, World!"  # 13 bytes
MEDIUM = os.urandom(1024)  # 1 KB
LARGE = os.urandom(64 * 1024)  # 64 KB


def _pycrypto_encrypt(data: bytes, key: bytes) -> bytes:
    cipher = PyCryptoAES.new(key, PyCryptoAES.MODE_ECB)
    return cipher.encrypt(pad(data, PyCryptoAES.block_size))


def _pycrypto_decrypt(ciphertext: bytes, key: bytes) -> bytes:
    cipher = PyCryptoAES.new(key, PyCryptoAES.MODE_ECB)
    return unpad(cipher.decrypt(ciphertext), PyCryptoAES.block_size)


# ── Encrypt benchmarks ──


class TestEncryptSmall:
    def test_pure_python(self, benchmark):
        benchmark(pure_encrypt, SMALL, KEY)

    def test_openssl(self, benchmark):
        benchmark(openssl_encrypt, SMALL, KEY)

    def test_pycryptodome(self, benchmark):
        benchmark(_pycrypto_encrypt, SMALL, KEY)


class TestEncryptMedium:
    def test_pure_python(self, benchmark):
        benchmark(pure_encrypt, MEDIUM, KEY)

    def test_openssl(self, benchmark):
        benchmark(openssl_encrypt, MEDIUM, KEY)

    def test_pycryptodome(self, benchmark):
        benchmark(_pycrypto_encrypt, MEDIUM, KEY)


class TestEncryptLarge:
    def test_pure_python(self, benchmark):
        benchmark(pure_encrypt, LARGE, KEY)

    def test_openssl(self, benchmark):
        benchmark(openssl_encrypt, LARGE, KEY)

    def test_pycryptodome(self, benchmark):
        benchmark(_pycrypto_encrypt, LARGE, KEY)


# ── Decrypt benchmarks ──

SMALL_CT = _pycrypto_encrypt(SMALL, KEY)
MEDIUM_CT = _pycrypto_encrypt(MEDIUM, KEY)
LARGE_CT = _pycrypto_encrypt(LARGE, KEY)


class TestDecryptSmall:
    def test_pure_python(self, benchmark):
        benchmark(pure_decrypt, SMALL_CT, KEY)

    def test_openssl(self, benchmark):
        benchmark(openssl_decrypt, SMALL_CT, KEY)

    def test_pycryptodome(self, benchmark):
        benchmark(_pycrypto_decrypt, SMALL_CT, KEY)


class TestDecryptMedium:
    def test_pure_python(self, benchmark):
        benchmark(pure_decrypt, MEDIUM_CT, KEY)

    def test_openssl(self, benchmark):
        benchmark(openssl_decrypt, MEDIUM_CT, KEY)

    def test_pycryptodome(self, benchmark):
        benchmark(_pycrypto_decrypt, MEDIUM_CT, KEY)


class TestDecryptLarge:
    def test_pure_python(self, benchmark):
        benchmark(pure_decrypt, LARGE_CT, KEY)

    def test_openssl(self, benchmark):
        benchmark(openssl_decrypt, LARGE_CT, KEY)

    def test_pycryptodome(self, benchmark):
        benchmark(_pycrypto_decrypt, LARGE_CT, KEY)
