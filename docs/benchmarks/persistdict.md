# 持久化字典性能测试

zerodep persistdict（JSON 和 SQLite 后端）与标准库 [`shelve`](https://docs.python.org/3/library/shelve.html) 及 [`sqlitedict`](https://pypi.org/project/sqlitedict/) 的性能对比。

!!! info "测试环境"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **工具:** pytest-benchmark 5.2.3（报告均值）
    - **对标库:** sqlitedict 2.1.0
    - **最后更新:** 2026-04-20

## 实现对比

| 实现 | 后端 | 说明 |
|------|------|------|
| **zerodep (JSON)** | `persistdict.py` | JSON 文件后端，缓冲写入，原子刷新 |
| **zerodep (SQLite)** | `persistdict.py` | SQLite WAL 后端，延迟提交 + `PRAGMA synchronous=NORMAL` |
| **shelve** | *（标准库）* | 基于 dbm 的持久化字典，pickle 序列化 |
| **sqlitedict** | *（参考库）* | 基于 SQLite 的字典，pickle 序列化 |

## 测试数据规模

| 标签 | 条目数 | 值结构 |
|------|--------|--------|
| 小型 | 50 | `{"index": int, "name": str}` |
| 大型 | 2,000 | `{"index": int, "name": str, "tags": [5 strings], "active": bool}` |

## 写入性能（均值）

| 数据规模 | zerodep JSON | zerodep SQLite | shelve | sqlitedict |
|----------|-------------|---------------|--------|------------|
| 小型 (50) | 307.4 μs | 1,279.4 μs | 1,446.4 μs | 13,415.6 μs |
| 大型 (2,000) | 12,236.1 μs | 36,017.8 μs | 47,169.7 μs | 526,946.9 μs |

### 写入加速倍数

| 数据规模 | vs shelve | vs sqlitedict |
|----------|-----------|---------------|
| 小型 (JSON) | **快 4.7x** | **快 43.6x** |
| 小型 (SQLite) | **快 1.1x** | **快 10.5x** |
| 大型 (JSON) | **快 3.9x** | **快 43.1x** |
| 大型 (SQLite) | **快 1.3x** | **快 14.6x** |

## 读取性能 — 小型（50 条目，均值）

| 实现 | 耗时 |
|------|------|
| zerodep JSON | 252.9 μs |
| zerodep SQLite | 532.3 μs |
| shelve | 1,006.2 μs |
| sqlitedict | 7,824.1 μs |

### 读取加速倍数

| 对比 | zerodep JSON | zerodep SQLite |
|------|-------------|---------------|
| shelve | **快 4.0x** | **快 1.9x** |
| sqlitedict | **快 30.9x** | **快 14.7x** |

## 遍历性能 — 小型（50 条目，均值）

| 实现 | 耗时 |
|------|------|
| zerodep JSON | 264.5 μs |
| zerodep SQLite | 591.7 μs |
| shelve | 1,032.6 μs |
| sqlitedict | 1,523.3 μs |

### 遍历加速倍数

| 对比 | zerodep JSON | zerodep SQLite |
|------|-------------|---------------|
| shelve | **快 3.9x** | **快 1.7x** |
| sqlitedict | **快 5.8x** | **快 2.6x** |

## 要点总结

- **JSON 后端整体最快** -- 缓冲写入 + 原子刷新使其成为中小型数据集的最佳选择。
- **SQLite 后端以写入速度换取持久性** -- 延迟提交配合 `PRAGMA synchronous=NORMAL` 在持久性和性能间取得平衡。通过 `commit_every` 参数进行批量写入可进一步降低每次写入的开销。
- **两种后端都远超 sqlitedict** -- 写入快 10-43 倍，读取快 15-31 倍。这是因为 sqlitedict 使用 pickle 序列化且每次操作都有提交开销。
- **明显快于 shelve** -- zerodep JSON 写入比 shelve 快 3.9-4.7 倍，读取快 4.0 倍。SQLite 后端也比 shelve 在各项操作中快 1.1-1.9 倍。
- **无 pickle** -- 不同于 shelve 和 sqlitedict，zerodep 默认使用 JSON 序列化，避免反序列化漏洞。

## 自行运行

```bash
pip install pytest pytest-benchmark sqlitedict
pytest persistdict/test_persistdict_benchmark.py --benchmark-only -v
```

---

## 最新 CI 结果

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/persistdict.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> 每次发版时通过 [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml) 自动更新。
