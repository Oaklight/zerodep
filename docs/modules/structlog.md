# 结构化日志

结构化日志与彩色控制台输出 -- 零依赖，仅标准库，Python 3.10+。

## 概述

Structlog 模块提供了 `structlog` 核心功能的直接替代方案。它支持绑定日志器（Bound Logger）的上下文传播、处理器管线（Processor Pipeline）、以及多种输出渲染器（控制台、JSON、键值对）——全部无需任何第三方依赖。

| 文件 | 说明 | 依赖 |
|------|------|------|
| `structlog.py` | 纯 Python 实现 | 无（仅标准库） |

### 核心概念

- **绑定日志器（Bound Logger）**：携带上下文的日志器，通过 `bind()` 添加键值对后返回新实例，采用写时复制（Copy-on-write）策略。
- **处理器管线（Processor Pipeline）**：有序的处理函数列表，依次对事件字典（Event Dict）进行变换或增强。
- **渲染器（Renderer）**：管线中的最后一个处理器，将事件字典转换为最终输出字符串（控制台、JSON 或键值对格式）。
- **事件字典（Event Dict）**：`dict[str, Any]` 类型的字典，在处理器管线中流转，包含日志事件的所有数据。

默认配置提供 loguru 风格的彩色控制台输出，零配置即可使用。

## 如何在你的项目中使用

只需将 `.py` 文件复制到你的项目中：

```bash
cp structlog/structlog.py your_project/
```

然后直接导入：

```python
from structlog import get_logger, setup_logging, configure
```

## API 参考

### `get_logger(*args, **initial_values) -> BoundLogger`

使用全局配置创建绑定日志器。

```python
def get_logger(*args: Any, **initial_values: Any) -> BoundLogger
```

**参数：**

| 名称 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `*args` | `Any` | -- | 传递给日志器工厂的位置参数（如日志器名称）。 |
| `**initial_values` | `Any` | -- | 初始绑定上下文的键值对。 |

**返回值：** `BoundLogger` -- 已配置的绑定日志器。

**示例：**

```python
from structlog import get_logger

logger = get_logger()
logger.info("server started", host="0.0.0.0", port=8080)
```

---

### `setup_logging(level, renderer, colors, processors, logger_name, stream) -> BoundLogger`

一行调用完成日志配置，同时配置 stdlib `logging` 和处理器管线。

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

**参数：**

| 名称 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `level` | `int \| str` | `INFO` | 日志级别（名称或整数）。 |
| `renderer` | `str` | `"console"` | 输出渲染器：`"console"`、`"json"` 或 `"kv"`。 |
| `colors` | `bool \| None` | `None` | 启用 ANSI 颜色。`None` 自动检测终端支持。 |
| `processors` | `list[Processor] \| None` | `None` | 自定义处理器列表，提供后将覆盖 `renderer` 参数。 |
| `logger_name` | `str \| None` | `None` | stdlib 日志器名称。 |
| `stream` | `IO[str] \| None` | `None` | 输出流，默认为 `sys.stderr`。 |

**返回值：** `BoundLogger` -- 即用型绑定日志器。

**示例：**

```python
from structlog import setup_logging

logger = setup_logging(level="DEBUG", renderer="json")
logger.info("structured", key="value")
```

---

### `configure(processors, wrapper_class, context_class, logger_factory, cache_logger_on_first_use)`

覆盖全局配置。仅非 `None` 的参数会被修改。

```python
def configure(
    processors: list[Processor] | None = None,
    wrapper_class: type[BoundLogger] | None = None,
    context_class: type[dict] | None = None,
    logger_factory: LoggerFactory | None = None,
    cache_logger_on_first_use: bool | None = None,
) -> None
```

**参数：**

| 名称 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `processors` | `list[Processor] \| None` | `None` | 有序处理器列表。 |
| `wrapper_class` | `type[BoundLogger] \| None` | `None` | 使用的 BoundLogger 子类。 |
| `context_class` | `type[dict] \| None` | `None` | 上下文存储的字典类。 |
| `logger_factory` | `LoggerFactory \| None` | `None` | 底层日志器的工厂函数。 |
| `cache_logger_on_first_use` | `bool \| None` | `None` | 缓存 `get_logger()` 返回的日志器。 |

**示例：**

