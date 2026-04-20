# QR 二维码性能测试

zerodep QR 实现与 [`qrcode`](https://pypi.org/project/qrcode/) 库（纯 Python）的同条件性能对比。

!!! info "测试环境"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **工具:** pytest-benchmark 5.2.3（报告均值）
    - **对标库:** qrcode 8.2, Pillow 12.2.0
    - **最后更新:** 2026-04-20

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
| 短文本（5 字符） | 1.9 ms | 1.7 ms | 慢 1.1 倍 |
| URL（46 字符） | 4.4 ms | 4.8 ms | **快 1.1 倍** |
| 长文本（200 字符） | 9.2 ms | 11.3 ms | **快 1.2 倍** |

## 要点总结

- **zerodep 现在具有竞争力甚至更快** -- 优化后，zerodep 在最短输入上仅慢 1.1 倍，在**中长输入上已反超**（快 1.1-1.2 倍）。此前在所有输入上均慢约 2 倍。
- **性能随输入长度增长表现更好** -- zerodep 优化后的编码路径具有更好的可扩展性，随着输入长度增加，相对 `qrcode` 越来越快。
- 两者都是纯 Python 实现。与 AES 可以通过 ctypes 调用系统 `libcrypto` 不同，QR Code 生成没有跨平台预装的 C 库可供利用。
- 对于大多数应用场景，两者都足够快——QR Code 生成很少成为性能瓶颈。即使最慢的情况（200 字符）也在 12 ms 内完成。

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
