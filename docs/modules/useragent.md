# User-Agent Generator

Zero-dependency Chrome/Edge User-Agent string generator with Client Hints headers -- stdlib only, Python 3.10+.

> **Replaces:** `fake-useragent`, `ua-generator`, `user-agents`

## Overview

The useragent module generates realistic browser User-Agent strings and matching `Sec-CH-UA-*` Client Hints headers for Chrome and Edge browsers across Windows, macOS, Linux, and Android platforms.

| File | Description | Dependencies |
|------|-------------|--------------|
| `useragent.py` | Pure Python implementation | None (stdlib only: `random`) |

## Features

- **Chrome + Edge** -- generates realistic UA strings for both browsers, including correct version ranges and platform tokens
- **Desktop + Mobile** -- covers Windows, macOS, Linux (desktop) and Android (mobile) with platform-specific formatting
- **Client Hints** -- full `Sec-CH-UA-*` header support: low-entropy (always included) and high-entropy (via `accept_ch()`)
- **Deterministic mode** -- seed `random` for reproducible output in tests
- **Lightweight** -- single file, ~470 lines, stdlib `random` only

## How to Use in Your Project

Copy the single `.py` file into your project:

```bash
cp useragent/useragent.py your_project/
```

Then import directly:

```python
from useragent import generate
```

## Usage Examples

### Basic Generation

```python
from useragent import generate

ua = generate()
print(ua.text)
# Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ...
print(ua.browser)   # "chrome" or "edge"
print(ua.platform)  # "windows", "macos", "linux", or "android"
print(ua.version)   # (136, 0, 7103, 42)
```

### Specify Browser and Device

```python
from useragent import generate

# Chrome desktop only
ua = generate(browser="chrome", device="desktop")
assert ua.browser == "chrome"
assert ua.platform in ("windows", "macos", "linux")

# Edge mobile only
ua = generate(browser="edge", device="mobile")
assert ua.platform == "android"
assert "EdgA/" in ua.text
```

### Pick from Multiple Browsers

```python
from useragent import generate

# Random choice from the given list
ua = generate(browser=["chrome", "edge"])
```

### Default Client Hints Headers

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

### High-Entropy Hints via Accept-CH

```python
from useragent import generate

ua = generate(browser="chrome")
ua.headers.accept_ch("Sec-CH-UA-Platform-Version, Sec-CH-UA-Arch, Sec-CH-UA-Bitness")
headers = ua.headers.get()
# Now also includes:
#   "sec-ch-ua-platform-version": '"15.0.0"'
#   "sec-ch-ua-arch": '"x86"'
#   "sec-ch-ua-bitness": '"64"'
```

### Full-Version Brand List

```python
from useragent import generate

ua = generate(browser="chrome")
ua.headers.accept_ch("Sec-CH-UA-Full-Version-List")
headers = ua.headers.get()
# "sec-ch-ua-full-version-list": '"Not A(Brand";v="99.0.0.0", "Chromium";v="136.0.7103.42", ...'
```

### Deterministic Output (Testing)

```python
import random
from useragent import generate

random.seed(42)
ua1 = generate(browser="chrome", device="desktop")

random.seed(42)
ua2 = generate(browser="chrome", device="desktop")

assert ua1.text == ua2.text
```

### Use with HTTP Requests

```python
from useragent import generate
import urllib.request

ua = generate(browser="chrome", device="desktop")
req = urllib.request.Request("https://example.com")
for key, value in ua.headers.get().items():
    req.add_header(key, value)
```

## Client Hints Support

### Low-Entropy Hints (Always Included)

These are always present in `headers.get()` without calling `accept_ch()`:

| Header | Description | Example |
|--------|-------------|---------|
| `sec-ch-ua` | Brand list with major version | `"Chromium";v="136", "Google Chrome";v="136"` |
| `sec-ch-ua-mobile` | Mobile flag | `?0` (desktop) / `?1` (mobile) |
| `sec-ch-ua-platform` | Platform name | `"Windows"`, `"macOS"`, `"Linux"`, `"Android"` |

### High-Entropy Hints (via `accept_ch()`)

Call `ua.headers.accept_ch(hint_names)` to add these:

| Hint Name | Header | Values |
|-----------|--------|--------|
| `Sec-CH-UA-Platform-Version` | `sec-ch-ua-platform-version` | `"15.0.0"`, `"10.0.0"`, etc. |
| `Sec-CH-UA-Full-Version-List` | `sec-ch-ua-full-version-list` | Full `x.y.z.w` brand list |
| `Sec-CH-UA-Arch` | `sec-ch-ua-arch` | `"x86"`, `"arm"` |
| `Sec-CH-UA-Bitness` | `sec-ch-ua-bitness` | `"64"`, `"32"` |
| `Sec-CH-UA-Model` | `sec-ch-ua-model` | `""` (desktop) / `"SM-S928B"` (mobile) |

## API Reference

### `generate(*, browser=None, device=None)`

Generate a random User-Agent with matching Client Hints.

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `browser` | `str \| list[str] \| None` | `None` | Browser name(s). Supported: `"chrome"`, `"edge"`. `None` = random. |
| `device` | `str \| None` | `None` | `"desktop"` or `"mobile"`. `None` = random across all platforms. |

**Returns:** `UserAgent` instance.

**Raises:** `ValueError` if browser is not `"chrome"` or `"edge"`.

---

### `UserAgent`

| Attribute | Type | Description |
|-----------|------|-------------|
| `browser` | `str` | `"chrome"` or `"edge"` |
| `platform` | `str` | `"windows"`, `"macos"`, `"linux"`, or `"android"` |
| `version` | `tuple[int, int, int, int]` | `(major, minor, build, patch)` |
| `text` | `str` | Full User-Agent string |
| `headers` | `_Headers` | Client Hints header builder |

**Methods:**

| Method | Description |
|--------|-------------|
| `str(ua)` | Returns `ua.text` |
| `repr(ua)` | `UserAgent(browser='chrome', platform='windows')` |

---

### `_Headers`

| Method | Description |
|--------|-------------|
| `get()` | Return all headers as `dict[str, str]` |
| `accept_ch(hints)` | Process `Accept-CH` value and populate matching high-entropy hints |

## Comparison with ua-generator

| Feature | zerodep useragent | ua-generator |
|---------|-------------------|--------------|
| Dependencies | None (stdlib only) | None |
| Browsers | Chrome, Edge | Chrome, Edge, Firefox, Safari |
| Platforms | Windows, macOS, Linux, Android | Windows, macOS, Linux, Android, iOS |
| Client Hints | Full low + high entropy | Full low + high entropy |
| Generation speed | ~3.1 μs | ~8.6 μs |
| Headers speed | ~5.2 μs | ~11.6 μs |
| Implementation | Single file (~470 lines) | Package (multiple files) |

**When to use zerodep:** You only need Chrome/Edge UA strings (covers 85%+ of web traffic), want zero dependencies, and prefer a single-file drop-in.

**When to use ua-generator:** You need Firefox/Safari support or iOS platform coverage.

## Benchmark

Benchmarked against `ua-generator` across default generation, browser-specific, and headers generation.

See [User-Agent Generator Benchmark](../benchmarks/useragent.md) for detailed results.
