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
| 5 | 子进程执行 | 计划中 | runner, vcs |
| 6 | Sync/Async API 镜像 | 计划中 | runner, httpclient |
| 7 | 错误类型设计 | 计划中 | 所有子系统模块 |
| 8 | 大模块内部分层 | 计划中 | httpclient, runner, scheduler |

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
