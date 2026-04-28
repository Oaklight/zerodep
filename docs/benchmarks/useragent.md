# User-Agent 生成器性能测试

zerodep useragent 与 [`ua-generator`](https://pypi.org/project/ua-generator/) 的性能对比。

!!! info "测试环境"
    - **CPU:** x86_64 Linux
    - **Python:** 3.10
    - **工具:** pytest-benchmark 5.2.3（报告均值）
    - **对标库:** ua-generator 2.0+
    - **最后更新:** 2026-04-29

## 实现对比

| 实现 | 文件/包 | 说明 |
|------|---------|------|
| **zerodep** | `useragent.py` | 单文件 Chrome/Edge UA 生成器，仅标准库 |
| **ua-generator** | *（参考库）* | 多浏览器 UA 生成器包 |

## 测试内容

两个库都生成 User-Agent 字符串及对应的 Client Hints 头部。测试衡量纯生成吞吐量——不涉及网络 I/O。

## 测试场景

| 场景 | 说明 |
|------|------|
| Default | 随机浏览器 + 平台（无过滤） |
| Chrome Desktop | `browser="chrome", device="desktop"` |
| Edge Mobile | `browser="edge", device="mobile"` |
| Headers | 生成 UA + 通过 `.headers.get()` 构建完整 Client Hints 头部 |

## 生成性能（均值）

| 场景 | zerodep | ua-generator | 加速比 |
|------|---------|--------------|--------|
| Default | 3.1 μs | 8.6 μs | **快 2.7 倍** |
| Chrome Desktop | 3.9 μs | 7.9 μs | **快 2.0 倍** |
| Edge Mobile | 3.4 μs | 9.2 μs | **快 2.7 倍** |
| Headers | 5.2 μs | 11.6 μs | **快 2.2 倍** |

## 要点总结

- **zerodep 快 2-3 倍** —— 更简单的架构（无动态插件加载、无多浏览器分发）直接转化为吞吐量优势。
- **两者都极快** —— 每次生成 3-12 μs，UA 生成在任何实际应用中都不会成为瓶颈（单次 HTTP 请求耗时以毫秒计）。
- **Headers 生成增加约 2 μs** —— 构建完整 `Sec-CH-UA-*` 头部集对两个库来说都很轻量。
- **zerodep 仅覆盖 Chrome + Edge** —— 这一有意的范围缩减（对比 ua-generator 的 Chrome/Edge/Firefox/Safari）是速度优势的主要来源。
- **零 pip 依赖** —— zerodep 仅使用标准库的 `random`。

## 自行运行

```bash
pip install pytest pytest-benchmark ua-generator
pytest useragent/test_useragent_benchmark.py --benchmark-only -v
```

---

## 最新 CI 结果

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/useragent.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> 每次发版时通过 [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml) 自动更新。
