# TOON 性能测试

zerodep TOON 与 [`toon_format`](https://github.com/toon-format/toon-python) 的性能对比。

!!! info "测试环境"
    - **CPU:** x86_64 Linux
    - **Python:** 3.10
    - **工具:** pytest-benchmark（报告均值）
    - **对标库:** toon-format @91413d14（spec 4.4）
    - **最后更新:** 2026-10-22

## 实现对比

| 实现 | 文件/包 | 说明 |
|------|---------|------|
| **zerodep** | `toon.py` | 单文件编码器/解码器，仅标准库 |
| **toon_format** | *（参考库）* | 7 个源文件，核心功能无依赖 |

## 测试数据

| 规模 | 描述 |
|------|------|
| Small | 简单的 3 字段对象（`{id, name, active}`） |
| Medium | 包含 20 行表格数组 + 嵌套配置的对象 |
| Large | 5 个部门 × 4 个团队 × 5 名成员（深度嵌套，约 100 个对象） |

## 编码性能（均值）

| 数据规模 | zerodep | toon_format | 倍数 |
|----------|---------|-------------|------|
| Small | 6.5 μs | 6.6 μs | 1.0x |
| Medium | 127.1 μs | 126.7 μs | 1.0x |
| Large | 869.8 μs | 1,093.3 μs | 快 1.3x |

## 解码性能（均值）

| 数据规模 | zerodep | toon_format | 倍数 |
|----------|---------|-------------|------|
| Small | 12.6 μs | 9.7 μs | 0.8x |
| Medium | 114.5 μs | 118.3 μs | 1.0x |
| Large | 810.8 μs | 787.6 μs | 1.0x |

## Token 效率（TOON vs JSON）

| 数据规模 | JSON（字符） | TOON（字符） | 节省 |
|----------|-------------|-------------|------|
| Small | 52 | 32 | 38.5% |
| Medium | 2,171 | 638 | 70.6% |
| Large | 16,829 | 4,882 | 71.0% |

## 要点总结

- **编码速度基本持平，大文档快约 1.3 倍** —— 实现沿用参考库算法，大文档的差异来自单文件布局而非不同格式。
- **解码速度基本持平** —— 小文档略慢，中大型文档在噪声范围内。
- **比 JSON 减少 38-71% 字符** —— TOON 的表格数组格式和裸键语法在结构化数据上实现显著压缩。表格数据越多节省越大。
- **无需任何 pip 依赖** —— 模块仅使用 Python 标准库。

## 自行运行

```bash
pip install pytest pytest-benchmark
pip install git+https://github.com/toon-format/toon-python.git
pytest toon/test_toon_benchmark.py --benchmark-only -v
```

---

## 最新 CI 结果

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/toon.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> 每次发版时通过 [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml) 自动更新。
