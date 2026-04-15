# TOON 性能测试

zerodep TOON 与 [`toon_format`](https://github.com/toon-format/toon-python) 的性能对比。

!!! info "测试环境"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **工具:** pytest-benchmark 5.2.3（报告均值）
    - **对标库:** toon_format 0.9.0b1
    - **最后更新:** 2026-04-15

## 实现对比

| 实现 | 文件/包 | 说明 |
|------|---------|------|
| **zerodep** | `toon.py` | 单文件编码器/解码器，仅标准库 |
| **toon_format** | *（参考库）* | 18 个源文件，依赖 typing-extensions |

## 测试数据

| 规模 | 描述 |
|------|------|
| Small | 简单的 3 字段对象（`{id, name, active}`） |
| Medium | 包含 20 行表格数组 + 嵌套配置的对象 |
| Large | 5 个部门 × 4 个团队 × 5 名成员（深度嵌套，约 100 个对象） |

## 编码性能（均值）

| 数据规模 | zerodep | toon_format | 倍数 |
|----------|---------|-------------|------|
| Small | 7.0 μs | 9.9 μs | 快 1.4x |
| Medium | 168.8 μs | 205.7 μs | 快 1.2x |
| Large | 995.4 μs | 1,238.4 μs | 快 1.2x |

## 解码性能（均值）

| 数据规模 | zerodep | toon_format | 倍数 |
|----------|---------|-------------|------|
| Small | 16.3 μs | 18.9 μs | 快 1.2x |
| Medium | 259.1 μs | 277.3 μs | 快 1.1x |
| Large | 1,770.2 μs | 1,873.0 μs | 快 1.1x |

## Token 效率（TOON vs JSON）

| 数据规模 | JSON（字符） | TOON（字符） | 节省 |
|----------|-------------|-------------|------|
| Small | 52 | 32 | 38.5% |
| Medium | 2,171 | 638 | 70.6% |
| Large | 16,829 | 4,882 | 71.0% |

## 要点总结

- **编码快 1.2-1.4 倍** —— 将 18 个源文件合并为单文件，减少了导入和调度开销。
- **解码快 1.1-1.2 倍** —— 单文件布局消除了跨模块函数调用开销。
- **比 JSON 减少 38-71% 字符** —— TOON 的表格数组格式和裸键语法在结构化数据上实现显著压缩。表格数据越多节省越大。
- **无需任何 pip 依赖** —— zerodep 仅使用标准库 `re`、`math`、`dataclasses`、`collections.abc`。

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
