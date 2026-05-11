# CDP Client

Zero-dependency Chrome DevTools Protocol client for headless browser automation -- sync + async, stdlib only, Python 3.10+.

> **Replaces:** `pychrome`, `pycdp`

## Overview

The cdp module provides synchronous and asynchronous CDP clients for communicating with Chrome/Chromium-based browsers over WebSocket. It supports tab management, page navigation, JavaScript evaluation, and high-level rendered content extraction. Built on top of the sibling `websocket` module.

| File | Description | Dependencies |
|------|-------------|--------------|
| `cdp.py` | Pure Python implementation | `websocket` module (sibling) |

## Features

- **High-level API** -- `get_rendered_text()` and `get_rendered_html()` for one-call content extraction
- **Low-level API** -- `send_command()` for arbitrary CDP method calls with command/response ID matching
- **Tab management** -- `create_target()`, `close_target()` for multi-tab workflows
- **Page navigation** -- `navigate()` with automatic `Page.loadEventFired` waiting
- **JavaScript evaluation** -- `evaluate()` with error propagation from browser exceptions
- **User-Agent override** -- `set_user_agent()` per target
- **Auto-discovery** -- automatically discovers browser debugger WebSocket URL via `/json/version`
- **Event buffering** -- non-matching events buffered during command/response waiting
- **Sync + async clients** -- `CDPClient` and `AsyncCDPClient` with identical APIs
- **Context manager** -- `with` / `async with` for automatic connect and cleanup

## How to Use in Your Project

Copy both files into your project (cdp depends on websocket):

```bash
zerodep add cdp
# or manually:
cp websocket/websocket.py your_project/
cp cdp/cdp.py your_project/
```

Then import directly:

```python
from cdp import CDPClient, AsyncCDPClient
```

## Usage Examples

### Extract Rendered Text (One-Call)

```python
from cdp import CDPClient

# Start Chrome: chrome --headless --remote-debugging-port=9222
with CDPClient("ws://localhost:9222") as client:
    text = client.get_rendered_text("https://react.dev", timeout=15)
    print(text)
```

### Extract Rendered HTML

```python
from cdp import CDPClient

with CDPClient("ws://localhost:9222") as client:
    html = client.get_rendered_html("https://example.com")
    print(html[:200])
```

### Low-Level Target Management

```python
from cdp import CDPClient

with CDPClient("ws://localhost:9222") as client:
    target_id = client.create_target("https://example.com")
    client.navigate(target_id, "https://example.com")

    # Evaluate JavaScript
    title = client.evaluate(target_id, "document.title")
    print(f"Page title: {title}")

    html = client.evaluate(target_id, "document.documentElement.outerHTML")
    print(f"HTML length: {len(html)}")

    client.close_target(target_id)
```

### Multi-Tab Workflow

```python
from cdp import CDPClient

with CDPClient("ws://localhost:9222") as client:
    urls = ["https://example.com", "https://httpbin.org", "https://google.com"]
    targets = []

    # Open multiple tabs
    for url in urls:
        tid = client.create_target()
        client.navigate(tid, url)
        targets.append(tid)

    # Extract content from all tabs
    for tid in targets:
        text = client.evaluate(tid, "document.body.innerText")
        print(f"Target {tid}: {len(text)} chars")

    # Close all tabs
    for tid in targets:
        client.close_target(tid)
```

### User-Agent Override

```python
from cdp import CDPClient

with CDPClient("ws://localhost:9222") as client:
    target_id = client.create_target()
    client.set_user_agent(target_id, "MyBot/1.0")
    client.navigate(target_id, "https://httpbin.org/user-agent")
    result = client.evaluate(target_id, "document.body.innerText")
    print(result)
    client.close_target(target_id)
```

### Async Client

```python
import asyncio
from cdp import AsyncCDPClient

async def main():
    async with AsyncCDPClient("ws://localhost:9222") as client:
        text = await client.get_rendered_text("https://example.com")
        print(text)

asyncio.run(main())
```

