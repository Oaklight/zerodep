# User-Agent 生成器

零依赖的 Chrome/Edge User-Agent 字符串生成器，附带 Client Hints 头部，仅标准库，Python 3.10+。

> **可替代:** `fake-useragent`、`ua-generator`、`user-agents`

## 概述

useragent 模块生成逼真的浏览器 User-Agent 字符串和对应的 `Sec-CH-UA-*` Client Hints 头部，覆盖 Chrome 和 Edge 浏览器在 Windows、macOS、Linux 和 Android 平台上的组合。

| 文件 | 说明 | 依赖 |
|------|------|------|
| `useragent.py` | 纯 Python 实现 | 无（仅标准库：`random`） |

## 功能特性

- **Chrome + Edge** —— 生成逼真的 UA 字符串，版本范围和平台标识均符合真实浏览器格式
- **桌面 + 移动** —— 覆盖 Windows、macOS、Linux（桌面）和 Android（移动），各平台格式正确
- **Client Hints** —— 完整的 `Sec-CH-UA-*` 头部支持：低熵（始终包含）和高熵（通过 `accept_ch()`）
- **确定性模式** —— 通过 seed `random` 实现可重现输出，适用于测试
- **轻量级** —— 单文件，约 470 行，仅使用标准库 `random`

## 快速开始

### 复制文件

```bash
cp useragent/useragent.py your_project/
```

然后直接导入：

```python
from useragent import generate
```

## 使用示例

### 基本生成

```python
from useragent import generate

ua = generate()
print(ua.text)
# Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ...
print(ua.browser)   # "chrome" 或 "edge"
print(ua.platform)  # "windows"、"macos"、"linux" 或 "android"
print(ua.version)   # (136, 0, 7103, 42)
```

### 指定浏览器和设备

```python
from useragent import generate

# 仅 Chrome 桌面
ua = generate(browser="chrome", device="desktop")
assert ua.browser == "chrome"
assert ua.platform in ("windows", "macos", "linux")

# 仅 Edge 移动端
ua = generate(browser="edge", device="mobile")
assert ua.platform == "android"
assert "EdgA/" in ua.text
```

### 从多个浏览器中随机选择

```python
from useragent import generate

# 从给定列表中随机选择
ua = generate(browser=["chrome", "edge"])
```

### 默认 Client Hints 头部

```python
from useragent import generate

ua = generate(browser="chrome", device="desktop")
headers = ua.headers.get()
# {
#   "user-agent": "Mozilla/5.0 ...",
#   "sec-ch-ua": '"Not A(Brand";v="99", "Chromium";v="136", "Google Chrome";v="136"',
#   "sec-ch-ua-mobile": "?0",
#   "sec-ch-ua-platform": '"Windows"',
# }
```

### 通过 Accept-CH 获取高熵 Hints

```python
from useragent import generate

ua = generate(browser="chrome")
ua.headers.accept_ch("Sec-CH-UA-Platform-Version, Sec-CH-UA-Arch, Sec-CH-UA-Bitness")
headers = ua.headers.get()
# 现在还包含：
#   "sec-ch-ua-platform-version": '"15.0.0"'
#   "sec-ch-ua-arch": '"x86"'
#   "sec-ch-ua-bitness": '"64"'
```

### 完整版本品牌列表

```python
from useragent import generate

ua = generate(browser="chrome")
ua.headers.accept_ch("Sec-CH-UA-Full-Version-List")
headers = ua.headers.get()
# "sec-ch-ua-full-version-list": '"Not A(Brand";v="99.0.0.0", "Chromium";v="136.0.7103.42", ...'
```

### 确定性输出（测试用）

```python
import random
from useragent import generate

random.seed(42)
ua1 = generate(browser="chrome", device="desktop")

random.seed(42)
ua2 = generate(browser="chrome", device="desktop")

assert ua1.text == ua2.text
```

### 配合 HTTP 请求使用

```python
from useragent import generate
import urllib.request

ua = generate(browser="chrome", device="desktop")
req = urllib.request.Request("https://example.com")
for key, value in ua.headers.get().items():
    req.add_header(key, value)
```

