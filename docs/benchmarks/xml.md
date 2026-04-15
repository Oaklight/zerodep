# XML 性能测试

zerodep XML 与 [`xmltodict`](https://pypi.org/project/xmltodict/) 的同类对比性能测试。

!!! info "测试环境"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **工具:** pytest-benchmark 5.2.3（报告均值）
    - **对标库:** xmltodict 1.0.4
    - **最后更新:** 2026-04-15

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
| 小型 | 19.5 μs | 15.7 μs | 慢 1.2x |
| 中型 | 337.7 μs | 350.4 μs | 快 1.0x |
| 大型 | 4,676.4 μs | 4,708.9 μs | 快 1.0x |

## 反序列化性能（均值）

| 数据规模 | zerodep | xmltodict | 倍数 |
|----------|---------|-----------|------|
| 小型 | 12.7 μs | 16.6 μs | 快 1.3x |
| 中型 | 238.2 μs | 395.0 μs | 快 1.7x |
| 大型 | 3,613.4 μs | 5,604.0 μs | 快 1.6x |

## extract_tags 性能（均值）

| 操作 | 耗时 |
|------|------|
| 提取全部标签（100 个标签） | 569.2 μs |
| 按名称过滤（50 个匹配） | 346.5 μs |
| 仅提取第一个 | 7.7 μs |

## 要点总结

- **解析性能基本持平** -- 中型和大型文档两者性能几乎一致。小型输入下 zerodep 略慢约 1.2 倍，因 dict 构建逻辑更丰富。
- **反序列化快 1.3-1.7 倍** -- 序列化是 zerodep 优势最明显的环节，数据越大差距越大。
- **extract_tags 无竞品** -- 这是专为 LLM 输出解析设计的独特功能。`first_only=True` 优化极快（约 7.7 μs）。
- **两者都使用 expat** -- 不同于 YAML/JSON 中 zerodep 重新实现了解析器，zerodep 和 xmltodict 底层使用相同的 C 语言 expat 解析器，反序列化加速来自更高效的字符串构建。

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
