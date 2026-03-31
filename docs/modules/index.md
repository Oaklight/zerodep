---
title: 模块概览
---

# 模块概览

每个 zerodep 模块都是一个**独立的单 `.py` 文件**，可以直接复制到你的项目中使用，运行时无需 `pip install`。

## 全部模块

### 智能体协议

| 模块 | 描述 | 性能对标 |
|------|------|---------|
| [a2a](a2a.md) | Google A2A 协议：JSON-RPC 2.0、SSE 流式传输、任务管理 | `a2a-python` |
| [acp](acp.md) | Anthropic ACP 协议：JSON-RPC 2.0 over stdio、异步客户端/代理 | `acp-python` |
| [skills](skills.md) | Agent Skills 运行时：解析、发现、管理、选择技能 | -- |

### Network

| 模块 | 描述 | 性能对标 |
|------|------|---------|
| [httpclient](http.md) | 同步 + 异步 REST 客户端 | `httpx` |
| [sse](sse.md) | Server-Sent Events 客户端（自动重连） | `httpx-sse` |

### Terminal

| 模块 | 描述 | 性能对标 |
|------|------|---------|
| [ansi](ansi.md) | ANSI 终端样式：颜色、属性、检测、strip/visible_len | -- |
| [markdown](markdown.md) | Markdown 转 HTML 渲染器（CommonMark 子集 + GFM 表格） | `mistune` |
| [prompt](prompt.md) | 交互式 CLI 提示（confirm、select、text） | `questionary` |
| [tabulate](tabulate.md) | 多种输出样式的表格格式化 | `tabulate` |

### Data

| 模块 | 描述 | 性能对标 |
|------|------|---------|
| [config](config.md) | 统一配置加载器（环境变量、.env、JSON/YAML/TOML/INI） | `python-decouple` |
| [dotenv](dotenv.md) | .env 文件解析（load_dotenv, dotenv_values） | `python-dotenv` |
| [frontmatter](frontmatter.md) | Frontmatter 解析与序列化（YAML/TOML/JSON） | `python-frontmatter` |
| [jsonc](jsonc.md) | JSONC 解析（JSON + 注释 + 尾逗号） | `commentjson` |
| [soup](soup.md) | 类 BeautifulSoup API 的 HTML 解析器（find、select、CSS 选择器） | `beautifulsoup4` |
| [toon](toon.md) | TOON（面向 Token 的对象表示法）编码器/解码器 | `toon_format` |
| [validate](validate.md) | TypedDict/dataclass 运行时验证器 + JSON Schema 生成 | `pydantic` |
| [xml](xml.md) | XML 转字典转换器（容错解析） | `xmltodict` |
| [yaml](yaml.md) | YAML 解析与序列化（常用子集） | `PyYAML` |

### Crypto

| 模块 | 描述 | 性能对标 |
|------|------|---------|
| [aes](aes.md) | AES 加密：ECB、CBC、CTR、GCM 模式（纯 Python + OpenSSL ctypes） | `pycryptodome` |

### Process

| 模块 | 描述 | 性能对标 |
|------|------|---------|
| [runner](runner.md) | 结构化子进程执行（超时升级） | -- |
| [scheduler](scheduler.md) | 进程内任务调度器（cron、间隔、一次性触发） | `APScheduler` |

### Dev Tools

| 模块 | 描述 | 性能对标 |
|------|------|---------|
| [diff](diff.md) | Unified diff 解析、补丁应用/反转、三方合并 | `unidiff` |
| [vcs](vcs.md) | Git/Hg/Jujutsu CLI 包装器（diff、status、log、blame） | -- |

### Utility

| 模块 | 描述 | 性能对标 |
|------|------|---------|
| [cache](cache.md) | 内存缓存（TTL、LRU/LFU 淘汰、异步支持） | -- |
| [qr](qr.md) | QR Code 生成与终端渲染 | `qrcode` |
| [retry](retry.md) | 装饰器式自动重试（退避、抖动、过滤） | `tenacity` |
| [search](search.md) | BM25/BM25+/BM25L/BM25F + TF-IDF 全文搜索引擎 | `rank-bm25` |
| [structlog](structlog.md) | 结构化日志与彩色控制台输出 | `structlog` |
