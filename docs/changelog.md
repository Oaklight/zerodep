# 更新日志

本项目的所有重要变更都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。

## [未发布]

### 新增

- **Frontmatter 模块**：解析和序列化 YAML/TOML/JSON 文件头元数据。
- **Scheduler 模块**：零依赖进程内任务调度器，支持 cron 表达式。
- **Sparse Search 模块**：BM25 系列（BM25、BM25+、BM25L）和 TF-IDF 全文搜索引擎。
- `zerodep` CLI 工具，支持模块发现和依赖感知的模块复制。

### 变更

- 模块元数据从 `__version__`/`__deps__` 迁移至 PEP 723 内联脚本元数据（frontmatter）。
- 稀疏搜索反向索引优化，提升检索性能。

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
