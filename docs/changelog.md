# 更新日志

本项目的所有重要变更都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。

## [未发布]

### 新增模块

- **httpserver 模块**：零依赖的异步 HTTP 服务器，兼容 Flask/microdot 的装饰器路由 API。基于 `asyncio.start_server()` 构建，原生 HTTP/1.1 解析。`@app.route(path, methods=)`、`@app.get()`、`@app.post()` 等路由注册方式。支持带类型转换的路径参数（`<name>`、`<int:id>`、`<float:price>`、`<path:filepath>`）。返回值自动转换（dict → JSON、str → 文本、bytes → 二进制、tuple → 状态码/头部、None → 204）。`StreamingResponse` 支持 chunked 编码用于 SSE。`FileResponse` 提供静态文件服务，内置目录遍历防护。`before_request`/`after_request`/`errorhandler` 中间件钩子。同步处理器通过 `asyncio.to_thread()` 自动包装。SIGINT/SIGTERM 优雅关闭。单文件，约 1000 行，仅标准库。58 个正确性测试 + 26 个性能测试（对标 Flask、microdot、bottle — 串行、并发、同步/异步、大负载）。
- **SyncTeX 模块**：零依赖的 SyncTeX 双向搜索解析器（PDF 位置与源代码位置互转）。解析 TeX 引擎生成的 `.synctex` 和 `.synctex.gz` 文件。`parse_synctex()` 提取输入文件映射、页面 hbox 记录和前导元数据。`inverse_search()` 通过多阶段空间匹配算法将 PDF 页面坐标映射回源文件和行号。`forward_search()` 将源文件和行号映射到 PDF 页面坐标。支持可配置的路径前缀去除，适用于 Docker/远程构建场景。29 个正确性测试。
- **useragent 模块**：轻量级 Chrome/Edge User-Agent 字符串生成器，附带 Client Hints 头部。`generate()` 为 Windows、macOS、Linux（桌面）和 Android（移动端）生成逼真的 UA 字符串及对应的 `Sec-CH-UA-*` 头部。支持低熵 hints（始终包含）和通过 `accept_ch()` 获取的高熵 hints（平台版本、架构、位数、型号、完整版本列表）。通过 `random.seed()` 实现确定性输出。单文件，约 470 行，仅标准库 `random`。47 个正确性测试 + 8 个性能测试（比 ua-generator 快 2-3 倍）。灵感来自 [ua-generator](https://github.com/iamdual/ua-generator)（Apache-2.0）。

### 基础设施

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
