# 调度器性能测试

zerodep scheduler 与 [`APScheduler`](https://pypi.org/project/APScheduler/)、[`croniter`](https://pypi.org/project/croniter/) 和 [`schedule`](https://pypi.org/project/schedule/) 的性能对比。

!!! info "测试环境"
    - **CPU:** x86_64 Linux
    - **Python:** 3.10
    - **工具:** pytest-benchmark（报告均值）

## 实现对比

| 实现 | 文件/包 | 说明 |
|------|---------|------|
| **zerodep** | `scheduler.py` | 仅依赖标准库的进程内调度器 |
| **APScheduler** | *（参考库）* | 全功能调度库 |
| **croniter** | *（参考库）* | Cron 表达式解析与迭代 |
| **schedule** | *（参考库）* | 轻量级进程内调度 |

## 性能对比（均值）

| 测试项 | zerodep | croniter | APScheduler | schedule | 倍数 |
|--------|---------|----------|-------------|----------|------|
| Cron 解析（5 条表达式） | ~20 μs | ~236 μs | ~74 μs | 不适用 | 3.6x--11.5x 更快 |
| 下次触发时间（5 条表达式） | ~28 μs | ~436 μs | ~127 μs | 不适用 | 4.5x--15.3x 更快 |
| 批量下次触发（100 次迭代） | ~310 μs | ~2,523 μs | ~575 μs | 不适用 | 1.9x--8.1x 更快 |
| 任务添加开销（100 个任务） | ~377 μs | 不适用 | 不适用 | ~349 μs | ~1.1x |

## 要点总结

- **Cron 解析**比 APScheduler 快 3.6 倍，比 croniter 快 11.5 倍，得益于精简的集合式解析器。
- **下次触发时间计算**快 4.5x--15x，zerodep 使用直接的 datetime 算术，无需时区转换开销。
- **批量计算**（100 次连续触发时间）在规模化场景下仍保持速度优势。
- **任务添加开销**与 `schedule` 相当，两者都采用轻量设计。
- zerodep **无需任何 pip 依赖**——仅使用标准库 `threading`、`asyncio`、`datetime`、`inspect` 和 `logging`。

## 自行运行

```bash
pip install pytest pytest-benchmark APScheduler croniter schedule
pytest scheduler/test_scheduler_benchmark.py --benchmark-only -v
```

---

## 最新 CI 结果

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/scheduler.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> 每次发版时通过 [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml) 自动更新。
