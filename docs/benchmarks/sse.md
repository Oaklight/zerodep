# SSE 客户端性能测试

zerodep SSE 与 [`httpx-sse`](https://pypi.org/project/httpx-sse/) 的解析性能对比。

!!! info "测试环境"
    - **平台:** x86_64 Linux
    - **Python:** 3.10.20
    - **工具:** pytest-benchmark 5.2.3（报告均值）

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
| Small | 14.9 μs | 13.2 μs | 慢 ~1.13x |
| Medium | 200.9 μs | 186.9 μs | 慢 ~1.07x |
| Large | 1,526.4 μs | 1,379.9 μs | 慢 ~1.11x |

## 要点总结

- **解析性能几乎一致** —— 两个库实现了相同的 W3C SSE 解析算法，~10% 的差异来自实现细节。
- **吞吐量对两者都很优秀** —— 解析 1,000 个事件（200 字符载荷）仅需约 1.5 ms，说明在实际 SSE 场景中解析永远不会成为瓶颈（网络延迟才是主导因素）。
- **zerodep 功能更丰富** —— 不同于 httpx-sse（仅是 httpx 扩展），zerodep SSE 包含独立解析器（无需 HTTP 依赖）、自动重连、同步+异步客户端和 Last-Event-ID 跟踪。
- **零 pip 依赖** —— zerodep 仅使用标准库 `dataclasses`、`asyncio`、`time`、`os`（高级客户端另需同项目的 `httpclient` 模块）。

## 自行运行

```bash
pip install pytest pytest-benchmark httpx-sse httpx
pytest sse/test_sse_benchmark.py --benchmark-only -v
```
