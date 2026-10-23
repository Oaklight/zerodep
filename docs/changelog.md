# 更新日志

本项目的所有重要变更都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。

## [未发布]

### 新功能

- **sse**（v0.4.0）：模块现在既能消费事件流，也能生成事件流。`encode_event()` 由 `data`、`event`、`id`、`retry` 格式化一个 `text/event-stream` 块：多行数据每行生成一个 `data:` 字段，CRLF 与 CR 会被归一化；`event` 或 `id` 含换行、`id` 含 NUL、`retry` 为负数或非整数时抛出 `ValueError`。`encode_comment()` 生成心跳注释块。两者都是无网络依赖的纯函数，可直接配合 `httpserver.StreamingResponse` 或其他流式传输使用。([#241](https://github.com/Oaklight/zerodep/issues/241))
- **toon**（v0.6.0）：模块现已完整实现 TOON 4.4，编码器与解码器基于参考实现算法重写。全部 564 个官方一致性 fixture 通过（此前为 359/564），`toon/conformance_baseline.json` 已清空；`bench-toon` 升级到 `toon-python@91413d14`（spec 4.4）。规范移除了 4.0 之前的 `lengthMarker` 选项：编码器不再输出 `[#N]`，解码器拒绝该形式，传入该选项会抛出 `ValueError`。([#184](https://github.com/Oaklight/zerodep/issues/184))
- **httpclient**（v0.6.0）：模块级函数现在会复用连接。`get()`、`post()` 等（以及 `async_get()` 等）共享进程级连接池，不再每次调用新建连接——针对 keep-alive 服务端实测，顺序 `get()` 从约 990 次/秒提升到约 1900 次/秒，300 次请求只用了 3 个连接。异步连接池按事件循环隔离，因为池中的数据流属于创建它的事件循环；可用 `close_pools()` / `aclose_pools()` 释放。服务端空闲时关闭的池化连接会在使用前被检测出来（socket 窥探、异步 `at_eof()`），若仍发生竞态，`GET`/`HEAD`/`OPTIONS`/`PUT`/`DELETE` 会在新连接上重试一次。连接池的键现在包含 `verify`，因此以 `verify=False` 建立的连接绝不会交给需要校验的请求。空闲套接字还有全局上限：所有主机合计最多保留 `DEFAULT_MAX_TOTAL_CONNECTIONS`（100）个，超出时优先关闭最旧的连接；空闲超过连接池超时的条目会在下一次归还时清理，因此即使访问大量主机也不会每个主机各占一个套接字。上限与空闲时间都按客户端配置（`max_total_connections`、`pool_idle_timeout`）。
- **httpclient**：`on_timing` 以 `(event, elapsed)` 形式报告请求里程碑——`request_started`、`headers_received`（首字节时间）与 `body_complete`——耗时以单调时钟计量。模块级函数与 `Client` / `AsyncClient` 均可接受该回调；流式响应在响应体被消费时而非流打开时报告 `body_complete`，重定向会为每一跳报告 `headers_received`。([#172](https://github.com/Oaklight/zerodep/issues/172))
- **semantic_search**（v0.1.0）：新增零依赖稠密向量检索模块。Flat、IVF 与 LSH 三种索引共用 cosine、euclidean 与 inner_product 度量；文本查询通过任意 `list[str] -> list[list[float]]` 可调用对象完成，并内置 OpenAI、Cohere、Voyage 与 Jina 适配器。文档可附带 JSON 元数据用于检索时过滤，索引支持 JSON 与 SQLite 持久化，`rrf()` / `mmr()` 覆盖混合重排。`quantize=True` 在构建时把向量压缩为 SQ8 并释放 float32 副本，检索距离由量化数据重建，内存占用约为原来的四分之一。([#171](https://github.com/Oaklight/zerodep/pull/171))

### 新功能

- **httpserver**（v0.6.0）：同一连接现在可以处理多个请求。HTTP/1.1 连接默认保持，除非请求或响应发送 `Connection: close`（按大小写不敏感匹配）；HTTP/1.0 仅在请求要求时保持；无法识别的协议版本一律关闭；流式响应仍然关闭连接。新增 `App(keep_alive=..., keep_alive_timeout=..., max_requests_per_connection=...)` 选项用于调整或关闭该行为。`keep_alive_timeout` 只约束等待下一个请求行的时间，请求头与慢速请求体仍使用完整的 `read_timeout`；空闲连接到期后静默关闭而不再返回 `408`，但请求行之后卡住的请求仍会收到 `408`。`HEAD` 交给匹配的 `GET` 路由处理，返回相同的响应头（含 `Content-Length`）但不发送响应体，保持连接的客户端不会读到残余字节。客户端在请求之间关闭连接也不再被当作错误请求。([#210](https://github.com/Oaklight/zerodep/issues/210))

### 问题修复

- **httpclient**（v0.6.1）：同步 `stream=True` 响应体现在会边到达边产出。`iter_bytes()` 原先用 `read(4096)`，该调用会等到缓冲区填满或流结束才返回，因此每 0.4 秒一个的 23 字节 SSE 事件要等到 2.0 秒才一起到达 `EventSource`——心跳、`Last-Event-ID` 重连与逐 token 输出全部被阻塞。`read1()` 返回传输层当前已有的数据，与本来就按块读取的异步路径一致。
- **httpserver**（v0.6.1）：阻塞在 `await` 中的流式生成器现在可以在客户端断开时停止。对端 FIN 之后 `writer.is_closing()` 可能仍为 false，而 `reader.at_eof()` 已为 true，因此周期性检查只能等生成器自己的定时器结束——实测为 5 秒——套接字一直停留在 CLOSE_WAIT。`StreamingResponse(disconnect_on_eof=True)` 让检查同时参考读取端。由于 EOF 与合法的半关闭（客户端停止发送但仍继续读取）在协议上无法区分，该选项默认关闭；仅对不会半关闭的客户端（浏览器与常见 HTTP 库）启用。能及时 yield 的生成器不受影响；默认情况下，只发送 FIN 而从不发送 RST 的对端会在下一次 yield 时才被发现，而不是在阻塞期间。
- **sse**（v0.4.1）：当 `data`、`event` 或 `id` 不是字符串时，`encode_event()` 抛出指明参数名的 `TypeError`，不再在格式化过程中抛出 `AttributeError` 或提示 bytes-like object 的错误。文档也说明行源只能按 CR/LF 切分：`str.splitlines()` 还会在 U+2028、U+2029、U+0085、VT 与 FF 处分行，而事件流格式把这些字符视为数据，导致载荷被静默截断。
- **httpclient**：流式响应体若在达到声明的 `Content-Length` 之前结束，现在会抛出 `HttpConnectionError`，而不再把截断的响应体当作完整内容返回。对于定长响应，`iter_bytes()`、`iter_lines()`、`read()` 及其异步版本会统计已接收字节，在对端提前关闭时失败，且截断的响应体不会报告 `body_complete`。本身不携带响应体的响应——`HEAD` 请求以及 `204`/`304` 状态——不受影响。([#236](https://github.com/Oaklight/zerodep/issues/236))

- **toon**（v0.6.1）：`encode()` / `decode()` 现在拒绝未知选项键并抛出 `TypeError`，因此诸如参考实现的 `indent_size` 这类移植笔误不再静默生成不同的文档。`decode()` 接受 UTF-8 编码的 `bytes` / `bytearray`，非法 UTF-8 抛出 `ToonDecodeError`；`ToonDecodeError` 的 docstring 现在明确说明它不继承 `ValueError`。
- **jsonx**（v1.0.2）：`loads_lines()` 在传入自定义解码器或钩子时退出批量快速路径，与 `loads()` 一致：回调对每个值只执行一次，不再被试探性调用最多三次；钩子抛出的 `JSONDecodeError` 拒绝也不会被重试。`loads()` 对 `bytes` 抛出明确的 `TypeError` 说明该限制，不再泄漏正则扫描器的内部错误。
- **toon**（v0.6.0）：列表形式现在能往返嵌套对象值。`[{'d': {}}]` 编码为 `- d:` 并能解码回来，不再丢失 `d`；子对象键不同的对象数组也能解码自身编码器的输出，不再抛错。编码器现在把列表项头部与第一个键写在同一行，与参考实现一致。([#188](https://github.com/Oaklight/zerodep/issues/188))
- **jsonx** (v1.0.1)：`loads()` 先对原始文本直接调用 `json.loads`，只有失败时才运行注释与尾逗号扫描器——JSON 是 JSONC 的子集。对于不含注释的文档，这省去了两轮正则预处理，其开销约为解析本身的 14 倍（129 KiB 文档：65.6 ms → 4.05 ms）；真正的 JSONC 文档则多付出一次失败的解析。钩子与自定义解码器会退出快速路径，因此不会在试探性解析中被调用；当预处理没有改变文本时无需重试，失败只会报告一次——通过抛出 `JSONDecodeError` 拒绝文档的 hook 不会被再次调用，其拒绝也不会被覆盖。([#206](https://github.com/Oaklight/zerodep/issues/206), [#208](https://github.com/Oaklight/zerodep/pull/208))
- **toon**：`decode()` 遇到非法转义序列和结尾反斜杠时抛出 `ToonDecodeError`，而不再抛出裸的 `ValueError`，与文档化的契约以及一致性门禁对 `shouldError` 用例的期望一致。九个 fixture 由失败转为通过（564 个中 350 → 359）。`ToonDecodeError` 不继承 `ValueError`，因此调用方在 `decode()` 外围的 `except ValueError` 不再捕获格式错误——这是有意的契约，`docs/modules/toon.md` 现在已明确说明。与规范之间剩余的差距是解码器静默接受了本应拒绝的输入，而非错误类型问题；它仍记录在一致性 baseline 中，并由 [#184](https://github.com/Oaklight/zerodep/issues/184) 跟踪。([#198](https://github.com/Oaklight/zerodep/issues/198), [#209](https://github.com/Oaklight/zerodep/pull/209))
- **httpserver**：已接受但尚未发送任何请求的连接不再让关闭过程等满 `shutdown_grace_timeout`。等待请求行——无论是首个请求还是复用连接上的下一个——都算空闲，因此 TCP 健康探针或负载均衡检查会被立即关闭，而不会被当作正在处理的请求去排空。边界在于这段等待的结束：请求行一旦到达，连接就不再空闲，因此仍在上传的请求体会被排空并正常应答，而不会被中途切断。([#220](https://github.com/Oaklight/zerodep/issues/220))
- **httpserver**：在 3.10/3.11 上，关闭服务时也会等待正在处理的请求。这两个版本上 `Server.wait_closed()` 会立即返回，此前 `_serve` 随即退出，`asyncio.run` 会在响应写到一半时取消连接处理任务；现在服务器会跟踪处理任务并最多等待 `shutdown_grace_timeout`（默认 5 秒）再取消，关闭开始后才生成的响应会带上 `Connection: close`。事件循环已关闭后再次调用 `App.shutdown()` 现在是空操作，不再抛出 `Event loop is closed`。([#216](https://github.com/Oaklight/zerodep/issues/216))
- **httpserver**：优雅关闭不再为每个空闲客户端等满 `keep_alive_timeout`。Python 3.12 起 `Server.wait_closed()` 会等待所有打开的连接，而空闲的保持连接会一直开到空闲窗口结束——默认 5 秒，配置更长则更久。现在关闭开始时就会关闭正在等待下一个请求行的连接；正在处理的请求仍会完成。([#215](https://github.com/Oaklight/zerodep/pull/215))
- **httpclient**：套接字超时现在抛出 `HttpTimeoutError` 而不是 `HttpConnectionError` —— 模块为向后兼容提供的 `TimeoutError = HttpTimeoutError` 别名遮蔽了内置异常，使通用的 `OSError` 分支先被命中。超时也不再重试，因为重试会让调用者的实际耗时翻倍，还可能让同一个请求到达服务端两次；复用连接采用当次调用的超时；读取响应体中途失败的连接会被关闭，而不是把半消费的连接放回池中；HTTP/1.0 响应只有在带有 `Connection: keep-alive` 时才入池（RFC 7230 §6.3）。异步默认连接池改为挂在事件循环上，因此循环结束后连接池可被回收，不再每次 `asyncio.run()` 泄漏一个套接字；fork 出的子进程会丢弃继承的套接字。([#212](https://github.com/Oaklight/zerodep/issues/212), [#213](https://github.com/Oaklight/zerodep/pull/213))
- **soup** (v0.7.1)：引号内的逗号被直接跳过，导致 `[title="a,b"], [title="c"]` 这类选择器列表被解析成后代选择器并返回空列表，连解析正常的分组也一并丢弃。现在只在顶层逗号处切分，跟踪引号、方括号与圆括号，并按文档顺序取各分组的并集。空分组（尾随或连续逗号）改为抛异常，不再扩大为匹配所有元素；不支持的伪元素同样抛异常，不再静默丢弃所在分组。([#196](https://github.com/Oaklight/zerodep/pull/196))
- **soup** (v0.8.0)：属性选择器现在对 HTML 标准中大小写不敏感的 legacy 属性集（`type`、`lang`、`dir`、`rel`、`method` 等共 46 个名字）按 ASCII 大小写不敏感比较，作用于 `=`、`~=`、`|=`、`^=`、`$=`、`*=`。此前另外 45 个名字在大小写不同时匹配不足。这是有意与 soupsieve 2.10 分叉的——它只折叠 `type`——因此 `[lang="en"]` 现在能匹配 `lang="EN"`，与所有浏览器一致。([#194](https://github.com/Oaklight/zerodep/pull/194))
- **soup** (v0.8.1)：`[attr|=""]` 现在既能匹配恰好为空的值，也能匹配以 `-` 开头的值。Selectors Level 4 §6.1 对 `|=` 的定义中不含空字符串排除——与同一节的 `~=` 以及 §6.2 的 `^=`、`$=`、`*=` 都不同，后四者各自带有排除规则——此前的行为属于匹配不足。([#201](https://github.com/Oaklight/zerodep/pull/201))
- **toon** (v0.5.0)：空数组现在按规范 §9.1 编码为 `key: []`，不再输出 legacy 的 `key[0]:` 形式；空字符串 key 的值为空数组时不再丢失该 key。([#195](https://github.com/Oaklight/zerodep/pull/195))

### 基础设施

- **manifest**：生成清单时会规范化 `last_updated` 时间戳。不同版本的 git 会把 UTC 作者时间写成 `Z` 或 `+00:00`，导致同一份清单在另一个环境重新生成时出现无关差异；现在重新生成只会改变 `generated` 时间戳。清单中已有八条记录被一次性规范化。
- **Makefile**：`make test` 与 `make benchmark` 现在覆盖全部模块——73 个测试文件与 42 个基准测试。此前手工维护的聚合列表漏掉了 24 个模块（包括 `httpserver` 与 `s3`），而帮助文本承诺的是“所有模块”；`make test` 也会传入 `-rs`，让跳过原因可见。CI 直接运行 `pytest`，因此不受影响，但 `AGENTS.md` 所述的本地门禁并不完整。
- **Makefile**：`sse` 一直没有对应目标，`make test` 会静默跳过它的 67 个测试，而 CI 中直接调用的 `pytest` 却会运行。现在新增 `make test-sse` 与 `make benchmark-sse`，两者都已加入 `test`/`benchmark` 聚合目标，并由 `-rs` 报告跳过原因。httpclient 与 httpserver 文档页也已交叉链接到 `sse`，分别对应事件流消费与服务端编码。([#242](https://github.com/Oaklight/zerodep/issues/242))
- **基准测试模块在缺少 `pytest-benchmark` 时跳过**：41 个 `test_*_benchmark.py` 中有 40 个直接使用 `benchmark` fixture 而未做防护，因此在未安装基准测试 extras 的环境中，每个用例都会被报告为 `fixture 'benchmark' not found` 错误而不是跳过。现在它们都会调用 `pytest.importorskip("pytest_benchmark")`。
- **基准测试**：基准工作流现在通过 `bench-toon` 的 git pin 安装 TOON 参考实现，而不是未固定的 `git+` 安装加 `|| true`，并断言产物中存在 `toon/` 行。参考实现安装失败现在会让任务失败，而不是静默丢弃对比结果，与 `s3` 已有的保护一致。
- **基准测试 extras 在 Python 3.11+ 上使用 Pillow 13**：针对 `bench-qr` / `bench-png` 的全部 39 条 Dependabot 安全公告（4 条严重、23 条高危、12 条中危）都在 Pillow 13.0.0 中修复。该版本要求 Python 3.11，因此钉版本按版本拆分——3.11 起用 13.0.0，3.10 用最后一个支持它的 12.3.0。仅影响基准测试的参考依赖，模块本身不依赖 Pillow。
- **`python -m pytest` 下测试套件重新可以收集**：`import qrcode` 会导入 `png`，而 `python -m` 会把仓库根目录放进 `sys.path`（`pytest` 命令行脚本不会），于是 `png/` 被当作空的 namespace package 缓存下来，png 测试自身的导入随之失败，导致整个收集过程中断。现在 png 测试模块在导入被测模块前，会清除任何不属于该目录自身的 `png` 缓存条目——既包括 namespace 条目，也包括安装了 `pypng` 时 `qrcode` 绑定的真实模块。完整收集为 8805 个用例，无错误。([#223](https://github.com/Oaklight/zerodep/issues/223))
- **dotenv 与 frontmatter 基准测试现在测量真正的参考实现**：这两个测试目录与它们对比的包同名，而 pytest 的 prepend 导入模式使它们排在 site-packages 之前，于是 `pytest.importorskip` 绑定到仓库自己的模块，报告中 `test_python_dotenv` / `test_python_frontmatter` 两列实际测的是同一个 zerodep 实现。现在两个基准在导入参考实现时会临时隐藏这些遮蔽路径并在之后恢复，同时校验被绑定的模块不在仓库内，使这类冲突直接报错而不是产出看似合理的数字。([#205](https://github.com/Oaklight/zerodep/issues/205))
- **tabulate 正确性测试重新不受环境影响**：参考实现在安装了 `wcwidth` 时改用它计算列宽，而 zerodep 的默认实现使用 `len(s)`。当 `wcwidth` 作为传递依赖出现时，四个 unicode/CJK 对比实际上在比较两套不同的宽度规则并因此失败。测试现在对参考实现的导入隐藏 `wcwidth`，并断言它确实保持隐藏。`WIDE_CHARS_MODE` 现在把零宽符号（非占位组合符号、占位组合符号、包围符号与格式字符）以及 Hangul 的中声/终声字母计为零宽——`café` 为四列——与 `wcwidth` 的逐字符宽度一致；emoji 表现序列按组成部分计算，并作为两者唯一的差异写入文档。新增测试把每个形状与逐字符 `wcwidth` 之和对比，并把 `WIDE_CHARS_MODE=True` 的表格输出与带 `wcwidth` 的参考实现对比；字素簇（emoji 表现序列、印地语连写）按组成部分计算，并作为两者的差异写入文档。([#228](https://github.com/Oaklight/zerodep/issues/228))
- **soup 正确性测试只在 soupsieve 是参考实现时进行比对**：测试会拿 zerodep 的结果与 soupsieve 对比，但其中两组依赖 soupsieve 2.10 才加入的行为——`^=`、`$=`、`*=` 的 Selectors 4 空值规则（#201）以及选择器列表中逗号两侧的空白（#204）。在较旧的 soupsieve（固定依赖的环境常见 2.8.x）下，这 8 个对比会在参考侧失败，尽管 zerodep 遵循规范。直接断言仍然在所有版本运行；低于 2.10 时跳过参考比对。
- **CI** 现在对任意 base 分支的 pull request 运行测试套件，不再只限于 `master`，stacked PR 无需再手工 `workflow_dispatch` 才能拿到 checks。([#190](https://github.com/Oaklight/zerodep/pull/190))
- **toon 规范一致性 gate**：官方 TOON spec 4.4 的 fixtures（564 个用例——encode 160、decode 404）已入库到 `toon/fixtures/`，钉在 `toon-format/spec` 的 `v4.4.0`，由只能收缩的 ratchet baseline 在 CI 中把关。当前进度 350/564。这是 [#184](https://github.com/Oaklight/zerodep/issues/184) 的第一阶段。([#195](https://github.com/Oaklight/zerodep/pull/195))
- **s3 基准测试**改用 SeaweedFS 容器，替代已停止开源的 MinIO。CI 通过 GitHub Actions service container 与 `S3_TEST_ENDPOINT` 约定提供服务端，s3 基准对比数据得以在每次运行时正常发布。

## [2026.9.28] - 2026-09-28

### 新增模块

- **aiosqlite** (v0.1.0)：Python 内置 `sqlite3` 的异步封装 — 每个连接使用独立工作线程，完整镜像 `sqlite3.Connection`/`sqlite3.Cursor` API，提供便捷方法（`execute_fetchall`、`execute_fetchone`、`execute_insert`）。([#180](https://github.com/Oaklight/zerodep/pull/180))

### 问题修复

- **httpclient**：在 `StreamingResponse.aclose()` 中关闭 `StreamReader` 并释放 reader/writer 引用，防止 CLOSE_WAIT 套接字泄漏。关闭前调用 `feed_eof()` 以解除阻塞的读取操作。([#178](https://github.com/Oaklight/zerodep/pull/178))
- **httpserver**：在流式响应中检测客户端断开连接，防止 CLOSE_WAIT 泄漏。当生成器因慢速上游 I/O 阻塞时，通过 `asyncio.shield()` + `wait_for()` 定期检查 `is_closing()`。可通过 `StreamingResponse(disconnect_check_interval=...)` 配置检查间隔。([#179](https://github.com/Oaklight/zerodep/pull/179))
- **jsonschema**：保留真正的多分支 `anyOf`/`oneOf` 联合类型，不再将其折叠为第一个非 null 分支。此前 `float | list[float] | None` 会静默丢弃除第一个之外的所有分支。现在含 2 个及以上非 null 分支的联合类型会在原有关键字（`anyOf` 或 `oneOf`）下保留剩余分支，同时剥离 null 分支并设置 `nullable: true`。([#173](https://github.com/Oaklight/zerodep/pull/173))

### 文档

- 在文档索引配置中注册 `s3` 模块。([#174](https://github.com/Oaklight/zerodep/pull/174))

### 基础设施

- 在 `_scripts/experiments/` 下新增测量脚本：供应链攻击面、导入内存占用、冷启动延迟和安装体积。([abc8d78](https://github.com/Oaklight/zerodep/commit/abc8d78), [77cecc0](https://github.com/Oaklight/zerodep/commit/77cecc0), [499b8c5](https://github.com/Oaklight/zerodep/commit/499b8c5))

## [2026.9.15] - 2026-09-15

### 新增模块

- **profiler** (v0.1.0)：cProfile 封装模块，支持文本和 HTML 报告输出（表格、火焰图、冰柱图样式）。提供同步和异步上下文管理器，方便进行性能分析。([#161](https://github.com/Oaklight/zerodep/pull/161), [#166](https://github.com/Oaklight/zerodep/pull/166))

### 新功能

- **profiler**：新增 `TracingProfiler` — 逐调用跟踪分析器，支持线程感知的数据采集，使用 `sys.monitoring`（PEP 669，Python 3.12+）并回退到 `sys.settrace`。与 `Profiler` 共享相同的输出接口，另外支持通过 `traces()` 访问原始调用轨迹。([#168](https://github.com/Oaklight/zerodep/issues/168), [#169](https://github.com/Oaklight/zerodep/pull/169))
- **profiler**：新增火焰图和冰柱图可视化样式，支持交互式缩放、搜索、工具提示和可折叠调用栈。([#166](https://github.com/Oaklight/zerodep/pull/166))
- **ratelimit**：新增 `CompositeLimiter`，支持多窗口速率限制组合执行（如 RPM + RPD）。([#159](https://github.com/Oaklight/zerodep/pull/159))
- **ratelimit**：新增 `CompositeLimiter` 内省 API — 所有限流器类支持 `detail()`、`__iter__`、`__repr__`。([#163](https://github.com/Oaklight/zerodep/pull/163), [#164](https://github.com/Oaklight/zerodep/pull/164))
- **httpserver**：新增 TLS 支持（`ssl_certfile`/`ssl_keyfile`）和套接字调优参数（`backlog`、`reuse_port`）。([#165](https://github.com/Oaklight/zerodep/pull/165))
- **httpserver**：新增请求生命周期信号 — `on_request_start`、`on_request_end`、`on_error` 钩子。([5356aa4](https://github.com/Oaklight/zerodep/commit/5356aa4))
- **jsonschema**：新增 JSON Schema 数据验证 — `schema_validate()` 和 `iter_errors()` 用于根据 JSON Schema 文档（Draft 2020-12 OpenAPI 3.x 子集）验证数据实例。支持 type、enum、const、字符串/数值约束、对象关键字、数组关键字、组合（allOf/anyOf/oneOf/not）、if/then/else 和布尔 schema。比 `jsonschema` PyPI 快 60-180 倍。模块层级从 `medium` 升级为 `subsystem`。([#131](https://github.com/Oaklight/zerodep/issues/131), [#157](https://github.com/Oaklight/zerodep/pull/157))
- **jsonschema**：为 `iter_errors()` / `schema_validate()` 新增 `resolved=True` 参数，支持"解析一次、验证多次"模式 — 当调用方已调用 `resolve_refs()` 时跳过重复的 `$ref` 解析。对同一 schema 重复验证时约提速 3.4 倍。注意：`resolved=False` 仍为安全默认值；对未解析的 schema 传入 `resolved=True` 会静默跳过 `$ref` 引用目标。([#157](https://github.com/Oaklight/zerodep/pull/157))

### 问题修复

- **httpserver**：防止 `_dispatch` 中 `BrokenPipeError` 异常向上传播。([c0229d1](https://github.com/Oaklight/zerodep/commit/c0229d1))

### 基础设施

- 新增冷启动基准测试，测量导入和首次调用的开销。([#160](https://github.com/Oaklight/zerodep/pull/160))


## [2026.9.12] - 2026-09-12

### 问题修复

- **jsonschema**：位置感知的 walker 现在能正确保留与 schema 关键字冲突的用户参数名（如 `title`、`deprecated`、`examples`）。此前这些参数名在 `properties` 映射中会被静默删除。同时将 `dependentSchemas` 加入属性映射键集合。([#153](https://github.com/Oaklight/zerodep/issues/153), [#154](https://github.com/Oaklight/zerodep/pull/154))

### 基础设施

- **CI**：将 PyPI 发布内联到 `release.yml` 中作为直接 job，替代通过 `GITHUB_TOKEN` 的 `gh workflow run` 调度（该方式不可靠）。([#152](https://github.com/Oaklight/zerodep/issues/152), [#155](https://github.com/Oaklight/zerodep/pull/155))

## [2026.9.9] - 2026-09-09

### 新功能

- **CLI**：新增 `outdated --json` 标志，提供机器可读的 JSON 输出，包含模块列表和 `outdated_count`。([#149](https://github.com/Oaklight/zerodep/pull/149))
- **CLI**：新增 `outdated --exit-code` 标志——存在过期或已重命名的模块时以退出码 1 退出，遵循 `git diff --exit-code` 惯例。([#149](https://github.com/Oaklight/zerodep/pull/149))
- **CLI**：新增 `update --all` 标志，一键发现并更新所有过期模块，无需逐个指定模块名。([#149](https://github.com/Oaklight/zerodep/pull/149))
- **CLI**：新增 `pyproject.toml` 中的 `[tool.zerodep]` 配置支持——通过 `vendor-dir` 键声明 vendor 目录，省略 `-d` 参数。使用轻量正则解析器（无 `tomllib` 依赖，Python 3.10+ 可用）。([#149](https://github.com/Oaklight/zerodep/pull/149))
- **httpclient**：新增 Cookie 支持——`Response.cookies` / `StreamingResponse.cookies` 属性、所有请求函数的 `cookies=` 参数、`Client` / `AsyncClient` 的会话 Cookie Jar。([#150](https://github.com/Oaklight/zerodep/issues/150))
- **httpserver**：新增 Cookie 支持——`Request.cookies` 属性（延迟解析）、所有响应类型的 `Response.set_cookie()` / `delete_cookie()` 方法。([#150](https://github.com/Oaklight/zerodep/issues/150))

### 问题修复

- **httpclient**：修复多个 `Set-Cookie` 头部丢失的问题，此前 `CaseInsensitiveDict` 仅保留最后一个值。([#150](https://github.com/Oaklight/zerodep/issues/150))

### 基础设施

- **CLI**：提取 `_scan_outdated()` 辅助函数，供 `cmd_outdated` 和 `cmd_update --all` 共享使用。
- **CLI**：新增 `test_cli.py`，包含 11 个测试，覆盖 `--json` 输出结构、`--exit-code` 行为、`update --all` 及 `pyproject.toml` 配置读取。
- **文档**：在 zerodep skill 文件中新增 CI 自动化章节，记录工作流模式和新增 CLI 标志。

## [2026.9.7] - 2026-09-07

### 问题修复

- **validate**：修复 struct 字段验证中类型强制转换值丢失的问题——此前强制转换的值（如字符串转整数）在 `create_struct` 字段处理过程中被丢弃。([#148](https://github.com/Oaklight/zerodep/pull/148))
- **validate**：修复所有集合类验证器（list、set、frozenset、tuple、dict）中类型强制转换值丢失的问题——嵌套集合验证路径中转换结果被丢弃。([#148](https://github.com/Oaklight/zerodep/pull/148))

## [2026.9.6] - 2026-09-06

### 新功能

- **validate**：添加 `Doc` 注解标记，用于在 JSON Schema 中为字段添加描述。通过 `Annotated[str, Doc("...")]` 使用，支持静态 TypedDict/dataclass 字段和动态创建的类型。([#142](https://github.com/Oaklight/zerodep/issues/142)、[#143](https://github.com/Oaklight/zerodep/pull/143))
- **validate**：添加 `create_struct(name, fields)` 用于运行时动态构建 TypedDict。字段以 `(type, default)` 元组指定，`...` 表示必填。返回的 TypedDict 兼容 `validate()`、`json_schema()` 和 `model_validator()`。([#142](https://github.com/Oaklight/zerodep/issues/142)、[#143](https://github.com/Oaklight/zerodep/pull/143))
- **validate**：`json_schema()` 现在为 `create_struct` 类型和 dataclass 静态默认值输出 `"default"` 属性。([#142](https://github.com/Oaklight/zerodep/issues/142)、[#143](https://github.com/Oaklight/zerodep/pull/143))

### 问题修复

- **validate**：支持 PEP 604 联合类型（`X | Y` 语法）。此前 `types.UnionType` 未被识别，导致 PEP 604 联合类型静默通过验证并生成空 schema。同时修复 `get_type_hints()` 双重包装 `Optional[X | None]` 时 schema 中出现重复 null 的问题。([#143](https://github.com/Oaklight/zerodep/pull/143))
- **validate**：修复 Python 3.10 上 `Required`/`NotRequired` 注解检测问题，该版本 `typing.TypedDict` 未正确填充 `__required_keys__`/`__optional_keys__`。([#141](https://github.com/Oaklight/zerodep/pull/141))
- **httpclient**：在 `iter_lines()`/`aiter_lines()` 中使用字节缓冲区，防止多字节字符跨 chunk 边界时 UTF-8 编码损坏。([#140](https://github.com/Oaklight/zerodep/pull/140))
- **httpclient**：修复 `iter_lines()` 绕过 gzip 解压的问题。

### 性能优化

- **retry**：装饰器开销优化 -60%（430→170 ns），重试循环优化 -30%（3,374→2,348 ns）。成功路径快速返回，绕过 `_retry_sync` 循环。模块级缓存 `random.random`。([#144](https://github.com/Oaklight/zerodep/pull/144))

## [2026.9.4] - 2026-09-04

### 新功能

- **httpserver**：为 `StreamingResponse` 添加可选的 `background` 回调参数——流式生成器完成后（包括客户端断开连接时）调用的同步或异步可调用对象。遵循 Starlette 的 `BackgroundTask` 模式。回调异常以 warning 级别记录并被抑制。([#132](https://github.com/Oaklight/zerodep/issues/132)、[#133](https://github.com/Oaklight/zerodep/pull/133))
- **httpserver**：添加 `on_startup` 和 `on_shutdown` 装饰器钩子用于服务器生命周期管理。启动钩子按注册顺序在接受连接前运行；关闭钩子按反序（LIFO）在服务器停止后运行。支持同步和异步可调用对象。即使启动部分失败，关闭钩子也保证运行。([#134](https://github.com/Oaklight/zerodep/issues/134)、[#137](https://github.com/Oaklight/zerodep/pull/137))
- **httpserver**：添加 `State` 类和 `request.state` 属性，用于在中间件和处理器之间共享每请求数据。遵循 Starlette 模式，使用基于 `__dict__` 的属性访问。([#135](https://github.com/Oaklight/zerodep/issues/135)、[#138](https://github.com/Oaklight/zerodep/pull/138))

### 问题修复

- **httpserver**：`shutdown()` 现在是线程安全的——使用 `loop.call_soon_threadsafe()` 替代直接调用 `asyncio.Event.set()`，后者在从不同线程调用时会静默失败。
- **httpserver**：`StreamingResponse` 中生成器 `aclose()` 失败不再阻止 background 回调的执行。

## [2026.8.30] - 2026-08-30

### 问题修复

- **httpclient**：`_aiter_chunked` 不再因 chunk-size 行非合法十六进制（例如上游反向代理向活跃的 chunked 流中注入原始 HTTP 错误响应）而抛出裸 `ValueError`。现改为抛出 `HttpConnectionError`，包含原始行内容（截断至 100 字节）。([#129](https://github.com/Oaklight/zerodep/issues/129)、[#130](https://github.com/Oaklight/zerodep/pull/130))

### 基础设施

- **benchmarks**：从 `pyproject.toml` extras 自动发现参考库，替代硬编码列表。修复 ratelimit benchmark 在 limiter 缺失时跳过整个测试套件的问题。

## [2026.8.25] - 2026-08-25

### 新模块

- **ratelimit** (v0.1.0)：零依赖多算法限流器，提供 4 种算法（令牌桶、固定窗口、滑动窗口计数器、GCRA）并统一于 `RateLimiter` Protocol。便捷 API：`ratelimit()` 装饰器/上下文管理器（同步 + 异步）、`create_limiter()` 工厂函数、`parse_quota()` 字符串解析（`"10/s"`、`"100/m burst 200"`）、per-key 锁的 `ThreadSafeLimiter`、`RateLimitExceeded` 异常、带超时的等待重试。所有算法类均支持完整异步 API（`aacquire`/`apeek`）。性能比 `limits` 库快 2-4 倍，FixedWindow 与 `token-bucket` C 扩展差距仅 1.05 倍。([#120](https://github.com/Oaklight/zerodep/issues/120)、[#121](https://github.com/Oaklight/zerodep/pull/121))

### 问题修复

- **兄弟模块导入**：`_ensure_sibling_path()` 现同时支持扁平（`_vendor/soup.py`）和嵌套（`soup/soup.py`）vendor 布局。此前仅嵌套布局可用，导致扁平 vendor 项目中兄弟导入静默失败。恢复 `os.path.abspath(__file__)` 以增强健壮性。涉及 9 个模块：readability、qr、vcs、skills、sse、config、a2a、acp、cdp。([#124](https://github.com/Oaklight/zerodep/issues/124)、[#125](https://github.com/Oaklight/zerodep/pull/125))
- **CLI**：`bump` 子命令现使用 `primary_file` 而非 `files[0]`。`outdated` 子命令新增 `-d/--dir` 标志。Benchmark 文件（`benchmark_*.py`）已从模块文件列表中排除。

### 性能优化

- **ratelimit**：单线程吞吐量提升 75%——通过 `__slots__` 结果类、内联热路径、per-key 线程锁、消除 `int()`/`round()` 开销。TokenBucket：1338→762 ns/op。多线程不同 key 场景提升 76%。([#126](https://github.com/Oaklight/zerodep/pull/126))

## [2026.7.20] - 2026-07-20

### 问题修复

- **httpclient**：在同步 `close()` 中关闭 async writer，防止长连接场景下的文件描述符泄漏。

### 基础设施

- **release**：在 release workflow 中重新生成 `manifest.json`，确保与源码保持同步。

## [2026.7.16] - 2026-07-16

### 新模块

- **s3** (v0.2.0)：纯标准库 S3 兼容客户端。第一阶段：SigV4 签名、`get_object`、`put_object`、`head_object`、`delete_object`、`list_objects_v2`。第二阶段：`create_bucket`、`delete_bucket`、`head_bucket`、`list_buckets`、`copy_object`。已在 MinIO Docker 上与 boto3 和 minio 进行基准测试。

### 功能增强

- **validate**：`validate()` 现支持直接传入 dataclass 实例。实例在每个嵌套层级通过 `dataclasses.fields()` 自动转换为 dict，支持嵌套 dataclass 树的递归验证。跨类型验证（dataclass 实例对 TypedDict schema）同样可用。此前传入 dataclass 实例会抛出 `ValidationError: Expected dict, got <ClassName>`。
- **httpclient**：新增 `CaseInsensitiveDict` 用于 header 处理，贯穿整个 header 管道。修复大小写不敏感的 header 去重问题。([#116](https://github.com/Oaklight/zerodep/issues/116))
- **httpclient**：统一同步/异步客户端行为和接口一致性。`AsyncClient.close()` 不再对空操作发出警告。

### 基础设施

- 为 Claude Code 和 Hermes Agent 添加 `zerodep` CLI skill。

## [2026.6.29] - 2026-07-02

### 功能增强

- **httpserver**：新增 Unix domain socket 支持。返回 HTTP 错误响应而非静默断开连接。提取 `_send_error_and_close` 辅助方法以减少重复代码。

### 问题修复

- **httpserver**：修复 Python 3.13 兼容性问题（使用 `socket.bind()` 替代 `socket.connect()` 进行旧 socket 测试）。
- **sse**：在 `_SSEParser` 中使用关键字参数替代私有 slot 写入，修复初始化问题。版本升至 0.3.2。

### 性能优化

- **validate**：O(1) 可辨识联合类型分发——`_try_discriminated` 现使用缓存的 `{字面量值: TypedDict}` 分发表代替每次调用的 O(variants) 线性扫描。大规模联合类型验证约 230 倍加速（例如 500 项 × 10 变体联合：生产环境 917ms → 4ms）。([#107](https://github.com/Oaklight/zerodep/issues/107)、[#108](https://github.com/Oaklight/zerodep/pull/108))

### 基础设施

- 锁定 CI workflow 中的开发工具版本：ruff 0.15.20、ty 0.0.54、complexipy 5.6.1。

## [2026.6.13] - 2026-06-13

### 新模块

- **jsonx** (v1.0.0)：由 `jsonc` 改名而来，现为扩展 JSON 解析器，支持 JSONC（注释 + 尾逗号）和 JSONL/NDJSON。新增 API：`loads_lines`、`load_lines`、`dumps_lines`、`dump_lines`。干净 JSONL 场景下采用批量快速路径，性能与 `ndjson` 持平。([#95](https://github.com/Oaklight/zerodep/issues/95)、[#99](https://github.com/Oaklight/zerodep/pull/99))

### 新功能

- **readability**：在 `ReadabilityResult` 中暴露 best-candidate 评分（[#97](https://github.com/Oaklight/zerodep/pull/97)）。新增 `score: float` 字段（默认 `0.0`），携带评分算法选出的最佳候选容器的 readability 分数。分数越高，表示提取内容为真实文章而非导航/样板内容的信心越强。未找到评分候选容器（body 回退）时为 `0.0`。使下游消费者能够做出更智能的内容质量决策（例如 SPA 空壳检测）。

### 功能增强

- **config**：内部依赖从 `jsonc` 更新为 `jsonx`，保留对旧版 `jsonc` 模块的向后兼容 fallback。
- **CLI**：新增 `replaced_by` 机制——`zerodep add jsonc` 会自动安装 `jsonx` 并提示迁移；`zerodep outdated` 检测本地 `jsonc.py` 并建议升级。

### 性能优化

- **jsonx**：`loads_lines` 对干净 JSONL 使用批量解析（将所有行拼接为 JSON 数组，单次 `json.loads` 调用），达到 ndjson 级别性能。有注释时自动降级为逐行 JSONC 处理。

## [2026.6.1] - 2026-06-01

### 问题修复

- **httpclient**：`_prepare_body(data={"key": "value"})` 在未提供 `files` 时不再静默丢弃 dict 数据。Dict 数据现在会被 URL 编码为 `application/x-www-form-urlencoded`，与 `httpx`/`requests` 行为一致。([#93](https://github.com/Oaklight/zerodep/issues/93))

### 测试

- 新增 httpclient、websocket 和 cache 模块的并发性能测试。
- 新增 yaml/soup/protobuf/multipart 的几何级数规模曲线测试。([#86](https://github.com/Oaklight/zerodep/issues/86))
- 新增解析器模块的 tracemalloc 内存基准测试。([#84](https://github.com/Oaklight/zerodep/issues/84)、[#85](https://github.com/Oaklight/zerodep/issues/85))
- 基准测试报告新增 min/max/stddev/P95 统计指标。([#81](https://github.com/Oaklight/zerodep/issues/81))
- 新增解析器模块的真实场景 fixture 数据。([#83](https://github.com/Oaklight/zerodep/issues/83))

### 基础设施

- 重构 CI 为可复用的 `lint-test.yml` 工作流，由 `ci.yml` 和 `release.yml` 共同调用。
- Lint 作业改用 `pre-commit run --all-files` 替代原始 ruff 命令。
- 统一 CI/release 参考库安装方式，通过 `pyproject.toml` extras 动态提取。
- 使用官方 complexipy pre-commit hook。
- 新增 `CONTRIBUTING.md` 及工作流文档中的禁止 AI co-author 策略。
- 新增 arXiv 徽章和引用 BibTeX。

## [2026.5.17] - 2026-05-17

### 新增模块

- **multipart 模块**：零依赖的 multipart/form-data 解析与编码器，遵循 RFC 7578 / RFC 2046。`parse_multipart()` 使用 boundary-split 算法配合 `bytes.find()` 在 C 层解析请求体。`encode_multipart()` 编码表单字段和文件上传。`extract_boundary()` 从 Content-Type 头提取 boundary。`Part` 冻结数据类，包含 name、data、filename、content_type、headers、`.text` 和 `.is_file` 属性。健壮的 boundary 检测（验证前后字节避免误匹配）。支持 Content-Transfer-Encoding（base64、quoted-printable）。RFC 5987 `filename*` 参数解码。安全限制：max_part_size（10 MB）、max_parts（1000）、max_header_size（16 KB）。单文件，约 590 行，仅标准库。57 个正确性测试 + 11 个性能测试（比 python-multipart 快 3-7 倍）。

### 问题修复

- **httpclient**：移除 `AsyncClient` / `Client` 中多余的全局 `asyncio.Lock()` / `threading.Lock()`，该锁会序列化并发请求并可能导致死锁。连接池内部已有细粒度锁机制。

### 基础设施

- 在 AGENTS.md 中新增文档/更新日志更新工作流指引。

## [2026.5.2.1] - 2026-05-02

### 问题修复

- **CLI**：`version-check` 和 `bump` 不再对没有历史 release tag 的全新模块执行错误的自动版本递增。新模块现在显示 `"new (initial release)"` 而非 `"new (needs version bump)"`，并从自动 bump 目标中排除。
- **模块版本**：回退 5 个新模块的错误版本递增 — httpserver (0.1.0)、websocket (0.1.0)、cdp (0.1.0)、useragent (0.1.0)、synctex (0.2.0)。

## [2026.5.2] - 2026-05-02

### 新增模块

- **websocket 模块**：零依赖的 RFC 6455 WebSocket 客户端，同步 + 异步支持。`WebSocketClient` 和 `AsyncWebSocketClient` 支持 `ws://` 和 `wss://` 连接。完整协议实现：升级握手、文本帧编解码（含客户端侧掩码）、ping/pong 自动响应、关闭帧交换（含状态码）。支持自定义头部（认证令牌等）、子协议协商、可配置超时。上下文管理器（`with`/`async with`）。TLS 支持可选证书验证。单文件，约 1000 行，仅标准库（`socket`、`ssl`、`asyncio`、`hashlib`、`struct`）。27 个正确性测试（同步 + 异步、echo、超时、自定义服务器、URL 解析）+ 8 个性能测试（对标 `websockets` — JSON-RPC 往返、大负载、突发消息、连接建立）。
- **cdp 模块**：零依赖的 Chrome DevTools Protocol 客户端，用于无头浏览器自动化。`CDPClient` 和 `AsyncCDPClient` 通过 WebSocket 通信，自动命令/响应 ID 匹配和事件缓冲。高级 API：`get_rendered_text()` 和 `get_rendered_html()` 一行代码提取 SPA 渲染内容。低级 API：`create_target()`、`close_target()`、`navigate()`（自动等待 `Page.loadEventFired`）、`evaluate()`（异常传播）、`set_user_agent()` 和原始 `send_command()`。通过 `/json/version` 自动发现浏览器调试 WebSocket URL。依赖兄弟模块 `websocket`。约 900 行，仅标准库。18 个正确性测试（mock CDP 服务器 + 可选真实 Chromium）+ 10 个性能测试（完整渲染管线、多标签页、JS 执行吞吐、命令吞吐）。
- **httpserver 模块**：零依赖的异步 HTTP 服务器，兼容 Flask/microdot 的装饰器路由 API。基于 `asyncio.start_server()` 构建，原生 HTTP/1.1 解析。`@app.route(path, methods=)`、`@app.get()`、`@app.post()` 等路由注册方式。支持带类型转换的路径参数（`<name>`、`<int:id>`、`<float:price>`、`<path:filepath>`）。返回值自动转换（dict → JSON、str → 文本、bytes → 二进制、tuple → 状态码/头部、None → 204）。`StreamingResponse` 支持 chunked 编码用于 SSE。`FileResponse` 提供静态文件服务，内置目录遍历防护。`before_request`/`after_request`/`errorhandler` 中间件钩子。同步处理器通过 `asyncio.to_thread()` 自动包装。SIGINT/SIGTERM 优雅关闭。单文件，约 1000 行，仅标准库。58 个正确性测试 + 26 个性能测试（对标 Flask、microdot、bottle — 串行、并发、同步/异步、大负载）。
- **SyncTeX 模块**：零依赖的 SyncTeX 双向搜索解析器（PDF 位置与源代码位置互转）。解析 TeX 引擎生成的 `.synctex` 和 `.synctex.gz` 文件。`parse_synctex()` 提取输入文件映射、页面 hbox 记录和前导元数据。`inverse_search()` 通过多阶段空间匹配算法将 PDF 页面坐标映射回源文件和行号。`forward_search()` 将源文件和行号映射到 PDF 页面坐标。支持可配置的路径前缀去除，适用于 Docker/远程构建场景。29 个正确性测试。
- **useragent 模块**：轻量级 Chrome/Edge User-Agent 字符串生成器，附带 Client Hints 头部。`generate()` 为 Windows、macOS、Linux（桌面）和 Android（移动端）生成逼真的 UA 字符串及对应的 `Sec-CH-UA-*` 头部。支持低熵 hints（始终包含）和通过 `accept_ch()` 获取的高熵 hints（平台版本、架构、位数、型号、完整版本列表）。通过 `random.seed()` 实现确定性输出。单文件，约 470 行，仅标准库 `random`。47 个正确性测试 + 8 个性能测试（比 ua-generator 快 2-3 倍）。灵感来自 [ua-generator](https://github.com/iamdual/ua-generator)（Apache-2.0）。

### 基础设施

- 在 benchmark CI 工作流中添加 `websockets`，用于 websocket 和 cdp 性能跟踪。
- 在 benchmark CI 工作流中添加 `ua-generator`，用于 useragent 性能跟踪。
- 新增自动 PyPI 发布工作流（`.github/workflows/pypi.yml`），在 GitHub Release 发布时触发，带变更检测以跳过仅版本号变更。
- 新增 `AGENTS.md`（统一的 AI 编程助手指令文件），附 `CLAUDE.md` 软链接，兼容 Claude Code、Codex、Cursor、Copilot、Gemini CLI 等工具。

### 功能增强

- **CLI**：为 `zerodep new` 新增 `--from FILE` 参数，支持从已有 Python 源文件创建模块。自动注入 frontmatter（保留 shebang/encoding 声明），复用已有 frontmatter 并支持 CLI 参数覆盖，检测到第三方 import 时输出警告。

## [2026.4.27] - 2026-04-27

### 新增模块

- **llms.txt 模块**：零依赖的 [llms.txt 规范](https://llmstxt.org/) 解析器。`parse()` 从 llms.txt 文件中提取结构化数据（标题、描述、详情、H2 分节、Optional 条目）。`find_candidates()` 提供统一的 URL 发现功能 — 搜索已解析的 llms.txt 条目（精确 > 扩展名变体 > 路径前缀），无可用 llms.txt 时回退到启发式 `.md` URL 推导。`discover()` 自动探测任意 URL 所在站点的 `/llms.txt` 和 `/llms-full.txt`，通过 `DiscoveryResult` 返回原始内容。冻结 dataclass（`LlmsTxt`、`FileEntry`、`DiscoveryResult`）作为不可变结果。55 个正确性测试 + 4 个性能测试。
- **PNG 模块**：零依赖的 PNG/BMP 图像编解码器，附带矩阵压缩 API。`decode_png`/`encode_png` 支持 PNG 图像（灰度/RGB/RGBA、8/16 位、全部 5 种行滤波器），`decode_bmp`/`encode_bmp` 支持 BMP（24/32 位未压缩），`convert()` 支持 L/LA/RGB/RGBA 模式互转，`matrix_to_png`/`png_to_matrix` 通过 PNG 行滤波器实现二维数值数据压缩，通过 tEXt 元数据实现浮点数无损往返。104 个正确性测试（与 Pillow Apple-to-Apple 对比）+ 24 个性能测试。

### 新功能

- **Protobuf 模块**：新增 `byte_size()` 方法，计算序列化消息大小而无需实际分配 bytes。适用于预分配缓冲区和协议帧长度计算。
- **QR 模块**：新增 `qr_to_svg()` 和 `qr_to_png()`，将 QR Code 渲染为 SVG 和 PNG 图像。SVG 使用单个 `<path>` 元素（零依赖）；PNG 通过 sibling `png` 模块懒加载渲染灰度图像。两者均支持可配置的缩放比例、静默区边框和前景/背景色。24 个渲染测试。
- **Validate 模块**：新增 `FieldValidator` 和 `model_validator` 自定义验证机制。`FieldValidator` 是基于 `Annotated` 的约束，可转换值并在失败时抛出 `ValueError`/`AssertionError`（不同于只返回 bool 的 `Predicate`）。`model_validator` 是装饰器，用于在 TypedDict/dataclass 上注册跨字段验证器，在所有字段验证通过后执行。新增 18 个测试。版本 0.4.2 → 0.5.0。
- **Sparse Search 模块**：新增检索后重排序工具，用于混合搜索和 RAG 管道。`rrf()` 实现倒数排名融合（Reciprocal Rank Fusion，Cormack et al., SIGIR 2009），用于合并多路排名结果列表（如 BM25 稀疏搜索 + 稠密向量搜索），支持各列表独立权重和 top_k 截断。`mmr()` 实现最大边际相关性（Maximal Marginal Relevance）结果多样化重排序，接受用户自定义相似度函数，内部自动 min-max 归一化相关性分数。`jaccard_similarity()` 提供基于集合的相似度计算工具，作为 MMR 相似度函数的构建块。三个函数均为独立的模块级函数，操作通用 `list[Result]`。新增 31 个正确性测试 + 5 个性能测试。版本 0.3.2 → 0.4.0。

### 功能增强

- **Markdown 模块**：新增 GFM 删除线（`~~text~~` → `<del>`）、任务列表（`- [ ]` / `- [x]`，带 checkbox 和 class 属性）、扩展自动链接（裸 `https://` / `http://` URL 自动链接，自动剥离尾部标点）。所有输出与 mistune GFM 插件完全一致。新增 28 个正确性测试 + 4 个 GFM 性能测试。版本 0.3.1 → 0.4.0。
- **Soup 模块**：新增 CSS 伪选择器支持——`:first-child`、`:last-child`、`:only-child` 和 `:not(selector)`。涵盖最常用的结构性伪类。`:not()` 接受任意简单选择器（标签、类名、ID、属性或嵌套伪类）。新增 CSS 选择器和伪选择器性能测试。版本 0.5.0 → 0.6.0。

### 性能优化

- **PNG 模块**：优化 BMP 编解码器、PNG 行滤波器和模式转换。BMP 编解码将逐像素 BGR↔RGB 循环替换为 `bytearray` slice 赋值（C 级操作）——**提速 42-44 倍**（从比 Pillow 慢 193-265 倍降至约慢 4.6-6.1 倍）。PNG 行滤波器优化：Up 滤波器使用 list comprehension + `zip`，Sub 滤波器前缀单独处理，Paeth 缓存函数引用为局部变量。解码/编码路径预分配像素缓冲区。7 种无损模式转换（L↔RGB↔RGBA 等）从逐像素循环改为 slice 操作。PNG 编解码整体**提速约 10%**。
- **Protobuf 模块**：全面优化编解码热路径——FieldInfo 上绑定 encoder 分发（消除 11 路 if/elif）、每字段特化 `_is_default` 检查、内联 1 字节 tag 解码快速路径（字段号 1-15）、write-to-buffer varint/scalar 编码器（消除中间 `bytes` 分配）、缓存 map entry 类型元数据（`_MapMeta`）、`__dict__.update` 批量构造消息实例。编码**提速约 41-65%**，解码**提速约 7-27%**，大型消息往返**提速约 39%**。

### 基础设施

- 模块分类从 7 个细化为 12 个更精确的分组：network、protocol、serialization、validation、text、config、terminal、crypto、image、process、storage、devtools。
- 重命名 `scripts/` → `_scripts/`（内部约定）。
- 文档构建时从 `manifest.json` + 配置文件自动生成 `modules/index.md`。
- 修复 `version-check` 误报：旧的项目级 SemVer tag 冲突和主文件选取错误导致的 false positive。

## [2026.4.25] - 2026-04-25

### 新增模块

- **JSON Schema 模块**：零依赖的 JSON Schema 展平与清理。`flatten_schema()` 解析 `$ref`、合并 `allOf`（深度合并，支持 type 取交集、数值约束取严格值、required 取并集）、简化 `anyOf`/`oneOf`（nullable 检测、单变体展开）并剥离不支持的关键字。每个阶段可独立调用：`resolve_refs`、`merge_allof`、`simplify_unions`、`sanitize`。与 `allof-merge`（JS）在 5 个复杂度层级对比——**快 1.7-5.3 倍**。57 个单元测试 + 13 个跨实现正确性测试。
- **Readability 模块**：零依赖的文章正文提取器，移植自 Mozilla Readability.js。`extract()` 执行完整的文章提取并返回元数据（标题、作者、摘要、发布时间、站点名称、语言、文字方向）。`is_probably_readable()` 提供快速可读性启发式检查。支持 JSON-LD 和 OpenGraph 元数据提取。两级重试机制（ruthless 开/关）确保提取鲁棒性。18 个 Mozilla Readability.js 测试用例用于交叉验证。三方 benchmark 对比：zerodep vs readability-lxml vs Mozilla JS。依赖 `soup` 模块（无 pip 依赖）。

### 功能增强

- **Soup 模块**：扩展树操作和序列化 API——`append()`、`insert()`、`extract()`、`replace_with()`、`unwrap()` 用于 DOM 树操作；`to_html()` / `__str__()` 用于 HTML 序列化；`__setitem__` / `__delitem__` 用于属性设置/删除；`Soup.new_tag()` 工厂方法用于创建独立的 Tag 节点。

### 性能优化

- **A2A 模块**：优化序列化和反序列化路径——`to_dict()` 避免了 `dataclasses.asdict()` 风格的深拷贝开销。序列化现已比 a2a-protocol **快 2.2-2.6 倍**（此前慢 1.4-2.1 倍）。反序列化从慢 1.8-4.1 倍收窄至**慢 1.1-1.7 倍**，得益于优化的枚举解析和类型分发。JSON 往返现已端到端**快 1.4-1.5 倍**。
- **Cache 模块**：优化 `TypedKey` 构造、装饰器包装路径和 LFU 淘汰。LRU 装饰器开销现已比 cachetools **快 1.2 倍**。TTL 装饰器达到持平。LFU 淘汰现已**基本持平**（此前慢 1.4 倍）。
- **PersistDict 模块**：优化 SQLite 写入性能——`PRAGMA synchronous=NORMAL`、`commit_every` 参数支持批量写入、延迟提交。
- **QR 模块**：优化编码路径——短输入现仅慢 1.1 倍（此前慢 2.1 倍）。中型/长输入现已比 `qrcode` 库**快 1.1-1.2 倍**（此前慢 1.7-1.9 倍）。
- **Readability 模块**：优化评分和树遍历算法——小型页面**快 2.1 倍**，中型页面现已**快 1.2 倍**（此前慢 2 倍）。大型页面从慢 2 倍改善至慢 1.4 倍（vs readability-lxml）。
- **Semver 模块**：优化解析、比较和属性访问。解析**快约 1.3 倍**，排序**快约 1.4 倍**，比较**快约 1.4 倍**，属性访问**快约 4.5 倍**。

### 问题修复

- **文档**：修复 `search` → `sparse_search` 模块重命名导致的 ReadTheDocs 构建失败。

## [2026.4.15] - 2026-04-15

### 新增命令

- **`zerodep bump`**：自动检测变更模块（通过内容哈希与 git tag 对比）并 bump 其 frontmatter 版本号。支持 `--patch`（默认）、`--minor` 和 `--major` 级别。可选指定模块名。Bump 后自动重新生成 `manifest.json`。
- **`zerodep new`**：生成新模块目录的脚手架模板——包含 frontmatter、版权信息和 `__all__` 的模块源文件，正确性测试文件。支持 `--category`、`--tier` 和 `--deps` 选项。

### 功能增强

- **`zerodep version-check --strict`**：新增标志，当有模块需要 bump 时以退出码 1 退出，支持 CI 集成。

### CI

- **Release 工作流**：新增 GitHub Actions 工作流（`.github/workflows/release.yml`），自动化完整发布流程——lint、测试、自动检测 CalVer 版本、bump 模块版本、更新项目版本、提交、打 tag、创建 GitHub Release。通过 `workflow_dispatch` 触发，支持手动指定版本号。
- **Benchmark 版本检查**：在 benchmark 工作流中添加非阻塞的 `version-check` 步骤，提醒未 bump 的模块。
- Benchmark 告警阈值从 150% 提高至 200%，减少 CI 运行环境波动导致的误报。

### 问题修复

- **a2a 模块**：修复 Python 3.11+ 下 `StrEnum` 字符串表示测试（使用 `.value` 属性替代 f-string 格式化）。
- **httpclient 模块**：benchmark 测试从 `httpbin.org` 切换到本地测试服务器，提升可靠性。

### 重构

- **复杂度治理**：对 19 个模块进行重构，使所有函数的认知复杂度（complexipy）和圈复杂度（ruff C901）均降至 20 以下。涉及模块：cache、validate、tabulate、dotenv、runner、xml、diff、soup、sse、search、scheduler、depdetect、qr、acp、yaml、toon、protobuf、markdown、httpclient。
- 采用的重构模式：按类型分派表、try-parse 提取、分阶段分解、辅助函数提取——均在单文件约束下完成。
- **qr 模块**：更新版权声明，反映大幅重构（不再是直接移植）。

### Benchmark

- 自定义 HTML 报告生成器，支持明暗主题切换和按模块生成独立 benchmark 页面，可嵌入文档。
- 修正 benchmark 报告颜色阈值和 AES 模块分类。

### 内部改进

- 新增 `complexipy>=5.2.0` 开发依赖及 `pyproject.toml` 中的 `[tool.complexipy]` 配置。
- 启用 ruff `C901` 检查规则，`max-complexity = 20`。

## [2026.4.11] - 2026-04-11

### 不兼容变更

- **版本策略**：项目级版本号采用 [CalVer](https://calver.org/)（`YYYY.M.patch`）日历版本。各模块继续使用独立的 SemVer 语义版本。每次发布代表 CLI 和全部模块的稳定快照。

### 新增命令

- **`zerodep dep-graph`**：显示模块依赖关系——全量模块表格视图，或指定单个模块查看传递性影响分析（`zerodep dep-graph yaml`）。
- **`zerodep dep-check`**：自动检测变更模块（通过内容哈希与 git tag 对比），然后运行变更模块及其所有下游依赖的正确性测试。测试失败时退出码为 1，支持 CI 集成。可指定模块名检查特定模块（`zerodep dep-check yaml config`）。
- **`zerodep version-check`**：检查哪些模块在其声明版本后有代码修改（此前已存在，现重构以与 `dep-check` 共享检测逻辑）。

### 功能增强

- **模块 frontmatter**：为所有模块添加 `note` 字段，指向 CLI 文档，提示手动拷贝文件可能遗漏依赖。
- **`zerodep add`**：拷贝文件时将通用 note 替换为具体模块的安装命令（如 `zerodep add config`）。
- **模块版本**：修正所有模块级版本号，反映各模块实际的变更历史，而非跟随项目版本统一 bump。如 `cache`（0.2.0）、`prompt`（0.2.0）、`tabulate`（0.1.0）现显示其真实版本。

### 内部改进

- 从 `cmd_version_check` 提取 `_find_changed_modules()` 辅助函数，在 `version-check` 和 `dep-check` 间共享变更检测逻辑。
- 新增 `_build_reverse_deps()`、`_transitive_dependents()` 和 `_find_test_file()` 工具函数。

## [0.4.1] - 2026-04-10

### 性能优化

- **Validate 模块**：为 `_typeddict_fields()`、`_dataclass_fields()`、`_find_discriminator()`、`_is_typeddict()`、`_is_dataclass_type()` 和 `_unwrap_annotated()` 内部辅助函数添加 `@functools.lru_cache(maxsize=None)` 缓存。消除冗余的 `get_type_hints()` 和类型内省调用。简单验证**提速 3 倍**（9.9 → 3.3 us），批量数据验证现已**比 pydantic 快 2 倍**。

### 问题修复

- **Validate 模块**：新增 `_strip_required()` 辅助函数，用于在 discriminated union 匹配前解包 `Required[T]`/`NotRequired[T]` 包装器。此前当联合类型成员使用 `Required[Literal[...]]` 字段注解时，discriminated union 分发可能失败。

## [0.4.0] - 2026-04-09

### 新增模块

- **Semver 模块**：PEP 440 版本解析与比较器——零依赖，可直接替换 `packaging.version`。支持完整的 PEP 440 版本方案，包括 epoch、pre/post/dev 发布、local 版本和字母规范化。排序性能比 `packaging` 快约 2 倍。
- **Protobuf 模块**：零依赖 proto3 编解码器，使用 Python dataclass 定义消息 schema。支持全部 proto3 标量类型（int32/64、uint32/64、sint32/64、fixed32/64、sfixed32/64、float32、double、bool、string、bytes）、嵌套消息、packed repeated 字段、map 字段、枚举、oneof 分组和未知字段保留。通过 `@message` 装饰器 + `field(number)` + `Annotated` 类型别名定义 schema——无需 `.proto` 文件或 `protoc` 编译器。Proto3 语义：零值字段不序列化，repeated 标量默认 packed 编码。
- **持久化字典模块**：基于 `MutableMapping` 的持久化字典，支持可插拔后端（JSON 文件、SQLite）和可插拔序列化（默认 JSON，无 pickle）。线程安全、原子写入、通过 SQLite 表支持命名空间。工厂函数 `open()` 根据文件扩展名自动检测后端。
- **DepDetect 模块**：依赖检测与验证工具。

### 功能增强

- **zerodep CLI**：新增 `outdated` 命令——将本地文件的内容哈希与上游 manifest 对比，检测实质性内容变更，忽略仅元数据更新（如版本号变化）。
- **zerodep CLI**：manifest 新增 `content_hash` 字段——去除 frontmatter 后的模块文件 SHA-256 摘要，实现可靠的变更检测。
- **zerodep CLI**：manifest 新增 `last_updated` 字段——每个模块主文件最后一次 git 提交的 ISO 8601 时间戳。
- **zerodep CLI**：manifest 生成现在跳过 `build/` 和 `dist/` 目录，避免将过期构建产物注册为模块。
- **Skills 模块**：`to_markdown()` 和 `from_dict()` 方法，支持 SKILL.md 往返序列化——程序化技能创建、模板生成和迁移工具。
- **Skills 模块**：BM25 索引缓存——避免在相同技能集上重复调用 `select()` 时冗余重建索引。
- **Skills 模块**：`SkillRegistry.select()` 新增 `min_score` 阈值——在注入系统提示词前过滤低相关性结果。
- **Skills 模块**：递归目录发现（`discover(..., recursive=True)`）——支持 `category/sub-skill/` 分层布局。
- **Skills 模块**：优先级/覆盖机制（`register(override=True)`、`discover(override=True)`）——实现项目 > 用户 > 系统的技能优先级链。
- **Skills 模块**：资源内容内联（`to_prompt(inline_resources=True)`）——将 scripts/references/assets 文件内容直接嵌入激活提示词 XML。
- **Skills 模块**：兼容性过滤（`filter_compatible()`、`select()` 的 `available_tools` 参数）——根据当前环境的可用工具过滤技能。
- **AES 模块**：`aes_ecb_padded_size()` 工具函数——无需实际加密即可计算 PKCS7 填充后的密文大小。

## [0.3.0] - 2026-04-01

### 新增模块

- **文件锁模块**：仅标准库的跨平台咨询式文件锁。Unix/macOS 使用 `fcntl.flock`，Windows 使用 `msvcrt.locking` 配合指数退避轮询。支持上下文管理器、非阻塞 `try_lock()`、自动创建父目录。
- **JSON-RPC 模块**：JSON-RPC 2.0 协议实现，包含核心数据类型（`JSONRPCError`、`JSONRPCRequest`、`JSONRPCResponse`）、异常层次结构、支持流式的方法分发器，以及基于换行分隔 JSON 流的异步传输层。性能测试比 `jsonrpcserver` 快约 12-17 倍。

### 功能增强

- **Search 模块**：Bayesian BM25 概率校准——通过 sigmoid 似然、复合先验和贝叶斯后验，将无界 BM25 分数转换为校准概率 [0,1]。支持从语料统计自动估计 α/β 参数和可选的基准率校正。校准状态在 JSON 和 SQLite 中持久化。
- **A2A 模块**：将内联 JSON-RPC 层提取至共享 `jsonrpc` 模块；`A2AError` 现继承 `JSONRPCException`，实现统一的错误处理。
- **ACP 模块**：将内联 JSON-RPC 层提取至共享 `jsonrpc` 模块；用基于正则的算法转换替换 39 条硬编码 camelCase 映射表；序列化统一为 A2A 风格的单一递归 `to_dict()`，支持空集合过滤。

### 风格

- 现代化类型标注：将 `Optional`/`Dict`/`List` 替换为 PEP 604/585 风格。
- 为所有模块添加 `__all__` 导出。
- 统一模块间的段落分隔符风格。
- 为 frozen dataclass 添加 `slots=True`。
- 重命名 httpclient 测试文件以保持命名一致性。
- 统一测试文件 docstring 格式。

## [0.2.2] - 2026-03-31

### 功能增强

- **HTTP Client**：新增 `HttpClientError` 作为公共基础异常；将 `ConnectionError` / `TimeoutError` 重命名为 `HttpConnectionError` / `HttpTimeoutError`，避免遮蔽 Python 内置名（保留向后兼容别名）。
- **Config 模块**：为 `UndefinedValueError` 新增 `ConfigError` 基础异常。
- **Frontmatter 模块**：`HandlerError` 新增 `handler` 上下文字段。
- **VCS 模块**：`CommandError` 在超时时捕获部分输出，并新增 `timeout` 字段。

### 内部改进

- 标准化所有子系统模块的错误类型约定：两层层次结构、`<模块><名词>Error` 命名、带上下文字段的 f-string 消息。
- 文档化子进程执行约定（二进制发现、超时、编码、返回码）。
- 文档化 sync/async API 镜像约定（命名、阶段注释、共享逻辑提取）。
- 文档化大模块内部分层约定（段落标记、顺序、阶段注释）。
- `internals.md` 中全部 8 个模式现已标准化或已实现。

## [0.2.1] - 2026-03-30

### 功能增强

- **VCS 模块**：`Mercurial` 和 `Jujutsu` 构造函数接受 `merge_func` 参数，支持显式注入三路合并函数；`detect()` 将其转发给后端。
- **Config 模块**：`Config` 构造函数接受 `loaders` 和 `dotenv_loader` 参数，支持显式注入文件格式加载器和 dotenv 加载器。
- **SSE 模块**：`SSEClient` 和 `AsyncSSEClient` 构造函数接受 `transport` 参数，支持显式注入 HTTP 传输层；重连错误处理自动适配。

### 内部改进

- 在 vcs、config、sse 模块中引入 `_Unset` 哨兵模式，实现三态注入参数（`_UNSET` = 自动发现、`None` = 禁用、可调用对象 = 注入）。
- 在内部约定文档中新增"显式注入"章节（中英文）。

## [0.2.0] - 2026-03-30

### 新增模块

- **Scheduler 模块**：零依赖进程内任务调度器，支持 cron 表达式。
- **Sparse Search 模块**：BM25 系列（BM25、BM25+、BM25L）和 TF-IDF 全文搜索引擎。
- **Frontmatter 模块**：解析和序列化 YAML/TOML/JSON 文件头元数据。
- **Config 模块**：统一多源配置加载器，支持环境变量、.env 文件、JSON/JSONC/YAML/TOML/INI，类型转换和前缀过滤。
- **Cache 模块**：内存缓存，支持 LRU/FIFO/LFU/TTL 淘汰策略、同步+异步装饰器、线程安全、缓存统计。
- **Runner 模块**：结构化子进程执行，支持同步+异步 API、流式输出（回调+迭代器）、SIGTERM 到 SIGKILL 超时升级、环境隔离、命令白名单/黑名单。
- **XML 模块**：兼容 xmltodict 的字典与 XML 互转，支持 LLM 标签提取。

### 功能增强

- **HTTP Client**：连接池，支持可配置的池大小和空闲超时。
- **HTTP Client**：透明 gzip/deflate 自动解压缩，覆盖普通和流式响应。
- **HTTP Client**：HTTP/HTTPS 代理支持，含 CONNECT 隧道。
- **HTTP Client**：Basic 和 Digest 认证，支持自动 401 质询-响应。
- **VCS 模块**：工作区、分支和提交生命周期操作。
- `zerodep` CLI 工具，支持模块发现和依赖感知的模块复制。
- **zerodep CLI**：递归模块扫描，支持嵌套目录结构和重名检测。
- 模块元数据从 `__version__`/`__deps__` 迁移至 PEP 723 内联脚本元数据（frontmatter）。
- 稀疏搜索反向索引优化，提升检索性能。

### 问题修复

- **Runner**：对齐异步路径下的部分输出处理和进程回收逻辑与同步路径一致。
- **Scheduler**：收紧任务状态转换的锁纪律，修复竞态条件。
- **HTTP Client**：修复同步/异步路径差异并丰富错误上下文。
- **HTTP Client**：修复 `ty` 类型检查器发现的类型错误。

### 内部改进

- **Tier 1 重构**：统一 config、sse、vcs 模块的兄弟导入模式；延迟加载 config 兄弟模块和 vcs 中的 diff 模块以减少导入时副作用；对齐 prompt 和 structlog 的终端颜色检测逻辑；为清理路径添加层级分类注释。
- **Tier 2 重构**：将 httpclient 重组为 12 层内部结构以提升清晰度；为 runner 添加 14 段结构及同步/异步对齐审计；明确 scheduler 并发模型并添加错误约定。

## [0.1.0] - 2026-03-27

### 新增

- **AES 模块**：AES 加解密，支持 ECB、CBC、CTR、GCM 模式及 128/192/256 位密钥。
- **QR Code 模块**：零外部依赖的二维码生成。
- **HTTP Client 模块**：同步和异步 HTTP 客户端，支持流式响应和文件上传。
- **Dotenv 模块**：`.env` 文件解析和加载。
- **YAML 模块**：YAML 解析和生成。
- **JSONC 模块**：JSON with Comments (JSONC) 解析器。
- **Retry 模块**：可配置的重试装饰器，支持退避策略。
- **Structured Logging 模块**：结构化日志，支持 JSON 输出和终端彩色显示。
- **TOON 模块**：Token-Oriented Object Notation 序列化/反序列化。
- **Tabulate 模块**：纯文本表格格式化。
- **Soup 模块**：轻量级 HTML 解析。
- **Prompt 模块**：交互式终端输入工具。
- **Validate 模块**：TypedDict/dataclass 运行时校验器，支持 JSON Schema 生成。
- **SSE 模块**：Server-Sent Events (SSE) 客户端。
- **Markdown 模块**：Markdown 到 HTML 渲染器。
- **Diff 模块**：统一和上下文差异生成。
- **VCS 模块**：版本控制系统工具。
- **ANSI 模块**：ANSI 终端样式，支持自动颜色检测。
- 所有模块添加 `__version__` 属性，支持跨模块兼容性检查。
- 在 `pyproject.toml` 中添加 `ty` 类型检查器配置。
- 添加 CI 工作流，覆盖 Python 3.10–3.13 兼容性测试。

### 修复

- 修复 HTTP 客户端异步 body 读取竞态条件。
- 修复 `ty` 类型检查器在多个模块中发现的类型错误。

### 变更

- 统一 prompt、structlog 和 ansi 模块的终端颜色检测逻辑。
- 将 HTTP 测试从 `httpbin.org` 替换为本地测试服务器，提升测试可靠性。

### 移除

- 移除 validate 模块对 `typing_extensions` 的依赖。
