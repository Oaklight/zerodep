# Multipart 性能测试

zerodep multipart（纯 Python）与 [`python-multipart`](https://pypi.org/project/python-multipart/)（基于回调的解析器）的同类对比性能测试。

!!! info "测试环境"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **工具:** pytest-benchmark 5.2.3（报告均值）
    - **对标库:** python-multipart 0.0.20
    - **最后更新:** 2026-05-16

## 实现对比

| 实现 | 文件/包 | 说明 |
|------|---------|------|
| **zerodep** | `multipart.py` | 仅标准库的边界分割解析器和编码器 |
| **python-multipart** | *（参考库）* | 基于回调的流式 multipart 解析器 |

## 载荷规模

| 标签 | 说明 | 大约大小 |
|------|------|----------|
| 小型 | 3 个文本字段 | ~200 B |
| 中型 | 5 个文本字段 + 2 个小文件（各 2 KB） | ~10 KB |
| 大型 | 10 个文本字段 + 5 个文件（各 80 KB） | ~500 KB |

## 解析性能（均值）

| 载荷 | zerodep | python-multipart | 加速比 |
|------|---------|------------------|--------|
| 小型 | 21.7 μs | 87.6 μs | **快 4.0x** |
| 中型 | 63.0 μs | 239.9 μs | **快 3.8x** |
| 大型 | 463.4 μs | 645.0 μs | **快 1.4x** |

## 编码性能（均值，仅 zerodep）

python-multipart 不提供编码器，因此仅测量 zerodep。

| 载荷 | zerodep |
|------|---------|
| 小型 | 4.0 μs |
| 中型 | 7.8 μs |
| 大型 | 38.8 μs |

## 往返性能（均值，仅 zerodep）

编码 → 解析循环。

| 载荷 | zerodep |
|------|---------|
| 小型 | 24.2 μs |
| 中型 | 73.2 μs |

## 要点总结

- **解析快 1.4–4.0 倍** — zerodep 的边界分割算法在所有载荷规模上均优于 python-multipart 的基于回调的流式解析器。
- **小载荷加速比最高** — 小消息体中每次调用的开销占主导地位；zerodep 完全避免了回调建立的成本。
- **编码速度快** — 构建 500 KB 的 multipart 消息体仅需约 39 μs，相比网络 I/O 可以忽略不计。
- **往返不到 75 μs** — 中型载荷（10 KB）的编码 + 解析在约 73 μs 内完成。
- **python-multipart 没有编码器** — zerodep 在一个文件中同时提供解析和编码；python-multipart 仅支持解析。
- **基准测试使用预构建载荷** — 载荷生成成本不计入计时。
- zerodep **零 pip 依赖** — 仅使用标准库（`re`、`base64`、`quopri`、`dataclasses`）。

## 自行运行

```bash
pip install pytest pytest-benchmark python-multipart
pytest multipart/test_multipart_benchmark.py --benchmark-only -v
```

---

## 最新 CI 结果

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/multipart.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> 每次发版时通过 [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml) 自动更新。
