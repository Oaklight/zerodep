# 缓存

零依赖的内存缓存模块，支持 TTL 过期、多种淘汰策略，兼容同步与异步装饰器。

## 概述

`cache.py` 是一个单文件缓存模块，提供四种淘汰策略（LRU、FIFO、LFU、TTL）的 `MutableMapping` 缓存类和自动检测同步/异步的 `cached()` 装饰器。要求 **Python 3.10+**，**无需任何 pip 依赖**。

| 文件 | 说明 | 依赖 |
|------|------|------|
| `cache.py` | 纯 Python 实现 | 无（仅标准库：`collections`、`functools`、`time`、`threading`、`asyncio`、`inspect`） |

## 功能特性

- **四种缓存类** -- `LRUCache`、`FIFOCache`、`LFUCache`、`TTLCache`，均实现 `MutableMapping` 协议
- **同步 + 异步装饰器** -- `cached()` 自动检测协程函数，使用对应的锁类型
- **便捷装饰器** -- `lru_cache()`、`ttl_cache()`、`lfu_cache()`、`fifo_cache()`，支持三种调用形式（`@dec`、`@dec()`、`@dec(args)`）
- **线程安全** -- 可选 `lock` 参数，支持 `threading.Lock`（同步）或 `asyncio.Lock`（异步）
- **TTL 过期** -- 全局 TTL，惰性过期 + 显式 `expire()` 方法
- **O(1) LFU** -- 双向链表频率表，常数时间淘汰和访问
- **缓存统计** -- `info=True` 时提供 `cache_info()` 返回 `CacheInfo(hits, misses, maxsize, currsize)`
- **自定义键函数** -- `hashkey`、`methodkey`、`typedkey`
- **自定义大小** -- `getsizeof` 参数支持按值大小加权

## 快速开始

### 便捷装饰器

```python
from cache import lru_cache, ttl_cache, lfu_cache, fifo_cache

# LRU 缓存（类似 functools.lru_cache，功能更多）
@lru_cache(maxsize=256)
def fibonacci(n):
    return n if n < 2 else fibonacci(n - 1) + fibonacci(n - 2)

# TTL 缓存 -- 条目 60 秒后过期
@ttl_cache(maxsize=100, ttl=60)
def fetch_config(key):
    return load_from_db(key)

# LFU 缓存 -- 淘汰最不常用的条目
@lfu_cache(maxsize=128)
def get_user(user_id):
    return db.query(user_id)

# FIFO 缓存 -- 淘汰最早插入的条目
@fifo_cache(maxsize=64)
def parse_template(name):
    return compile_template(name)
```

所有便捷装饰器支持三种调用形式：

```python
# 裸装饰器（默认参数）
@lru_cache
def f(x): ...

# 空括号（与裸装饰器相同）
@lru_cache()
def f(x): ...

# 带参数
@lru_cache(maxsize=512)
def f(x): ...
```

### 异步支持

```python
import asyncio
from cache import lru_cache, ttl_cache, cached, LRUCache

# 便捷装饰器自动检测异步
@lru_cache(maxsize=128)
async def fetch_user(user_id):
    return await db.get_user(user_id)

# TTL 缓存用于 API 响应
@ttl_cache(maxsize=50, ttl=300)
async def get_weather(city):
    return await api.get(f"/weather/{city}")

# 底层 cached() 配合异步锁
@cached(LRUCache(maxsize=128), lock=asyncio.Lock(), info=True)
async def expensive_query(params):
    return await run_query(params)

async def main():
    result = await fetch_user(42)
    info = expensive_query.cache_info()
    print(f"命中: {info.hits}, 未命中: {info.misses}")

asyncio.run(main())
```

### 直接使用缓存类

