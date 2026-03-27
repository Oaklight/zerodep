# QR Code

QR Code generation with terminal rendering — zero dependencies.

## Usage

```python
from qr import QrCode

qr = QrCode.encode_text("https://example.com", QrCode.Ecc.MEDIUM)
qr.print_terminal()
```

## Benchmark

Benchmarked against `qrcode`. See [Benchmarks](../benchmarks.md) for details.