## Client Hints 支持

### 低熵 Hints（始终包含）

无需调用 `accept_ch()` 即可在 `headers.get()` 中获得：

| 头部 | 说明 | 示例 |
|------|------|------|
| `sec-ch-ua` | 品牌列表（主版本号） | `"Chromium";v="136", "Google Chrome";v="136"` |
| `sec-ch-ua-mobile` | 移动端标识 | `?0`（桌面）/ `?1`（移动端） |
| `sec-ch-ua-platform` | 平台名称 | `"Windows"`、`"macOS"`、`"Linux"`、`"Android"` |

### 高熵 Hints（通过 `accept_ch()`）

调用 `ua.headers.accept_ch(hint_names)` 以添加：

| Hint 名称 | 头部 | 可能的值 |
|-----------|------|----------|
| `Sec-CH-UA-Platform-Version` | `sec-ch-ua-platform-version` | `"15.0.0"`、`"10.0.0"` 等 |
| `Sec-CH-UA-Full-Version-List` | `sec-ch-ua-full-version-list` | 完整 `x.y.z.w` 品牌列表 |
| `Sec-CH-UA-Arch` | `sec-ch-ua-arch` | `"x86"`、`"arm"` |
| `Sec-CH-UA-Bitness` | `sec-ch-ua-bitness` | `"64"`、`"32"` |
| `Sec-CH-UA-Model` | `sec-ch-ua-model` | `""`（桌面）/ `"SM-S928B"`（移动端） |

## API 参考

### `generate(*, browser=None, device=None)`

生成随机 User-Agent 及对应的 Client Hints。

**参数：**

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `browser` | `str \| list[str] \| None` | `None` | 浏览器名称。支持：`"chrome"`、`"edge"`。`None` = 随机选择。 |
| `device` | `str \| None` | `None` | `"desktop"` 或 `"mobile"`。`None` = 随机选择所有平台。 |

**返回：** `UserAgent` 实例。

**异常：** 若浏览器不是 `"chrome"` 或 `"edge"` 则抛出 `ValueError`。

---

### `UserAgent`

| 属性 | 类型 | 说明 |
|------|------|------|
| `browser` | `str` | `"chrome"` 或 `"edge"` |
| `platform` | `str` | `"windows"`、`"macos"`、`"linux"` 或 `"android"` |
| `version` | `tuple[int, int, int, int]` | `(major, minor, build, patch)` |
| `text` | `str` | 完整的 User-Agent 字符串 |
| `headers` | `_Headers` | Client Hints 头部构建器 |

**方法：**

| 方法 | 说明 |
|------|------|
| `str(ua)` | 返回 `ua.text` |
| `repr(ua)` | `UserAgent(browser='chrome', platform='windows')` |

---

### `_Headers`

| 方法 | 说明 |
|------|------|
| `get()` | 返回所有头部的 `dict[str, str]` |
| `accept_ch(hints)` | 处理 `Accept-CH` 值并填充对应的高熵 hints |

## 与 ua-generator 的对比

| 特性 | zerodep useragent | ua-generator |
|------|-------------------|--------------|
| 依赖 | 无（仅标准库） | 无 |
| 浏览器 | Chrome、Edge | Chrome、Edge、Firefox、Safari |
| 平台 | Windows、macOS、Linux、Android | Windows、macOS、Linux、Android、iOS |
| Client Hints | 完整低熵 + 高熵 | 完整低熵 + 高熵 |
| 生成速度 | ~3.1 μs | ~8.6 μs |
| Headers 速度 | ~5.2 μs | ~11.6 μs |
| 实现 | 单文件（约 470 行） | 包（多文件） |

**何时使用 zerodep：** 只需 Chrome/Edge UA 字符串（覆盖 85%+ 的 Web 流量），需要零依赖，偏好单文件即拷即用。

**何时使用 ua-generator：** 需要 Firefox/Safari 支持或 iOS 平台覆盖。

## 性能测试

与 `ua-generator` 在默认生成、指定浏览器和 Headers 生成场景下的性能对比。

详见 [User-Agent 生成器性能测试](../benchmarks/useragent.md)。
