# CDP 性能测试

使用 mock CDP 服务器的 Chrome DevTools Protocol 客户端性能测试。

!!! info "测试环境"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **工具:** pytest-benchmark 5.2.3（报告均值）
    - **最后更新:** 2026-05-02

## 实现方式

| 实现 | 类型 | 描述 |
|------|------|------|
| **zerodep cdp** | 同步 | 基于 zerodep websocket 构建的 CDP 客户端，仅标准库 |

## 测试内容

CDP 客户端连接到标准库 mock CDP 服务器，该服务器模拟基本的 Chrome DevTools Protocol 交互（Target 管理、Page 导航、Runtime 执行）。性能测试测量端到端 CDP 命令延迟，包括 WebSocket 帧编码、JSON 序列化和事件缓冲。

## 测试场景

| 场景 | 描述 | 操作 |
|------|------|------|
| 完整渲染管线 | create_target → navigate → evaluate(innerText) → close_target | 6+ 条 CDP 命令 |
| HTML 渲染 | create_target → navigate → evaluate(outerHTML) → close_target | 6+ 条 CDP 命令 |
| 多标签页（5 个） | 创建 5 个 target，各自 navigate + evaluate，逐个关闭 | 30+ 条 CDP 命令 |
| JS 执行吞吐 | 在同一 target 上连续 10 次 evaluate() | 10 条 CDP 命令 |
| 命令吞吐 | 快速发送 20 条混合方法的 send_command() | 20 条 CDP 命令 |

## 关键发现

- **完整渲染管线** -- 完整的创建 → 导航 → 执行 → 关闭周期在 mock 服务器上毫秒级完成，展示了低 CDP 客户端开销。
- **多标签页** -- 管理 5 个并发 target（标签页）线性扩展，单标签页开销极小。
- **JS 执行** -- 连续 evaluate() 调用显示一致的延迟，验证了高效的命令/响应 ID 匹配和事件缓冲区管理。
- **命令吞吐** -- 原始命令分发速率衡量 JSON 序列化、WebSocket 帧封装和响应关联的开销。

## 自行运行

```bash
pip install pytest pytest-benchmark
pytest cdp/test_cdp_benchmark.py --benchmark-only -v
```

---

## 最新 CI 结果

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/cdp.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> 每次发布时通过 [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml) 自动更新。
