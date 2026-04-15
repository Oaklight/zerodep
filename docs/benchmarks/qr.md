# QR 二维码性能测试

zerodep QR 实现与 [`qrcode`](https://pypi.org/project/qrcode/) 库（纯 Python）的同条件性能对比。

!!! info "测试环境"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **工具:** pytest-benchmark 5.2.3（报告均值）
    - **对标库:** qrcode 8.2, Pillow 12.2.0
    - **最后更新:** 2026-04-15

## 实现对比

两个实现都是纯 Python，因此对比的是两个解释执行的代码库之间的效率差异。

| 实现 | 文件/包 | 说明 |
|------|---------|------|
| **zerodep** | `qr.py` | 基于 Nayuki，单文件 |
| **qrcode** | *（参考库）* | 流行的 `qrcode` PyPI 包 |

## 测试输入

| 标签 | 内容 | 长度 |
|------|------|------|
| 短文本 | `"Hello"` | 5 字符 |
| URL | `"https://example.com/path?query=value&foo=bar"` | 46 字符 |
| 长文本 | `"A" * 200` | 200 字符 |

## 编码性能（均值）

| 输入 | zerodep（`qr.py`） | `qrcode` 库 | 倍率 |
|------|---------------------|-------------|------|
| 短文本（5 字符） | 3.5 ms | 1.7 ms | 慢 2.1 倍 |
| URL（46 字符） | 9.2 ms | 4.8 ms | 慢 1.9 倍 |
| 长文本（200 字符） | 19.4 ms | 11.3 ms | 慢 1.7 倍 |

## 要点总结

- **zerodep**（`qr.py`）比 `qrcode` 库**慢约 2 倍**。随着输入变长，差距逐渐缩小（从 2.1 倍到 1.7 倍）。
- 两者都是纯 Python 实现。与 AES 可以通过 ctypes 调用系统 `libcrypto` 不同，QR Code 生成没有跨平台预装的 C 库可供利用。zerodep 优先保证**正确性**和**零依赖**，而非追求极致速度。
- 对于大多数应用场景，两者都足够快——QR Code 生成很少成为性能瓶颈。即使最慢的情况（200 字符）也在 20 ms 内完成。

## 自行运行

```bash
pip install pytest pytest-benchmark qrcode
pytest qr/test_qr_benchmark.py --benchmark-only -v
```

---

## 最新 CI 结果

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/qr.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> 每次发版时通过 [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml) 自动更新。
