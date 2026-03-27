---
title: Home
hide:
  - navigation
---

# zerodep

Zero-dependency, single-file Python implementations of popular libraries — stdlib only, Python 3.10+.

## Overview

Each module is a **self-contained single file** that you can copy directly into your project. No `pip install` required.

## Available Modules

| Module | Description | Benchmark Against |
|--------|-------------|-------------------|
| [AES](modules/aes.md) | AES-128-ECB encryption (pure Python + OpenSSL via ctypes) | `pycryptodome` |
| [QR Code](modules/qr.md) | QR Code generation with terminal rendering | `qrcode` |
| [HTTP Client](modules/http.md) | Sync + async REST client | `httpx` |

## Philosophy

- **Zero external dependencies** — only Python standard library
- **Single file** — copy one `.py` file into your project
- **Python 3.10+** — leverages modern Python features
- **Correctness first** — apple-to-apple tests against reference libraries
- **Performance parity** — benchmarked against popular alternatives
