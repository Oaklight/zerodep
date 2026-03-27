# Structured Logging

Zero-dependency structured logging with pretty console output -- stdlib only, Python 3.10+.

## Overview

The Structured Logging module provides a drop-in replacement for `structlog` core functionality. It offers bound loggers with context propagation, a processor pipeline, and multiple output renderers (console, JSON, key-value) -- all without any third-party dependencies.

| File | Description | Dependencies |
|------|-------------|--------------|
| `structlog.py` | Pure Python implementation | None (stdlib only) |

The module supports loguru-style colorized console output, JSON rendering for production, key-value rendering, custom processor pipelines, stdlib `logging` integration, and context propagation through bound loggers.

## How to Use in Your Project

Just copy the single `.py` file into your project:

```bash
cp structlog/structlog.py your_project/
```

Then import directly:

```python
from structlog import get_logger, setup_logging, configure
```

## API Reference

### `get_logger(*args, **initial_values)`

Create a `BoundLogger` using the global configuration.

```python
def get_logger(
    *args: Any,
    **initial_values: Any,
) -> BoundLogger
```

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `*args` | `Any` | -- | Forwarded to the logger factory (e.g. a logger name). |
| `**initial_values` | `Any` | -- | Key-value pairs that become the initial bound context. |

**Returns:** `BoundLogger` -- A configured bound logger.

**Example:**

```python
from structlog import get_logger

# Zero-config quick start
logger = get_logger()
logger.info("server started", host="0.0.0.0", port=8080)

# With initial context
logger = get_logger(service="auth")
```

---

### `setup_logging(level, renderer, colors, processors, logger_name, stream)`

One-call logging setup with stdlib integration.

```python
def setup_logging(
    level: int | str = logging.INFO,
    renderer: str = "console",
    colors: bool | None = None,
    processors: list[Processor] | None = None,
    logger_name: str | None = None,
    stream: IO[str] | None = None,
) -> BoundLogger
```

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `level` | `int \| str` | `logging.INFO` | Log level (name or int). |
| `renderer` | `str` | `"console"` | Output renderer: `"console"`, `"json"`, or `"kv"`. |
| `colors` | `bool \| None` | `None` | Enable ANSI colors. `None` auto-detects terminal support. |
| `processors` | `list[Processor] \| None` | `None` | Custom processor list. Overrides `renderer` if given. |
| `logger_name` | `str \| None` | `None` | stdlib logger name. |
| `stream` | `IO[str] \| None` | `None` | Output stream. Defaults to `sys.stderr`. |

**Returns:** `BoundLogger` -- A ready-to-use bound logger.

**Example:**

```python
from structlog import setup_logging

# Console output with DEBUG level
logger = setup_logging(level="DEBUG")

# JSON output for production
logger = setup_logging(renderer="json")

# Key-value output
logger = setup_logging(renderer="kv", level="WARNING")
```

---

### `configure(processors, wrapper_class, context_class, logger_factory, cache_logger_on_first_use)`

Override the global configuration.

```python
def configure(
    processors: list[Processor] | None = None,
    wrapper_class: type[BoundLogger] | None = None,
    context_class: type[dict] | None = None,
    logger_factory: LoggerFactory | None = None,
    cache_logger_on_first_use: bool | None = None,
) -> None
```

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `processors` | `list[Processor] \| None` | `None` | Ordered processor list. |
| `wrapper_class` | `type[BoundLogger] \| None` | `None` | BoundLogger subclass to use. |
| `context_class` | `type[dict] \| None` | `None` | Dict-like class for context storage. |
| `logger_factory` | `LoggerFactory \| None` | `None` | Factory for the underlying logger. |
| `cache_logger_on_first_use` | `bool \| None` | `None` | Cache loggers returned by `get_logger()`. |

**Returns:** `None`

**Example:**

```python
from structlog import configure, add_log_level, TimeStamper, JSONRenderer

configure(
    processors=[add_log_level, TimeStamper(), JSONRenderer()],
)
```

---

### `reset_defaults()`

Restore the global configuration to factory defaults.

```python
def reset_defaults() -> None
```

**Returns:** `None`

**Example:**

```python
from structlog import reset_defaults

reset_defaults()
```

---

