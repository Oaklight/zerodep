"""Tests for QR image output: qr_to_svg() and qr_to_png()."""

import os
import sys
import tempfile
import xml.etree.ElementTree as ET

import pytest

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "png"))

from qr import QrCode, qr_to_png, qr_to_svg

# Reusable fixture: a small QR code.
_QR = QrCode.encode_text("Hello", QrCode.Ecc.LOW)


# ---- SVG tests ----


class TestQrToSvg:
    """Tests for qr_to_svg()."""

    def test_returns_string(self):
        result = qr_to_svg(_QR)
        assert isinstance(result, str)

    def test_valid_xml(self):
        svg = qr_to_svg(_QR)
        root = ET.fromstring(svg)
        assert root.tag == "{http://www.w3.org/2000/svg}svg"

    def test_dimensions_default(self):
        svg = qr_to_svg(_QR, scale=10, border=4)
        root = ET.fromstring(svg)
        expected = (_QR.get_size() + 2 * 4) * 10
        assert root.attrib["width"] == str(expected)
        assert root.attrib["height"] == str(expected)
        assert root.attrib["viewBox"] == f"0 0 {expected} {expected}"

    def test_custom_scale_and_border(self):
        svg = qr_to_svg(_QR, scale=5, border=2)
        root = ET.fromstring(svg)
        expected = (_QR.get_size() + 2 * 2) * 5
        assert root.attrib["width"] == str(expected)

    def test_custom_colors(self):
        svg = qr_to_svg(_QR, fg_color="red", bg_color="blue")
        assert 'fill="red"' in svg
        assert 'fill="blue"' in svg

    def test_border_zero(self):
        svg = qr_to_svg(_QR, border=0)
        root = ET.fromstring(svg)
        expected = _QR.get_size() * 10
        assert root.attrib["width"] == str(expected)

    def test_scale_one(self):
        svg = qr_to_svg(_QR, scale=1, border=0)
        root = ET.fromstring(svg)
        assert root.attrib["width"] == str(_QR.get_size())

    def test_write_to_file(self):
        with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            result = qr_to_svg(_QR, dest=tmp_path)
            assert result is None
            with open(tmp_path, encoding="utf-8") as fh:
                content = fh.read()
            assert content == qr_to_svg(_QR)
        finally:
            os.unlink(tmp_path)

    def test_path_element_exists(self):
        svg = qr_to_svg(_QR)
        root = ET.fromstring(svg)
        ns = {"svg": "http://www.w3.org/2000/svg"}
        path = root.find("svg:path", ns)
        assert path is not None
        assert "M" in path.attrib["d"]


# ---- PNG tests ----


class TestQrToPng:
    """Tests for qr_to_png()."""

    def test_returns_bytes(self):
        result = qr_to_png(_QR)
        assert isinstance(result, bytes)

    def test_png_signature(self):
        data = qr_to_png(_QR)
        assert data[:8] == b"\x89PNG\r\n\x1a\n"

    def test_roundtrip_dimensions(self):
        from png import decode_png

        data = qr_to_png(_QR, scale=10, border=4)
        img = decode_png(data)
        expected = (_QR.get_size() + 2 * 4) * 10
        assert img.width == expected
        assert img.height == expected

    def test_grayscale_mode(self):
        from png import decode_png

        data = qr_to_png(_QR)
        img = decode_png(data)
        assert img.mode == "L"

    def test_roundtrip_colors(self):
        from png import decode_png

        data = qr_to_png(_QR, scale=10, border=4, fg_color=0, bg_color=255)
        img = decode_png(data)
        # Top-left corner should be background (inside quiet zone).
        assert img.data[0] == 255
        # Finder pattern top-left at (border*scale, border*scale).
        offset = 4 * 10 * img.width + 4 * 10
        assert img.data[offset] == 0

    def test_custom_scale(self):
        from png import decode_png

        data = qr_to_png(_QR, scale=5, border=2)
        img = decode_png(data)
        expected = (_QR.get_size() + 2 * 2) * 5
        assert img.width == expected

    def test_border_zero(self):
        from png import decode_png

        data = qr_to_png(_QR, scale=4, border=0)
        img = decode_png(data)
        expected = _QR.get_size() * 4
        assert img.width == expected

    def test_custom_fg_bg(self):
        from png import decode_png

        data = qr_to_png(_QR, scale=10, border=4, fg_color=50, bg_color=200)
        img = decode_png(data)
        assert img.data[0] == 200
        offset = 4 * 10 * img.width + 4 * 10
        assert img.data[offset] == 50

    def test_write_to_file(self):
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            result = qr_to_png(_QR, dest=tmp_path)
            assert result is None
            with open(tmp_path, "rb") as fh:
                content = fh.read()
            assert content[:8] == b"\x89PNG\r\n\x1a\n"
        finally:
            os.unlink(tmp_path)

    def test_fg_color_out_of_range(self):
        with pytest.raises(ValueError, match="fg_color"):
            qr_to_png(_QR, fg_color=256)

    def test_bg_color_out_of_range(self):
        with pytest.raises(ValueError, match="bg_color"):
            qr_to_png(_QR, bg_color=-1)

    def test_scale_one(self):
        from png import decode_png

        data = qr_to_png(_QR, scale=1, border=0)
        img = decode_png(data)
        assert img.width == _QR.get_size()
        assert img.height == _QR.get_size()


# ---- Edge cases ----


class TestEdgeCases:
    """Edge case tests for both outputs."""

    def test_large_qr_svg(self):
        """Version 10+ QR code renders without error."""
        qr = QrCode.encode_text("A" * 200, QrCode.Ecc.LOW)
        svg = qr_to_svg(qr, scale=2, border=1)
        assert isinstance(svg, str)
        ET.fromstring(svg)  # must be valid XML

    def test_large_qr_png(self):
        """Version 10+ QR code renders without error."""
        qr = QrCode.encode_text("A" * 200, QrCode.Ecc.LOW)
        data = qr_to_png(qr, scale=2, border=1)
        assert data[:8] == b"\x89PNG\r\n\x1a\n"

    def test_empty_border_produces_smaller_output(self):
        size_with_border = len(qr_to_svg(_QR, border=4))
        size_no_border = len(qr_to_svg(_QR, border=0))
        assert size_no_border < size_with_border
