# HTTP 服务器

零依赖的异步 HTTP 服务器，Flask 风格的装饰器路由、流式响应（SSE）、静态文件服务和优雅关闭 -- 仅标准库，Python 3.10+。

> **可替代:** `flask`（轻量场景）、`microdot`、`bottle`、`starlette`（基础场景）、`aiohttp`（服务端部分）

## 概览

httpserver 模块基于 `asyncio.start_server()` 构建轻量级异步 HTTP/1.1 服务器。作为 Flask/microdot 的无依赖替代方案，适用于不想引入第三方依赖的 HTTP 服务场景。

| 文件 | 描述 | 依赖 |
|------|------|------|
| `httpserver.py` | 纯 Python 实现 | 无（仅标准库：`asyncio`、`json`、`re`、`signal`、`mimetypes`） |

## 特性

- **兼容 Flask/microdot API** -- `@app.route()`、`@app.get()`、`@app.post()` 签名完全一致
- **路径参数** -- `<name>`、`<int:id>`、`<float:price>`、`<path:filepath>` 自动类型转换
- **返回值自动转换** -- `dict` → JSON、`str` → 文本、`bytes` → 二进制、`tuple` → (body, status, headers)、`None` → 204
- **流式响应** -- 异步生成器 + chunked 传输编码，兼容 SSE
- **静态文件服务** -- `app.static()` 内置目录遍历防护
- **中间件** -- `before_request`、`after_request`、`errorhandler` 钩子
- **同步 + 异步处理器** -- 同步函数自动通过 `asyncio.to_thread()` 包装
- **优雅关闭** -- SIGINT/SIGTERM 信号处理，`app.shutdown()` 可从处理器中调用

## 在项目中使用

将单个 `.py` 文件复制到你的项目中：

```bash
cp httpserver/httpserver.py your_project/
```

然后直接导入：

```python
from httpserver import App, JSONResponse
```

## 使用示例

### 基本应用

```python
from httpserver import App, JSONResponse

app = App()

@app.get("/hello")
async def hello(request):
    return {"message": "Hello, World!"}

@app.post("/echo")
async def echo(request):
    return JSONResponse(request.json())

app.run(host="127.0.0.1", port=8000)
```

### 路径参数

```python
@app.get("/users/<int:id>")
async def get_user(request, id):
    return {"user_id": id}

@app.get("/files/<path:filepath>")
async def get_file(request, filepath):
    return {"path": filepath}
```

### 多方法路由

```python
@app.route("/items", methods=["GET", "POST"])
async def items(request):
    if request.method == "GET":
        return {"items": []}
    data = request.json()
    return JSONResponse({"created": data}, status_code=201)
```

### 查询参数和请求头

```python
@app.get("/search")
async def search(request):
    q = request.query_params.get("q", [""])[0]
    auth = request.headers.get("authorization", "")
    return {"query": q, "auth_present": bool(auth)}
```

### 同步处理器

同步函数自动通过 `asyncio.to_thread()` 包装：

```python
@app.get("/sync")
def sync_handler(request):
    import time
    time.sleep(0.01)  # 阻塞 I/O 也没问题
    return {"sync": True}
```

### 流式响应（SSE）

```python
from httpserver import StreamingResponse

@app.get("/events")
async def events(request):
    async def generate():
        for i in range(5):
            yield f"data: event {i}\n\n"

    return StreamingResponse(generate(), content_type="text/event-stream")
```

### 静态文件

```python
app.static("/assets", "./public")
# GET /assets/style.css → 提供 ./public/style.css
```

### 中间件

```python
@app.before_request
async def auth_check(request):
    if not request.headers.get("authorization"):
        return JSONResponse({"error": "unauthorized"}, status_code=401)

@app.after_request
async def add_cors(request, response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response

@app.errorhandler(404)
async def not_found(request, exc):
    return JSONResponse({"error": "not found"}, status_code=404)

@app.errorhandler(ValueError)
async def bad_value(request, exc):
    return JSONResponse({"error": str(exc)}, status_code=400)
```

### 文件响应

```python
from httpserver import FileResponse

@app.get("/download")
async def download(request):
    return FileResponse("report.pdf")
```

### 返回值自动转换

处理器可以返回多种类型，自动转换为响应：

```python
@app.get("/dict")
async def as_dict(request):
    return {"key": "value"}           # → JSONResponse

@app.get("/text")
async def as_text(request):
    return "Hello"                     # → Response (text/plain)

@app.get("/bytes")
async def as_bytes(request):
    return b"\x89PNG..."               # → Response (application/octet-stream)

@app.get("/tuple")
async def as_tuple(request):
    return {"ok": True}, 201           # → JSONResponse，状态码 201

@app.get("/empty")
async def as_none(request):
    return None                        # → 204 No Content
```

### 优雅关闭

```python
@app.post("/shutdown")
async def trigger_shutdown(request):
    request.app.shutdown()
    return {"status": "shutting down"}
```

## API 参考

### `App(*, max_body_size=1048576, read_timeout=30.0)`

主应用类。

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `max_body_size` | `int` | `1048576`（1 MB） | 请求体最大字节数 |
| `read_timeout` | `float` | `30.0` | 单次请求读取超时（秒） |

**路由方法：**