### `wrap_logger(logger, processors, **initial_values)`

Wrap an existing logger with a processor pipeline.

```python
def wrap_logger(
    logger: Any,
    processors: list[Processor] | None = None,
    **initial_values: Any,
) -> BoundLogger
```

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `logger` | `Any` | -- | Any object with `debug`/`info`/... methods. |
| `processors` | `list[Processor] \| None` | `None` | Processor list. Defaults to the global config. |
| `**initial_values` | `Any` | -- | Initial bound context. |

**Returns:** `BoundLogger` -- A bound logger wrapping the given logger.

**Example:**

```python
import logging
from structlog import wrap_logger, add_log_level, ConsoleRenderer

stdlib_logger = logging.getLogger("myapp")
logger = wrap_logger(stdlib_logger, processors=[add_log_level, ConsoleRenderer()])
logger.info("wrapped stdlib logger")
```

---

### `BoundLogger`

A logger that carries bound context through a processor pipeline. Do not instantiate directly; use `get_logger()` or `wrap_logger()` instead.

#### `bind(**new_values)`

Return a new logger with `new_values` merged into the context.

```python
def bind(self, **new_values: Any) -> BoundLogger
```

#### `unbind(*keys)`

Return a new logger with `keys` removed from the context.

```python
def unbind(self, *keys: str) -> BoundLogger
```

#### `new(**new_values)`

Return a new logger with `new_values` replacing the context entirely.

```python
def new(self, **new_values: Any) -> BoundLogger
```

#### Log Methods

All log methods accept an optional positional `event` string and arbitrary keyword arguments:

```python
def debug(self, event: str | None = None, /, **kw: Any) -> None
def info(self, event: str | None = None, /, **kw: Any) -> None
def warning(self, event: str | None = None, /, **kw: Any) -> None
def error(self, event: str | None = None, /, **kw: Any) -> None
def critical(self, event: str | None = None, /, **kw: Any) -> None
def exception(self, event: str | None = None, /, **kw: Any) -> None
def log(self, level: int, event: str | None = None, /, **kw: Any) -> None
```

- `exception()` automatically sets `exc_info=True`.
- `log()` accepts a numeric level (e.g. `logging.WARNING`).

**Example:**

```python
from structlog import get_logger

log = get_logger().bind(request_id="abc-123")
log.info("handling request")

log = log.bind(user_id=42)
log.info("authenticated")

log = log.unbind("user_id")
log.info("context without user_id")
```

---

### Processors

#### `add_log_level`

Add a `level` key derived from the log method name.

```python
def add_log_level(
    logger: Any,
    method_name: str,
    event_dict: EventDict,
) -> EventDict
```

Calling `logger.info(...)` will set `event_dict["level"] = "info"`.

---

#### `add_logger_name`

Add a `logger` key from the underlying logger's name.

```python
def add_logger_name(
    logger: Any,
    method_name: str,
    event_dict: EventDict,
) -> EventDict
```

---

#### `TimeStamper(fmt, utc, key)`

Processor that adds a timestamp to the event dict.

```python
class TimeStamper:
    def __init__(
        self,
        fmt: str | None = "iso",
        utc: bool = True,
        key: str = "timestamp",
    ) -> None
```

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `fmt` | `str \| None` | `"iso"` | Timestamp format. `"iso"` for ISO 8601, `None` for a UNIX float, or a `strftime` format string. |
| `utc` | `bool` | `True` | If `True`, use UTC; otherwise local time. |
| `key` | `str` | `"timestamp"` | Dict key for the timestamp. |

**Example:**

```python
from structlog import configure, add_log_level, TimeStamper, ConsoleRenderer

# ISO 8601 UTC timestamps (default)
configure(processors=[add_log_level, TimeStamper(), ConsoleRenderer()])

# Custom format with local time
configure(processors=[add_log_level, TimeStamper(fmt="%H:%M:%S", utc=False), ConsoleRenderer()])
```

---

#### `format_exc_info`

Replace `exc_info` with a formatted `exception` string.

```python
def format_exc_info(
    logger: Any,
    method_name: str,
    event_dict: EventDict,
) -> EventDict
```

If `exc_info` is `True`, captures the current exception via `sys.exc_info()`. If it is an exception tuple, formats it directly. The `exc_info` key is removed and replaced with `exception`.

