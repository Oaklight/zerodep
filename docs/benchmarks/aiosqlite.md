# 异步 SQLite 基准测试

zerodep aiosqlite 与 [`aiosqlite`](https://pypi.org/project/aiosqlite/) 的同类性能对比。

!!! info "测试环境"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **工具:** pytest-benchmark 5.2.3（报告均值）
    - **参考库:** aiosqlite 0.22.0
    - **最后更新:** 2026-09-28

## 实现

| 实现 | 文件/包 | 说明 |
|------|---------|------|
| **zerodep** | `aiosqlite.py` | 仅标准库的异步 sqlite3 封装 |
| **aiosqlite** | *（参考库）* | 流行的异步 sqlite3 库 |

## 测试项目

| 测试 | 说明 |
|------|------|
| 单行插入+查询 | 连接、建表、插入 1 行、查询、关闭 |
| 批量插入 | `executemany` 插入 1000 行 |
| 批量查询 | `execute_fetchall` 读取 1000 行 |
| 游标迭代 | `async for` 遍历 1000 行游标 |
| execute_insert | 100 次顺序 `execute_insert` 调用 |
| 大行插入 | `executemany` 插入 500 行 × 4KB 载荷 |
| 大行查询 | `execute_fetchall` 读取 500 行 × 4KB 载荷 |
| 大结果集 Fetchall | `execute_fetchall` 读取 10K 行 |
| 大结果集迭代 | `async for` 遍历 10K 行游标 |
| 并发任务 | 8 个协程，各插入 50 行后读取全部 |
| 混合读写 | 200 次交替插入和查询 |

## 自行运行

```bash
pip install pytest pytest-benchmark aiosqlite
pytest aiosqlite/test_aiosqlite_benchmark.py --benchmark-only -v
```

---

## 最新 CI 结果

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/aiosqlite.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> 每次发版时通过 [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml) 自动更新。
