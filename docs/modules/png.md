# PNG / BMP Image Codec

Zero-dependency PNG and BMP image codec with matrix compression API -- stdlib only, Python 3.10+.

## Overview

The `png` module encodes and decodes PNG and BMP images using only the Python standard library (`zlib`, `struct`). It provides a shared `Image` dataclass for format conversion and a `matrix_to_png` / `png_to_matrix` API that exploits PNG row filters for efficient 2D numeric data compression.

| File | Description | Dependencies |
|------|-------------|--------------|
| `png/png.py` | PNG/BMP codec + matrix API | None (stdlib only) |

### Key Features

- **PNG codec** -- encode and decode PNG images via stdlib `zlib`
- **BMP codec** -- encode and decode 24-bit RGB and 32-bit RGBA uncompressed BMP
- **Color modes** -- grayscale (L), grayscale+alpha (LA), RGB, RGBA
- **Bit depths** -- 8 and 16 bits per channel
- **All 5 row filters** -- None, Sub, Up, Average, Paeth with auto-selection heuristic
- **tEXt metadata** -- read and write ancillary text chunks
- **Mode conversion** -- convert between L/LA/RGB/RGBA with luminosity-based grayscale
- **Matrix API** -- compress 2D numeric data as grayscale PNG with lossless float round-trip

## How to Use in Your Project

```bash
cp png/png.py your_project/
```

```python
from png import decode_png, encode_png, Image
```

## Usage Examples

### Decode a PNG File

```python
from png import decode_png

img = decode_png("photo.png")
print(f"{img.width}x{img.height} {img.mode} {img.bit_depth}-bit")
print(f"pixel data: {len(img.data)} bytes")
```

### Create and Encode a PNG

```python
from png import encode_png, Image

# Create a 2x2 red image
pixels = bytes([255, 0, 0, 255, 0, 0, 0, 255, 0, 0, 255, 0])
img = Image(width=2, height=2, data=pixels, mode="RGB")

# Save to file
encode_png(img, "output.png")

# Or get bytes
png_bytes = encode_png(img)
```

### BMP Support

```python
from png import decode_bmp, encode_bmp

# Decode BMP
img = decode_bmp("image.bmp")

# Convert PNG to BMP
from png import decode_png, encode_bmp
img = decode_png("input.png")
encode_bmp(img, "output.bmp")
```

### Mode Conversion

```python
from png import decode_png, convert

img = decode_png("color.png")  # RGBA
gray = convert(img, "L")       # grayscale
rgb = convert(img, "RGB")      # drop alpha
```

### Matrix Compression

```python
import math
from png import matrix_to_png, png_to_matrix

# Compress a 2D float matrix as PNG
matrix = [[math.sin(x * 0.1 + y * 0.2) for x in range(256)]
          for y in range(256)]
matrix_to_png(matrix, "data.png", bit_depth=16)

# Reconstruct (lossless for integers, quantized for floats)
restored = png_to_matrix("data.png")
```

### Filter Strategies

```python
from png import encode_png, Image

img = Image(width=100, height=100, data=pixels, mode="RGB")

# Auto-select best filter per row (default)
encode_png(img, filter_strategy="auto")

# Force a specific filter
encode_png(img, filter_strategy="sub")    # good for photos
encode_png(img, filter_strategy="paeth")  # good for gradients
encode_png(img, filter_strategy="none")   # fastest, largest
```

## API Reference

### Functions

| Function | Description |
|----------|-------------|
| `decode_png(source)` | Decode PNG file/bytes into `Image` |
| `encode_png(image, dest, *, filter_strategy, compression_level)` | Encode `Image` as PNG |
| `decode_bmp(source)` | Decode BMP file/bytes into `Image` |
| `encode_bmp(image, dest)` | Encode `Image` as BMP |
| `matrix_to_png(matrix, dest, *, bit_depth, filter_strategy, compression_level)` | Compress 2D matrix as grayscale PNG |
| `png_to_matrix(source)` | Decompress grayscale PNG back to 2D matrix |
| `convert(image, mode)` | Convert image to different pixel mode |

### Classes

| Class | Description |
|-------|-------------|
| `Image` | Dataclass holding decoded pixel data (width, height, data, mode, bit_depth, metadata) |

### Exceptions

| Exception | Description |
|-----------|-------------|
| `ImageError` | Base exception for image codec errors |
| `DecodeError` | Raised when image decoding fails |
| `EncodeError` | Raised when image encoding fails |

## Supported Formats

### PNG

| Feature | Supported |
|---------|-----------|
| Color types | Grayscale (0), RGB (2), Grayscale+Alpha (4), RGBA (6) |
| Bit depths | 8, 16 per channel |
| Row filters | None, Sub, Up, Average, Paeth |
| Metadata | tEXt chunks (read/write) |
| Interlacing | Not supported (Adam7) |
| Palette | Not supported (color type 3) |

### BMP

| Feature | Supported |
|---------|-----------|
| Bit depths | 24-bit RGB, 32-bit RGBA |
| Compression | Uncompressed only |
| Row order | Bottom-up and top-down |
| Palette/RLE | Not supported |

## Comparison with Pillow

| Feature | zerodep | Pillow |
|---------|---------|--------|
| Dependencies | None (stdlib only) | C extensions (~50 MB) |
| File size | Single .py file | Full package |
| PNG encode/decode | Yes (8/16-bit, 4 color types) | Yes (all PNG features) |
| BMP encode/decode | Yes (24/32-bit) | Yes (all BMP variants) |
| JPEG | No | Yes |
| Image manipulation | Mode conversion only | Full image processing |
| Matrix compression | Built-in API | Via numpy integration |
| Install | Copy one file | `pip install Pillow` |

## Benchmark

Benchmarked against `Pillow`. See [PNG Benchmark](../benchmarks/png.md).
