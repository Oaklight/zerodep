# YAML 性能测试

zerodep YAML 与 [`PyYAML`](https://pypi.org/project/PyYAML/) 在三种输入大小下进行加载（load）和序列化（dump）操作的性能对比。

!!! info "测试环境"
    - **平台:** x86_64 Linux
    - **Python:** 3.10.20
    - **工具:** pytest-benchmark 5.2.3（报告均值）

## 实现对比

| 实现 | 文件/包 | 说明 |
|------|---------|------|
| **zerodep** | `yaml.py` | 仅依赖标准库的 YAML 解析/序列化 |
| **PyYAML** | *（参考库）* | Python 生态中最广泛使用的 YAML 库 |

## 加载性能对比（均值）

| 测试项 | zerodep | PyYAML | 倍数 |
|--------|---------|--------|------|
| 小型 | 11.2 μs | 118.2 μs | 快 10.6x |
| 中型 | 64.2 μs | 685.3 μs | 快 10.7x |
| 大型 | 1,403.9 μs | 14,576.1 μs | 快 10.4x |

## 序列化性能对比（均值）

| 测试项 | zerodep | PyYAML | 倍数 |
|--------|---------|--------|------|
| 小型 | 23.8 μs | 188.5 μs | 快 7.9x |
| 中型 | 170.8 μs | 1,234.1 μs | 快 7.2x |
| 大型 | 3,901.1 μs | 27,279.1 μs | 快 7.0x |

## 要点总结

- **加载**场景下 zerodep 比 PyYAML 快约 **10 倍**，优势在各种规模下保持稳定。
- **序列化**场景下 zerodep 比 PyYAML 快约 **7-8 倍**。
- zerodep **无需任何 pip 依赖**——仅使用标准库，而 PyYAML 需要通过 pip 安装（含 C 扩展构建）。
- 适合对性能和依赖数量同时有要求的场景。

## 自行运行

```bash
pip install pytest pytest-benchmark pyyaml
pytest yaml/test_yaml_benchmark.py --benchmark-only -v
```
