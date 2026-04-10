# 更新日志

本项目的所有重要变更都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。

## [未发布]

## [0.4.2] - 2026-04-10

### 性能优化

- **Validate 模块**：为 `_typeddict_fields()`、`_dataclass_fields()` 和 `_find_discriminator()` 内部辅助函数添加 `@functools.lru_cache(maxsize=None)` 缓存，避免冗余的 `get_type_hints()` 调用。对复杂嵌套 TypedDict 结构的验证性能提升 **8-10 倍**。

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
