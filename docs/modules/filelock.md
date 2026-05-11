# 文件锁

跨平台的咨询式文件锁，仅依赖 Python 标准库。要求 Python 3.10+。

> **可替代:** `filelock`

## 概述

`filelock` 模块提供单文件、零依赖的咨询式文件锁。在 Unix/macOS 上使用 `fcntl.flock`；在 Windows 上使用 `msvcrt.locking` 配合指数退避轮询实现阻塞语义。

| 文件 | 说明 | 依赖 |
|------|------|------|
| `filelock.py` | 跨平台文件锁 | 无（仅标准库：`os`、`sys`、`time`、`pathlib`） |

### 功能特性

- **跨平台** -- Unix/macOS 使用 `fcntl.flock`，Windows 使用 `msvcrt.locking`
- **上下文管理器** -- 支持 `with lock:` 语法，安全获取/释放
- **非阻塞尝试** -- `try_lock()` 返回 `True`/`False`，不等待
- **自动创建父目录** -- 如需要会自动创建中间目录
- **安全生命周期** -- 重复 `close()` 和未持有锁时 `unlock()` 均为空操作

## 快速开始

将单文件复制到你的项目中：

```bash
cp filelock/filelock.py your_project/
```

然后导入：

```python
from filelock import FileLock
```

## 使用示例

### 阻塞锁（上下文管理器）

```python
from pathlib import Path
from filelock import FileLock

lock = FileLock(Path("/tmp/.my.lock"))

with lock:
    # 保证独占访问
    ...
```

### 非阻塞尝试

```python
lock = FileLock("/tmp/.my.lock")

if lock.try_lock():
    try:
        # 获得了锁
        ...
    finally:
        lock.unlock()
else:
    print("锁被另一个进程持有")
```

### 手动锁定/解锁

```python
lock = FileLock("/tmp/.my.lock")

lock.lock()      # 阻塞直到可用
try:
    ...
finally:
    lock.unlock()

lock.close()     # 释放锁 + 关闭文件描述符
```

### 自动创建父目录

```python
# 中间目录会自动创建
lock = FileLock("/tmp/sub/dir/.lock")
with lock:
    ...  # /tmp/sub/dir/ 已被创建
```

## 设计说明

### 咨询式锁

该锁是*咨询式*的——仅在主动使用同一锁文件的进程间协调。它**不会**阻止其他程序读写被锁定的文件。

### 可重入性

`FileLock` 在跨实例时**不可重入**。两个不同的 `FileLock` 对象指向同一路径时，在 Unix 上如果一个持有锁另一个尝试获取会死锁。在同一实例内，未先 `unlock()` 就再次调用 `lock()` 是安全的（操作系统静默成功）。

### Windows 阻塞策略

Windows 的 `msvcrt.locking` 使用 `LK_LOCK` 仅重试约 1 秒。为实现可靠的阻塞语义，模块使用 `LK_NBLCK` 配合指数退避轮询（10ms 到 500ms）。

## API 参考

### `FileLock(path)`

基于 `fcntl.flock`（Unix）或 `msvcrt.locking`（Windows）的咨询式文件锁。

**参数：**

| 参数名 | 类型 | 说明 |
|--------|------|------|
| `path` | `Path \| str` | 锁文件路径（不存在时自动创建） |

**方法：**

| 方法 | 说明 |
|------|------|
| `lock()` | 获取锁，阻塞直到可用 |
| `try_lock()` | 非阻塞尝试获取锁。成功返回 `True` |
| `unlock()` | 释放锁（未持有时为空操作） |
| `close()` | 释放锁并关闭底层文件描述符 |

**属性：**

| 属性 | 类型 | 说明 |
|------|------|------|
| `path` | `Path` | 锁文件路径 |

**上下文管理器：**

```python
with FileLock("/tmp/.lock") as lock:
    ...  # 退出时自动调用 lock.unlock()
```
