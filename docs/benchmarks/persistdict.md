# 持久化字典性能测试

zerodep persistdict（JSON 和 SQLite 后端）与标准库 [`shelve`](https://docs.python.org/3/library/shelve.html) 及 [`sqlitedict`](https://pypi.org/project/sqlitedict/) 的性能对比。

!!! info "测试环境"
    - **平台:** x86_64 Linux
    - **Python:** 3.10.20
    - **工具:** pytest-benchmark 5.2.3（报告均值）

## 实现对比

| 实现 | 后端 | 说明 |
|------|------|------|
| **zerodep (JSON)** | `persistdict.py` | JSON 文件后端，缓冲写入，原子刷新 |
| **zerodep (SQLite)** | `persistdict.py` | SQLite WAL 后端，直写模式 |
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
| 小型 (50) | 210.3 μs | 675.6 μs | 644.3 μs | 14,849.8 μs |
| 大型 (2,000) | 12,825.1 μs | 20,957.7 μs | 26,082.2 μs | 685,824.9 μs |

### 写入加速倍数

| 数据规模 | vs shelve | vs sqlitedict |
|----------|-----------|---------------|
| 小型 (JSON) | **快 3.1x** | **快 70.6x** |
| 大型 (JSON) | **快 2.0x** | **快 53.5x** |
| 大型 (SQLite) | **快 1.2x** | **快 32.7x** |

## 读取性能 — 小型（50 条目，均值）

| 实现 | 耗时 |
|------|------|
| zerodep JSON | 302.7 μs |
| zerodep SQLite | 347.9 μs |
| shelve | 521.7 μs |
| sqlitedict | 9,785.8 μs |

### 读取加速倍数

| 对比 | zerodep JSON | zerodep SQLite |
|------|-------------|---------------|
| shelve | **快 1.7x** | **快 1.5x** |
| sqlitedict | **快 32.3x** | **快 28.1x** |

## 遍历性能 — 小型（50 条目，均值）

| 实现 | 耗时 |
|------|------|
| zerodep JSON | 308.7 μs |
| zerodep SQLite | 370.7 μs |
| shelve | 534.5 μs |
| sqlitedict | 1,841.4 μs |

### 遍历加速倍数

| 对比 | zerodep JSON | zerodep SQLite |
|------|-------------|---------------|
| shelve | **快 1.7x** | **快 1.4x** |
| sqlitedict | **快 6.0x** | **快 5.0x** |

## 要点总结

- **JSON 后端整体最快** -- 缓冲写入 + 原子刷新使其成为中小型数据集的最佳选择。
- **SQLite 后端以写入速度换取持久性** -- 直写提交比 JSON 的缓冲方式慢，但每次写入都立即持久化。
- **两种后端都远超 sqlitedict** -- 写入快 30-70 倍，读取快 28-32 倍。这是因为 sqlitedict 使用 pickle 序列化且每次操作都有提交开销。
- **与 shelve 相当甚至更快** -- zerodep JSON 在所有操作中比 shelve 快 1.7-3.1 倍，还具有人类可读存储和无 pickle 漏洞的额外优势。
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
