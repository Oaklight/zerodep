# 持久化字典性能测试

zerodep persistdict（JSON 和 SQLite 后端）与标准库 [`shelve`](https://docs.python.org/3/library/shelve.html) 及 [`sqlitedict`](https://pypi.org/project/sqlitedict/) 的性能对比。

!!! info "测试环境"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **工具:** pytest-benchmark 5.2.3（报告均值）
    - **对标库:** sqlitedict 2.1.0
    - **最后更新:** 2026-04-21

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
| 小型 (50) | 422.7 μs | 2,970.0 μs | 449.1 μs | -- |
| 大型 (2,000) | 16,110.0 μs | 24,510.0 μs | 12,450.0 μs | -- |

### 写入对比 vs shelve

| 数据规模 | zerodep JSON vs shelve | zerodep SQLite vs shelve |
|----------|------------------------|--------------------------|
| 小型 | 持平 | 慢 6.6x |
| 大型 | 慢 1.3x | 慢 2.0x |

## 读取性能 — 小型（50 条目，均值）

| 实现 | 耗时 |
|------|------|
| zerodep JSON | 403.6 μs |
| zerodep SQLite | 811.2 μs |
| shelve | 184.5 μs |

### 读取对比 vs shelve

| zerodep JSON | zerodep SQLite |
|-------------|---------------|
| 慢 2.2x | 慢 4.4x |

## 遍历性能 — 小型（50 条目，均值）

| 实现 | 耗时 |
|------|------|
| zerodep JSON | 427.4 μs |
| zerodep SQLite | 847.1 μs |
| shelve | 204.0 μs |

### 遍历对比 vs shelve

| zerodep JSON | zerodep SQLite |
|-------------|---------------|
| 慢 2.1x | 慢 4.2x |

## 要点总结

- **JSON 后端小规模写入持平** -- 50 条目时，zerodep JSON 写入性能与 shelve 持平（速度相当）。
- **SQLite 后端以速度换取持久性** -- 延迟提交配合 `PRAGMA synchronous=NORMAL` 在持久性和性能间取得平衡。通过 `commit_every` 参数进行批量写入可进一步降低每次写入的开销，但 shelve 的 dbm 后端在原始吞吐量上仍更快。
- **shelve 读取和遍历更快** -- shelve 基于 dbm 的键值查找比 zerodep 在小型数据集上的读取和遍历操作快 2-4 倍。
- **无 pickle** -- 不同于 shelve，zerodep 默认使用 JSON 序列化，避免反序列化漏洞。这是安全性需求场景下的主要优势。
- **可移植性和透明性** -- zerodep 的 JSON 后端生成人类可读的文件，SQLite 后端使用标准数据库格式，两者都比 dbm 文件更便携、更易于检查。

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
