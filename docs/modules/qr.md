# QR 二维码

QR Code 生成与终端渲染 —— 零依赖。

## 用法

```python
from qr import QrCode

qr = QrCode.encode_text("https://example.com", QrCode.Ecc.MEDIUM)
qr.print_terminal()
```

## 性能测试

与 `qrcode` 进行对比测试。详见[性能测试](../benchmarks.md)。
