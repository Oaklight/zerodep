# 更新日志

本项目的所有重要变更都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。

## [未发布]

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
