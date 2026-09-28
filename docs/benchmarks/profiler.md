# 性能分析器基准测试

zerodep profiler 与 [`pyinstrument`](https://pypi.org/project/pyinstrument/) 的同类性能对比。

!!! info "测试环境"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **工具:** pytest-benchmark 5.2.3（报告均值）
    - **参考库:** pyinstrument
    - **最后更新:** 2026-09-28

## 实现

| 实现 | 文件/包 | 说明 |
|------|---------|------|
| **zerodep** | `profiler.py` | cProfile 封装，支持 HTML 输出 |
| **pyinstrument** | *（参考库）* | 统计式分析器，支持调用栈记录 |

## 测试项目

| 测试 | 说明 |
|------|------|
| Profiler 开销 | 分析 CPU 密集型工作负载的开销 |
| 输出生成 | 从分析数据生成文本和 HTML 报告 |
| TracingProfiler 开销 | 逐调用跟踪在 CPU 密集型工作负载上的开销 |
| 跟踪输出生成 | 从跟踪数据生成报告 |
| 多线程开销 | 分析多线程工作负载 |

## 自行运行

```bash
pip install pytest pytest-benchmark pyinstrument
pytest profiler/test_profiler_benchmark.py --benchmark-only -v
```

---

## 最新 CI 结果

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/profiler.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> 每次发版时通过 [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml) 自动更新。
