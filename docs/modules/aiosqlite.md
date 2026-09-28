# Async SQLite

Zero-dependency async wrapper for Python's built-in `sqlite3` module.

> **Replaces:** `aiosqlite`

## Overview

The aiosqlite module provides an async interface to `sqlite3` using a dedicated worker thread per connection. All blocking SQLite operations run on the worker thread and are awaited from asyncio coroutines, preventing database I/O from blocking the event loop.

| File | Description | Dependencies |
|------|-------------|--------------|
| `aiosqlite.py` | Async sqlite3 wrapper | None (stdlib only: `asyncio`, `sqlite3`, `threading`, `queue`) |

## Key Features

- **Dedicated worker thread** -- one daemon thread per connection for thread-safe SQLite access
- **Full API mirror** -- `execute`, `executemany`, `executescript`, `commit`, `rollback`, async cursor iteration
- **Convenience shortcuts** -- `execute_fetchall`, `execute_fetchone`, `execute_insert` for single-roundtrip operations
- **Dual connect pattern** -- both `async with connect(...)` and `db = await connect(...)` supported
- **Property passthrough** -- `row_factory`, `isolation_level`, `in_transaction`, `total_changes`
- **Exception re-exports** -- `aiosqlite.OperationalError` etc. without importing `sqlite3`
- **Resource safety** -- `ResourceWarning` on unclosed connections, worker thread cleanup in `__del__`

## How to Use in Your Project

Copy the single `.py` file into your project:

```bash
cp aiosqlite/aiosqlite.py your_project/
```

Then import directly:

```python
import aiosqlite
```

## Usage Examples

### Basic CRUD

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

### Async Cursor Iteration

```python
async with aiosqlite.connect("app.db") as db:
    async for row in await db.execute("SELECT * FROM kv"):
        print(row)
```

### Convenience Methods

```python
async with aiosqlite.connect("app.db") as db:
    # Fetch all rows in one call
    rows = await db.execute_fetchall("SELECT * FROM kv WHERE k LIKE ?", ("%h%",))

    # Fetch single row
    row = await db.execute_fetchone("SELECT COUNT(*) FROM kv")

    # Insert and get lastrowid
    rowid = await db.execute_insert("INSERT INTO kv (k, v) VALUES (?, ?)", ("key", "val"))
    await db.commit()
```

### Bulk Operations

```python
async with aiosqlite.connect("app.db") as db:
    data = [("k1", "v1"), ("k2", "v2"), ("k3", "v3")]
    await db.executemany("INSERT INTO kv VALUES (?, ?)", data)
    await db.commit()
```

### Row Factory

```python
import sqlite3
import aiosqlite

async with aiosqlite.connect("app.db") as db:
    db.row_factory = sqlite3.Row
    cursor = await db.execute("SELECT * FROM kv")
    row = await cursor.fetchone()
    print(row["k"], row["v"])
```

### WAL Mode for Concurrent Reads

```python
async with aiosqlite.connect("app.db") as db:
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA synchronous=NORMAL")
    # Now safe for concurrent readers
```
