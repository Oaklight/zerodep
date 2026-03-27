# Tabulate 性能测试

zerodep tabulate 与 [`tabulate`](https://pypi.org/project/tabulate/) 的性能对比。

!!! info "测试环境"
    - **平台:** x86_64 Linux
    - **Python:** 3.10.20
    - **工具:** pytest-benchmark 5.2.3（报告均值）

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
| Small | 32.5 μs | 93.8 μs | 快 2.89x |
| Medium | 266.4 μs | 910.1 μs | 快 3.42x |
| Large | 3,883.4 μs | 13,804.4 μs | 快 3.56x |

## 要点总结

- **格式化快 2.9-3.6 倍** —— 单文件实现避免了参考库多模块调度和功能协商的开销。
- **数据越大优势越明显** —— zerodep 的列宽计算和行渲染具有更好的扩展性。
- **无需任何 pip 依赖** —— zerodep 仅使用标准库 `re`、`math`、`unicodedata`、`dataclasses`。

## 自行运行

```bash
pip install pytest pytest-benchmark tabulate
pytest tabulate/test_tabulate_benchmark.py --benchmark-only -v
```
