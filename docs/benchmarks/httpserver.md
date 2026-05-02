# HTTP 服务器性能测试

zerodep httpserver 与 [Flask](https://pypi.org/project/Flask/)、[microdot](https://pypi.org/project/microdot/)、[bottle](https://pypi.org/project/bottle/) 的端到端服务性能对比。

!!! info "测试环境"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **工具:** pytest-benchmark 5.2.3（报告均值）
    - **参考库:** Flask 3.1.3、microdot 2.6.1、bottle 0.13.4
    - **最后更新:** 2026-05-02

## 实现方式

| 实现 | 类型 | 描述 |
|------|------|------|
| **zerodep** | 异步（`asyncio`） | 单文件 HTTP 服务器，仅标准库 |
| **Flask** | 同步（WSGI） | 全功能 Web 框架（werkzeug） |
| **microdot** | 异步（`asyncio`） | 极简 Flask 风格异步框架 |
| **bottle** | 同步（WSGI） | 单文件 WSGI 框架（wsgiref） |

## 测试内容

每个框架在后台线程启动 HTTP 服务器。基准测试使用 zerodep `httpclient` 模块测量完整的请求-响应往返延迟。

## 测试场景

| 场景 | 描述 | 客户端 |
|------|------|--------|
| 串行 GET JSON | 单次 GET 返回 `{"pong": true}` | 同步 `get()` |
| 串行 POST JSON | 单次 POST 回显小 JSON 负载 | 同步 `post()` |
| 串行 GET 文本 | 单次 GET 返回 `"Hello, World!"` | 同步 `get()` |
| 同步 vs 异步处理器 | 对比 `async def` 与 `def`（仅 zerodep） | 同步 `get()` |
| 并发 GET (x10) | 10 个同时发起的 GET 请求 | `asyncio.gather` + `async_get()` |
| 并发 POST (x10) | 10 个同时发起的 POST 请求（含 JSON） | `asyncio.gather` + `async_post()` |
| 大负载 POST | POST ~30KB JSON 请求体 | 同步 `post()` |

## 关键发现

- **串行延迟** -- 四个框架在单请求延迟上表现相近（~250-400 us），无明显优劣。
- **并发处理** -- 异步框架（zerodep、microdot）处理 10 个并发请求约需 ~5 ms。WSGI 框架（Flask、bottle）串行处理请求，耗时约 ~1 秒（慢 200 倍）。
- **同步处理器开销** -- `asyncio.to_thread()` 相比原生异步处理器增加约 20% 开销，但在并发负载下仍优于 WSGI 框架。
- **大负载** -- JSON 解析/序列化吞吐在各框架间相当，瓶颈在 `json.dumps()`/`json.loads()` 而非 HTTP 层。
- **零依赖** -- zerodep 在无 pip 依赖的情况下达到了 Flask/microdot 级别的性能。

## 自行运行

```bash
pip install pytest pytest-benchmark flask microdot bottle
pytest httpserver/test_httpserver_benchmark.py --benchmark-only -v
```

---

## 最新 CI 结果

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/httpserver.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> 每次发布时通过 [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml) 自动更新。
