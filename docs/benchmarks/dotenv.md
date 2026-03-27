# Dotenv 性能测试

zerodep dotenv 与 [`python-dotenv`](https://pypi.org/project/python-dotenv/) 在三种 `.env` 文件大小下的性能对比。

!!! info "测试环境"
    - **平台:** x86_64 Linux
    - **Python:** 3.10.20
    - **工具:** pytest-benchmark 5.2.3（报告均值）

## 实现对比

| 实现 | 文件/包 | 说明 |
|------|---------|------|
| **zerodep** | `dotenv.py` | 仅依赖标准库的 `.env` 文件解析器 |
| **python-dotenv** | *（参考库）* | 广泛使用的 dotenv 解析库 |

## 性能对比（均值）

| 测试项 | zerodep | python-dotenv | 倍数 |
|--------|---------|---------------|------|
| 小型（10 条目） | 16.5 μs | 16.8 μs | ~1.0x |
| 中型（50 条目） | 118.8 μs | 120.8 μs | ~1.0x |
| 大型（500 条目） | 841.7 μs | 845.3 μs | ~1.0x |

## 要点总结

- **性能持平**——两者在各种规模的 `.env` 文件下表现基本一致。
- zerodep 的核心优势在于 **零依赖**——无需 `pip install` 任何第三方包，仅使用标准库。
- 适合对依赖数量有严格限制的项目，或不希望为简单的 dotenv 解析引入额外依赖的场景。

## 自行运行

```bash
pip install pytest pytest-benchmark python-dotenv
pytest dotenv/test_dotenv_benchmark.py --benchmark-only -v
```
