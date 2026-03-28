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
| 同步 GET | ~1,091 ms | ~1,165 ms | 基本持平（网络受限） |
| 同步 POST JSON | ~1,039 ms | ~1,154 ms | 基本持平（网络受限） |
| 同步 Client GET | ~1,613 ms | ~462 ms | 两者均使用连接池 |
| 异步 GET | ~1,147 ms | ~1,207 ms | 基本持平 |
| 异步 POST JSON | ~1,437 ms | ~1,352 ms | 基本持平 |

### 流式传输

| 测试项 | zerodep | httpx | 备注 |
|--------|---------|-------|------|
| 同步流式传输 | ~1,666 ms | ~2,295 ms | zerodep 更快（流式开销更低） |
| 异步流式传输 | ~1,476 ms | ~1,448 ms | 基本持平 |

### 文件上传（multipart/form-data）

| 测试项 | zerodep | httpx | 备注 |
|--------|---------|-------|------|
| 同步文件上传 | ~1,731 ms | ~1,398 ms | 基本持平（网络受限） |
| 异步文件上传 | ~2,003 ms | ~1,571 ms | httpx 略快 |

### 内容解压缩

| 测试项 | zerodep | httpx | 备注 |
|--------|---------|-------|------|
| 同步 Gzip GET | 待测 | 待测 | 两者均自动解压缩 |

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
