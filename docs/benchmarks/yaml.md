# YAML 性能测试

zerodep YAML 与 [`PyYAML`](https://pypi.org/project/PyYAML/) 在三种输入大小下进行加载（load）和序列化（dump）操作的性能对比。

!!! info "测试环境"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **工具:** pytest-benchmark 5.2.3（报告均值）
    - **对标库:** PyYAML 6.0.3
    - **最后更新:** 2026-04-15

## 实现对比

| 实现 | 文件/包 | 说明 |
|------|---------|------|
| **zerodep** | `yaml.py` | 仅依赖标准库的 YAML 解析/序列化 |
| **PyYAML** | *（参考库）* | Python 生态中最广泛使用的 YAML 库 |

## 加载性能对比（均值）

| 测试项 | zerodep | PyYAML | 倍数 |
|--------|---------|--------|------|
| 小型 | 33.7 μs | 256.5 μs | 快 7.6x |
| 中型 | 229.0 μs | 1,650.0 μs | 快 7.2x |
| 大型 | 4,764.9 μs | 38,628.7 μs | 快 8.1x |

## 序列化性能对比（均值）

| 测试项 | zerodep | PyYAML | 倍数 |
|--------|---------|--------|------|
| 小型 | 16.1 μs | 152.5 μs | 快 9.5x |
| 中型 | 110.8 μs | 859.0 μs | 快 7.8x |
| 大型 | 2,612.9 μs | 18,975.4 μs | 快 7.3x |

## 要点总结

- **加载**场景下 zerodep 比 PyYAML 快约 **7--8 倍**，优势在各种规模下保持稳定。
- **序列化**场景下 zerodep 比 PyYAML 快约 **7--10 倍**，小输入时加速比最高。
- zerodep **无需任何 pip 依赖**——仅使用标准库，而 PyYAML 需要通过 pip 安装（含 C 扩展构建）。
- 适合对性能和依赖数量同时有要求的场景。

## 自行运行

```bash
pip install pytest pytest-benchmark pyyaml
pytest yaml/test_yaml_benchmark.py --benchmark-only -v
```

---

## 最新 CI 结果

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/yaml.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> 每次发版时通过 [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml) 自动更新。
