"""Benchmark: zerodep AES vs pycryptodome."""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from aes_openssl import aes_cbc_decrypt as openssl_cbc_decrypt
from aes_openssl import aes_cbc_encrypt as openssl_cbc_encrypt
from aes_openssl import aes_ctr_encrypt as openssl_ctr_encrypt
from aes_openssl import aes_ecb_decrypt as openssl_ecb_decrypt
from aes_openssl import aes_ecb_encrypt as openssl_ecb_encrypt
from aes_openssl import aes_gcm_decrypt as openssl_gcm_decrypt
from aes_openssl import aes_gcm_encrypt as openssl_gcm_encrypt

from aes import aes_cbc_decrypt as pure_cbc_decrypt
from aes import aes_cbc_encrypt as pure_cbc_encrypt
from aes import aes_ctr_encrypt as pure_ctr_encrypt
from aes import aes_ecb_decrypt as pure_ecb_decrypt
from aes import aes_ecb_encrypt as pure_ecb_encrypt
from aes import aes_gcm_decrypt as pure_gcm_decrypt
from aes import aes_gcm_encrypt as pure_gcm_encrypt

Cipher = pytest.importorskip("Crypto.Cipher", reason="pycryptodome not installed")
from Crypto.Cipher import AES as PyCryptoAES
from Crypto.Util.Padding import pad, unpad

KEY_128 = b"0123456789abcdef"
KEY_256 = os.urandom(32)
IV = os.urandom(16)
NONCE_12 = os.urandom(12)
NONCE_16 = os.urandom(16)
AAD = b"benchmark aad"

SMALL = b"Hello, World!"  # 13 bytes
MEDIUM = os.urandom(1024)  # 1 KB
LARGE = os.urandom(64 * 1024)  # 64 KB


def _pycrypto_ecb_encrypt(data: bytes, key: bytes) -> bytes:
    cipher = PyCryptoAES.new(key, PyCryptoAES.MODE_ECB)
    return cipher.encrypt(pad(data, PyCryptoAES.block_size))


def _pycrypto_ecb_decrypt(ct: bytes, key: bytes) -> bytes:
    cipher = PyCryptoAES.new(key, PyCryptoAES.MODE_ECB)
    return unpad(cipher.decrypt(ct), PyCryptoAES.block_size)


def _pycrypto_cbc_encrypt(data: bytes, key: bytes, iv: bytes) -> bytes:
    cipher = PyCryptoAES.new(key, PyCryptoAES.MODE_CBC, iv=iv)
    return cipher.encrypt(pad(data, PyCryptoAES.block_size))


def _pycrypto_cbc_decrypt(ct: bytes, key: bytes, iv: bytes) -> bytes:
    cipher = PyCryptoAES.new(key, PyCryptoAES.MODE_CBC, iv=iv)
    return unpad(cipher.decrypt(ct), PyCryptoAES.block_size)


def _pycrypto_ctr_encrypt(data: bytes, key: bytes, nonce: bytes) -> bytes:
    iv = int.from_bytes(nonce, "big")
    cipher = PyCryptoAES.new(key, PyCryptoAES.MODE_CTR, nonce=b"", initial_value=iv)
    return cipher.encrypt(data)


def _pycrypto_gcm_encrypt(
    data: bytes, key: bytes, nonce: bytes, aad: bytes = b""
) -> tuple[bytes, bytes]:
    cipher = PyCryptoAES.new(key, PyCryptoAES.MODE_GCM, nonce=nonce)
    if aad:
        cipher.update(aad)
    return cipher.encrypt_and_digest(data)


def _pycrypto_gcm_decrypt(
    ct: bytes, key: bytes, nonce: bytes, tag: bytes, aad: bytes = b""
) -> bytes:
    cipher = PyCryptoAES.new(key, PyCryptoAES.MODE_GCM, nonce=nonce)
    if aad:
        cipher.update(aad)
    return cipher.decrypt_and_verify(ct, tag)


# Pre-compute ciphertexts for decrypt benchmarks
_ECB_SMALL_CT = _pycrypto_ecb_encrypt(SMALL, KEY_128)
_ECB_MEDIUM_CT = _pycrypto_ecb_encrypt(MEDIUM, KEY_128)
_ECB_LARGE_CT = _pycrypto_ecb_encrypt(LARGE, KEY_128)

