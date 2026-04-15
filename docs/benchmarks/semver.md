# 版本解析器性能测试

zerodep semver 与 [`packaging`](https://pypi.org/project/packaging/) 的性能对比。

!!! info "测试环境"
    - **平台:** x86_64 Linux
    - **Python:** 3.10.20
    - **工具:** pytest-benchmark 5.2.3（报告均值）

## 实现对比

| 实现 | 文件/包 | 说明 |
|------|---------|------|
| **zerodep** | `semver.py` | 纯 Python PEP 440 解析器，使用 `re` + `functools.total_ordering` |
| **packaging** | *（参考库）* | Python 标准打包库 |

## 测试场景

| 场景 | 说明 |
|------|------|
| 解析简单版本 | 5 个基础版本字符串（`1.0`、`2.3.4` 等） |
| 解析预发布版本 | 6 个 pre/post/dev 版本（`1.0a1`、`2.0.dev3` 等） |
| 解析复杂版本 | 5 个含 epoch、local、组合后缀的版本 |
| 排序 | 对 10 个混合版本排序 |
| 比较 | 对 10 个已解析版本进行逐对 `<` 和 `==` 比较 |
| 属性访问 | 对 6 个版本访问 `is_prerelease`、`is_devrelease`、`str()` |

## 性能对比（均值）

| 场景 | zerodep | packaging | 比率 |
|------|---------|-----------|------|
| 解析简单版本 | 10.8 μs | 8.0 μs | 0.74x |
| 解析预发布版本 | 14.6 μs | 11.0 μs | 0.76x |
| 解析复杂版本 | 16.0 μs | 11.5 μs | 0.72x |
| 排序 | 1.2 μs | 2.5 μs | 快 2.1x |
| 比较 | 5.0 μs | 6.6 μs | 快 1.3x |
| 属性访问 | 4.7 μs | 5.8 μs | 快 1.2x |

## 要点总结

- **整体性能相当** -- zerodep 在所有场景下与 packaging 处于同一数量级。
- **比较和排序更快** -- 解析后的 Version 对象比较和排序比 packaging 快 1.2-2.1 倍，这在版本检查工作流中最为关键。
- **解析略慢** -- 初始解析因纯 Python 正则比 packaging 优化后的解析器慢约 1.3 倍，但绝对差异仅几微秒。
- **零 pip 依赖** -- zerodep 仅使用标准库 `re` 和 `functools`。
- **实际权衡** -- 典型使用场景（解析一次版本，多次比较）下，zerodep 性能等同或优于 packaging。

## 自行运行

```bash
pip install pytest pytest-benchmark packaging
pytest semver/test_semver_benchmark.py --benchmark-only -v
```

---

## 最新 CI 结果

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/semver.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> 每次发版时通过 [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml) 自动更新。
