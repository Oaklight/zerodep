# llms.txt 性能测试

zerodep llms.txt 解析器的基线性能测量。由于不存在竞争性的零依赖 Python 库，此基准测试为未来优化建立基线。

!!! info "测试环境"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **工具:** pytest-benchmark 5.2.3（报告均值）
    - **参考实现:** 无（无竞争库）
    - **更新日期:** 2026-04-27

## 实现

| 实现 | 文件/包 | 说明 |
|------|---------|------|
| **zerodep** | `llmstxt.py` | 基于 Regex-split 的解析器 + `urllib.parse` URL 处理 |

## 测试数据规模

| 标签 | 说明 |
|------|------|
| Small | H1、引用、1 个分节含 3 个条目（约 10 行） |
| Medium | H1、引用、详情、4 个分节各含 6-10 个条目、Optional 分节（约 50 行） |
| Large | H1、引用、详情、10 个分节 × 50 个条目 + Optional（约 600 行） |

## 解析性能（均值）

| 数据规模 | zerodep |
|----------|---------|
| Small | ~7 us |
| Medium | ~12 us |
| Large | ~1,050 us |

## 要点

- **微秒级解析** — 小型和中型文件解析在 15 us 以内完成。
- **线性扩展** — 性能随条目数线性增长。
- **Regex-split 方法** — 按 H2 标题分割实现 O(n) 解析，开销极小。
- **零 pip 依赖** — 仅使用标准库的 `re`、`dataclasses` 和 `urllib.parse`。

## 自行测试

```bash
pip install pytest pytest-benchmark
pytest llmstxt/test_llmstxt_benchmark.py --benchmark-only -v
```

---

## 最新 CI 结果

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/llmstxt.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> 每次发布时通过 [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml) 自动更新。
