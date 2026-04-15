# Tabulate 性能测试

zerodep tabulate 与 [`tabulate`](https://pypi.org/project/tabulate/) 的性能对比。

!!! info "测试环境"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **工具:** pytest-benchmark 5.2.3（报告均值）
    - **对标库:** tabulate 0.10.0
    - **最后更新:** 2026-04-15

## 实现对比

| 实现 | 文件/包 | 说明 |
|------|---------|------|
| **zerodep** | `tabulate.py` | 单文件表格格式化，仅标准库 |
| **tabulate** | *（参考库）* | 流行的表格格式化库 |

## 测试数据

| 规模 | 描述 |
|------|------|
| Small | 简单的 3 列 3 行表格 |
| Medium | 10 列 20 行混合类型表格 |
| Large | 15 列 100 行数字和字符串表格 |

## 格式化性能（均值）

| 数据规模 | zerodep | tabulate | 倍数 |
|----------|---------|----------|------|
| Small | 45.1 μs | 144.2 μs | 快 3.2x |
| Medium | 335.1 μs | 1,428.8 μs | 快 4.3x |
| Large | 5,405.9 μs | 21,904.8 μs | 快 4.1x |

## 要点总结

- **格式化快 3.2-4.3 倍** —— 单文件实现避免了参考库多模块调度和功能协商的开销。
- **数据越大优势越明显** —— zerodep 的列宽计算和行渲染具有更好的扩展性，中型表格可达 4.3 倍加速。
- **无需任何 pip 依赖** —— zerodep 仅使用标准库 `re`、`math`、`unicodedata`、`dataclasses`。

## 自行运行

```bash
pip install pytest pytest-benchmark tabulate
pytest tabulate/test_tabulate_benchmark.py --benchmark-only -v
```

---

## 最新 CI 结果

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/tabulate.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> 每次发版时通过 [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml) 自动更新。
