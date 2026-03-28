---
title: 模块概览
---

# 模块概览

每个 zerodep 模块都是一个**独立的单 `.py` 文件**，可以直接复制到你的项目中使用，运行时无需 `pip install`。

## 全部模块

### 网络与通信

| 模块 | 描述 | 性能对标 |
|------|------|---------|
| [httpclient](http.md) | 同步 + 异步 REST 客户端 | `httpx` |
| [sse](sse.md) | Server-Sent Events 客户端（自动重连） | `httpx-sse` |

### 数据格式

| 模块 | 描述 | 性能对标 |
|------|------|---------|
| [yaml](yaml.md) | YAML 解析与序列化（常用子集） | `PyYAML` |
| [jsonc](jsonc.md) | JSONC 解析（JSON + 注释 + 尾逗号） | `commentjson` |
| [toon](toon.md) | TOON（面向 Token 的对象表示法）编码器/解码器 | `toon_format` |
| [frontmatter](frontmatter.md) | Frontmatter 解析与序列化（YAML/TOML/JSON） | `python-frontmatter` |

### 数据验证

| 模块 | 描述 | 性能对标 |
|------|------|---------|
| [validate](validate.md) | TypedDict/dataclass 运行时验证器 + JSON Schema 生成 | `pydantic` |

### 文本与标记

| 模块 | 描述 | 性能对标 |
|------|------|---------|
| [markdown](markdown.md) | Markdown 转 HTML 渲染器（CommonMark 子集 + GFM 表格） | `mistune` |
| [soup](soup.md) | 类 BeautifulSoup API 的 HTML 解析器（find、select、CSS 选择器） | `beautifulsoup4` |
| [diff](diff.md) | Unified diff 解析、补丁应用/反转、三方合并 | `unidiff` |

### 搜索与检索

| 模块 | 描述 | 性能对标 |
|------|------|---------|
| [search](search.md) | BM25/BM25+/BM25L/BM25F + TF-IDF 全文搜索引擎 | `rank-bm25` |

### 配置

| 模块 | 描述 | 性能对标 |
|------|------|---------|
| [dotenv](dotenv.md) | .env 文件解析（load_dotenv, dotenv_values） | `python-dotenv` |
| [config](config.md) | 统一配置加载器（环境变量、.env、JSON/YAML/TOML/INI） | `python-decouple` |

### 命令行与终端

| 模块 | 描述 | 性能对标 |
|------|------|---------|
| [ansi](ansi.md) | ANSI 终端样式：颜色、属性、检测、strip/visible_len | -- |
| [tabulate](tabulate.md) | 多种输出样式的表格格式化 | `tabulate` |
| [prompt](prompt.md) | 交互式 CLI 提示（confirm、select、text） | `questionary` |

### 安全与编码

| 模块 | 描述 | 性能对标 |
|------|------|---------|
| [aes](aes.md) | AES 加密：ECB、CBC、CTR、GCM 模式（纯 Python + OpenSSL ctypes） | `pycryptodome` |
| [qr](qr.md) | QR Code 生成与终端渲染 | `qrcode` |

### 基础设施与工具

| 模块 | 描述 | 性能对标 |
|------|------|---------|
| [retry](retry.md) | 装饰器式自动重试（退避、抖动、过滤） | `tenacity` |
| [scheduler](scheduler.md) | 进程内任务调度器（cron、间隔、一次性触发） | `APScheduler` |
| [structlog](structlog.md) | 结构化日志与彩色控制台输出 | `structlog` |
| [vcs](vcs.md) | Git/Hg/Jujutsu CLI 包装器（diff、status、log、blame） | -- |
