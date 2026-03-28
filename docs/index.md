---
title: 首页
hide:
  - navigation
---

# zerodep

零依赖、单文件的 Python 常用库实现 —— 仅使用标准库，支持 Python 3.10+。

## 概述

每个模块都是一个**独立的单文件**，可以直接复制到你的项目中使用，无需 `pip install`。

## 可用模块

### 网络与通信

| 模块 | 描述 | 性能对标 |
|------|------|---------|
| [HTTP 客户端](modules/http.md) | 同步 + 异步 REST 客户端 | `httpx` |
| [SSE 客户端](modules/sse.md) | Server-Sent Events 客户端（自动重连） | `httpx-sse` |

### 数据格式

| 模块 | 描述 | 性能对标 |
|------|------|---------|
| [YAML 解析器](modules/yaml.md) | YAML 解析与序列化（常用子集） | `PyYAML` |
| [JSONC 解析器](modules/jsonc.md) | JSONC 解析（JSON + 注释 + 尾逗号） | `commentjson` |
| [TOON 序列化](modules/toon.md) | TOON（面向 Token 的对象表示法）编码器/解码器 | `toon_format` |

### 数据验证

| 模块 | 描述 | 性能对标 |
|------|------|---------|
| [验证器](modules/validate.md) | TypedDict/dataclass 运行时验证器 + JSON Schema 生成 | `pydantic` |

### 文本与标记

| 模块 | 描述 | 性能对标 |
|------|------|---------|
| [Markdown 渲染器](modules/markdown.md) | Markdown 转 HTML 渲染器（CommonMark 子集 + GFM 表格） | `mistune` |
| [HTML 解析器](modules/soup.md) | 类 BeautifulSoup API 的 HTML 解析器（find、select、CSS 选择器） | `beautifulsoup4` |
| [Diff 差异工具](modules/diff.md) | Unified diff 解析、补丁应用/反转、三方合并 | `unidiff` |

### 搜索与检索

| 模块 | 描述 | 性能对标 |
|------|------|---------|
| [稀疏搜索](modules/search.md) | BM25/BM25+/BM25L/BM25F + TF-IDF 全文搜索引擎 | `rank-bm25` |

### 配置

| 模块 | 描述 | 性能对标 |
|------|------|---------|
| [Dotenv 环境变量](modules/dotenv.md) | .env 文件解析（load_dotenv, dotenv_values） | `python-dotenv` |

### 命令行与终端

| 模块 | 描述 | 性能对标 |
|------|------|---------|
| [ANSI 终端样式](modules/ansi.md) | ANSI 终端样式：颜色、属性、检测、strip/visible_len | — |
| [表格格式化](modules/tabulate.md) | 多种输出样式的表格格式化 | `tabulate` |
| [交互式提示](modules/prompt.md) | 交互式 CLI 提示（confirm、select、text） | `questionary` |

### 安全与编码

| 模块 | 描述 | 性能对标 |
|------|------|---------|
| [AES 加密](modules/aes.md) | AES 加密：ECB、CBC、CTR、GCM 模式（纯 Python + OpenSSL ctypes） | `pycryptodome` |
| [QR 二维码](modules/qr.md) | QR Code 生成与终端渲染 | `qrcode` |

### 基础设施与工具

| 模块 | 描述 | 性能对标 |
|------|------|---------|
| [重试](modules/retry.md) | 装饰器式自动重试（退避、抖动、过滤） | `tenacity` |
| [任务调度器](modules/scheduler.md) | 进程内任务调度器（cron、间隔、一次性触发） | `APScheduler` |
| [结构化日志](modules/structlog.md) | 结构化日志与彩色控制台输出 | `structlog` |
| [VCS 版本控制](modules/vcs.md) | Git/Hg/Jujutsu CLI 包装器（diff、status、log、blame） | — |

## 设计理念

- **零外部依赖** —— 仅使用 Python 标准库
- **单文件** —— 复制一个 `.py` 文件到你的项目即可
- **Python 3.10+** —— 利用现代 Python 特性
- **正确性优先** —— 与参考库进行 apple-to-apple 测试
- **性能对等** —— 与流行替代方案进行基准测试
