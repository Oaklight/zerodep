# WebSocket 性能测试

zerodep websocket 与 [websockets](https://pypi.org/project/websockets/) 库的 WebSocket 往返性能对比。

!!! info "测试环境"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **工具:** pytest-benchmark 5.2.3（报告均值）
    - **参考库:** websockets 15.0.1
    - **最后更新:** 2026-05-02

## 实现方式

| 实现 | 类型 | 描述 |
|------|------|------|
| **zerodep** | 同步 + 异步 | 单文件 RFC 6455 客户端，仅标准库 |
| **websockets** | 同步 + 异步 | 全功能 WebSocket 库 |

## 测试内容

两个客户端均连接到标准库 echo 服务器（共享 fixture）。性能测试测量完整的发送-接收往返延迟，包括帧编码、掩码和解码。

## 测试场景

| 场景 | 描述 | 负载 |
|------|------|------|
| JSON-RPC 往返 | 发送 CDP 大小的 JSON 消息，接收 echo | ~200B |
| 大负载 | 发送 SPA outerHTML 大小的内容，接收 echo | ~50KB |
| 突发消息 | 连续发送 100 条 JSON-RPC 消息，然后全部接收 | 100 x ~150B |
| 连接建立 | 连接 + 关闭握手周期 | N/A |

## 关键发现

- **JSON-RPC 消息** -- 两种实现对典型 CDP 命令大小的消息均可实现亚毫秒级往返。
- **大负载** -- zerodep 处理 50KB 负载的延迟与 websockets 相当，瓶颈在 TCP I/O 而非帧编码。
- **突发消息** -- 100 条消息的顺序发送/接收测试帧编码吞吐和缓冲区管理。
- **连接开销** -- 测量 WebSocket 升级握手延迟，包括 TCP 连接、HTTP 升级和密钥验证。
- **零依赖** -- zerodep 在无 pip 依赖的情况下实现了相当的性能表现。

## 自行运行

```bash
pip install pytest pytest-benchmark websockets
pytest websocket/test_websocket_benchmark.py --benchmark-only -v
```

---

## 最新 CI 结果

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/websocket.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> 每次发布时通过 [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml) 自动更新。
