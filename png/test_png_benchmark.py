"""Performance benchmarks for zerodep png module.

Apple-to-apple comparisons: each TestClass contains test_zerodep and
test_pillow measuring the same operation on the same input.
"""

import io
import os
import random
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from png import (
    Image,
    decode_bmp,
    decode_png,
    encode_bmp,
    encode_png,
    matrix_to_png,
    png_to_matrix,
)

PIL_Image = pytest.importorskip("PIL.Image")


# ============================================================================
# Helpers — generate test data once, reuse across benchmarks
# ============================================================================


def _make_pixels(mode, width, height, seed=42):
    rng = random.Random(seed)
    bpp = {"L": 1, "LA": 2, "RGB": 3, "RGBA": 4}[mode]
    return bytes(rng.randint(0, 255) for _ in range(width * height * bpp))


def _make_png_bytes_pillow(mode, width, height, seed=42):
    """Generate PNG bytes using Pillow (reference encoder)."""
    pixels = _make_pixels(mode, width, height, seed)
    pil = PIL_Image.frombytes(mode, (width, height), pixels)
    buf = io.BytesIO()
    pil.save(buf, format="PNG")
    return buf.getvalue(), pixels


def _make_bmp_bytes_pillow(mode, width, height, seed=42):
    """Generate BMP bytes using Pillow."""
    pixels = _make_pixels(mode, width, height, seed)
    pil = PIL_Image.frombytes(mode, (width, height), pixels)
    buf = io.BytesIO()
    pil.save(buf, format="BMP")
    return buf.getvalue(), pixels


def _pillow_decode(png_bytes):
    pil = PIL_Image.open(io.BytesIO(png_bytes))
    pil.load()
    return pil


def _pillow_encode(pil_img):
    buf = io.BytesIO()
    pil_img.save(buf, format="PNG")
    return buf.getvalue()


def _pillow_decode_bmp(bmp_bytes):
    pil = PIL_Image.open(io.BytesIO(bmp_bytes))
    pil.load()
    return pil


def _pillow_encode_bmp(pil_img):
    buf = io.BytesIO()
    pil_img.save(buf, format="BMP")
    return buf.getvalue()


# ============================================================================
# PNG Decode
# ============================================================================


class TestDecodeSmallRGBA:
    """Decode 64x64 RGBA PNG."""

    PNG, _ = _make_png_bytes_pillow("RGBA", 64, 64)

    def test_zerodep(self, benchmark):
        benchmark(decode_png, self.PNG)

    def test_pillow(self, benchmark):
        benchmark(_pillow_decode, self.PNG)


class TestDecodeMediumRGBA:
    """Decode 256x256 RGBA PNG."""

    PNG, _ = _make_png_bytes_pillow("RGBA", 256, 256)

    def test_zerodep(self, benchmark):
        benchmark(decode_png, self.PNG)

    def test_pillow(self, benchmark):
        benchmark(_pillow_decode, self.PNG)


class TestDecodeLargeRGBA:
    """Decode 1024x1024 RGBA PNG."""

    PNG, _ = _make_png_bytes_pillow("RGBA", 1024, 1024)

    def test_zerodep(self, benchmark):
        benchmark(decode_png, self.PNG)

    def test_pillow(self, benchmark):
        benchmark(_pillow_decode, self.PNG)


class TestDecodeMediumRGB:
    """Decode 256x256 RGB PNG."""

    PNG, _ = _make_png_bytes_pillow("RGB", 256, 256)

    def test_zerodep(self, benchmark):
        benchmark(decode_png, self.PNG)

    def test_pillow(self, benchmark):
        benchmark(_pillow_decode, self.PNG)


class TestDecodeMediumGray:
    """Decode 256x256 grayscale PNG."""

    PNG, _ = _make_png_bytes_pillow("L", 256, 256)

    def test_zerodep(self, benchmark):
        benchmark(decode_png, self.PNG)

    def test_pillow(self, benchmark):
        benchmark(_pillow_decode, self.PNG)


# ============================================================================
# PNG Encode
# ============================================================================