_CBC_SMALL_CT = _pycrypto_cbc_encrypt(SMALL, KEY_128, IV)
_CBC_MEDIUM_CT = _pycrypto_cbc_encrypt(MEDIUM, KEY_128, IV)

_CTR_SMALL_CT = _pycrypto_ctr_encrypt(SMALL, KEY_128, NONCE_16)
_CTR_MEDIUM_CT = _pycrypto_ctr_encrypt(MEDIUM, KEY_128, NONCE_16)

_GCM_SMALL_CT, _GCM_SMALL_TAG = _pycrypto_gcm_encrypt(SMALL, KEY_128, NONCE_12)
_GCM_MEDIUM_CT, _GCM_MEDIUM_TAG = _pycrypto_gcm_encrypt(MEDIUM, KEY_128, NONCE_12)


# ── ECB encrypt ──


class TestEcbEncryptSmall:
    def test_pure_python(self, benchmark):
        benchmark(pure_ecb_encrypt, SMALL, KEY_128)

    def test_openssl(self, benchmark):
        benchmark(openssl_ecb_encrypt, SMALL, KEY_128)

    def test_pycryptodome(self, benchmark):
        benchmark(_pycrypto_ecb_encrypt, SMALL, KEY_128)


class TestEcbEncryptMedium:
    def test_pure_python(self, benchmark):
        benchmark(pure_ecb_encrypt, MEDIUM, KEY_128)

    def test_openssl(self, benchmark):
        benchmark(openssl_ecb_encrypt, MEDIUM, KEY_128)

    def test_pycryptodome(self, benchmark):
        benchmark(_pycrypto_ecb_encrypt, MEDIUM, KEY_128)


class TestEcbEncryptLarge:
    def test_pure_python(self, benchmark):
        benchmark(pure_ecb_encrypt, LARGE, KEY_128)

    def test_openssl(self, benchmark):
        benchmark(openssl_ecb_encrypt, LARGE, KEY_128)

    def test_pycryptodome(self, benchmark):
        benchmark(_pycrypto_ecb_encrypt, LARGE, KEY_128)


# ── ECB decrypt ──


class TestEcbDecryptSmall:
    def test_pure_python(self, benchmark):
        benchmark(pure_ecb_decrypt, _ECB_SMALL_CT, KEY_128)

    def test_openssl(self, benchmark):
        benchmark(openssl_ecb_decrypt, _ECB_SMALL_CT, KEY_128)

    def test_pycryptodome(self, benchmark):
        benchmark(_pycrypto_ecb_decrypt, _ECB_SMALL_CT, KEY_128)


class TestEcbDecryptMedium:
    def test_pure_python(self, benchmark):
        benchmark(pure_ecb_decrypt, _ECB_MEDIUM_CT, KEY_128)

    def test_openssl(self, benchmark):
        benchmark(openssl_ecb_decrypt, _ECB_MEDIUM_CT, KEY_128)

    def test_pycryptodome(self, benchmark):
        benchmark(_pycrypto_ecb_decrypt, _ECB_MEDIUM_CT, KEY_128)


class TestEcbDecryptLarge:
    def test_pure_python(self, benchmark):
        benchmark(pure_ecb_decrypt, _ECB_LARGE_CT, KEY_128)

    def test_openssl(self, benchmark):
        benchmark(openssl_ecb_decrypt, _ECB_LARGE_CT, KEY_128)

    def test_pycryptodome(self, benchmark):
        benchmark(_pycrypto_ecb_decrypt, _ECB_LARGE_CT, KEY_128)


# ── CBC encrypt ──


class TestCbcEncryptSmall:
    def test_pure_python(self, benchmark):
        benchmark(pure_cbc_encrypt, SMALL, KEY_128, IV)

    def test_openssl(self, benchmark):
        benchmark(openssl_cbc_encrypt, SMALL, KEY_128, IV)

    def test_pycryptodome(self, benchmark):
        benchmark(_pycrypto_cbc_encrypt, SMALL, KEY_128, IV)


class TestCbcEncryptMedium:
    def test_pure_python(self, benchmark):
        benchmark(pure_cbc_encrypt, MEDIUM, KEY_128, IV)

    def test_openssl(self, benchmark):
        benchmark(openssl_cbc_encrypt, MEDIUM, KEY_128, IV)

    def test_pycryptodome(self, benchmark):
        benchmark(_pycrypto_cbc_encrypt, MEDIUM, KEY_128, IV)