```python
from cache import LRUCache, TTLCache, FIFOCache, LFUCache

# LRU 缓存作为字典容器
cache = LRUCache(maxsize=100)
cache["key1"] = "value1"
cache["key2"] = "value2"
print(cache["key1"])      # "value1" -- 同时标记为最近使用
print(len(cache))         # 2

# TTL 缓存 -- 条目自动过期
import time
ttl = TTLCache(maxsize=100, ttl=10)  # 10 秒 TTL
ttl["session"] = {"user": "alice"}
time.sleep(11)
print(ttl.get("session"))  # None -- 已过期

# 显式清理过期条目
ttl.expire()
```

### 缓存统计

```python
from cache import lru_cache

@lru_cache(maxsize=128, info=True)
def compute(x, y):
    return x ** y

compute(2, 10)  # 未命中
compute(2, 10)  # 命中
compute(3, 10)  # 未命中

info = compute.cache_info()
print(info)  # CacheInfo(hits=1, misses=2, maxsize=128, currsize=2)

compute.cache_clear()
info = compute.cache_info()
print(info.currsize)  # 0
```

### 线程安全

```python
import threading
from cache import cached, LRUCache

@cached(LRUCache(maxsize=256), lock=threading.Lock())
def thread_safe_lookup(key):
    return expensive_computation(key)
```

!!! note "计算期间释放锁"
    锁在被包装函数执行期间会被释放，避免慢操作阻塞其他线程。重新获取锁后使用 `setdefault()` 处理竞态条件——另一个线程可能已经填充了同一缓存条目。

### 自定义键函数

```python
from cache import cached, LRUCache, methodkey, typedkey

# 用于方法 -- 缓存键忽略 self
class MyService:
    @cached(LRUCache(maxsize=128), key=methodkey)
    def get_data(self, query):
        return self.db.execute(query)

# 类型感知键 -- f(1) 和 f(1.0) 视为不同调用
@cached(LRUCache(maxsize=128), key=typedkey)
def convert(value):
    return process(value)
```

### 自定义大小

```python
from cache import LRUCache

# 按值长度加权的缓存
cache = LRUCache(maxsize=1000, getsizeof=len)
cache["small"] = "hi"       # 大小 2
cache["large"] = "x" * 500  # 大小 500
print(cache.currsize)        # 502
```

## API 参考

### 缓存类

#### `Cache(maxsize, getsizeof=None)`

抽象基类，实现 `MutableMapping`。所有缓存类型继承自此类。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `maxsize` | `int` | -- | 缓存最大容量 |
| `getsizeof` | `Callable \| None` | `None` | 自定义大小函数 `(value) -> int`，默认每个条目大小为 1 |

| 属性 | 类型 | 说明 |
|------|------|------|
| `maxsize` | `int` | 缓存最大容量 |
| `currsize` | `int` | 当前缓存大小 |

---

#### `LRUCache(maxsize, getsizeof=None)`

最近最少使用缓存。访问条目会将其移到末尾（最近使用），缓存满时淘汰最久未使用的条目。

---

#### `FIFOCache(maxsize, getsizeof=None)`

先进先出缓存。访问条目**不会**改变其位置，缓存满时淘汰最早插入的条目。

---

#### `LFUCache(maxsize, getsizeof=None)`

最不常用缓存。使用 O(1) 双向链表跟踪访问频率，缓存满时淘汰访问次数最少的条目。

---

#### `TTLCache(maxsize, ttl, timer=time.monotonic, getsizeof=None)`

带 TTL 过期的 LRU 缓存。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `maxsize` | `int` | -- | 缓存最大容量 |
| `ttl` | `float` | -- | 所有条目的存活时间（秒） |
| `timer` | `Callable` | `time.monotonic` | 计时器函数 |
| `getsizeof` | `Callable \| None` | `None` | 自定义大小函数 |

| 方法 | 说明 |
|------|------|
| `expire(time=None)` | 清除截至 `time`（默认当前时间）的所有过期条目 |

---

### 键函数

#### `hashkey(*args, **kwargs)`

默认键函数。返回位置参数和关键字参数的可哈希元组。

