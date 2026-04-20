# QR 二维码性能测试

zerodep QR 实现与 [`qrcode`](https://pypi.org/project/qrcode/) 库（纯 Python）的同条件性能对比。

!!! info "测试环境"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **工具:** pytest-benchmark 5.2.3（报告均值）
    - **对标库:** qrcode 8.2, Pillow 12.2.0
    - **最后更新:** 2026-04-21

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
| 纯数字 | `"0123456789" * 10` | 100 字符 |
| 二进制 | 512 字节随机数据 | 512 字节 |
| 高纠错 | URL，使用 `ERROR_CORRECT_H` | 46 字符 |
| 大数据 | `"A" * 1000`，使用 `ERROR_CORRECT_L` | 1000 字符 |

## 编码性能（均值）

| 输入 | zerodep（`qr.py`） | `qrcode` 库 | 倍率 |
|------|---------------------|-------------|------|
| 短文本（5 字符） | 2.34 ms | 1.84 ms | 慢 1.3 倍 |
| URL（46 字符） | 5.40 ms | 5.22 ms | 持平 |
| 长文本（200 字符） | 11.06 ms | 11.69 ms | 持平 |
| 纯数字（100 字符） | 4.30 ms | 4.02 ms | 慢 1.1 倍 |
| 二进制（512 字节） | 34.33 ms | 41.75 ms | **快 1.2 倍** |
| 高纠错（URL, HIGH） | 6.43 ms | 6.36 ms | 持平 |
| 大数据（1000 字符, LOW） | 34.87 ms | 44.88 ms | **快 1.3 倍** |

## 要点总结

- **zerodep 在大负载上表现出色** -- 对于二进制数据（512 字节）和大文本（1000 字符），zerodep 比 `qrcode` **快 1.2-1.3 倍**，在大数据量输入上展现出更优的扩展性。
- **中等输入上旗鼓相当** -- URL、长文本（200 字符）和高纠错等场景下两者持平。
- **短/数字输入上略慢** -- zerodep 在最短输入（5 字符、纯数字）上慢 1.1-1.3 倍，`qrcode` 的编码路径在这些场景下开销更小。
- 两者都是纯 Python 实现。与 AES 可以通过 ctypes 调用系统 `libcrypto` 不同，QR Code 生成没有跨平台预装的 C 库可供利用。
- 对于大多数应用场景，两者都足够快——QR Code 生成很少成为性能瓶颈。即使最大的情况（1000 字符）也在 45 ms 内完成。

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
