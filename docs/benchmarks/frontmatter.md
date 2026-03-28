# Frontmatter 性能测试

zerodep frontmatter 与 [`python-frontmatter`](https://pypi.org/project/python-frontmatter/) 的性能对比。

!!! info "测试环境"
    - **平台:** x86_64 Linux
    - **Python:** 3.10.20
    - **工具:** pytest-benchmark 5.2.3（报告均值）

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
| 小型 | 8.7 μs | 8.6 μs | ~1.0x（对等） |
| 中型 | 13.4 μs | 13.4 μs | ~1.0x（对等） |
| 大型 | 55.0 μs | 55.0 μs | ~1.0x（对等） |

## 序列化性能对比（均值）

| 测试项 | zerodep | python-frontmatter | 倍数 |
|--------|---------|---------------------|------|
| 小型 | 84.0 μs | 84.2 μs | ~1.0x（对等） |
| 中型 | 276.7 μs | 276.8 μs | ~1.0x（对等） |
| 大型 | 407.8 μs | 409.8 μs | ~1.0x（对等） |

## 要点总结

- **性能对等** -- zerodep frontmatter 在所有数据规模下的解析和序列化速度均与 `python-frontmatter` 持平。这是预期结果，因为两者使用的底层 YAML 库（zerodep 的 `yaml` 模块 vs PyYAML）相同，而 frontmatter 分割逻辑是轻量级的字符串操作。
- **零 pip 依赖** -- 与依赖 `PyYAML` 的 `python-frontmatter` 不同，zerodep 仅使用兄弟 `yaml` 模块和标准库。
- **额外格式支持** -- zerodep frontmatter 还原生支持 TOML（`+++`）和 JSON（`{}`）frontmatter，而 `python-frontmatter` 默认仅支持 YAML。

## 自行运行

```bash
pip install pytest pytest-benchmark python-frontmatter
pytest frontmatter/test_frontmatter_benchmark.py --benchmark-only -v
```
