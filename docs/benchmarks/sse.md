# SSE 客户端性能测试

zerodep SSE 与 [`httpx-sse`](https://pypi.org/project/httpx-sse/) 的解析性能对比。

!!! info "测试环境"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **工具:** pytest-benchmark 5.2.3（报告均值）
    - **对标库:** httpx-sse 0.4.3
    - **最后更新:** 2026-04-21

## 实现对比

| 实现 | 文件/包 | 说明 |
|------|---------|------|
| **zerodep** | `sse.py` | 单文件 SSE 解析器 + 客户端，仅标准库 |
| **httpx-sse** | *（参考库）* | httpx 的 SSE 扩展 |

## 测试内容

两个库都实现了相同的 W3C SSE 逐行解析算法。测试将相同的预构建行数组喂给各自的解析器，测量纯解析吞吐量——不涉及网络 I/O。

## 测试数据

| 规模 | 事件数 | 每事件 data 行数 | 每行字符数 | 说明 |
|------|--------|------------------|------------|------|
| Small | 10 | 1 | 20 | 简单通知流 |
| Medium | 100 | 3 | 50 | 典型 LLM token 流 |
| Large | 1,000 | 1 | 200 | 批量数据流 |

## 解析性能（均值）

| 数据规模 | zerodep | httpx-sse | 比率 |
|----------|---------|-----------|------|
| Small | 30.7 μs | 22.3 μs | 慢 ~1.4x |
| Medium | 399.6 μs | 317.2 μs | 慢 ~1.3x |
| Large | 3,180.0 μs | 2,320.0 μs | 慢 ~1.4x |

## 要点总结

- **zerodep 慢约 30-40%** —— 两个库实现了相同的 W3C SSE 解析算法。差异来自 zerodep 对每个事件的额外处理（字段规范化、事件类型分发），而 httpx-sse 解析器更为精简。
- **吞吐量对两者都很优秀** —— 解析 1,000 个事件（200 字符载荷）仅需约 3.2 ms，说明在实际 SSE 场景中解析永远不会成为瓶颈（网络延迟才是主导因素）。
- **zerodep 功能更丰富** —— 不同于 httpx-sse（仅是 httpx 扩展），zerodep SSE 包含独立解析器（无需 HTTP 依赖）、自动重连、同步+异步客户端和 Last-Event-ID 跟踪。
- **零 pip 依赖** —— zerodep 仅使用标准库 `dataclasses`、`asyncio`、`time`、`os`（高级客户端另需同项目的 `httpclient` 模块）。

## 自行运行

```bash
pip install pytest pytest-benchmark httpx-sse httpx
pytest sse/test_sse_benchmark.py --benchmark-only -v
```

---

## 最新 CI 结果

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/sse.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> 每次发版时通过 [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml) 自动更新。
