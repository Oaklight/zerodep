---
title: 迁移指南
---

# 迁移指南

本页面记录 zerodep 各版本之间的破坏性变更及对应的代码更新方法。

## 迁移到 2026.4.11（CalVer）

### 版本策略变更

从此版本开始，**项目级**版本号使用 [CalVer](https://calver.org/)（`YYYY.M.patch`）日历版本：

- `2026.4.11` — 2026 年 4 月第一个稳定版本
- `2026.4.1` — 同月第二个版本（如有需要）
- `2026.5.0` — 2026 年 5 月第一个版本

**模块级**版本号继续使用独立的 SemVer（如 `yaml` 0.3.0、`aes` 0.4.0）。每个模块的版本跟踪其自身的 API 演化，在 frontmatter 的 `version` 字段中声明。

**对用户的影响：**

- `pip install zerodep` 安装的 CLI 使用 CalVer 版本号
- 通过 `zerodep add` 获取的模块携带各自的 SemVer 版本号
- 同一 CalVer 版本内的所有模块保证兼容
- 手动拷贝模块时，请始终使用同一版本的文件

### 模块 Frontmatter Note

所有模块的 frontmatter 中新增 `note` 字段：

```python
# /// zerodep
# version = "0.3.0"
# deps = ["dotenv", "yaml", "jsonx"]
# note = "Install/update via zerodep CLI (...). Manual copy may miss deps."
# ///
```

通过 `zerodep add` 拷贝时，note 会自动替换为具体的模块名。**无需代码修改**——这仅为提示信息。

### 新增维护者命令

三个新 CLI 命令用于模块间依赖管理：

- `zerodep version-check` — 检测在声明版本后有代码变更的模块
- `zerodep dep-graph` — 可视化模块依赖图
- `zerodep dep-check` — 运行变更模块及其下游依赖的测试

详见 [CLI 工具](cli.md) 了解使用方法。

## 迁移到 0.3.0

### 类型注解（风格变更）

所有模块现在使用 PEP 604 联合类型语法和 PEP 585 内置泛型，不再使用 `typing` 中的别名。

```python
# 迁移前
from typing import Optional, Dict, List

def fetch(url: str, headers: Optional[Dict[str, str]] = None) -> List[str]: ...

# 迁移后
def fetch(url: str, headers: dict[str, str] | None = None) -> list[str]: ...
```

如果你从 zerodep 模块中导入了类型别名，请更新为新风格。新写法在运行时需要 Python 3.10+，或在 3.9 中添加 `from __future__ import annotations`。

### A2A 和 ACP：JSON-RPC 层提取

JSON-RPC 层已被提取为独立的 `jsonrpc` 模块。如果使用 `a2a.py` 或 `acp.py`，现在还需要同时复制 `jsonrpc.py`。

```python
# 迁移前：a2a.py 是自包含的
project/
    a2a.py

# 迁移后：jsonrpc.py 是必需的同级文件
project/
    a2a.py
    jsonrpc.py
```

`A2AError` 现在继承自 `jsonrpc` 模块的 `JSONRPCException`，而非自行定义基类：

```python
# 迁移前
except A2AError:  # 独立的异常层级

# 迁移后 - 仍可捕获，但基类已变更
from jsonrpc import JSONRPCException
except JSONRPCException:  # 可同时捕获 A2A 和 ACP 的错误
```

ACP 的序列化方法已统一为单个递归 `to_dict()` 方法。如果你调用了其他序列化辅助方法，请改用 `to_dict()`。

### 新增 `__all__` 导出

所有模块现在定义了 `__all__`。如果你使用 `from module import *`，只有显式导出的名称可用。需要按名称导入之前隐式可用的名称：

```python
# 迁移前 - 导入所有内容
from yaml import *

# 迁移后 - 如果某个辅助函数不在 __all__ 中，请显式导入
from yaml import parse, dump, _internal_helper  # 显式导入
```

### 冻结 Dataclass：`slots=True`

冻结的 dataclass 现在添加了 `slots=True`。这改善了内存使用，但不允许动态添加属性：

```python
# 以下代码现在会抛出 AttributeError
msg = A2AMessage(...)
msg.custom_field = "value"  # AttributeError: 'A2AMessage' has no __dict__
```

如果你之前在冻结 dataclass 实例上附加了临时属性，请改用单独的字典存储。

---

## 迁移到 0.2.2

### HTTP 客户端异常重命名

两个与内置类型同名的异常已被重命名：

| 旧名称 | 新名称 | 说明 |
|---|---|---|
| `ConnectionError` | `HttpConnectionError` | 避免覆盖内置类型 |
| `TimeoutError` | `HttpTimeoutError` | 避免覆盖内置类型 |

旧名称作为别名保留但已弃用，将在未来版本中移除。请尽快更新 `except` 子句：

```python
# 迁移前
from httpclient import ConnectionError, TimeoutError

try:
    resp = fetch(url)
except ConnectionError:
    ...
except TimeoutError:
    ...

# 迁移后
from httpclient import HttpConnectionError, HttpTimeoutError

try:
    resp = fetch(url)
except HttpConnectionError:
    ...
except HttpTimeoutError:
    ...
```

### 新增基础异常类

引入了两个新的基础异常类：

- `HttpClientError` -- 所有 HTTP 客户端异常的基类，可用于统一捕获所有 HTTP 相关错误。
- `ConfigError` -- 所有 config 模块异常的基类。

```python
# 统一捕获所有 HTTP 错误
from httpclient import HttpClientError

try:
    resp = fetch(url)
except HttpClientError:
    ...
```

---

## 迁移到 0.2.0

### 模块元数据：PEP 723 Frontmatter

模块元数据从模块级属性迁移到了 PEP 723 内联脚本元数据（文件顶部的 frontmatter 注释块）。

- `module.__version__` 仍然可用（为兼容性而重新导出）。
- `module.__deps__` 已**移除**。依赖现在在 PEP 723 `# /// script` 块中声明：

```python
# 迁移前 (0.1.x)
__version__ = "0.1.5"
__deps__ = ["pycryptodome>=3.20"]

# 迁移后 (0.2.0+) - 文件顶部的 frontmatter
# /// script
# version = "0.2.0"
# deps = ["pycryptodome>=3.20"]
# ///
```

如果你以编程方式读取 `__deps__`，请改为解析 frontmatter。zerodep CLI 提供了 `zerodep info <module>` 命令用于此目的。

### CLI：递归扫描

CLI 现在支持递归模块扫描和嵌套目录结构。无需修改代码，但请注意 `zerodep list` 现在可能返回之前不可见的子目录中的模块。