```python
from structlog import configure, add_log_level, TimeStamper, JSONRenderer

configure(processors=[add_log_level, TimeStamper(), JSONRenderer()])
```

---

### `reset_defaults()`

将全局配置恢复为出厂默认值。

```python
def reset_defaults() -> None
```

---

### `wrap_logger(logger, processors, **initial_values) -> BoundLogger`

将已有日志器包装为带有处理器管线的绑定日志器。

```python
def wrap_logger(
    logger: Any,
    processors: list[Processor] | None = None,
    **initial_values: Any,
) -> BoundLogger
```

**参数：**

| 名称 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `logger` | `Any` | -- | 任何具有 `debug`/`info`/... 方法的对象。 |
| `processors` | `list[Processor] \| None` | `None` | 处理器列表，默认使用全局配置。 |
| `**initial_values` | `Any` | -- | 初始绑定上下文。 |

**返回值：** `BoundLogger` -- 包装了 *logger* 的绑定日志器。

**示例：**

```python
import logging
from structlog import wrap_logger, add_log_level, TimeStamper, ConsoleRenderer

stdlib_logger = logging.getLogger("myapp")
log = wrap_logger(
    stdlib_logger,
    processors=[add_log_level, TimeStamper(), ConsoleRenderer()],
    service="api",
)
log.info("ready")
```

---

### `BoundLogger` 类

携带绑定上下文并通过处理器管线处理日志的日志器。不要直接实例化，请使用 `get_logger()` 或 `wrap_logger()`。

#### `bind(**new_values) -> BoundLogger`

返回一个新日志器，将 *new_values* 合并到上下文中。

#### `unbind(*keys) -> BoundLogger`

返回一个新日志器，从上下文中移除指定的 *keys*。

#### `new(**new_values) -> BoundLogger`

返回一个新日志器，用 *new_values* 替换整个上下文。

#### 日志方法

- `debug(event, **kw)` -- 记录 DEBUG 级别日志。
- `info(event, **kw)` -- 记录 INFO 级别日志。
- `warning(event, **kw)` -- 记录 WARNING 级别日志。
- `error(event, **kw)` -- 记录 ERROR 级别日志。
- `critical(event, **kw)` -- 记录 CRITICAL 级别日志。
- `exception(event, **kw)` -- 记录 ERROR 级别日志并附带异常信息（自动设置 `exc_info=True`）。
- `log(level, event, **kw)` -- 使用指定的整数级别记录日志。

---

### 内置处理器

#### `add_log_level`

从日志方法名推导出 `level` 键并添加到事件字典中。

```python
def add_log_level(logger, method_name, event_dict) -> EventDict
```

**示例：** 调用 `logger.info(...)` 后，`event_dict["level"]` 的值为 `"info"`。

---

#### `add_logger_name`

从底层日志器的名称中提取 `logger` 键并添加到事件字典中。

```python
def add_logger_name(logger, method_name, event_dict) -> EventDict
```

---

#### `TimeStamper(fmt, utc, key)`

向事件字典中添加时间戳的处理器。

```python
class TimeStamper(
    fmt: str | None = "iso",
    utc: bool = True,
    key: str = "timestamp",
)
```

**参数：**

| 名称 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `fmt` | `str \| None` | `"iso"` | 时间戳格式。`"iso"` 表示 ISO 8601，`None` 表示 UNIX 浮点数，或自定义 `strftime` 格式字符串。 |
| `utc` | `bool` | `True` | 如果为 `True`，使用 UTC 时间；否则使用本地时间。 |
| `key` | `str` | `"timestamp"` | 时间戳在字典中的键名。 |

---

#### `format_exc_info`

将 `exc_info` 替换为格式化的 `exception` 字符串。

```python
def format_exc_info(logger, method_name, event_dict) -> EventDict
```

如果 `exc_info` 为 `True`，通过 `sys.exc_info()` 捕获当前异常；如果是异常元组，则直接格式化。`exc_info` 键被移除并替换为 `exception`。

---

### 渲染器

#### `ConsoleRenderer(colors, pad_event, level_styles)`

将事件字典渲染为 loguru 风格的彩色控制台输出。

```python
class ConsoleRenderer(
    colors: bool | None = None,
    pad_event: int = 30,
    level_styles: dict[str, str] | None = None,
)
```

