# 持久化字典

持久化字典，支持可插拔后端——零依赖，仅标准库，Python 3.10+。

## 概述

`persistdict` 模块提供一个将键值对持久化到磁盘的 `MutableMapping`。支持多种存储后端、可插拔序列化器，默认线程安全。

| 后端 | 存储 | 写入模式 | 适用场景 |
|------|------|----------|----------|
| `JsonFileBackend` | 单个 JSON 文件 | 缓冲写入（关闭时刷盘） | 小数据集、可读性优先 |
| `SqliteBackend` | SQLite 数据库 | 即时写入（每次操作提交） | 大数据集、并发访问 |

### 核心特性

- **dict 替代品** —— 实现 `collections.abc.MutableMapping`
- **默认 JSON 序列化** —— 无 pickle，无反序列化漏洞
- **可插拔序列化器** —— 注入自定义 `dumps`/`loads` 支持任意格式
- **可插拔后端** —— JSON 文件或 SQLite，根据文件扩展名自动检测
- **线程安全** —— 可选 `threading.Lock`（默认开启）
- **原子写入** —— JSON 后端使用临时文件 + `os.replace`；SQLite 使用事务
- **命名空间** —— 通过 `table` 参数在一个 SQLite 文件中存储多组逻辑 dict

## 如何在你的项目中使用

```bash
cp persistdict/persistdict.py your_project/
```

```python
from persistdict import open
```

## 使用示例

### 基本用法（自动检测后端）

```python
from persistdict import open

# .json 扩展名 → JSON 文件后端
with open("data.json") as d:
    d["name"] = "Alice"
    d["scores"] = [95, 87, 92]

# 重新打开——数据持久化
with open("data.json") as d:
    print(d["name"])      # "Alice"
    print(len(d))         # 2
```

### SQLite 后端处理大数据集

```python
from persistdict import open

# .db 扩展名 → SQLite 后端（WAL 模式，即时写入）
with open("data.db") as d:
    for i in range(10000):
        d[f"key_{i}"] = {"index": i, "active": True}
    print(len(d))  # 10000
```

### 在一个数据库中使用多个命名空间

```python
from persistdict import open

with open("app.db", table="users") as users:
    users["alice"] = {"email": "alice@example.com", "role": "admin"}

with open("app.db", table="config") as config:
    config["debug"] = False
    config["max_workers"] = 4
```

### 自定义序列化器

```python
from persistdict import PersistDict, SqliteBackend

class CompactSerializer:
    """将值存储为 repr() 字符串。"""
    def dumps(self, obj):
        return repr(obj)
    def loads(self, s):
        return eval(s)  # 仅用于可信数据！

backend = SqliteBackend("custom.db")
d = PersistDict(backend, serializer=CompactSerializer())
d["key"] = (1, 2, 3)
d.close()
```

### 显式指定后端

```python
from persistdict import open

# 即使是 .dat 扩展名也强制使用 SQLite
with open("data.dat", backend="sqlite") as d:
    d["key"] = "value"

# 强制使用 JSON
with open("store.bin", backend="json") as d:
    d["key"] = "value"
```

### 线程安全操作

```python
import threading
from persistdict import open

d = open("shared.db")

def writer(prefix: str):
    for i in range(100):
        d[f"{prefix}_{i}"] = i

threads = [threading.Thread(target=writer, args=(f"t{i}",)) for i in range(4)]
for t in threads:
    t.start()
for t in threads:
    t.join()

print(len(d))  # 400
d.close()
```

禁用锁定（单线程使用）：

```python
d = open("data.db", lock=False)
```

## API 参考

### 工厂函数

```python
open(
    path: str | os.PathLike,
    *,
    backend: str = "auto",
    serializer: Serializer | None = None,
    lock: threading.Lock | bool = True,
    table: str = "items",
) -> PersistDict
```

- **path**：存储文件路径
- **backend**：`"auto"`（根据扩展名检测）、`"json"` 或 `"sqlite"`
    - 自动检测：`.json` → JSON，`.db` / `.sqlite` / `.sqlite3` → SQLite
- **serializer**：值序列化器（默认：`JsonSerializer`）
- **lock**：`True`（新建 Lock）、`False`（不加锁）或 `threading.Lock` 实例
- **table**：SQLite 后端的表名（JSON 后端忽略）

### PersistDict

```python
class PersistDict(collections.abc.MutableMapping):
    def __init__(
        self,
        backend: Backend,
        *,
        serializer: Serializer | None = None,
        lock: threading.Lock | bool = True,
    ) -> None: ...
```

支持所有标准 `dict` 操作：`__getitem__`、`__setitem__`、`__delitem__`、`__iter__`、`__len__`、`__contains__`、`get`、`pop`、`popitem`、`clear`、`update`、`setdefault`、`keys`、`values`、`items`。

额外方法：

- `flush()` —— 将待写入的更改刷盘
- `close()` —— 刷盘并关闭后端
- 支持上下文管理器（`with ... as d:`）

键必须是 `str`。非字符串键抛出 `TypeError`。

### JsonFileBackend

```python
JsonFileBackend(path: str | os.PathLike)
```

将整个 JSON 文件加载到内存。变更在内存中缓冲，在 `flush()` 或 `close()` 时原子写入（临时文件 + `os.replace`）。

### SqliteBackend

```python
SqliteBackend(path: str | os.PathLike, table: str = "items")
```

每次 `set`/`delete`/`clear` 立即提交。使用 WAL 日志模式支持并发访问。表名必须匹配 `[A-Za-z_][A-Za-z0-9_]*`。

### Serializer 协议

```python
class Serializer(Protocol):
    def dumps(self, obj: Any) -> str: ...
    def loads(self, s: str) -> Any: ...
```

### JsonSerializer

```python
JsonSerializer(*, ensure_ascii: bool = False, **kwargs)
```

默认序列化器，封装 `json.dumps` / `json.loads`。额外 `**kwargs` 转发给 `json.dumps`。

## 注意事项

!!! warning "键必须是字符串"
    所有键必须是 `str`。这与 JSON 的对象键限制和 SQLite 的 `TEXT PRIMARY KEY` 一致。使用非字符串键会抛出 `TypeError`。

!!! tip "JSON 与 SQLite 的选择"
    对于小数据集（几百条记录）且需要人类可读性时，使用 **JSON 后端**。对于大数据集、频繁写入或多进程访问，使用 **SQLite 后端**（WAL 模式提供安全的并发）。

!!! info "JSON 后端仅单进程"
    JSON 文件后端不支持多进程并发访问。多进程场景请使用 SQLite 后端。

!!! info "无 Pickle"
    与 `sqlitedict` 和 `shelve` 不同，本模块默认使用 JSON 序列化，避免反序列化漏洞（CVE-2024-35515）。如需其他格式，可注入自定义序列化器，但有意不提供 pickle。

- **线程安全**：默认通过 `threading.Lock` 开启。单线程场景可用 `lock=False` 禁用。
- **原子写入**：JSON 后端先写临时文件再重命名。SQLite 使用数据库事务。
- **Python 版本**：需要 Python 3.10+。
