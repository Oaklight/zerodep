# HTTP 客户端性能测试

zerodep HTTP 客户端与 [`httpx`](https://pypi.org/project/httpx/)（带连接池）的同条件性能对比。

!!! info "测试环境"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **工具:** pytest-benchmark 5.2.3（报告均值）
    - **对标库:** httpx 0.28.1
    - **最后更新:** 2026-04-15

## 实现对比

| 实现 | 文件/包 | 说明 |
|------|---------|------|
| **zerodep** | `httpclient.py` | 仅依赖标准库的 HTTP/1.1 客户端 |
| **httpx** | *（参考库）* | 带连接池的流行 HTTP 库 |

## 性能对比（均值）

### 基本请求

| 测试项 | zerodep | httpx | 倍数 |
|--------|---------|-------|------|
| 同步 GET | 729.7 μs | 11,970.0 μs | **快 16.4x** |
| 同步 POST JSON | 871.4 μs | 12,279.4 μs | **快 14.1x** |
| 同步 Client GET | 808.4 μs | 1,541.4 μs | **快 1.9x** |
| 异步 GET | 1,328.2 μs | 19,339.9 μs | **快 14.6x** |
| 异步 POST JSON | 1,583.1 μs | 19,356.7 μs | **快 12.2x** |
| 异步 Client GET | 1,434.9 μs | 20,134.9 μs | **快 14.0x** |

### 流式传输

| 测试项 | zerodep | httpx | 倍数 |
|--------|---------|-------|------|
| 同步流式传输 | 725.4 μs | 12,059.9 μs | **快 16.6x** |
| 异步流式传输 | 1,432.7 μs | 20,228.3 μs | **快 14.1x** |

### 文件上传（multipart/form-data）

| 测试项 | zerodep | httpx | 倍数 |
|--------|---------|-------|------|
| 同步文件上传 | 1,472.0 μs | 14,130.2 μs | **快 9.6x** |
| 异步文件上传 | 1,904.0 μs | 22,040.0 μs | **快 11.6x** |

### 内容解压缩

| 测试项 | zerodep | httpx | 倍数 |
|--------|---------|-------|------|
| 同步 Gzip GET | 846.6 μs | 12,454.8 μs | **快 14.7x** |

## 要点总结

- **一次性请求快 10--17 倍**——不使用连接池时，zerodep 大幅快于 httpx，因为避免了 httpx 的重量级客户端初始化和中间件栈开销。
- **连接池场景快约 2 倍**——即使两者复用连接，zerodep 更轻量的抽象层仍有可测量的优势。
- **流式传输快 14--17 倍**——zerodep 精简的流式抽象直接转化为吞吐量提升。
- **文件上传快 10--12 倍**——zerodep 简洁的 multipart 编码器优于 httpx 的功能更丰富的实现。
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
