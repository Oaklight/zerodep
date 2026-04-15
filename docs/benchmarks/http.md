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

### 基本请求

| 测试项 | zerodep | httpx | 备注 |
|--------|---------|-------|------|
| 同步 GET | ~1,288 ms | ~1,206 ms | 基本持平（网络受限） |
| 同步 POST JSON | ~1,436 ms | ~1,209 ms | 基本持平（网络受限） |
| 同步 Client GET | ~287 ms | ~264 ms | 两者均使用连接池 |
| 异步 GET | ~1,035 ms | ~1,334 ms | 基本持平 |
| 异步 POST JSON | ~1,312 ms | ~1,253 ms | 基本持平 |
| 异步 Client GET | ~1,593 ms | ~1,591 ms | 两者均使用连接池 |

### 流式传输

| 测试项 | zerodep | httpx | 备注 |
|--------|---------|-------|------|
| 同步流式传输 | ~1,378 ms | ~1,287 ms | 基本持平 |
| 异步流式传输 | ~1,129 ms | ~1,751 ms | zerodep 更快 |

### 文件上传（multipart/form-data）

| 测试项 | zerodep | httpx | 备注 |
|--------|---------|-------|------|
| 同步文件上传 | ~2,790 ms | ~2,063 ms | 基本持平（网络受限） |
| 异步文件上传 | ~1,470 ms | ~1,643 ms | 基本持平 |

### 内容解压缩

| 测试项 | zerodep | httpx | 备注 |
|--------|---------|-------|------|
| 同步 Gzip GET | ~1,229 ms | ~1,720 ms | zerodep 更快 |

## 要点总结

- **一次性请求**时，两者基本持平，性能受限于网络延迟。
- 使用**会话/连接池**时，两个库性能基本持平。
- **流式传输**性能相当甚至更优，得益于 zerodep 精简的流式抽象。
- **文件上传**性能基本相当，httpx 略有优势。
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
