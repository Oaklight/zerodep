"""Benchmark: zerodep QR vs qrcode library."""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from qr import QrCode

qrcode = pytest.importorskip("qrcode", reason="qrcode not installed")

# ── Test data ──

SHORT_TEXT = "Hello"
URL_TEXT = "https://example.com/path?query=value&foo=bar"
LONG_TEXT = "A" * 200
NUMERIC_TEXT = "0123456789" * 10  # 100 digits, triggers numeric mode
BINARY_DATA = bytes(range(256)) * 2  # 512 bytes of binary data
LARGE_TEXT = "A" * 1000  # Forces high QR version


# ── Helpers ──


def _zerodep_qr(text: str, ecc=QrCode.Ecc.MEDIUM):
    return QrCode.encode_text(text, ecc)


def _zerodep_qr_binary(data: bytes, ecc=QrCode.Ecc.MEDIUM):
    return QrCode.encode_binary(data, ecc)


def _qrcode_qr(text: str, ecc=qrcode.constants.ERROR_CORRECT_M):
    q = qrcode.QRCode(error_correction=ecc)
    q.add_data(text)
    q.make(fit=True)
    return q


def _qrcode_qr_binary(data: bytes, ecc=qrcode.constants.ERROR_CORRECT_M):
    q = qrcode.QRCode(error_correction=ecc)
    q.add_data(data, optimize=0)
    q.make(fit=True)
    return q


# ── Existing: text encoding at MEDIUM ECC ──


class TestEncodeShort:
    def test_zerodep(self, benchmark):
        benchmark(_zerodep_qr, SHORT_TEXT)

    def test_qrcode(self, benchmark):
        benchmark(_qrcode_qr, SHORT_TEXT)


class TestEncodeURL:
    def test_zerodep(self, benchmark):
        benchmark(_zerodep_qr, URL_TEXT)

    def test_qrcode(self, benchmark):
        benchmark(_qrcode_qr, URL_TEXT)


class TestEncodeLong:
    def test_zerodep(self, benchmark):
        benchmark(_zerodep_qr, LONG_TEXT)

    def test_qrcode(self, benchmark):
        benchmark(_qrcode_qr, LONG_TEXT)


# ── Numeric mode (digits only, most compact encoding) ──


class TestEncodeNumeric:
    def test_zerodep(self, benchmark):
        benchmark(_zerodep_qr, NUMERIC_TEXT)

    def test_qrcode(self, benchmark):
        benchmark(_qrcode_qr, NUMERIC_TEXT)


# ── Binary data encoding ──


class TestEncodeBinary:
    def test_zerodep(self, benchmark):
        benchmark(_zerodep_qr_binary, BINARY_DATA)

    def test_qrcode(self, benchmark):
        benchmark(_qrcode_qr_binary, BINARY_DATA)


# ── High ECC (same URL data, but HIGH error correction → more work) ──


class TestEncodeHighEcc:
    def test_zerodep(self, benchmark):
        benchmark(_zerodep_qr, URL_TEXT, QrCode.Ecc.HIGH)

    def test_qrcode(self, benchmark):
        benchmark(_qrcode_qr, URL_TEXT, qrcode.constants.ERROR_CORRECT_H)


# ── Large data (high QR version, large matrix) ──


class TestEncodeLargeData:
    def test_zerodep(self, benchmark):
        benchmark(_zerodep_qr, LARGE_TEXT, QrCode.Ecc.LOW)

    def test_qrcode(self, benchmark):
        benchmark(_qrcode_qr, LARGE_TEXT, qrcode.constants.ERROR_CORRECT_L)
