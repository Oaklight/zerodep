# 结构化日志性能测试

zerodep structlog 与 [`structlog`](https://pypi.org/project/structlog/) 在四个场景下的性能对比。

!!! info "测试环境"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **工具:** pytest-benchmark 5.2.3（报告均值）
    - **对标库:** structlog 25.5.0
    - **最后更新:** 2026-04-21

## 实现对比

| 实现 | 文件/包 | 说明 |
|------|---------|------|
| **zerodep** | `structlog.py` | 仅依赖标准库的结构化日志 |
| **structlog** | *（参考库）* | 功能丰富的结构化日志库 |

## 性能对比（均值）

| 测试项 | zerodep | structlog | 倍数 |
|--------|---------|-----------|------|
| 简单日志 | 10.2 μs | 14.0 μs | 快 1.4x |
| 绑定上下文日志 | 12.7 μs | 19.9 μs | 快 1.6x |
| JSON 渲染 | 10.0 μs | 12.4 μs | 快 1.2x |
| 绑定 + 日志 | 11.5 μs | 23.0 μs | 快 2.0x |

## 要点总结

- **全场景快 1.2-2.0 倍** —— zerodep 在所有场景下均优于 structlog，上下文绑定操作优势更大。
- **简单日志和 JSON 渲染**场景下两者性能接近（约 10-14 μs），zerodep 快约 1.2-1.4 倍。
- **上下文操作优势最大** —— 绑定上下文日志（1.6x）和绑定+日志（2.0x）加速比最高，structlog 的处理器链和包装开销更明显。
- zerodep **无需任何 pip 依赖** —— 仅使用标准库 `json`、`logging`、`io` 和 `time`。

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
