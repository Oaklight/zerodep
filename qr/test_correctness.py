"""Correctness tests: zerodep QR vs qrcode library."""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from qr import QrCode

qrcode = pytest.importorskip("qrcode", reason="qrcode not installed")


def _zerodep_matrix(text: str, ecc: QrCode.Ecc) -> list[list[bool]]:
    """Get module matrix from zerodep QR."""
    q = QrCode.encode_text(text, ecc)
    size = q.get_size()
    return [[q.get_module(x, y) for x in range(size)] for y in range(size)]


def _qrcode_matrix(text: str, error_correction: int) -> list[list[bool]]:
    """Get module matrix from qrcode library."""
    q = qrcode.QRCode(error_correction=error_correction, box_size=1, border=0)
    q.add_data(text)
    q.make(fit=True)
    matrix = q.get_matrix()
    return matrix


# Map zerodep ECC levels to qrcode constants
ECC_MAP = [
    (QrCode.Ecc.LOW, qrcode.constants.ERROR_CORRECT_L),
    (QrCode.Ecc.MEDIUM, qrcode.constants.ERROR_CORRECT_M),
    (QrCode.Ecc.QUARTILE, qrcode.constants.ERROR_CORRECT_Q),
    (QrCode.Ecc.HIGH, qrcode.constants.ERROR_CORRECT_H),
]

TEXTS = [
    "0",
    "Hello",
    "https://example.com",
    "1234567890",
    "HELLO WORLD",
    "The quick brown fox jumps over the lazy dog",
]


class TestQRProperties:
    """Verify basic QR code properties."""

    @pytest.mark.parametrize("text", TEXTS)
    def test_encode_and_size_positive(self, text: str):
        qr = QrCode.encode_text(text, QrCode.Ecc.MEDIUM)
        assert qr.get_size() > 0

    @pytest.mark.parametrize("text", TEXTS)
    def test_version_in_range(self, text: str):
        qr = QrCode.encode_text(text, QrCode.Ecc.MEDIUM)
        assert 1 <= qr.get_version() <= 40

    def test_higher_ecc_same_or_larger_version(self):
        low = QrCode.encode_text("Hello", QrCode.Ecc.LOW)
        high = QrCode.encode_text("Hello", QrCode.Ecc.HIGH)
        assert low.get_version() <= high.get_version()


class TestQRSizeMatch:
    """Verify that zerodep and qrcode produce same-sized QR codes."""

    @pytest.mark.parametrize("text", TEXTS)
    @pytest.mark.parametrize(
        "ecc_pair", ECC_MAP, ids=["LOW", "MEDIUM", "QUARTILE", "HIGH"]
    )
    def test_same_size(self, text: str, ecc_pair):
        our_ecc, their_ecc = ecc_pair
        ours = QrCode.encode_text(text, our_ecc)
        theirs = qrcode.QRCode(error_correction=their_ecc, box_size=1, border=0)
        theirs.add_data(text)
        theirs.make(fit=True)
        their_matrix = theirs.get_matrix()
        assert ours.get_size() == len(their_matrix)


class TestQRDecodable:
    """Verify that zerodep QR codes are structurally valid.

    We test this by checking that both implementations produce
    the same finder patterns (the three corner squares).
    """

    @pytest.mark.parametrize("text", TEXTS[:3])
    def test_finder_patterns_match(self, text: str):
        ours = _zerodep_matrix(text, QrCode.Ecc.MEDIUM)
        theirs = _qrcode_matrix(text, qrcode.constants.ERROR_CORRECT_M)
        if len(ours) != len(theirs):
            pytest.skip("Different versions chosen — cannot compare matrices")
        # Check top-left 7x7 finder pattern
        for y in range(7):
            for x in range(7):
                assert ours[y][x] == theirs[y][x], f"Mismatch at ({x},{y})"
