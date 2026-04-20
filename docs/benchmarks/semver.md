# 版本解析器性能测试

zerodep semver 与 [`packaging`](https://pypi.org/project/packaging/) 的性能对比。

!!! info "测试环境"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **工具:** pytest-benchmark 5.2.3（报告均值）
    - **对标库:** packaging 26.1
    - **最后更新:** 2026-04-21

## 实现对比

| 实现 | 文件/包 | 说明 |
|------|---------|------|
| **zerodep** | `semver.py` | 纯 Python PEP 440 解析器，使用 `re`，内联比较键 + 整数哨兵 |
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
| 解析简单版本 | 14.0 μs | 6.0 μs | 慢 2.3x |
| 解析预发布版本 | 19.2 μs | 21.1 μs | **快 1.1x** |
| 解析复杂版本 | 22.8 μs | 22.9 μs | ~1.0x |
| 排序 | 1.7 μs | 1.9 μs | **快 1.1x** |
| 比较 | 3.4 μs | 4.0 μs | **快 1.2x** |
| 属性访问 | 1.2 μs | 9.3 μs | **快 7.8x** |

## 要点总结

- **简单版本解析慢 2.3 倍** -- 简单版本解析仍有差距，因为 packaging 使用高度优化的 C 正则内部实现。预发布和复杂版本解析现已持平或更快。
- **排序和比较更快** -- 整数哨兵比较键和内联 `_cmpkey` 使排序快 1.1 倍，比较快 1.2 倍。
- **属性访问快 7.8 倍** -- 缓存 `__str__`、直接访问 `_pre`/`_post`/`_dev` 属性替代属性分发，使布尔检查和字符串转换大幅加速。
- **零 pip 依赖** -- zerodep 仅使用标准库 `re` 和 `functools`。
- **实际权衡** -- 对于典型使用场景（版本比较、排序、属性检查、预发布版本解析），zerodep 现已**快于** packaging。仅批量解析简单版本时较慢。

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
