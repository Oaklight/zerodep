# QR Code

QR Code generation with terminal, SVG, and PNG rendering -- zero dependencies (PNG requires sibling `png` module), stdlib only, Python 3.10+.

## Overview

The QR module provides a complete QR Code encoder conforming to the **QR Code Model 2** specification (ISO/IEC 18004). It supports all versions (sizes) from 1 to 40, all 4 error correction levels, and 4 character encoding modes. The module includes rendering functions for terminal output (Unicode block characters), SVG export (string templating), and PNG export (via sibling `png` module).

Based on [Project Nayuki's QR Code generator library](https://www.nayuki.io/page/qr-code-generator-library) (MIT License), with rendering functions added for zerodep.

| File | Description | Dependencies |
|------|-------------|--------------|
| `qr.py` | Full QR Code encoder + terminal/SVG/PNG renderer | `png` (sibling, optional -- only for PNG output) |

## How to Use in Your Project

Copy the single file into your project:

```bash
cp qr/qr.py your_project/
```

Then import the classes you need:

```python
from qr import QrCode, QrSegment, print_qr_terminal, qr_to_svg, qr_to_png
```

## API Reference

### `QrCode` Class

The main class representing a QR Code symbol -- an immutable square grid of dark and light modules.

#### Static Factory Functions (High Level)

##### `QrCode.encode_text(text, ecl)`

Returns a QR Code representing the given Unicode text string at the given error correction level. Automatically chooses the smallest QR Code version that fits the data and selects the optimal encoding mode (numeric, alphanumeric, or byte).

```python
@staticmethod
def encode_text(text: str, ecl: QrCode.Ecc) -> QrCode
```

**Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `text` | `str` | Unicode text string to encode. Guaranteed to succeed for strings with 738 or fewer code points at `Ecc.LOW`. |
| `ecl` | `QrCode.Ecc` | Minimum error correction level. May be boosted if possible without increasing the version. |

**Returns:** `QrCode` -- The generated QR Code object.

**Raises:** `DataTooLongError` -- If the text is too long to fit in any QR Code version.

---

##### `QrCode.encode_binary(data, ecl)`

Returns a QR Code representing the given binary data at the given error correction level. Always uses binary segment mode. Maximum 2953 bytes.

```python
@staticmethod
def encode_binary(data: bytes | Sequence[int], ecl: QrCode.Ecc) -> QrCode
```

**Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `data` | `bytes \| Sequence[int]` | Binary data to encode. Maximum 2953 bytes. |
| `ecl` | `QrCode.Ecc` | Minimum error correction level. |

**Returns:** `QrCode` -- The generated QR Code object.

**Raises:** `DataTooLongError` -- If the data is too long.

---

#### Static Factory Functions (Mid Level)

##### `QrCode.encode_segments(segs, ecl, ...)`

Returns a QR Code representing the given segments with the given encoding parameters. This mid-level API allows custom sequences of segments that switch between modes (such as alphanumeric and byte) to encode text in less space.

```python
@staticmethod
def encode_segments(
    segs: Sequence[QrSegment],
    ecl: QrCode.Ecc,
    minversion: int = 1,
    maxversion: int = 40,
    mask: int = -1,
    boostecl: bool = True,
) -> QrCode
```

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `segs` | `Sequence[QrSegment]` | *(required)* | List of segments to encode. |
| `ecl` | `QrCode.Ecc` | *(required)* | Minimum error correction level. |
| `minversion` | `int` | `1` | Minimum QR Code version (1--40). |
| `maxversion` | `int` | `40` | Maximum QR Code version (1--40). |
| `mask` | `int` | `-1` | Mask pattern (0--7), or -1 for automatic selection. |
| `boostecl` | `bool` | `True` | Whether to boost ECC level if possible without increasing version. |

**Returns:** `QrCode` -- The generated QR Code object.

**Raises:** `DataTooLongError` -- If the segments cannot fit within the specified version range.

---

#### Accessor Methods

| Method | Return Type | Description |
|--------|-------------|-------------|
| `get_version()` | `int` | Version number in the range [1, 40]. |
| `get_size()` | `int` | Size in modules, in the range [21, 177]. Equal to `version * 4 + 17`. |
| `get_error_correction_level()` | `QrCode.Ecc` | Error correction level used. |
| `get_mask()` | `int` | Mask pattern index in the range [0, 7]. |
| `get_module(x, y)` | `bool` | Color of the module at (x, y). `True` = dark, `False` = light. Returns `False` for out-of-bounds coordinates. |

---

### `QrCode.Ecc` Class

Error correction level enumeration. Immutable instances.

| Constant | Tolerance | Description |
|----------|-----------|-------------|
| `QrCode.Ecc.LOW` | ~7% | Lowest redundancy, smallest QR code |
| `QrCode.Ecc.MEDIUM` | ~15% | Balanced choice for most use cases |
| `QrCode.Ecc.QUARTILE` | ~25% | Higher redundancy |
| `QrCode.Ecc.HIGH` | ~30% | Maximum error tolerance, largest QR code |

---

### `QrSegment` Class

A segment of character/binary/control data in a QR Code symbol. Immutable.

#### Static Factory Functions

| Method | Description |
|--------|-------------|
| `QrSegment.make_bytes(data)` | Create a segment from binary data (`bytes` or `Sequence[int]`). |
| `QrSegment.make_numeric(digits)` | Create a segment from a string of decimal digits. |
| `QrSegment.make_alphanumeric(text)` | Create a segment from alphanumeric text (0--9, A--Z uppercase, space, `$%*+-./:` ). |
| `QrSegment.make_segments(text)` | Automatically choose the most efficient encoding for the given text. |
| `QrSegment.make_eci(assignval)` | Create an Extended Channel Interpretation designator segment. |

#### Validation Functions

| Method | Description |
|--------|-------------|
| `QrSegment.is_numeric(text)` | Returns `True` if the string can be encoded in numeric mode. |
| `QrSegment.is_alphanumeric(text)` | Returns `True` if the string can be encoded in alphanumeric mode. |

#### Accessor Methods

| Method | Return Type | Description |
|--------|-------------|-------------|
| `get_mode()` | `QrSegment.Mode` | The encoding mode of this segment. |
| `get_num_chars()` | `int` | Number of characters in this segment. |
| `get_data()` | `list[int]` | A copy of the segment's bit data. |

---

### `QrSegment.Mode` Class

Encoding mode enumeration.

| Constant | Description |
|----------|-------------|
| `QrSegment.Mode.NUMERIC` | Encodes decimal digits (0--9). |
| `QrSegment.Mode.ALPHANUMERIC` | Encodes digits, uppercase letters, and some symbols. |
| `QrSegment.Mode.BYTE` | Encodes arbitrary binary data. |
| `QrSegment.Mode.KANJI` | Encodes Kanji characters (Shift JIS). |
| `QrSegment.Mode.ECI` | Extended Channel Interpretation designator. |

---

### `print_qr_terminal(text)`

Encode text as a QR Code and print it to the terminal using Unicode half-block characters. Uses `Ecc.LOW` for the smallest possible output.

```python
def print_qr_terminal(text: str) -> None
```

**Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `text` | `str` | Text to encode as a QR Code. |

---

### `qr_to_svg(qr, dest, *, scale, border, fg_color, bg_color)`

Render a QR Code as an SVG image. Uses a single `<path>` element for compact output. No dependencies.

```python
def qr_to_svg(
    qr: QrCode,
    dest: str | os.PathLike[str] | None = None,
    *,
    scale: int = 10,
    border: int = 4,
    fg_color: str = "#000000",
    bg_color: str = "#ffffff",
) -> str | None
```

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `qr` | `QrCode` | *(required)* | QR Code to render. |
| `dest` | `str \| PathLike \| None` | `None` | File path to write SVG to, or `None` to return the SVG string. |
| `scale` | `int` | `10` | Size of each QR module in SVG user units. |
| `border` | `int` | `4` | Width of the quiet zone in QR modules. |
| `fg_color` | `str` | `"#000000"` | CSS color for dark modules. |
| `bg_color` | `str` | `"#ffffff"` | CSS color for light modules. |

**Returns:** SVG string when `dest` is `None`, otherwise `None`.

---

### `qr_to_png(qr, dest, *, scale, border, fg_color, bg_color)`

Render a QR Code as a PNG image. Requires the sibling `png` module (lazy-loaded on first call).

```python
def qr_to_png(
    qr: QrCode,
    dest: str | os.PathLike[str] | None = None,
    *,
    scale: int = 10,
    border: int = 4,
    fg_color: int = 0,
    bg_color: int = 255,
) -> bytes | None
```

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `qr` | `QrCode` | *(required)* | QR Code to render. |
| `dest` | `str \| PathLike \| None` | `None` | File path to write PNG to, or `None` to return PNG bytes. |
| `scale` | `int` | `10` | Pixels per QR module. |
| `border` | `int` | `4` | Width of the quiet zone in QR modules. |
| `fg_color` | `int` | `0` | Grayscale value (0--255) for dark modules. |
| `bg_color` | `int` | `255` | Grayscale value (0--255) for light modules. |

**Returns:** PNG bytes when `dest` is `None`, otherwise `None`.

**Raises:**

- `ImportError` -- If the sibling `png` module is not available.
- `ValueError` -- If `fg_color` or `bg_color` is outside 0--255.

---

### `DataTooLongError`

Exception raised when the supplied data does not fit any QR Code version. Subclass of `ValueError`.

## Usage Examples

### Quick Terminal QR Code

```python
from qr import print_qr_terminal

print_qr_terminal("https://example.com")
```

### Encode Text with Error Correction

```python
from qr import QrCode

qr = QrCode.encode_text("Hello, World!", QrCode.Ecc.MEDIUM)
print(f"Version: {qr.get_version()}")
print(f"Size: {qr.get_size()}x{qr.get_size()} modules")
print(f"ECC: {qr.get_error_correction_level().ordinal}")
```

### Encode Binary Data

```python
from qr import QrCode

data = bytes(range(256))
qr = QrCode.encode_binary(data, QrCode.Ecc.LOW)
print(f"Version: {qr.get_version()}")
```

### Custom Segments for Mixed Content

```python
from qr import QrCode, QrSegment

# Mix numeric and alphanumeric segments for better compression
seg1 = QrSegment.make_numeric("314159265")
seg2 = QrSegment.make_alphanumeric("HELLO WORLD")

qr = QrCode.encode_segments([seg1, seg2], QrCode.Ecc.MEDIUM)
```

### Constrain Version Range

```python
from qr import QrCode, DataTooLongError

try:
    # Only allow versions 1--5 (small QR codes)
    qr = QrCode.encode_segments(
        QrSegment.make_segments("Hello"),
        QrCode.Ecc.HIGH,
        minversion=1,
        maxversion=5,
    )
except DataTooLongError:
    print("Data too long for the requested version range")
```

### Export as SVG

```python
from qr import QrCode, qr_to_svg

qr = QrCode.encode_text("https://example.com", QrCode.Ecc.MEDIUM)

# Return SVG string
svg = qr_to_svg(qr)

# Write to file with custom colors
qr_to_svg(qr, "qr.svg", fg_color="darkblue", bg_color="#f0f0f0")
```

### Export as PNG

```python
from qr import QrCode, qr_to_png

qr = QrCode.encode_text("https://example.com", QrCode.Ecc.MEDIUM)

# Return PNG bytes
png_bytes = qr_to_png(qr)

# Write to file with custom scale
qr_to_png(qr, "qr.png", scale=20, border=2)
```

## Notes and Caveats

!!! info "Version Range"
    QR Code versions range from **1** (21x21 modules) to **40** (177x177 modules). Each version increases the size by 4 modules per side. The library automatically selects the smallest version that can hold your data.

!!! info "Automatic Mode Selection"
    When using `encode_text()` or `QrSegment.make_segments()`, the library automatically selects the most efficient encoding mode:

    - **Numeric** mode for strings containing only digits (0--9)
    - **Alphanumeric** mode for strings with digits, uppercase letters, and a few symbols
    - **Byte** mode for all other strings (encoded as UTF-8)

- **Maximum data capacity** (at `Ecc.LOW`): 7,089 numeric characters, 4,296 alphanumeric characters, or 2,953 bytes.
- **Mask selection:** Automatic mask selection (`mask=-1`) tries all 8 masks and picks the one with the lowest penalty score. This can be slow for large QR codes. Specify a mask (0--7) if speed matters.
- **Immutability:** `QrCode` and `QrSegment` instances are immutable after construction. Module data is accessed read-only via `get_module()`.
- **Python version:** Requires Python 3.10+ (uses `X | Y` union type syntax).

## Benchmark

Benchmarked against the `qrcode` library. zerodep is ~2x slower (both pure Python), but still under 20 ms for all tested inputs.

See [QR Code Benchmark](../benchmarks/qr.md) for detailed results.
