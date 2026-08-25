# 限流器性能测试

zerodep ratelimit 与 [`limits`](https://pypi.org/project/limits/) / [`limiter`](https://pypi.org/project/limiter/)（token-bucket）的对等性能对比。

!!! info "测试环境"
    - **CPU:** x86_64 Linux
    - **Python:** 3.10
    - **工具:** pytest-benchmark 5.2.3（报告均值）
    - **参考库:** limits 5.8.0、limiter 0.5.0（token-bucket 0.3.0）
    - **更新日期:** 2026-08-25

## 实现

| 实现 | 文件/包 | 描述 |
|------|---------|------|
| **zerodep** | `ratelimit.py` | 4 算法限流器，仅标准库 |
| **limits** | *(参考)* | 多策略限流器，可插拔后端 |
| **limiter** | *(参考)* | 令牌桶装饰器，底层为 C 级 `token-bucket` |

## 测试内容

单 key `acquire()` / `hit()` / `consume()` 吞吐量 — 纯内存计算，无 I/O。所有限流器配置为 rate=10000/s 以避免 benchmark 期间触发限制。

## 结果

### zerodep vs limits（同算法对比）

| 操作 | zerodep (ns) | limits (ns) | 加速比 |
|------|-------------|-------------|--------|
| 固定窗口 acquire vs hit | ~575 | ~3,478 | **6.0x** |
| 滑动窗口 acquire vs hit | ~873 | ~6,261 | **7.2x** |
| 固定窗口 peek vs test | ~722 | ~2,318 | **3.2x** |

### zerodep vs limiter（令牌桶对比）

| 操作 | zerodep (ns) | limiter (ns) | 比率 |
|------|-------------|-------------|------|
| 令牌桶 acquire vs consume | ~762 | ~571 | 慢 1.3 倍 |
| — | — | 装饰器：~84,000 | zerodep 快 110 倍 |

!!! note
    `limiter` 的裸 `consume()` 更快，因为它只返回 `bool`，无结果对象分配。其装饰器模式每次调用增加约 84μs 开销，比 zerodep 的 `acquire()` **慢 110 倍**。

### 全算法（zerodep）

| 算法 | acquire (ns) | peek (ns) |
|------|-------------|-----------|
| 固定窗口 | ~575 | ~722 |
| GCRA | ~740 | — |
| 令牌桶 | ~762 | ~922 |
| 滑动窗口 | ~873 | — |

### 多线程吞吐量（ThreadSafeLimiter）

| 场景 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| 4 线程同 key | 4,590 ns/op | 4,732 ns/op | GIL 瓶颈 |
| 4 线程不同 key | 4,713 ns/op | 2,686 ns/op | **+76%** |

### 优化历程

| 步骤 | TokenBucket (ns) | 提升 |
|------|-----------------|------|
| 基线（frozen dataclass） | 1,338 | — |
| `__slots__` 结果类 | 996 | +34% |
| 内联热路径方法 | 813 | +65% |
| 去除 `int()`/`round()` | 762 | **+75%** |

## CI Benchmark 看板

<iframe src="https://oaklight.github.io/zerodep/dev/bench/" style="width:100%;height:400px;border:none;"></iframe>
