# 版本解析器性能测试

zerodep semver 与 [`packaging`](https://pypi.org/project/packaging/) 的性能对比。

!!! info "测试环境"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **工具:** pytest-benchmark 5.2.3（报告均值）
    - **对标库:** packaging 26.1
    - **最后更新:** 2026-04-15

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
| 解析简单版本 | 18.5 μs | 4.1 μs | 慢 4.5x |
| 解析预发布版本 | 24.4 μs | 17.5 μs | 慢 1.4x |
| 解析复杂版本 | 29.1 μs | 17.7 μs | 慢 1.6x |
| 排序 | 1.8 μs | 1.6 μs | 慢 1.2x |
| 比较 | 4.1 μs | 3.3 μs | 慢 1.2x |
| 属性访问 | 6.2 μs | 7.3 μs | 快 1.2x |

## 要点总结

- **zerodep 整体慢于 packaging** -- 解析慢 1.4-4.5 倍，比较和排序慢约 1.2 倍。绝对差异很小（几微秒级别）。
- **属性访问略快** -- `is_prerelease`、`is_devrelease`、`str()` 快 1.2 倍。
- **简单版本解析差距最大**（4.5 倍），因为 packaging 的解析器针对常见版本字符串进行了高度优化，而 zerodep 使用纯 Python 正则。
- **零 pip 依赖** -- zerodep 仅使用标准库 `re` 和 `functools`。
- **实际权衡** -- 对于版本解析不在热路径上的典型使用场景，微秒级差异可以忽略。zerodep 的价值在于消除对 packaging 的依赖。

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
