# 重试性能测试

zerodep retry 与 [`tenacity`](https://pypi.org/project/tenacity/) 的性能对比。

!!! info "测试环境"
    - **CPU:** x86_64 Linux
    - **Python:** 3.10
    - **工具:** pytest-benchmark（报告均值）

## 实现对比

| 实现 | 文件/包 | 说明 |
|------|---------|------|
| **zerodep** | `retry.py` | 仅依赖标准库的装饰器式重试 |
| **tenacity** | *（参考库）* | 功能丰富的重试库 |

## 性能对比（均值）

| 测试项 | zerodep | tenacity | 倍数 |
|--------|---------|----------|------|
| 装饰器开销 | ~377 ns | ~8.4 μs | ~22x 更快 |
| 含 2 次失败的重试 | ~2.5 μs | ~9.5 μs | ~4x 更快 |
| 退避计算 | ~3.0 μs | ~30 μs | ~10x 更快 |

## 要点总结

- **装饰器开销**极低（纳秒级），适合高频调用场景。
- **含实际重试**的场景下仍保持 4 倍以上的性能优势。
- **退避计算**由于无需构建复杂的等待对象，性能优势达 10 倍。
- zerodep **无需任何 pip 依赖**——仅使用标准库 `time`、`functools`、`random`。

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