**参数：**

| 名称 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `colors` | `bool \| None` | `None` | 启用 ANSI 颜色代码。`None` 自动检测终端支持。 |
| `pad_event` | `int` | `30` | 事件字段的填充宽度，用于对齐。 |
| `level_styles` | `dict[str, str] \| None` | `None` | 自定义每个级别的 ANSI 颜色字符串。 |

**输出格式：**

```
2026-03-27 14:30:00.123 | INFO     | event message    key=val key=val
```

---

#### `JSONRenderer(serializer, **dumps_kw)`

将事件字典渲染为 JSON 字符串。

```python
class JSONRenderer(
    serializer: Callable[..., str] = json.dumps,
    **dumps_kw: Any,
)
```

**参数：**

| 名称 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `serializer` | `Callable[..., str]` | `json.dumps` | JSON 序列化函数。 |
| `**dumps_kw` | `Any` | -- | 传递给 `serializer` 的额外关键字参数。 |

---

#### `KeyValueRenderer(key_order, sort_keys, drop_missing)`

将事件字典渲染为 `key=value` 键值对。

```python
class KeyValueRenderer(
    key_order: list[str] | None = None,
    sort_keys: bool = False,
    drop_missing: bool = True,
)
```

**参数：**

| 名称 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `key_order` | `list[str] \| None` | `None` | 优先渲染的键列表，按此顺序输出。 |
| `sort_keys` | `bool` | `False` | 对剩余键按字母顺序排序。 |
| `drop_missing` | `bool` | `True` | 跳过 `key_order` 中不存在的键。 |

---

### 日志器工厂

#### `PrintLogger(file)`

通过 `print()` 写入文件句柄的最小日志器。这是默认的底层日志器。

```python
class PrintLogger(file: IO[str] | None = None)
```

**参数：**

| 名称 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `file` | `IO[str] \| None` | `None` | 输出流，默认为 `sys.stderr`。 |

---

#### `PrintLoggerFactory(file)`

创建 `PrintLogger` 实例的工厂。

```python
class PrintLoggerFactory(file: IO[str] | None = None)
```

---

#### `StdlibLoggerFactory(name)`

返回 stdlib `logging.Logger` 的工厂。

```python
class StdlibLoggerFactory(name: str | None = None)
```

**参数：**

| 名称 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `name` | `str \| None` | `None` | 传递给 `logging.getLogger()` 的日志器名称。`None` 使用根日志器。 |

---

### 异常

#### `DropEvent`

在处理器中抛出此异常可静默丢弃当前日志事件。

```python
class DropEvent(Exception)
```

---

### 工具函数

#### `truncate_string(s, max_length, suffix)`

将字符串截断到指定长度，并附加剩余字符数。

```python
def truncate_string(
    s: str,
    max_length: int,
    suffix: str = "...",
) -> str
```

**参数：**

| 名称 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `s` | `str` | -- | 要截断的字符串。 |
| `max_length` | `int` | -- | 保留的最大字符数。 |
| `suffix` | `str` | `"..."` | 保留文本与字符计数之间的分隔符。 |

**返回值：** `str` -- 原始字符串（如果足够短），否则返回截断后附加 `"...[N more chars]"` 后缀的字符串。

---

#### `truncate_base64(data_url, max_length)`

截断 base64 data-URL 以获得更简洁的日志输出。

```python
def truncate_base64(
    data_url: str,
    max_length: int = 100,
) -> str
```

**参数：**

| 名称 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `data_url` | `str` | -- | `data:` URL 或任意字符串。 |
| `max_length` | `int` | `100` | 保留的最大 base64 负载字符数。 |

**返回值：** `str` -- 截断后的 URL，如果不是 data-URL 则返回原始字符串。

## 使用示例

### 零配置快速开始

```python
from structlog import get_logger

logger = get_logger()
logger.info("server started", host="0.0.0.0", port=8080)
logger.warning("disk usage high", percent=92.5)
logger.error("connection failed", retry_in=5)
```

输出（彩色终端）：

```
2026-03-27 14:30:00.123 | INFO     | server started                 host='0.0.0.0' port=8080
2026-03-27 14:30:00.124 | WARNING  | disk usage high                percent=92.5
2026-03-27 14:30:00.125 | ERROR    | connection failed              retry_in=5
```

