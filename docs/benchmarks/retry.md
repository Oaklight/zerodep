# 重试性能测试

zerodep retry 与 [`tenacity`](https://pypi.org/project/tenacity/) 的性能对比。

!!! info "测试环境"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **工具:** pytest-benchmark 5.2.3（报告均值）
    - **对标库:** tenacity 9.1.4
    - **最后更新:** 2026-04-21

## 实现对比

| 实现 | 文件/包 | 说明 |
|------|---------|------|
| **zerodep** | `retry.py` | 仅依赖标准库的装饰器式重试 |
| **tenacity** | *（参考库）* | 功能丰富的重试库 |

## 性能对比（均值）

| 测试项 | zerodep | tenacity | 倍数 |
|--------|---------|----------|------|
| 装饰器开销 | 0.5 μs | 19.8 μs | 37.3x 更快 |
| 含 2 次失败的重试 | 246.9 μs | 322.1 μs | 1.3x 更快 |
| 退避计算 | 5.6 μs | 14.6 μs | 2.6x 更快 |

## 要点总结

- **装饰器开销**比 tenacity 低约 37 倍，适合高频调用场景。
- **含实际重试**的场景下仍快约 1.3 倍，zerodep 避免了 tenacity 的统计跟踪和等待链抽象开销。
- **退避计算**快约 2.6 倍，直接算术运算对比 tenacity 的可组合等待对象管道。
- zerodep **无需任何 pip 依赖**——仅使用标准库 `time`、`functools`、`random`、`asyncio` 和 `inspect`。

## 自行运行

```bash
pip install pytest pytest-benchmark tenacity
pytest retry/test_retry_benchmark.py --benchmark-only -v
```

---

## 最新 CI 结果

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/retry.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> 每次发版时通过 [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml) 自动更新。