# ── CBC decrypt ──


class TestCbcDecryptSmall:
    def test_pure_python(self, benchmark):
        benchmark(pure_cbc_decrypt, _CBC_SMALL_CT, KEY_128, IV)

    def test_openssl(self, benchmark):
        benchmark(openssl_cbc_decrypt, _CBC_SMALL_CT, KEY_128, IV)

    def test_pycryptodome(self, benchmark):
        benchmark(_pycrypto_cbc_decrypt, _CBC_SMALL_CT, KEY_128, IV)


class TestCbcDecryptMedium:
    def test_pure_python(self, benchmark):
        benchmark(pure_cbc_decrypt, _CBC_MEDIUM_CT, KEY_128, IV)

    def test_openssl(self, benchmark):
        benchmark(openssl_cbc_decrypt, _CBC_MEDIUM_CT, KEY_128, IV)

    def test_pycryptodome(self, benchmark):
        benchmark(_pycrypto_cbc_decrypt, _CBC_MEDIUM_CT, KEY_128, IV)


# ── CTR encrypt ──


class TestCtrEncryptSmall:
    def test_pure_python(self, benchmark):
        benchmark(pure_ctr_encrypt, SMALL, KEY_128, NONCE_16)

    def test_openssl(self, benchmark):
        benchmark(openssl_ctr_encrypt, SMALL, KEY_128, NONCE_16)

    def test_pycryptodome(self, benchmark):
        benchmark(_pycrypto_ctr_encrypt, SMALL, KEY_128, NONCE_16)


class TestCtrEncryptMedium:
    def test_pure_python(self, benchmark):
        benchmark(pure_ctr_encrypt, MEDIUM, KEY_128, NONCE_16)

    def test_openssl(self, benchmark):
        benchmark(openssl_ctr_encrypt, MEDIUM, KEY_128, NONCE_16)

    def test_pycryptodome(self, benchmark):
        benchmark(_pycrypto_ctr_encrypt, MEDIUM, KEY_128, NONCE_16)


# ── GCM encrypt ──


class TestGcmEncryptSmall:
    def test_pure_python(self, benchmark):
        benchmark(pure_gcm_encrypt, SMALL, KEY_128, NONCE_12)

    def test_openssl(self, benchmark):
        benchmark(openssl_gcm_encrypt, SMALL, KEY_128, NONCE_12)

    def test_pycryptodome(self, benchmark):
        benchmark(_pycrypto_gcm_encrypt, SMALL, KEY_128, NONCE_12)


class TestGcmEncryptMedium:
    def test_pure_python(self, benchmark):
        benchmark(pure_gcm_encrypt, MEDIUM, KEY_128, NONCE_12)

    def test_openssl(self, benchmark):
        benchmark(openssl_gcm_encrypt, MEDIUM, KEY_128, NONCE_12)

    def test_pycryptodome(self, benchmark):
        benchmark(_pycrypto_gcm_encrypt, MEDIUM, KEY_128, NONCE_12)


# ── GCM decrypt ──


class TestGcmDecryptSmall:
    def test_pure_python(self, benchmark):
        benchmark(pure_gcm_decrypt, _GCM_SMALL_CT, KEY_128, NONCE_12, _GCM_SMALL_TAG)

    def test_openssl(self, benchmark):
        benchmark(openssl_gcm_decrypt, _GCM_SMALL_CT, KEY_128, NONCE_12, _GCM_SMALL_TAG)

    def test_pycryptodome(self, benchmark):
        benchmark(
            _pycrypto_gcm_decrypt, _GCM_SMALL_CT, KEY_128, NONCE_12, _GCM_SMALL_TAG
        )


class TestGcmDecryptMedium:
    def test_pure_python(self, benchmark):
        benchmark(pure_gcm_decrypt, _GCM_MEDIUM_CT, KEY_128, NONCE_12, _GCM_MEDIUM_TAG)

    def test_openssl(self, benchmark):
        benchmark(
            openssl_gcm_decrypt, _GCM_MEDIUM_CT, KEY_128, NONCE_12, _GCM_MEDIUM_TAG
        )

    def test_pycryptodome(self, benchmark):
        benchmark(
            _pycrypto_gcm_decrypt, _GCM_MEDIUM_CT, KEY_128, NONCE_12, _GCM_MEDIUM_TAG
        )