#### `methodkey(self, *args, **kwargs)`

方法专用键函数。忽略第一个位置参数（`self`）。

#### `typedkey(*args, **kwargs)`

类似 `hashkey`，但在键中包含参数类型，`f(1)` 和 `f(1.0)` 会生成不同的键。

---

### 装饰器

#### `cached(cache, *, key=hashkey, lock=None, info=False)`

通用缓存装饰器，自动检测同步/异步函数。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `cache` | `MutableMapping \| None` | -- | 缓存实例。传 `None` 禁用缓存（直通调用） |
| `key` | `Callable` | `hashkey` | 缓存键生成函数 |
| `lock` | `Lock \| None` | `None` | `threading.Lock`（同步）或 `asyncio.Lock`（异步） |
| `info` | `bool` | `False` | 为 `True` 时为包装函数添加 `cache_info()` 和 `cache_clear()` 方法 |

**包装函数属性**（`info=True` 时）：

- `cache_info() -> CacheInfo` -- 返回 `CacheInfo(hits, misses, maxsize, currsize)`
- `cache_clear()` -- 清空缓存并重置统计
- `__wrapped__` -- 原始函数引用

---

#### `lru_cache(fn=None, *, maxsize=128, key=hashkey, lock=None, info=True)`

使用 `LRUCache` 的便捷装饰器。

#### `ttl_cache(fn=None, *, maxsize=128, ttl=600, timer=time.monotonic, key=hashkey, lock=None, info=True)`

使用 `TTLCache` 的便捷装饰器。

#### `lfu_cache(fn=None, *, maxsize=128, key=hashkey, lock=None, info=True)`

使用 `LFUCache` 的便捷装饰器。

#### `fifo_cache(fn=None, *, maxsize=128, key=hashkey, lock=None, info=True)`

使用 `FIFOCache` 的便捷装饰器。

所有便捷装饰器支持 `@dec`、`@dec()` 和 `@dec(args)` 三种调用形式。

---

### `CacheInfo`

`cache_info()` 返回的命名元组。

| 字段 | 类型 | 说明 |
|------|------|------|
| `hits` | `int` | 缓存命中次数 |
| `misses` | `int` | 缓存未命中次数 |
| `maxsize` | `int \| None` | 缓存最大容量，未知时为 `None` |
| `currsize` | `int` | 当前条目数量 |

## 与 cachetools / functools.lru_cache 对比

| 特性 | zerodep cache | cachetools | functools.lru_cache |
|------|--------------|------------|---------------------|
| 依赖 | 无（仅标准库） | 无 | 标准库 |
| LRU | 是 | 是 | 是 |
| FIFO | 是 | 是 | 否 |
| LFU | 是 | 是 | 否 |
| TTL | 是 | 是 | 否 |
| 异步装饰器 | **是** | **否** | **否** |
| 自定义键函数 | 是 | 是 | 仅 typed=True |
| 自定义大小 | 是 | 是 | 否 |
| 线程安全 | 是（lock 参数） | 是（lock 参数） | 内置 |
| cache_info() | 是 | 是 | 是 |
| MutableMapping | 是 | 是 | 否 |
| 实现 | 单文件（~1050 行） | 包（~1200 行） | C 扩展 |

**何时使用 zerodep：** 需要异步缓存支持、零 pip 依赖、或单文件嵌入。

**何时使用 cachetools：** 需要 `cachedmethod`、`TLRUCache`（按条目 TTL 函数）、`RRCache`（随机替换）或 `MRUCache`。

**何时使用 functools.lru_cache：** 简单 LRU 场景，无需 TTL/淘汰策略，追求 C 扩展的极致性能。

## 性能测试

与 `cachetools` 在 LRU 读写、淘汰压力、TTL 过期、装饰器开销、键函数、混合负载等场景下进行了对比测试。

详见 [缓存性能测试](../benchmarks/cache.md)。