| 方法 | 描述 |
|------|------|
| `route(url_pattern, methods=None)` | 注册 URL 模式处理器。默认：`["GET"]` |
| `get(path)` | `route(path, methods=["GET"])` 的简写 |
| `post(path)` | `route(path, methods=["POST"])` 的简写 |
| `put(path)` | `route(path, methods=["PUT"])` 的简写 |
| `delete(path)` | `route(path, methods=["DELETE"])` 的简写 |
| `patch(path)` | `route(path, methods=["PATCH"])` 的简写 |
| `static(url_prefix, directory)` | 从目录提供静态文件 |

**中间件方法：**

| 方法 | 描述 |
|------|------|
| `before_request(handler)` | 注册请求前钩子。返回 `Response` 可短路后续处理 |
| `after_request(handler)` | 注册请求后钩子。接收 `(request, response)` |
| `errorhandler(code_or_exc)` | 注册 HTTP 状态码或异常类的错误处理器 |

**生命周期方法：**

| 方法 | 描述 |
|------|------|
| `run(host="127.0.0.1", port=8000)` | 启动服务器（阻塞） |
| `shutdown()` | 请求优雅关闭（可在处理器中安全调用） |

---

### `Request`

解析后的 HTTP 请求对象，作为所有处理器的第一个参数传入。

| 属性 | 类型 | 描述 |
|------|------|------|
| `method` | `str` | 大写 HTTP 方法（GET、POST 等） |
| `path` | `str` | URL 路径（已 percent-decode） |
| `query_string` | `str` | 原始查询字符串（不含 `?`） |
| `query_params` | `dict[str, list[str]]` | 解析后的查询参数 |
| `headers` | `dict[str, str]` | 请求头（键存储为小写） |
| `body` | `bytes` | 原始请求体 |
| `path_params` | `dict[str, Any]` | 从路由模式提取的参数 |
| `client_addr` | `tuple[str, int]` | 客户端 `(host, port)` |
| `app` | `App` | 处理此请求的应用实例引用 |

| 方法 | 返回类型 | 描述 |
|------|----------|------|
| `json()` | `Any` | 解析请求体为 JSON（带缓存） |
| `text()` | `str` | 将请求体解码为 UTF-8 |
| `form()` | `dict[str, list[str]]` | 解析 URL 编码的表单体 |

---

### `Response(body="", status_code=200, headers=None, content_type=None)`

固定内容的 HTTP 响应。

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `body` | `bytes \| str` | `b""` | 响应体 |
| `status_code` | `int` | `200` | HTTP 状态码 |
| `headers` | `dict[str, str] \| None` | `None` | 额外响应头 |
| `content_type` | `str \| None` | `None` | Content-Type 头的简写 |

---

### `JSONResponse(data, status_code=200, headers=None)`

将 `data` 序列化为 JSON 的便捷响应。

---

### `StreamingResponse(generator, status_code=200, headers=None, content_type=None)`

使用 chunked 传输编码的流式响应。

| 参数 | 类型 | 描述 |
|------|------|------|
| `generator` | `AsyncIterator[str \| bytes]` | 产生响应块的异步生成器 |
| `content_type` | `str \| None` | SSE 场景使用 `"text/event-stream"` |

---

### `FileResponse(path, status_code=200, headers=None, content_type=None)`

从磁盘提供文件。通过 `mimetypes.guess_type()` 自动检测内容类型。

---

### `HTTPException(status_code, message=None)`

映射到 HTTP 状态码的异常。直接抛出或通过 `abort()` 使用。

### `abort(status_code, message=None)`

`HTTPException` 的简写。

## 与 Flask / microdot / bottle 的对比

| 特性 | zerodep httpserver | Flask | microdot | bottle |
|------|-------------------|-------|----------|--------|
| 依赖 | 无（仅标准库） | werkzeug、jinja2 等 | 无 | 无 |
| 原生异步 | 是（`asyncio`） | 否（WSGI） | 是（`asyncio`） | 否（WSGI） |
| 处理器第一个参数 | `request`（显式） | 全局 `flask.request` | `request`（显式） | 全局 `bottle.request` |
| 路由 API | `@app.route(path, methods=)` | 相同 | 相同 | 相同 |
| 返回值转换 | dict/str/bytes/tuple/None | dict/str/tuple | dict/str/tuple | str/dict |
| 流式响应 | `StreamingResponse` | `stream_with_context` | `Response(async_gen)` | 生成器 |
| 静态文件 | `app.static()` | `send_from_directory` | `send_file` | `static_file` |
| 文件大小 | ~1000 行 | ~2000 行 + 依赖 | ~1400 行 | ~4700 行 |
| 并发处理 | 异步（多连接） | 1 请求/线程 | 异步（多连接） | 1 请求/线程 |

**何时使用 zerodep：** 需要零依赖的轻量级异步服务器，Flask 兼容 API，适用于嵌入工具、守护进程或微服务。

**何时使用 Flask：** 需要完整生态（Jinja 模板、扩展、gunicorn 等生产级 WSGI 服务器）。

**何时使用 microdot：** 需要在 MicroPython 上运行异步服务，或希望获得比 zerodep 更多功能的极简 Flask 替代方案。

## 性能测试

与 Flask、microdot 和 bottle 进行了对比性能测试，覆盖串行请求、并发负载、同步/异步处理器和大负载场景。

详见 [HTTP 服务器性能测试](../benchmarks/httpserver.md)。