class TestEncodeSmallRGBA:
    """Encode 64x64 RGBA PNG."""

    PIXELS = _make_pixels("RGBA", 64, 64)
    IMG = Image(width=64, height=64, data=PIXELS, mode="RGBA")
    PIL = PIL_Image.frombytes("RGBA", (64, 64), PIXELS)

    def test_zerodep(self, benchmark):
        benchmark(encode_png, self.IMG)

    def test_pillow(self, benchmark):
        benchmark(_pillow_encode, self.PIL)


class TestEncodeMediumRGBA:
    """Encode 256x256 RGBA PNG."""

    PIXELS = _make_pixels("RGBA", 256, 256)
    IMG = Image(width=256, height=256, data=PIXELS, mode="RGBA")
    PIL = PIL_Image.frombytes("RGBA", (256, 256), PIXELS)

    def test_zerodep(self, benchmark):
        benchmark(encode_png, self.IMG)

    def test_pillow(self, benchmark):
        benchmark(_pillow_encode, self.PIL)


class TestEncodeLargeRGBA:
    """Encode 1024x1024 RGBA PNG."""

    PIXELS = _make_pixels("RGBA", 1024, 1024)
    IMG = Image(width=1024, height=1024, data=PIXELS, mode="RGBA")
    PIL = PIL_Image.frombytes("RGBA", (1024, 1024), PIXELS)

    def test_zerodep(self, benchmark):
        benchmark(encode_png, self.IMG)

    def test_pillow(self, benchmark):
        benchmark(_pillow_encode, self.PIL)


# ============================================================================
# BMP Decode / Encode
# ============================================================================


class TestDecodeBmpMediumRGB:
    """Decode 256x256 RGB BMP."""

    BMP, _ = _make_bmp_bytes_pillow("RGB", 256, 256)

    def test_zerodep(self, benchmark):
        benchmark(decode_bmp, self.BMP)

    def test_pillow(self, benchmark):
        benchmark(_pillow_decode_bmp, self.BMP)


class TestEncodeBmpMediumRGB:
    """Encode 256x256 RGB BMP."""

    PIXELS = _make_pixels("RGB", 256, 256)
    IMG = Image(width=256, height=256, data=PIXELS, mode="RGB")
    PIL = PIL_Image.frombytes("RGB", (256, 256), PIXELS)

    def test_zerodep(self, benchmark):
        benchmark(encode_bmp, self.IMG)

    def test_pillow(self, benchmark):
        benchmark(_pillow_encode_bmp, self.PIL)


# ============================================================================
# Matrix round-trip
# ============================================================================


def _make_float_matrix(rows, cols, seed=42):
    rng = random.Random(seed)
    return [[rng.random() * 100 - 50 for _ in range(cols)] for _ in range(rows)]


class TestMatrixRoundTrip:
    """Matrix -> PNG -> matrix round-trip, 256x256 float."""

    MATRIX = _make_float_matrix(256, 256)
    PNG = matrix_to_png(MATRIX)

    def test_zerodep_encode(self, benchmark):
        benchmark(matrix_to_png, self.MATRIX)

    def test_zerodep_decode(self, benchmark):
        benchmark(png_to_matrix, self.PNG)

    def test_pillow_encode(self, benchmark):
        """Pillow equivalent: flatten matrix to grayscale image bytes."""
        import numpy as np

        arr = np.array(self.MATRIX, dtype=np.float64)
        vmin, vmax = arr.min(), arr.max()
        scaled = ((arr - vmin) / (vmax - vmin) * 255).astype(np.uint8)
        pil = PIL_Image.fromarray(scaled, mode="L")

        def _encode():
            buf = io.BytesIO()
            pil.save(buf, format="PNG")
            return buf.getvalue()

        benchmark(_encode)

    def test_pillow_decode(self, benchmark):
        """Pillow equivalent: decode PNG to numpy array."""
        import numpy as np

        def _decode():
            pil = PIL_Image.open(io.BytesIO(self.PNG))
            return np.array(pil)

        benchmark(_decode)
