# 异步 SQLite

零依赖的 Python 内置 `sqlite3` 异步封装。

> **替代:** `aiosqlite`

## 概述

aiosqlite 模块通过每个连接一个独立工作线程的方式，为 `sqlite3` 提供异步接口。所有阻塞的 SQLite 操作在工作线程上执行，通过 asyncio 协程等待，防止数据库 I/O 阻塞事件循环。

| 文件 | 说明 | 依赖 |
|------|------|------|
| `aiosqlite.py` | 异步 sqlite3 封装 | 无（仅标准库：`asyncio`、`sqlite3`、`threading`、`queue`） |

## 主要特性

- **独立工作线程** -- 每个连接一个守护线程，确保线程安全的 SQLite 访问
- **完整 API 镜像** -- `execute`、`executemany`、`executescript`、`commit`、`rollback`、异步游标迭代
- **便捷方法** -- `execute_fetchall`、`execute_fetchone`、`execute_insert`，单次往返操作
- **双连接模式** -- 同时支持 `async with connect(...)` 和 `db = await connect(...)`
- **属性透传** -- `row_factory`、`isolation_level`、`in_transaction`、`total_changes`
- **异常重导出** -- `aiosqlite.OperationalError` 等，无需导入 `sqlite3`
- **资源安全** -- 未关闭连接触发 `ResourceWarning`，`__del__` 中清理工作线程

## 使用方式

```bash
cp aiosqlite/aiosqlite.py your_project/
```

## 使用示例

### 基本 CRUD

```python
import aiosqlite

async def main():
    async with aiosqlite.connect("app.db") as db:
        await db.execute("CREATE TABLE IF NOT EXISTS kv (k TEXT PRIMARY KEY, v TEXT)")
        await db.execute("INSERT INTO kv VALUES (?, ?)", ("hello", "world"))
        await db.commit()

        cursor = await db.execute("SELECT v FROM kv WHERE k = ?", ("hello",))
        row = await cursor.fetchone()
        print(row)  # ('world',)
```

### 异步游标迭代

```python
async with aiosqlite.connect("app.db") as db:
    async for row in await db.execute("SELECT * FROM kv"):
        print(row)
```

### 便捷方法

```python
async with aiosqlite.connect("app.db") as db:
    rows = await db.execute_fetchall("SELECT * FROM kv WHERE k LIKE ?", ("%h%",))
    row = await db.execute_fetchone("SELECT COUNT(*) FROM kv")
    rowid = await db.execute_insert("INSERT INTO kv (k, v) VALUES (?, ?)", ("key", "val"))
    await db.commit()
```

### 批量操作

```python
async with aiosqlite.connect("app.db") as db:
    data = [("k1", "v1"), ("k2", "v2"), ("k3", "v3")]
    await db.executemany("INSERT INTO kv VALUES (?, ?)", data)
    await db.commit()
```

### WAL 模式

```python
async with aiosqlite.connect("app.db") as db:
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA synchronous=NORMAL")
```