### Auto-Discovery via /json/version

```python
from cdp import CDPClient

# Just provide host:port — the client auto-discovers the WebSocket URL
with CDPClient("ws://localhost:9222") as client:
    text = client.get_rendered_text("https://example.com")
```

## API Reference

### `CDPClient(url, *, timeout=30.0)`

Synchronous Chrome DevTools Protocol client.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | `str` | -- | CDP WebSocket endpoint URL (e.g. `ws://localhost:9222`) |
| `timeout` | `float` | `30.0` | Default timeout for CDP commands |

**Connection Methods:**

| Method | Description |
|--------|-------------|
| `connect(*, timeout=None)` | Open WebSocket connection to CDP endpoint |
| `close()` | Close all targets and the WebSocket connection |

**High-Level Methods:**

| Method | Description |
|--------|-------------|
| `get_rendered_text(url, *, timeout=None) -> str` | Navigate and extract `document.body.innerText` |
| `get_rendered_html(url, *, timeout=None) -> str` | Navigate and extract `document.documentElement.outerHTML` |

**Target Management:**

| Method | Description |
|--------|-------------|
| `create_target(url="about:blank") -> str` | Create and attach to a new browser tab, returns target ID |
| `close_target(target_id)` | Close a browser tab |
| `navigate(target_id, url, *, timeout=None)` | Navigate a target to a URL and wait for page load |
| `wait_for_load(target_id, *, timeout=None)` | Wait for a target's page to finish loading |

**Evaluation & Configuration:**

| Method | Description |
|--------|-------------|
| `evaluate(target_id, expression) -> object` | Evaluate JavaScript in a target |
| `set_user_agent(target_id, user_agent)` | Override User-Agent for a target |
| `send_command(method, params=None, *, session_id=None, timeout=None) -> dict` | Send a raw CDP command |

---

### `AsyncCDPClient(url, *, timeout=30.0)`

Asynchronous Chrome DevTools Protocol client. Same constructor parameters as `CDPClient`. All methods are `async`.

---

### Exceptions

| Exception | Description |
|-----------|-------------|
| `CDPError` | Base exception for all CDP operations |
| `CDPConnectionError` | WebSocket connection failures to the CDP endpoint |
| `CDPTimeoutError` | CDP operation timed out |
| `CDPProtocolError` | CDP error response from the browser |

---

### Constants

| Constant | Value | Description |
|----------|-------|-------------|
| `DEFAULT_TIMEOUT` | `30.0` | Default command timeout (seconds) |
| `DEFAULT_PAGE_LOAD_TIMEOUT` | `30.0` | Default page load timeout (seconds) |

## Comparison with websockets + manual CDP

| Feature | zerodep cdp | websockets + manual |
|---------|-------------|---------------------|
| Dependencies | None (stdlib only) | websockets (pip) |
| High-level API | `get_rendered_text()` | Manual command sequencing |
| Tab management | Built-in `create_target()` / `close_target()` | Manual Target domain commands |
| Event buffering | Automatic | Must implement yourself |
| ID matching | Automatic command/response correlation | Must track IDs yourself |
| Auto-discovery | `/json/version` auto-probe | Manual endpoint lookup |
| Sync + async | Both included | websockets async only (sync wrapper) |
| File size | ~900 lines + websocket module | Varies |

**When to use zerodep cdp:** You need to extract rendered content from SPAs, automate browser tasks, or communicate with CDP-compatible browsers without Selenium/Playwright dependencies.

**When to use Playwright/Selenium:** You need cross-browser testing, complex user interaction simulation, or a mature ecosystem with extensive documentation.

## Benchmark

Benchmarked against mock CDP server across full render pipeline (create → navigate → evaluate → close), multi-target scenarios, JavaScript evaluation throughput, and command throughput.

See [CDP Benchmark](../benchmarks/cdp.md) for detailed results.
