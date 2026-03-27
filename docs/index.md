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

| 模块 | 描述 | 性能对标 |
|------|------|---------|
| [AES 加密](modules/aes.md) | AES-128-ECB 加密（纯 Python + OpenSSL ctypes） | `pycryptodome` |
| [QR 二维码](modules/qr.md) | QR Code 生成与终端渲染 | `qrcode` |
| [HTTP 客户端](modules/http.md) | 同步 + 异步 REST 客户端 | `httpx` |
| [Dotenv 环境变量](modules/dotenv.md) | .env 文件解析（load_dotenv, dotenv_values） | `python-dotenv` |
| [YAML 解析器](modules/yaml.md) | YAML 解析与序列化（常用子集） | `PyYAML` |
| [JSONC 解析器](modules/jsonc.md) | JSONC 解析（JSON + 注释 + 尾逗号） | `commentjson` |
| [结构化日志](modules/structlog.md) | 结构化日志与彩色控制台输出 | `structlog` |
| [重试](modules/retry.md) | 装饰器式自动重试（退避、抖动、过滤） | `tenacity` |

## 设计理念

- **零外部依赖** —— 仅使用 Python 标准库
- **单文件** —— 复制一个 `.py` 文件到你的项目即可
- **Python 3.10+** —— 利用现代 Python 特性
- **正确性优先** —— 与参考库进行 apple-to-apple 测试
- **性能对等** —— 与流行替代方案进行基准测试
