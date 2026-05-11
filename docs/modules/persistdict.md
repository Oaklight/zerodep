# Persistent Dictionary

Persistent dictionary with pluggable backends -- zero dependencies, stdlib only, Python 3.10+.

> **Replaces:** `sqlitedict`, `diskcache` (dict)

## Overview

The `persistdict` module provides a `MutableMapping` that persists key-value pairs to disk. It supports multiple storage backends with pluggable serialization and is thread-safe by default.

| Backend | Storage | Write Mode | Best For |
|---------|---------|------------|----------|
| `JsonFileBackend` | Single JSON file | Buffered (flush on close) | Small datasets, human-readable storage |
| `SqliteBackend` | SQLite database | Write-through (immediate) | Large datasets, concurrent access |

### Key Features

- **Drop-in `dict` replacement** — implements `collections.abc.MutableMapping`
- **JSON serialization by default** — no pickle, no deserialization vulnerabilities
- **Pluggable serializer** — inject custom `dumps`/`loads` for any format
- **Pluggable backends** — JSON file or SQLite, auto-detected from file extension
- **Thread-safe** — optional `threading.Lock` (enabled by default)
- **Atomic writes** — JSON backend uses temp file + `os.replace`; SQLite uses transactions
- **Namespaces** — multiple logical dicts in one SQLite file via `table` parameter

## How to Use in Your Project

```bash
cp persistdict/persistdict.py your_project/
```

```python
from persistdict import open
```

## Usage Examples

### Basic Usage (Auto-Detect Backend)

```python
from persistdict import open

# .json extension → JSON file backend
with open("data.json") as d:
    d["name"] = "Alice"
    d["scores"] = [95, 87, 92]

# Reopen — data persists
with open("data.json") as d:
    print(d["name"])      # "Alice"
    print(len(d))         # 2
```

### SQLite Backend for Larger Datasets

```python
from persistdict import open

# .db extension → SQLite backend (WAL mode, write-through)
with open("data.db") as d:
    for i in range(10000):
        d[f"key_{i}"] = {"index": i, "active": True}
    print(len(d))  # 10000
```

### Multiple Namespaces in One Database

```python
from persistdict import open

with open("app.db", table="users") as users:
    users["alice"] = {"email": "alice@example.com", "role": "admin"}

with open("app.db", table="config") as config:
    config["debug"] = False
    config["max_workers"] = 4
```

### Custom Serializer

```python
from persistdict import PersistDict, SqliteBackend

class CompactSerializer:
    """Store values as repr() strings."""
    def dumps(self, obj):
        return repr(obj)
    def loads(self, s):
        return eval(s)  # Only for trusted data!

backend = SqliteBackend("custom.db")
d = PersistDict(backend, serializer=CompactSerializer())
d["key"] = (1, 2, 3)
d.close()
```

### Explicit Backend Selection

```python
from persistdict import open

# Force SQLite even for .dat extension
with open("data.dat", backend="sqlite") as d:
    d["key"] = "value"

# Force JSON for any extension
with open("store.bin", backend="json") as d:
    d["key"] = "value"
```

### Thread-Safe Operations

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

To disable locking (single-threaded use):

```python
d = open("data.db", lock=False)
```

## API Reference

### Factory Function

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

- **path**: File path for storage
- **backend**: `"auto"` (detect from extension), `"json"`, or `"sqlite"`
    - Auto-detection: `.json` → JSON, `.db` / `.sqlite` / `.sqlite3` → SQLite
- **serializer**: Value serializer (default: `JsonSerializer`)
- **lock**: `True` (new Lock), `False` (no locking), or a `threading.Lock` instance
- **table**: Table name for SQLite backend (ignored for JSON)

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

Supports all standard `dict` operations: `__getitem__`, `__setitem__`, `__delitem__`, `__iter__`, `__len__`, `__contains__`, `get`, `pop`, `popitem`, `clear`, `update`, `setdefault`, `keys`, `values`, `items`.

Additional methods:

- `flush()` — write pending changes to disk
- `close()` — flush and close the backend
- Context manager support (`with ... as d:`)

Keys must be `str`. Non-string keys raise `TypeError`.

### JsonFileBackend

```python
JsonFileBackend(path: str | os.PathLike)
```

Loads the entire JSON file into memory. Mutations are buffered and flushed atomically (temp file + `os.replace`) on `flush()` or `close()`.

### SqliteBackend

```python
SqliteBackend(path: str | os.PathLike, table: str = "items")
```

Each `set`/`delete`/`clear` is committed immediately. Uses WAL journal mode for concurrent access. Table names must match `[A-Za-z_][A-Za-z0-9_]*`.

### Serializer Protocol

```python
class Serializer(Protocol):
    def dumps(self, obj: Any) -> str: ...
    def loads(self, s: str) -> Any: ...
```

### JsonSerializer

```python
JsonSerializer(*, ensure_ascii: bool = False, **kwargs)
```

Default serializer wrapping `json.dumps` / `json.loads`. Extra `**kwargs` are forwarded to `json.dumps`.

## Notes and Caveats

!!! warning "Keys Must Be Strings"
    All keys must be `str`. This matches JSON's object key restriction and SQLite's `TEXT PRIMARY KEY`. Using non-string keys raises `TypeError`.

!!! tip "JSON vs SQLite"
    Use the **JSON backend** for small datasets (hundreds of items) where human readability matters. Use the **SQLite backend** for larger datasets, frequent writes, or multi-process access (WAL mode provides safe concurrency).

!!! info "JSON Backend is Single-Process"
    The JSON file backend is not safe for concurrent access from multiple processes. For multi-process scenarios, use the SQLite backend.

!!! info "No Pickle"
    Unlike `sqlitedict` and `shelve`, this module uses JSON serialization by default, avoiding deserialization vulnerabilities (CVE-2024-35515). You can inject a custom serializer if needed, but pickle is intentionally not provided.

- **Thread safety**: Enabled by default via `threading.Lock`. Disable with `lock=False` for single-threaded use.
- **Atomic writes**: JSON backend writes to a temp file then renames. SQLite uses database transactions.
- **Python version**: Requires Python 3.10+.
