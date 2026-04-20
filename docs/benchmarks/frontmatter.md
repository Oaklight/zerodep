# Frontmatter 性能测试

zerodep frontmatter 与 [`python-frontmatter`](https://pypi.org/project/python-frontmatter/) 的性能对比。

!!! info "测试环境"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **工具:** pytest-benchmark 5.2.3（报告均值）
    - **对标库:** python-frontmatter 1.1.0
    - **最后更新:** 2026-04-21

## 实现对比

| 实现 | 文件/包 | 说明 |
|------|---------|------|
| **zerodep** | `frontmatter.py` | 仅依赖标准库的 frontmatter 解析器（使用兄弟 `yaml` 模块） |
| **python-frontmatter** | *（参考库）* | 流行的 frontmatter 库（依赖 PyYAML） |

## 测试数据规模

| 标签 | 说明 |
|------|------|
| 小型 | 简单的 YAML frontmatter，包含标题和短正文（约 3 行） |
| 中型 | 包含 7 个元数据字段和多段正文的 YAML frontmatter（约 20 行） |
| 大型 | 包含 50+ 元数据字段和 50 段正文的 YAML frontmatter |

## 解析性能对比（均值）

| 测试项 | zerodep | python-frontmatter | 倍数 |
|--------|---------|---------------------|------|
| 小型 | 14.7 μs | 14.6 μs | ~1.0x（对等） |
| 中型 | 96.0 μs | 95.7 μs | ~1.0x（对等） |
| 大型 | 444.5 μs | 445.8 μs | ~1.0x（对等） |

## 序列化性能对比（均值）

| 测试项 | zerodep | python-frontmatter | 倍数 |
|--------|---------|---------------------|------|
| 小型 | 22.5 μs | 22.3 μs | ~1.0x（对等） |
| 中型 | 152.1 μs | 134.6 μs | 慢 1.1x |
| 大型 | 683.8 μs | 679.1 μs | ~1.0x（对等） |

## 要点总结

- **性能对等** -- zerodep frontmatter 在所有数据规模下的解析和序列化速度均与 `python-frontmatter` 持平。这是预期结果，因为两者使用的底层 YAML 库（zerodep 的 `yaml` 模块 vs PyYAML）相同，而 frontmatter 分割逻辑是轻量级的字符串操作。
- **零 pip 依赖** -- 与依赖 `PyYAML` 的 `python-frontmatter` 不同，zerodep 仅使用兄弟 `yaml` 模块和标准库。
- **额外格式支持** -- zerodep frontmatter 还原生支持 TOML（`+++`）和 JSON（`{}`）frontmatter，而 `python-frontmatter` 默认仅支持 YAML。

## 自行运行

```bash
pip install pytest pytest-benchmark python-frontmatter
pytest frontmatter/test_frontmatter_benchmark.py --benchmark-only -v
```

---

## 最新 CI 结果

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/frontmatter.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> 每次发版时通过 [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml) 自动更新。
