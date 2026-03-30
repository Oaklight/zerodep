# 内部约定

本页面记录 zerodep 跨模块使用的实现模式。这些不是共享运行时代码——每个模块各自携带自己的副本——但它们遵循统一的约定，使得每个模块看起来都像同一个作者所写。

如果你正在贡献新模块或修改现有模块，请检查你的变更是否涉及以下模式，并遵循已建立的约定。

## 模式概览

| # | 模式 | 状态 | 涉及模块 |
|---|------|------|----------|
| 1 | [可选 Sibling Import](#可选-sibling-import) | 已标准化 | config, vcs, sse |
| 2 | [终端颜色检测](#终端颜色检测) | 已标准化 | ansi, structlog, prompt |
| 3 | [Cleanup 语义](#cleanup-语义) | 已标准化 | httpclient, runner, scheduler, sse, vcs |
| 4 | [显式注入](#显式注入) | 已实现 | vcs, config, sse |
| 5 | [子进程执行](#子进程执行) | 已标准化 | runner, vcs |
| 6 | [Sync/Async API 镜像](#syncasync-api-镜像) | 已标准化 | runner, httpclient |
| 7 | [错误类型设计](#错误类型设计) | 已标准化 | 所有子系统模块 |
| 8 | [大模块内部分层](#大模块内部分层) | 已标准化 | httpclient, runner, scheduler |

---

## 可选 Sibling Import

### 问题定义

zerodep 模块必须在单独复制时可独立工作，但当同级模块存在时应自动增强能力。

### 标准写法

每个 sibling import 遵循以下步骤：

1. **计算同级目录** — 相对于 `__file__`
2. **插入 `sys.path`** — 仅一次，仅在需要时
3. **尝试导入** — 捕获 `ImportError`
4. **设置能力标记** — `_HAS_<NAME> = True/False`
5. **延迟报错** — 仅在运行时真正需要该能力时才抛出用户可理解的错误

```python
# 步骤 1-2: 定位同级模块
_sibling_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "yaml")
if _sibling_dir not in sys.path:
    sys.path.insert(0, _sibling_dir)

# 步骤 3-4: 探测
try:
    from yaml import load as _yaml_load
    _HAS_YAML = True
except ImportError:
    _HAS_YAML = False

# 步骤 5: 延迟报错（在需要该能力的函数内部）
def load_yaml(path):
    if not _HAS_YAML:
        raise RuntimeError(
            "YAML support requires the zerodep yaml module. "
            "Copy yaml/yaml.py alongside this file."
        )
    ...
```

### 懒加载

为避免导入时副作用，sibling 模块采用懒加载。导入被延迟到首次使用时：

```python
_yaml_mod = None

def _get_yaml():
    global _yaml_mod
    if _yaml_mod is None:
        _sibling_dir = os.path.join(os.path.dirname(__file__), "..", "yaml")
        if _sibling_dir not in sys.path:
            sys.path.insert(0, _sibling_dir)
        try:
            import yaml as _mod
            _yaml_mod = _mod
        except ImportError:
            raise RuntimeError("YAML support requires the zerodep yaml module.")
    return _yaml_mod
```

### 命名约定

| 元素 | 约定 | 示例 |
|------|------|------|
| 路径变量 | `_<name>_dir` | `_yaml_dir`, `_diff_dir` |
| 能力标记 | `_HAS_<NAME>` | `_HAS_YAML`, `_HAS_DIFF_MODULE` |
| 导入别名 | `from mod import x as _x` | `from yaml import load as _yaml_load` |

---

## 终端颜色检测

### 问题定义

面向终端的模块需要统一判断是否输出 ANSI 转义序列，需尊重用户环境变量和操作系统信号。

### 标准优先级

所有终端模块使用以下判断顺序：

```
FORCE_COLOR  →  强制开启
NO_COLOR     →  强制关闭
isatty()     →  非 TTY 时关闭
TERM=dumb    →  关闭
默认          →  开启
```

### 参考实现

`ansi/ansi.py` 是颜色检测的参考实现，其他终端模块（`structlog`、`prompt`）与其对齐。

### 能力分层

| 模块 | 颜色范围 | 说明 |
|------|---------|------|
| `ansi` | 全量：命名色、亮色、256 色、hex、RGB、前景/背景 | 参考实现 |
| `prompt` | 16 命名色；需要时使用 hex 前景 | 交互层 |
| `structlog` | 固定 16 色映射 | 日志渲染；无自定义调色 |

---

## Cleanup 语义

### 问题定义

网络、进程和流式模块需要资源清理，清理通常是尽力而为（best-effort）的。如果没有统一约定，代码库会逐渐漂向到处都是 `except Exception: pass`，掩盖资源卫生问题。

### 三级分类

zerodep 中的每个 cleanup 路径都被归入以下三个级别之一：

#### Tier 1 — 必须成功

失败意味着对象处于不一致或不安全的状态。这些路径**抛出或传播异常**。

**典型场景：**

- 进程终止升级（SIGTERM 然后 SIGKILL）
- 连接池 finally 块管理（归还或关闭决策）
- 事件循环关闭
- 上下文管理器委托给 close 方法

**代码模式：**

```python
# Tier 1: 必须成功——失败时传播异常
finally:
    if not streaming:
        pool.release(conn)
    else:
        conn.close()
```

#### Tier 2 — 尽力而为但可观测

失败不影响正确性，但说明存在资源卫生问题。这些路径**记录日志或发出诊断信号**。

**典型场景：**

- 带活跃连接的流式响应关闭
- 调度器回调错误
- 进程拆除期间的管道读取器关闭

**代码模式：**

```python
# Tier 2: 尽力而为——失败时记录日志
try:
    response.close()
except Exception:
    logger.debug("failed to close response for %s", url, exc_info=True)
```

#### Tier 3 — 尽力而为静默

失败是预期的、无害的且高频发生的。这是**唯一**允许使用 `except Exception: pass` 的路径。

**典型场景：**

- 池健康检查时驱逐陈旧连接
- 对已关闭资源的二次关闭
- 临时文件清理（finally 中的 `os.unlink`）
- 解释器退出时的池批量关闭

**代码模式：**

```python
# Tier 3: 尽力而为静默——预期的失败
try:
    conn.close()
except Exception:
    pass
```

### 当前分类映射

| 模块 | Tier 1（必须成功） | Tier 2（可观测） | Tier 3（静默） |
|------|-------------------|-----------------|---------------|
| httpclient | `_sync_request` / `_async_request` finally、`Client.__exit__` | `StreamingResponse.close/aclose` | Pool acquire/release/close_all、代理清理 |
| runner | 进程终止升级、`stream()` / `stream_async()` 上下文管理器 | 管道读取器 `ValueError` | — |
| scheduler | finally 中的作业状态重置、事件循环关闭 | 事件监听器错误、`on_success` / `on_error` 回调 | — |
| sse | `SSEClient.__exit__` / `AsyncSSEClient.__aexit__` | — | `_close_response`（重连） |
| vcs | — | — | `merge_file` 临时文件清理 |

### 规则

1. **`except Exception: pass` 仅允许用于 Tier 3** — 真正无害的、预期的失败
2. **Tier 2 必须有信号** — `logger.debug(...)` 配合 `exc_info=True`，或 `warnings.warn(ResourceWarning(...))`
3. **cleanup 结构保持一致** — 先标记状态、再尝试释放资源、最后兜底

---

## 显式注入

### 问题定义

Sibling import 通过 `sys.path` 操纵来自动发现相邻模块。这种方式在复制使用场景中很方便，但会创建隐式依赖，难以测试，可能与用户代码冲突，且在模块嵌入较大包时无法工作。

### 解决方案：三态注入参数

使用 sibling import 的模块在构造函数上暴露显式注入参数。每个参数使用私有的 `_Unset` 哨兵类来区分三种状态：

| 值 | 含义 |
|----|------|
| `_UNSET`（默认） | 使用 sibling 自动发现 — 当前行为，完全向后兼容 |
| `None` | 显式禁用该能力 |
| 可调用对象 / 字典 | 用户注入的实现 — 完全绕过 `sys.path` |

### 哨兵模式

每个模块定义自己的 `_Unset` 单例（模块之间不共享代码）：

```python
class _Unset:
    """哨兵，表示'使用默认的 sibling 自动发现'。"""
    _instance: _Unset | None = None

    def __new__(cls) -> _Unset:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "UNSET"

_UNSET = _Unset()
```

使用 `isinstance(value, _Unset)` 做类型收窄（而非 `value is _UNSET`），以便 `ty` 能正确收窄联合类型。

### 各模块注入点

#### VCS — `merge_func`

`Mercurial` 和 `Jujutsu` 接受 `merge_func` 参数用于三路合并。`Git` 使用自身的 `git merge-file` CLI，不需要注入。

```python
from vcs import Mercurial

# 默认：自动发现 sibling diff 模块
hg = Mercurial("/path/to/repo")

# 注入：使用自定义合并函数
hg = Mercurial("/path/to/repo", merge_func=my_merge3)

# 禁用：merge_file() 抛出 NotImplementedError
hg = Mercurial("/path/to/repo", merge_func=None)
```

`detect()` 函数会将 `merge_func` 转发给它构造的后端。

#### Config — `loaders` 和 `dotenv_loader`

`Config` 接受两个注入参数：

- **`loaders`**：覆盖文件格式加载器注册表（默认使用 sibling yaml/jsonc 模块）
- **`dotenv_loader`**：覆盖 dotenv 加载机制（默认使用 sibling dotenv 模块）

```python
from config import Config

# 默认：自动发现 sibling yaml、jsonc、dotenv
cfg = Config(config_path="settings.yaml")

# 注入：使用自定义加载器
cfg = Config(
    config_path="settings.yaml",
    loaders={".yaml": my_yaml_loader},
    dotenv_loader=my_dotenv_factory,
)

# 禁用：跳过 .env 加载
cfg = Config(dotenv_loader=None)
```

#### SSE — `transport`

`SSEClient` 和 `AsyncSSEClient` 接受 `transport` 参数，替换 sibling `httpclient` 依赖。

```python
from sse import SSEClient, AsyncSSEClient

# 默认：自动发现 sibling httpclient
client = SSEClient("https://example.com/events")

# 注入：使用自定义 HTTP GET 函数
client = SSEClient("https://example.com/events", transport=my_get_func)
```

同步 transport 必须接受 `(url, *, headers, stream, timeout, verify)` 并返回具有 `.status_code`、`.ok`、`.close()`、`.iter_lines()` 属性的对象。异步 transport 返回具有 `.aclose()` 和 `.aiter_lines()` 的对象。

当注入自定义 transport 时，重连错误处理仅捕获标准库的 `ConnectionError` 和 `OSError`（不捕获 httpclient 特定的异常）。

### 设计规则

1. **按实例注入** — 注入目标是实例属性，绝不修改模块全局变量。这保证了线程安全。
2. **不新增文件** — 哨兵类在每个模块内联定义。不创建共享的 `_core` 或工具层。
3. **向后兼容** — 所有新参数默认值为 `_UNSET`，保留现有行为。
4. **`isinstance` 做收窄** — 使用 `isinstance(value, _Unset)` 而非 `value is _UNSET`，以便类型检查器能正确收窄联合类型。

---

## 错误类型设计

### 问题定义

子系统模块各自定义领域异常。如果没有约定，异常命名、层次深度、上下文字段和消息风格会在模块间逐渐分化，导致捕获、日志记录和错误展示的一致性下降。

### 标准约定

#### 层次结构

每个子系统模块定义一个继承自 `Exception` 的基础异常。所有模块特定异常继承该基础异常。最大深度为两层。

```python
class HttpClientError(Exception):
    """Base exception for all httpclient operations."""

class HTTPError(HttpClientError):
    """Raised on non-2xx status."""
    ...

class HttpConnectionError(HttpClientError):
    """Raised on connection failures."""
    ...
```

这样调用方可以用 `except HttpClientError` 捕获所有模块错误，或单独针对特定错误。

#### 命名规范

异常名遵循 `<模块><名词>Error` 模式：

| 模块 | 基类 | 示例 |
|------|------|------|
| httpclient | `HttpClientError` | `HTTPError`、`HttpConnectionError`、`HttpTimeoutError`、`TooManyRedirects` |
| runner | `RunnerError` | `CommandNotFoundError`、`CommandFailedError`、`CommandTimeoutError`、`CommandBlockedError` |
| scheduler | `SchedulerError` | `SchedulerAlreadyRunning`、`SchedulerNotRunning`、`JobNotFound`、`InvalidCronExpression` |
| vcs | `VCSError` | `BinaryNotFoundError`、`CommandError`、`NotARepoError` |
| sse | `SSEError` | `SSEConnectionError`、`SSEHTTPError` |
| config | `ConfigError` | `UndefinedValueError` |
| frontmatter | `FrontmatterError` | `HandlerError` |
| validate | `ValidationError` | *（独立使用 — 通过 `ErrorDetail` 数据类进行结构化报告）* |
| retry | `RetryError` | *（独立使用 — 携带 `last_exception` 和 `attempts`）* |

**规则**：绝不遮蔽 Python 内置异常名（`ConnectionError`、`TimeoutError` 等）。使用模块前缀的名称代替。

#### 上下文字段

异常通过 `__init__` 参数将上下文存储为实例属性。错误消息在构造时使用 f-string 计算。

```python
class HttpConnectionError(HttpClientError):
    def __init__(self, message: str, *, host: str = "", port: int = 0) -> None:
        self.host = host
        self.port = port
        self.message = message
        super().__init__(message)
```

各错误类别的最小上下文要求：

| 错误类别 | 必需上下文 |
|---------|-----------|
| 网络/HTTP | `url`、`host`、`port` 或 `status_code` |
| 命令执行 | `command`、`returncode`、关键 `stderr` |
| 调度 | `job_id` 或 `cron expression` |
| 配置 | 键名 |
| 文件格式 | handler 或格式名 |

#### 不需要自定义异常的模块

简单工具模块（`cache`、`search`、`dotenv`、`yaml`、`jsonc`、`aes`、`qr` 等）使用标准库异常（`ValueError`、`KeyError`、`FileNotFoundError`）。只有当模块具有调用方需要区分的领域特定故障模式时，才需要自定义异常。

---

## 子进程执行

### 问题定义

`runner` 和 `vcs` 都执行外部进程，但在二进制发现、超时处理、编码和错误报告方面使用不同约定。如果不对齐，新模块将没有明确的参考可循。

### 参考实现

`runner` 是功能完整的通用实现。`vcs` 是面向特定领域的轻量封装。两者分别作为不同使用场景的参考。

### 标准约定

#### 二进制发现

| 步骤 | 描述 | 使用模块 |
|------|------|----------|
| 1 | 环境变量覆盖（`ZERODEP_<NAME>_PATH`） | vcs |
| 2 | `shutil.which()` — 跨平台 PATH 搜索 | runner, vcs |
| 3 | 平台特定回退目录（仅 Windows） | vcs |

`runner` 将 `which()` 作为公开工具函数暴露。`vcs` 使用扩展的 `_find_binary()`，包含环境变量覆盖和 Windows 回退。两种都是合理的——简单模块只用第 2 步即可；需要在 Windows 上可靠发现二进制的模块应遵循 `vcs` 的做法。

#### 编码

默认编码为 `utf-8`，显式声明且可配置：

```python
def _run(cmd, *, encoding="utf-8", ...):
    result = subprocess.run(cmd, text=True, encoding=encoding, ...)
```

`runner` 和 `vcs` 都使用此约定。

#### 超时

- 默认：`30.0` 秒，显式声明且可按调用配置
- 错误：抛出包含命令和超时值的领域特定超时错误

**升级策略**（仅 runner）：对于长时间运行或不可信的进程，`runner` 使用 SIGTERM → SIGKILL 升级，带可配置的宽限期（`kill_delay=5.0`）。`vcs` 使用简单的 `subprocess.run(timeout=...)`，不带升级，这对短生命周期的 VCS 命令是合适的。

#### 返回码处理

使用 `allowed_returncodes` 元组指定可接受的退出码：

```python
def _run(cmd, *, allowed_returncodes=(0,), ...):
    ...
    if result.returncode not in allowed_returncodes:
        raise CommandError(cmd, result.returncode, result.stderr)
```

某些命令合法使用非零退出码（如 `git diff` 返回 1 表示"有变更"）。对这些情况传入 `allowed_returncodes=(0, 1)`。

#### 超时时的错误上下文

超时错误必须在可用时捕获部分输出，并包含超时值：

```python
except subprocess.TimeoutExpired as exc:
    raise CommandError(
        cmd, -1,
        (exc.stderr or "").strip() if isinstance(exc.stderr, str) else "",
        timeout=timeout,
    ) from exc
```

#### Windows 支持

在 Windows 上，为后台进程抑制控制台窗口：

```python
if os.name == "nt":
    kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
```

### 有意保留的差异

| 方面 | runner | vcs | 原因 |
|------|--------|-----|------|
| SIGTERM→SIGKILL | 有（5s 宽限期） | 无 | VCS 命令生命周期短，不需要优雅关闭 |
| 异步支持 | 有（`asyncio.create_subprocess_exec`） | 无 | VCS 操作足够快，同步即可 |
| 环境变量控制 | 完整 API（`env`、`env_extra`、`env_remove`） | 继承当前环境 | VCS 命令需要用户的 PATH、HOME 等 |
| 流式输出 | 有（回调 + 迭代器） | 无 | VCS 输出量小，完整捕获即可 |

---

## Sync/Async API 镜像

### 问题定义

同时提供同步和异步 API 的模块需要在两条路径之间保持一致的命名、结构和错误行为。如果没有约定，sync/async 对会在细节上逐渐漂移——不同的错误消息、缺少的上下文字段、不一致的清理顺序。

### 命名约定

#### 类

所有异步类变体使用 `Async` 前缀：

| 同步 | 异步 |
|------|------|
| `Client` | `AsyncClient` |
| `StreamHandle` | `AsyncStreamHandle` |
| `SSEClient` | `AsyncSSEClient` |
| `EventSource` | `AsyncEventSource` |

#### 公开函数

代码库中存在两种约定：

| 模块 | 同步 | 异步 | 约定 |
|------|------|------|------|
| runner | `run` | `run_async` | 后缀 `_async` |
| runner | `stream` | `stream_async` | 后缀 `_async` |
| httpclient | `get` | `async_get` | 前缀 `async_` |
| sse | `connect` | `async_connect` | 前缀 `async_` |

对于已有 API，两种都可接受。**新代码推荐使用 `_async` 后缀**（`foo_async`），因为阅读更自然，且按字母排序时与同步版本相邻。

#### 内部函数

使用显式 `_sync_` / `_async_` 前缀：

```python
def _sync_request(method, url, ...):    ...
async def _async_request(method, url, ...):    ...
```

### 结构约定

#### 共享逻辑

将请求校验、输入解析和策略检查提取为同步辅助函数，供两条路径调用：

```python
def _validate_command(cmd, policy):   ...  # run() 和 run_async() 都调用
```

#### 阶段注释

较长的 sync/async 函数对使用匹配的阶段注释来保持对齐：

```python
# 同步路径
def _sync_request(...):
    # Phase 1: 构建 URL
    # Phase 2: 设置请求头
    # Phase 3: 建立连接
    # Phase 4: 发送请求
    ...

# 异步路径
async def _async_request(...):
    # Phase 1: 构建 URL
    # Phase 2: 设置请求头
    # Phase 3: 建立连接 (asyncio.open_connection)
    # Phase 4: 发送请求 (writer.write)
    ...
```

这使得审计两条路径是否处理了相同情况变得容易。

#### 错误行为

两条路径必须抛出相同的异常类型，并携带相同的上下文字段。异常类本身是同步的——只有抛出它们的代码不同：

```python
# 两条路径抛出相同的错误类型
raise HttpTimeoutError(msg, url=url, timeout=timeout)
```

#### 上下文管理器

同步类实现 `__enter__` / `__exit__`。异步类实现 `__aenter__` / `__aexit__`。两者都委托给相同的 `close()` / `aclose()` 方法。

### 当前模块覆盖

| 模块 | 同步 API | 异步 API | 共享核心 |
|------|---------|---------|---------|
| httpclient | `Client`、`get`/`post`/... | `AsyncClient`、`async_get`/`async_post`/... | URL 构建、请求头设置、认证 |
| runner | `run`、`stream` | `run_async`、`stream_async` | 命令解析、策略校验、环境构建 |
| sse | `SSEClient`、`connect` | `AsyncSSEClient`、`async_connect` | `_SSEParser`、`SSEEvent` 数据类 |
| scheduler | `Scheduler`（统一类） | *（异步任务在隔离的事件循环中运行）* | 单一类处理两种情况 |

---

## 大模块内部分层

### 问题定义

子系统模块（`httpclient`、`runner`、`scheduler`）是 1000+ 行的单文件。如果没有内部结构，导航困难，sync/async 路径难以并排审计，贡献者无法快速定位正确的代码段。

### 段落标记约定

每个大模块使用水平线注释将文件划分为命名段落：

```python
# ── 段落名 ──────────────────────────────────────────────────────
```

末尾短横线延伸到第 72 列以保持视觉一致性。所有段落使用此格式。

### 标准段落顺序

段落遵循自上而下的依赖顺序——每个段落只引用在其上方定义的内容：

| 顺序 | 段落 | 内容 |
|------|------|------|
| 1 | Imports | 标准库，然后是条件性的 sibling import |
| 2 | Constants / Defaults | 模块级常量、默认值 |
| 3 | Exceptions | 异常类层次结构 |
| 4 | Data Models | 数据类、TypedDict、命名元组 |
| 5 | Internal Helpers | 私有工具函数 |
| 6 | Core Logic | 核心实现（同步块在前，异步块在后） |
| 7 | Public API | 用户可见的函数和类 |

并非每个模块都需要所有段落。简单模块可以跳过第 5-6 段，直接到公开 API。

### 阶段注释

在长函数内部（尤其是 sync/async 传输对），使用编号的阶段注释标记逻辑阶段：

```python
async def _async_request(method, url, ...):
    # Phase 1: 构建 URL 和请求头
    ...
    # Phase 2: 认证设置
    ...
    # Phase 3: 获取连接
    ...
    # Phase 4: 发送请求
    ...
    # Phase 5: 读取响应
    ...
    # Phase 6: 处理重定向
    ...
```

同步和异步路径使用相同的阶段编号。这使得对两条路径进行 `diff` 或并排审计变得容易。

### 当前模块结构

#### httpclient（12 段）

`Imports → Constants → Exceptions → Data Models (Response) → Auth → Compression → Streaming Response → Connection Pools → Transport → Request Building → Public API Functions → Client Classes`

#### runner（14 段）

`Imports → Defaults → Exceptions → Data Models → Platform → Environment → Command Parsing → Policy → Process Lifecycle → Sync Execution → Async Execution → Sync Streaming → Async Streaming → Public API`

#### scheduler（7 段）

`Imports → Constants → Exceptions → Cron Parser → Triggers → Data Models → Scheduler Core`

### 规则

1. **超过 500 行的文件必须使用段落标记**
2. **段落顺序遵循依赖关系** — 段落之间不存在前向引用
3. **同步在异步之前** — 当段落有 sync 和 async 变体时，同步块在前
4. **阶段编号匹配** — 同步阶段 N 和异步阶段 N 必须处理相同的逻辑阶段
