# 缓存性能测试

zerodep cache 与 [`cachetools`](https://pypi.org/project/cachetools/) 的性能对比。

!!! info "测试环境"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **工具:** pytest-benchmark 5.2.3（报告均值）
    - **对标库:** cachetools 7.0.5
    - **最后更新:** 2026-04-20

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
| LRU 读写 | 894 μs | 928 μs | **快 1.0x** |
| LRU 淘汰压力 | 1,503 μs | 1,572 μs | **快 1.0x** |
| LFU 淘汰压力 | 1,855 μs | 1,850 μs | 持平 |
| TTL 过期 | 3,587 μs | 3,520 μs | 持平 |
| 装饰器（LRU） | 203 μs | 202 μs | 持平 |
| 装饰器（TTL） | 304 μs | 233 μs | 慢 1.3x |
| hashkey | 405 μs | 430 μs | **快 1.1x** |
| typedkey | 1,056 μs | 1,256 μs | **快 1.2x** |
| 混合负载 | 748 μs | 774 μs | **快 1.0x** |

## 要点总结

- **核心缓存操作持平** -- LRU 读写、LRU 淘汰、TTL 过期、混合负载与 cachetools 在误差范围内持平，zerodep 在 LRU 和混合负载上略快。
- **LFU 淘汰现已持平** -- 在 `popitem` 中绕过 `__touch` 后，LFU 淘汰压力与 cachetools 持平（此前慢 1.4 倍）。
- **TTL 装饰器慢 1.3 倍** -- cachetools 更简单的包装路径在 TTL 装饰函数调用上开销更低。LRU 装饰器开销两者基本一致。
- **hashkey 快 1.1 倍，typedkey 快 1.2 倍** -- zerodep 的 `_HashedTuple` 实现在键生成上略优于 cachetools。typedkey 通过一次性元组构造和移除冗余 `sorted()` 后现快 1.2 倍（此前慢 1.3 倍）。
- **异步支持是核心差异化** -- cachetools **完全不支持异步装饰器**。zerodep 的 `cached()` 及所有便捷装饰器自动检测异步函数，使用 `asyncio.Lock` 保证并发安全。

## 自行运行

```bash
pip install pytest pytest-benchmark cachetools
pytest cache/test_cache_benchmark.py --benchmark-only -v
```

---

## 最新 CI 结果

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/cache.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> 每次发版时通过 [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml) 自动更新。
