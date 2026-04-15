# 结构化日志性能测试

zerodep structlog 与 [`structlog`](https://pypi.org/project/structlog/) 在四个场景下的性能对比。

!!! info "测试环境"
    - **平台:** x86_64 Linux
    - **Python:** 3.10.20
    - **工具:** pytest-benchmark 5.2.3（报告均值）

## 实现对比

| 实现 | 文件/包 | 说明 |
|------|---------|------|
| **zerodep** | `structlog.py` | 仅依赖标准库的结构化日志 |
| **structlog** | *（参考库）* | 功能丰富的结构化日志库 |

## 性能对比（均值）

| 测试项 | zerodep | structlog | 倍数 |
|--------|---------|-----------|------|
| 简单日志 | 5.0 μs | 5.7 μs | 快 1.1x |
| 绑定上下文日志 | 5.0 μs | 7.3 μs | 快 1.5x |
| JSON 渲染 | 5.5 μs | 10.9 μs | 快 2.0x |
| 绑定 + 日志 | 5.7 μs | 12.9 μs | 快 2.3x |

## 要点总结

- **简单日志**场景下两者性能接近，zerodep 略快。
- **复杂操作**（绑定上下文、JSON 渲染、绑定后立即记录）优势逐步增大，最高快 **2.3 倍**。
- zerodep 的轻量实现在处理上下文绑定和 JSON 序列化时开销更低。
- zerodep **无需任何 pip 依赖**——仅使用标准库 `logging` 和 `json`。

## 自行运行

```bash
pip install pytest pytest-benchmark structlog
pytest structlog/test_structlog_benchmark.py --benchmark-only -v
```

---

## 最新 CI 结果

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/structlog.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> 每次发版时通过 [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml) 自动更新。