---

### Renderers

#### `ConsoleRenderer(colors, pad_event, level_styles)`

Render the event dict as colorized, loguru-style console output.

```python
class ConsoleRenderer:
    def __init__(
        self,
        colors: bool | None = None,
        pad_event: int = 30,
        level_styles: dict[str, str] | None = None,
    ) -> None
```

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `colors` | `bool \| None` | `None` | Enable ANSI color codes. `None` auto-detects terminal support. |
| `pad_event` | `int` | `30` | Pad the event field to this width for alignment. |
| `level_styles` | `dict[str, str] \| None` | `None` | Override per-level ANSI color strings. |

Output format:

```
2026-03-27 14:30:00.123 | INFO     | event message    key=val key=val
```

---

#### `JSONRenderer(serializer, **dumps_kw)`

Render the event dict as a JSON string.

```python
class JSONRenderer:
    def __init__(
        self,
        serializer: Callable[..., str] = json.dumps,
        **dumps_kw: Any,
    ) -> None
```

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `serializer` | `Callable[..., str]` | `json.dumps` | JSON serialization function. |
| `**dumps_kw` | `Any` | -- | Extra keyword arguments passed to `serializer`. |

Automatically handles `datetime`, `date`, `set`, `frozenset`, and `bytes` objects.

---

#### `KeyValueRenderer(key_order, sort_keys, drop_missing)`

Render the event dict as `key=value` pairs.

```python
class KeyValueRenderer:
    def __init__(
        self,
        key_order: list[str] | None = None,
        sort_keys: bool = False,
        drop_missing: bool = True,
    ) -> None
```

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `key_order` | `list[str] \| None` | `None` | Keys to render first, in this order. |
| `sort_keys` | `bool` | `False` | Sort remaining keys alphabetically. |
| `drop_missing` | `bool` | `True` | Skip `key_order` keys that are absent from the dict. |

---

### Logger Factories

#### `PrintLogger(file)`

Minimal logger that writes to a file handle via `print()`. This is the default underlying logger.

```python
class PrintLogger:
    def __init__(self, file: IO[str] | None = None) -> None
```

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `file` | `IO[str] \| None` | `None` | Output stream. Defaults to `sys.stderr`. |

---

#### `PrintLoggerFactory(file)`

Factory that creates `PrintLogger` instances.

```python
class PrintLoggerFactory:
    def __init__(self, file: IO[str] | None = None) -> None
```

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `file` | `IO[str] \| None` | `None` | Output stream passed to each `PrintLogger`. |

---

#### `StdlibLoggerFactory(name)`

Factory that returns a `logging.Logger` from the stdlib.

```python
class StdlibLoggerFactory:
    def __init__(self, name: str | None = None) -> None
```

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `name` | `str \| None` | `None` | Logger name passed to `logging.getLogger()`. If `None`, uses the root logger. |

---

### Exceptions

#### `DropEvent`

Raise inside a processor to silently discard the current log event.

```python
class DropEvent(Exception)
```

**Example:**

```python
from structlog import DropEvent

def filter_debug(logger, method_name, event_dict):
    if method_name == "debug":
        raise DropEvent
    return event_dict
```

---

### Utilities

#### `truncate_string(s, max_length, suffix)`

Truncate a string to `max_length`, appending a count of remaining chars.

```python
def truncate_string(
    s: str,
    max_length: int,
    suffix: str = "...",
) -> str
```

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `s` | `str` | -- | The string to truncate. |
| `max_length` | `int` | -- | Maximum number of characters to keep. |
| `suffix` | `str` | `"..."` | Separator between the kept text and the count. |

**Returns:** `str` -- The original string if short enough, otherwise truncated with a `"...[N more chars]"` suffix.

**Example:**

```python
from structlog import truncate_string

truncate_string("hello world", 5)  # "hello...[6 more chars]"
```

---

#### `truncate_base64(data_url, max_length)`

Truncate base64 data-URLs for cleaner logging.

```python
def truncate_base64(
    data_url: str,
    max_length: int = 100,
) -> str
```

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `data_url` | `str` | -- | A `data:` URL or any string. |
| `max_length` | `int` | `100` | Maximum base64 payload chars to keep. |

