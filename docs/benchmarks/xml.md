# XML 性能测试

zerodep XML 与 [`xmltodict`](https://pypi.org/project/xmltodict/) 的同类对比性能测试。

!!! info "测试环境"
    - **平台:** x86_64 Linux
    - **Python:** 3.10.20
    - **工具:** pytest-benchmark 5.2.3（报告均值）

## 实现对比

| 实现 | 文件/包 | 说明 |
|------|---------|------|
| **zerodep** | `xml.py` | 仅依赖标准库的 XML ↔ dict 转换器，含 LLM 标签提取 |
| **xmltodict** | *（参考库）* | 流行的基于 expat 的 XML ↔ dict 转换器 |

## 测试数据规模

| 标签 | 说明 |
|------|------|
| 小型 | 包含 3 个子元素的简单元素 |
| 中型 | 包含 25 个 URL 条目的 Sitemap XML |
| 大型 | 包含 200 个商品的产品目录，含属性和嵌套标签 |

## 解析性能（均值）

| 数据规模 | zerodep | xmltodict | 倍数 |
|----------|---------|-----------|------|
| 小型 | 8.0 μs | 9.9 μs | 快 1.2x |
| 中型 | 176.4 μs | 240.1 μs | 快 1.4x |
| 大型 | 2,587.8 μs | 3,172.2 μs | 快 1.2x |

## 反序列化性能（均值）

| 数据规模 | zerodep | xmltodict | 倍数 |
|----------|---------|-----------|------|
| 小型 | 9.2 μs | 13.0 μs | 快 1.4x |
| 中型 | 221.4 μs | 289.1 μs | 快 1.3x |
| 大型 | 2,955.7 μs | 4,094.9 μs | 快 1.4x |

## extract_tags 性能（均值）

| 操作 | 耗时 |
|------|------|
| 提取全部标签（100 个标签） | 315.3 μs |
| 按名称过滤（50 个匹配） | 198.6 μs |
| 仅提取第一个 | 4.5 μs |

## 要点总结

- **解析快约 1.2-1.4 倍** -- zerodep 在所有数据规模下始终优于 xmltodict。
- **反序列化快约 1.3-1.4 倍** -- 序列化性能差距更为稳定。
- **extract_tags 无竞品** -- 这是专为 LLM 输出解析设计的独特功能。`first_only=True` 优化极快（约 4.5 μs）。
- **两者都使用 expat** -- 不同于 YAML/JSON 中 zerodep 重新实现了解析器，zerodep 和 xmltodict 底层使用相同的 C 语言 expat 解析器，因此加速来自更高效的 dict 构建。

## 自行运行

```bash
pip install pytest pytest-benchmark xmltodict
pytest xml/test_xml_benchmark.py --benchmark-only -v
```

---

## 最新 CI 结果

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/xml.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> 每次发版时通过 [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml) 自动更新。
