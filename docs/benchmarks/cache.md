# 缓存性能测试

zerodep cache 与 [`cachetools`](https://pypi.org/project/cachetools/) 的性能对比。

!!! info "测试环境"
    - **CPU:** x86_64 Linux
    - **Python:** 3.10
    - **工具:** pytest-benchmark 5.2.3（报告均值）

## 实现对比

| 实现 | 文件/包 | 说明 |
|------|---------|------|
| **zerodep** | `cache.py` | 仅依赖标准库，支持同步/异步 |
| **cachetools** | *（参考库）* | 流行的缓存库（无异步支持） |

## 测试项目

| 测试项 | 说明 |
|--------|------|
| LRU 读写 | 对 LRUCache（maxsize=256）执行 500 次写入 + 500 次读取 |
| LRU 淘汰压力 | 向 LRUCache（maxsize=64）写入 1000 次，持续触发淘汰 |
| LFU 淘汰压力 | 向 LFUCache（maxsize=64）写入 1000 次，持续触发淘汰 |
| TTL 过期 | 插入 500 个条目，等待过期后调用 `expire()` |
| 装饰器开销（LRU） | 通过 `@lru_cache` 执行 200 次缓存函数调用（50 个唯一键） |
| 装饰器开销（TTL） | 通过 `@ttl_cache` 执行 200 次缓存函数调用（50 个唯一键） |
| hashkey | 调用 `hashkey(1, "hello", 3.14, True, a=1, b="two", c=None)` 500 次 |
| typedkey | 调用 `typedkey(1, "hello", 3.14, True, a=1, b="two", c=None)` 500 次 |
| 混合负载 | 对 LRUCache（maxsize=128）执行 300 次写 + 300 次读 + 100 次删 + 150 次写 |

## 性能对比（均值）

| 测试项 | zerodep | cachetools | 倍数 |
|--------|---------|------------|------|
| LRU 读写 | 734 us | 695 us | 0.95x |
| LRU 淘汰压力 | 1,251 us | 1,196 us | 0.96x |
| LFU 淘汰压力 | 2,284 us | 3,680 us | **1.6x 更快** |
| TTL 过期 | 4,368 us | 4,119 us | 0.94x |
| 装饰器（LRU） | 258 us | 143 us | 0.56x |
| 装饰器（TTL） | 214 us | 167 us | 0.78x |
| hashkey | 232 us | 271 us | **1.2x 更快** |
| typedkey | 950 us | 899 us | 0.94x |
| 混合负载 | 623 us | 604 us | 0.97x |

## 要点总结

- **LFU 快 1.6 倍** -- zerodep 的 O(1) 双向链表频率表在淘汰压力下明显优于 cachetools 基于计数器的 LFU 实现。
- **缓存类操作持平** -- LRU 读写、淘汰、TTL 过期、混合负载与 cachetools 差距在 5% 以内。
- **装饰器开销较高** -- cachetools 更简单的包装路径使装饰函数调用快 1.3-1.8 倍。这是固定的每次调用开销（数十纳秒级），对于任何非简单的被包装函数可忽略不计。
- **hashkey 快 1.2 倍** -- zerodep 的 `_HashedTuple` 实现在键生成上略优于 cachetools。
- **异步支持是核心差异化** -- cachetools **完全不支持异步装饰器**。zerodep 的 `cached()` 及所有便捷装饰器自动检测异步函数，使用 `asyncio.Lock` 保证并发安全。

## 自行运行

```bash
pip install pytest pytest-benchmark cachetools
pytest cache/test_cache_benchmark.py --benchmark-only -v
```
