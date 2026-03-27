# HTTP 客户端性能测试

zerodep HTTP 客户端与 [`httpx`](https://pypi.org/project/httpx/)（带连接池）的同条件性能对比。

!!! info "测试环境"
    - **CPU:** x86_64 Linux
    - **Python:** 3.10
    - **工具:** pytest-benchmark（报告均值）
    - **目标:** httpbin.org（网络受限测试）

## 实现对比

| 实现 | 文件/包 | 说明 |
|------|---------|------|
| **zerodep** | `httpclient.py` | 仅依赖标准库的 HTTP/1.1 客户端 |
| **httpx** | *（参考库）* | 带连接池的流行 HTTP 库 |

## 性能对比（均值）

| 测试项 | zerodep | httpx | 备注 |
|--------|---------|-------|------|
| 同步 GET | ~1,100 ms | ~398 ms | httpx 受益于连接池 |
| 同步 POST JSON | ~1,086 ms | ~1,060 ms | 基本持平（网络受限） |
| 同步 Client GET | ~1,099 ms | ~1,088 ms | 使用会话时基本持平 |
| 异步 GET | ~1,228 ms | ~1,178 ms | 基本持平 |
| 异步 POST JSON | ~1,133 ms | ~1,152 ms | 基本持平 |

## 要点总结

- **一次性请求**时，httpx 由于连接池明显更快。
- 使用**会话或异步**模式时，两者性能几乎一致，因为此时都受限于网络延迟。
- zerodep **无需任何 pip 依赖**——同步模式使用标准库 `http.client`，异步模式使用 `asyncio` 流。

## 自行运行

```bash
pip install pytest pytest-benchmark httpx
pytest httpclient/test_http_benchmark.py --benchmark-only -v
```