**Returns:** `str` -- The truncated URL, or the original string if not a data-URL.

## Usage Examples

### Zero-Config Quick Start

```python
from structlog import get_logger

logger = get_logger()
logger.info("server started", host="0.0.0.0", port=8080)
logger.debug("loading config", path="/etc/app/config.yaml")
logger.error("connection failed", db="postgres", retries=3)
```

### Bound Logger Context Propagation

```python
from structlog import get_logger

log = get_logger().bind(request_id="abc-123")
log.info("handling request")

log = log.bind(user_id=42)
log.info("authenticated")

# Start fresh context
log = log.new(request_id="def-456")
log.info("new request")
```

### One-Call Setup with `setup_logging()`

```python
from structlog import setup_logging

# Pretty console output with DEBUG level
logger = setup_logging(level="DEBUG")
logger.info("application started")

# JSON output for production
logger = setup_logging(renderer="json", level="WARNING")
logger.warning("disk usage high", percent=92.5)
```

### JSON Output for Production

```python
from structlog import configure, get_logger, add_log_level, TimeStamper, JSONRenderer

configure(
    processors=[
        add_log_level,
        TimeStamper(),
        JSONRenderer(sort_keys=True),
    ],
)

logger = get_logger()
logger.info("order placed", order_id=12345, amount=99.99)
# {"amount": 99.99, "event": "order placed", "level": "info", "order_id": 12345, "timestamp": "2026-03-27T..."}
```

### Custom Processor Pipeline

```python
from structlog import (
    configure, get_logger, add_log_level, add_logger_name,
    TimeStamper, format_exc_info, ConsoleRenderer, DropEvent,
)

def filter_health_checks(logger, method_name, event_dict):
    if event_dict.get("event") == "health check":
        raise DropEvent
    return event_dict

configure(
    processors=[
        filter_health_checks,
        add_log_level,
        add_logger_name,
        TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
        format_exc_info,
        ConsoleRenderer(),
    ],
)

logger = get_logger()
logger.info("health check")   # silently dropped
logger.info("user login", user="alice")  # rendered normally
```

### Wrapping stdlib Logger

```python
import logging
from structlog import wrap_logger, add_log_level, TimeStamper, ConsoleRenderer

stdlib_logger = logging.getLogger("myapp")
stdlib_logger.setLevel(logging.DEBUG)
stdlib_logger.addHandler(logging.StreamHandler())

logger = wrap_logger(
    stdlib_logger,
    processors=[add_log_level, TimeStamper(), ConsoleRenderer()],
)
logger.info("using stdlib backend", component="auth")
```

### Exception Logging

```python
from structlog import get_logger

logger = get_logger()

try:
    result = 1 / 0
except ZeroDivisionError:
    logger.exception("calculation failed", operation="divide")
    # Automatically captures and formats the traceback
```

## Notes and Caveats

!!! info "API Compatibility with structlog"
    This module is inspired by the `structlog` library. The core concepts (bound loggers, processor pipelines, renderers) follow the same design, but this is a simplified single-file reimplementation, not a strict API-compatible drop-in.

!!! info "Default Processor Pipeline"
    The default pipeline is `[add_log_level, TimeStamper(), ConsoleRenderer()]` with a `PrintLoggerFactory`. This gives you colorized, loguru-style console output with zero configuration.

!!! info "Console Color Detection"
    The `ConsoleRenderer` auto-detects terminal color support. Set `colors=False` to force plain output, or set the `NO_COLOR` environment variable (see [no-color.org](https://no-color.org/)).

!!! info "Logger Caching"
    By default, `get_logger()` caches loggers by positional arguments. Loggers created with keyword arguments (initial context) are not cached. Call `reset_defaults()` to clear the cache.

- **Python version:** Requires Python 3.10+ (uses `X | Y` union type syntax).
- **Thread safety:** Bound loggers are immutable -- `bind()`, `unbind()`, and `new()` return new instances, making them safe to share across threads.
- **No CLI:** This module does not provide a command-line interface.

## Benchmark

Benchmarked against `structlog` across four scenarios.

See [Structured Logging Benchmark](../benchmarks/structlog.md) for detailed results.
