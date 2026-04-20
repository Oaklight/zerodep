# Dotenv 性能测试

zerodep dotenv 与 [`python-dotenv`](https://pypi.org/project/python-dotenv/) 在三种 `.env` 文件大小下的性能对比。

!!! info "测试环境"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **工具:** pytest-benchmark 5.2.3（报告均值）
    - **对标库:** python-dotenv 1.2.2
    - **最后更新:** 2026-04-21

## 实现对比

| 实现 | 文件/包 | 说明 |
|------|---------|------|
| **zerodep** | `dotenv.py` | 仅依赖标准库的 `.env` 文件解析器 |
| **python-dotenv** | *（参考库）* | 广泛使用的 dotenv 解析库 |

## 测试数据规模

| 规模 | 条目数 | 说明 |
|------|--------|------|
| 小型 | 10 | 包含 10 个键值对的 `.env` 文件 |
| 中型 | 50 | 包含 50 个键值对的 `.env` 文件 |
| 大型 | 500 | 包含 500 个键值对的 `.env` 文件 |

## 性能对比（均值）

| 测试项 | zerodep | python-dotenv | 倍数 |
|--------|---------|---------------|------|
| 小型（10 条目） | 27.3 μs | 27.1 μs | ~1.0x |
| 中型（50 条目） | 191.3 μs | 189.8 μs | ~1.0x |
| 大型（500 条目） | 1,350.0 μs | 1,350.0 μs | ~1.0x |

## 要点总结

- **全规模性能持平**——小型、中型和大型文件中，两者差异均在测量噪声范围内。
- **线性扩展**——两者均随条目数线性增长，符合逐行解析的预期。
- zerodep 的核心优势在于 **零依赖**——无需 `pip install` 任何第三方包，仅使用标准库。

## 自行运行

```bash
pip install pytest pytest-benchmark python-dotenv
pytest dotenv/test_dotenv_benchmark.py --benchmark-only -v
```

---

## 最新 CI 结果

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/dotenv.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> 每次发版时通过 [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml) 自动更新。
