# HTTP 客户端性能测试

zerodep HTTP 客户端与 [`httpx`](https://pypi.org/project/httpx/)（带连接池）的同条件性能对比。

!!! info "测试环境"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **工具:** pytest-benchmark 5.2.3（报告均值）
    - **对标库:** httpx 0.28.1
    - **最后更新:** 2026-04-21

## 实现对比

| 实现 | 文件/包 | 说明 |
|------|---------|------|
| **zerodep** | `httpclient.py` | 仅依赖标准库的 HTTP/1.1 客户端 |
| **httpx** | *（参考库）* | 带连接池的流行 HTTP 库 |

## 性能对比（均值）

### 基本请求

| 测试项 | zerodep | httpx | 倍数 |
|--------|---------|-------|------|
| 同步 GET | 613.9 μs | 20,830.0 μs | **快 33.9x** |
| 同步 POST JSON | 709.6 μs | 21,030.0 μs | **快 29.6x** |
| 同步 Client GET | 637.6 μs | 1,020.0 μs | **快 1.6x** |
| 异步 GET | 1,110.0 μs | 27,530.0 μs | **快 24.8x** |
| 异步 POST JSON | 1,220.0 μs | 28,130.0 μs | **快 23.1x** |
| 异步 Client GET | 1,160.0 μs | 26,590.0 μs | **快 22.9x** |

### 流式传输

| 测试项 | zerodep | httpx | 倍数 |
|--------|---------|-------|------|
| 同步流式传输 | 627.5 μs | 20,990.0 μs | **快 33.4x** |
| 异步流式传输 | 1,150.0 μs | 26,780.0 μs | **快 23.3x** |

### 文件上传（multipart/form-data）

| 测试项 | zerodep | httpx | 倍数 |
|--------|---------|-------|------|
| 同步文件上传 | 991.3 μs | 21,610.0 μs | **快 21.8x** |
| 异步文件上传 | 1,510.0 μs | 28,020.0 μs | **快 18.5x** |

### 内容解压缩

| 测试项 | zerodep | httpx | 倍数 |
|--------|---------|-------|------|
| 同步 Gzip GET | 646.2 μs | 20,710.0 μs | **快 32.1x** |

## 要点总结

- **一次性请求快 19--34 倍**——不使用连接池时，zerodep 大幅快于 httpx，因为避免了 httpx 的重量级客户端初始化和中间件栈开销。
- **连接池场景快约 1.6 倍**——即使两者复用连接，zerodep 更轻量的抽象层仍有可测量的优势。
- **流式传输快 23--33 倍**——zerodep 精简的流式抽象直接转化为吞吐量提升。
- **文件上传快 19--22 倍**——zerodep 简洁的 multipart 编码器优于 httpx 的功能更丰富的实现。
- **测试使用本地服务器**——所有请求访问 `localhost`，数据反映的是纯库开销，不含网络延迟。
- zerodep **无需任何 pip 依赖**——同步模式使用标准库 `http.client`，异步模式使用 `asyncio` 流。

## 自行运行

```bash
pip install pytest pytest-benchmark httpx
pytest httpclient/test_http_benchmark.py --benchmark-only -v
```

---

## 最新 CI 结果

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/httpclient.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> 每次发版时通过 [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml) 自动更新。
