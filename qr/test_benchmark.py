"""Benchmark: zerodep QR vs qrcode library."""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from qr import QrCode

qrcode = pytest.importorskip("qrcode", reason="qrcode not installed")

SHORT_TEXT = "Hello"
URL_TEXT = "https://example.com/path?query=value&foo=bar"
LONG_TEXT = "A" * 200


def _zerodep_qr(text: str):
    return QrCode.encode_text(text, QrCode.Ecc.MEDIUM)


def _qrcode_qr(text: str):
    q = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M)
    q.add_data(text)
    q.make(fit=True)
    return q


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
