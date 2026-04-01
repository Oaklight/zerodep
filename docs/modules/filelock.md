# File Lock

Cross-platform advisory file lock using only the Python standard library -- Python 3.10+.

## Overview

The `filelock` module provides a single-file, zero-dependency advisory file lock. On Unix/macOS it delegates to `fcntl.flock`; on Windows it uses `msvcrt.locking` with exponential-backoff polling for blocking semantics.

| File | Description | Dependencies |
|------|-------------|--------------|
| `filelock.py` | Cross-platform file lock | None (stdlib only: `os`, `sys`, `time`, `pathlib`) |

### Key Features

- **Cross-platform** -- `fcntl.flock` on Unix/macOS, `msvcrt.locking` on Windows
- **Context manager** -- `with lock:` syntax for safe acquire/release
- **Non-blocking try** -- `try_lock()` returns `True`/`False` without waiting
- **Auto parent-dir creation** -- creates intermediate directories if needed
- **Safe lifecycle** -- double `close()` and `unlock()` without prior `lock()` are no-ops

## How to Use in Your Project

Copy the single file into your project:

```bash
cp filelock/filelock.py your_project/
```

Then import:

```python
from filelock import FileLock
```

## Usage Examples

### Blocking Lock (Context Manager)

```python
from pathlib import Path
from filelock import FileLock

lock = FileLock(Path("/tmp/.my.lock"))

with lock:
    # Exclusive access guaranteed
    ...
```

### Non-Blocking Try

```python
lock = FileLock("/tmp/.my.lock")

if lock.try_lock():
    try:
        # Got the lock
        ...
    finally:
        lock.unlock()
else:
    print("Lock is held by another process")
```

### Manual Lock/Unlock

```python
lock = FileLock("/tmp/.my.lock")

lock.lock()      # blocks until available
try:
    ...
finally:
    lock.unlock()

lock.close()     # release lock + close file descriptor
```

### Auto Parent Directory Creation

```python
# Intermediate directories are created automatically
lock = FileLock("/tmp/sub/dir/.lock")
with lock:
    ...  # /tmp/sub/dir/ was created
```

## Design Notes

### Advisory Locking

The lock is *advisory* -- it coordinates only among processes that voluntarily use the same lock file. It does **not** prevent other programs from reading or writing the locked file.

### Reentrancy

`FileLock` is **not** reentrant across instances. Two different `FileLock` objects pointing at the same path will deadlock on Unix if one tries to lock while the other holds it. Within the same instance, calling `lock()` twice without an intermediate `unlock()` is safe (the OS silently succeeds).

### Windows Blocking Strategy

Windows `msvcrt.locking` with `LK_LOCK` retries for only ~1 second. For robust blocking, the module polls with `LK_NBLCK` using exponential backoff (10ms to 500ms).

## API Reference

### `FileLock(path)`

Advisory file lock backed by `fcntl.flock` (Unix) or `msvcrt.locking` (Windows).

**Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `path` | `Path \| str` | Path to the lock file (created automatically if missing) |

**Methods:**

| Method | Description |
|--------|-------------|
| `lock()` | Acquire the lock, blocking until available |
| `try_lock()` | Try to acquire without blocking. Returns `True` if acquired |
| `unlock()` | Release the lock (no-op if not held) |
| `close()` | Release lock and close the underlying file descriptor |

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `path` | `Path` | The lock-file path |

**Context Manager:**

```python
with FileLock("/tmp/.lock") as lock:
    ...  # lock.unlock() called automatically on exit
```
