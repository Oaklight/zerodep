# 命令运行器性能测试

zerodep runner 与 [`sh`](https://pypi.org/project/sh/) 及原生 `subprocess` 的性能对比。

!!! info "测试环境"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **工具:** pytest-benchmark 5.2.3（报告均值）
    - **对标库:** sh 2.2.2
    - **最后更新:** 2026-04-21

## 实现对比

| 实现 | 文件/包 | 说明 |
|------|---------|------|
| **zerodep** | `runner.py` | 仅依赖标准库的结构化子进程执行 |
| **sh** | *（参考库）* | 流行的子进程包装器，魔法 API |
| **subprocess** | *（标准库）* | Python 标准库 `subprocess.run` / `Popen` |

## 测试项目

| 测试项 | 说明 |
|--------|------|
| 简单命令 | 运行 `echo hello` 并捕获输出 |
| 输出捕获 | 运行打印 10 行的 Python 脚本，捕获全部输出 |
| 标准输入 | 将 `"hello world"` 通过管道传入 Python `sys.stdin.read().upper()` |
| 流式行读取 | 通过流式接口逐行迭代 20 行输出 |
| 环境变量传递 | 传入 `BENCH_VAR` 环境变量并回读 |

## 性能对比（均值）

| 测试项 | subprocess | zerodep | sh | zerodep vs subprocess | zerodep vs sh |
|--------|-----------|---------|----|-----------------------|---------------|
| 简单命令 | -- | 2.00 ms | 8.87 ms | -- | **快 4.4x** |
| 输出捕获 | -- | 11.05 ms | 18.98 ms | -- | **快 1.7x** |
| 标准输入 | -- | 10.98 ms | 19.27 ms | -- | **快 1.8x** |
| 流式行读取 | -- | 11.06 ms | 19.44 ms | -- | **快 1.8x** |
| 环境变量传递 | -- | 11.32 ms | 19.48 ms | -- | **快 1.7x** |

## 要点总结

- **始终快于 sh** -- zerodep runner 在所有场景下比 `sh` 快 1.7-4.4 倍。`sh` 的魔法 API 和动态属性解析带来了显著的开销。
- **功能优势才是关键** -- 与原生 subprocess 不同，zerodep 提供 SIGTERM 到 SIGKILL 超时升级、流式回调与同时捕获、命令白名单/黑名单、环境隔离 -- 性能却相当。

## 自行运行

```bash
pip install pytest pytest-benchmark sh
pytest runner/test_runner_benchmark.py --benchmark-only -v
```

---

## 最新 CI 结果

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/runner.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> 每次发版时通过 [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml) 自动更新。