### 绑定日志器与上下文传播

```python
from structlog import get_logger

# 创建带上下文的日志器
log = get_logger().bind(request_id="abc-123")
log.info("handling request")

# 追加更多上下文（返回新实例，原日志器不变）
log = log.bind(user_id=42)
log.info("authenticated")

# 移除上下文
log = log.unbind("user_id")
log.info("context removed")

# 替换整个上下文
log = log.new(trace_id="xyz-789")
log.info("fresh context")
```

### 使用 setup_logging() 一行配置

```python
from structlog import setup_logging

# 控制台输出（默认）
logger = setup_logging(level="DEBUG")
logger.debug("verbose output")

# JSON 输出
logger = setup_logging(level="INFO", renderer="json")
logger.info("structured log", key="value")

# 键值对输出
logger = setup_logging(renderer="kv")
logger.info("kv format", count=42)
```

### 生产环境 JSON 输出

```python
from structlog import configure, get_logger, add_log_level, TimeStamper, JSONRenderer

configure(processors=[
    add_log_level,
    TimeStamper(fmt="iso", utc=True),
    JSONRenderer(sort_keys=True),
])

logger = get_logger()
logger.info("order created", order_id=12345, total=99.99)
# {"event": "order created", "level": "info", "order_id": 12345, "timestamp": "2026-03-27T14:30:00.123456+00:00", "total": 99.99}
```

### 自定义处理器管线

```python
from structlog import configure, get_logger, add_log_level, add_logger_name
from structlog import TimeStamper, format_exc_info, ConsoleRenderer

configure(processors=[
    add_log_level,
    add_logger_name,
    TimeStamper(fmt="%Y-%m-%d %H:%M:%S", utc=False),
    format_exc_info,
    ConsoleRenderer(colors=True, pad_event=40),
])

logger = get_logger()
logger.info("pipeline configured")
```

### 包装 stdlib 日志器

```python
import logging
from structlog import wrap_logger, add_log_level, TimeStamper, ConsoleRenderer

# 配置 stdlib 日志
logging.basicConfig(level=logging.DEBUG, format="%(message)s")
stdlib_logger = logging.getLogger("myapp")

# 用 structlog 处理器管线包装
log = wrap_logger(
    stdlib_logger,
    processors=[add_log_level, TimeStamper(), ConsoleRenderer(colors=False)],
    service="api",
    version="1.0",
)

log.info("request received", method="GET", path="/api/users")
```

### 异常日志记录

```python
from structlog import get_logger

logger = get_logger()

try:
    result = 1 / 0
except ZeroDivisionError:
    # exception() 自动捕获当前异常信息
    logger.exception("calculation failed", operation="divide")
```

## 注意事项

!!! info "与 structlog 的 API 兼容性"
    本模块的 API 设计参考了 `structlog` 库，但并非完全兼容的直接替代品。核心概念（绑定日志器、处理器管线、渲染器）保持一致，但某些高级功能（如异步支持、stdlib 集成的完整适配器链）未包含在内。

!!! info "写时复制语义"
    `bind()`、`unbind()` 和 `new()` 方法均返回新的 `BoundLogger` 实例，不会修改原始日志器。这意味着在不同协程或线程中可以安全地使用同一个基础日志器。

!!! info "NO_COLOR 环境变量"
    `ConsoleRenderer` 尊重 `NO_COLOR` 环境变量（参见 [no-color.org](https://no-color.org/)）。设置 `NO_COLOR=1` 可全局禁用颜色输出。

- **Python 版本：** 需要 Python 3.10+（使用了 `X | Y` 联合类型语法）。
- **默认输出流：** 所有输出默认写入 `sys.stderr`。
- **日志器缓存：** 默认启用 `cache_logger_on_first_use`，相同参数的 `get_logger()` 调用将返回缓存实例。带有 `initial_values` 的调用不会被缓存。
- **DropEvent：** 在处理器中抛出 `DropEvent` 异常可静默丢弃日志事件，不会产生任何输出。

## 性能测试

与 `structlog` 在四个场景下进行对比：简单日志、带绑定上下文的日志、JSON 渲染、绑定后立即记录。

详见 [结构化日志性能测试](../benchmarks/structlog.md)。
