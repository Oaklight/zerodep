# 命令运行器性能测试

zerodep runner 与 [`sh`](https://pypi.org/project/sh/) 及原生 `subprocess` 的性能对比。

!!! info "测试环境"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **工具:** pytest-benchmark 5.2.3（报告均值）
    - **对标库:** sh 2.2.2
    - **最后更新:** 2026-04-15

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
| 简单命令 | 0.99 ms | 1.61 ms | 27.9 ms | 慢 1.6x | **快 17.3x** |
| 输出捕获 | 18.9 ms | 19.2 ms | 50.6 ms | 持平 | **快 2.6x** |
| 标准输入 | 18.1 ms | 18.7 ms | 37.7 ms | 持平 | **快 2.0x** |
| 流式行读取 | 18.5 ms | 18.5 ms | 35.9 ms | 持平 | **快 1.9x** |
| 环境变量传递 | 18.5 ms | 18.7 ms | 39.7 ms | 持平 | **快 2.1x** |

## 要点总结

- **始终快于 sh** -- zerodep runner 在所有场景下比 `sh` 快 1.9-17.3 倍。`sh` 的魔法 API 和动态属性解析带来了显著的开销。
- **接近原生 subprocess** -- 在真实负载（输出捕获、标准输入、流式读取、环境变量传递）下，zerodep runner 与原生 `subprocess.run` 在误差范围内持平，同时提供结构化结果、超时升级和流式回调。
- **简单命令的开销** -- `echo hello` 上的 1.6 倍差距反映了 zerodep 基于 `Popen` 的架构（用于超时升级和流式处理）vs `subprocess.run` 的优化快速路径。这一固定开销（约 0.6 ms）对于任何实际工作的命令可忽略不计。
- **功能优势才是关键** -- 与原生 subprocess 不同，zerodep 提供 SIGTERM 到 SIGKILL 超时升级、流式回调与同时捕获、命令白名单/黑名单、环境隔离 -- 性能却相当。

## 自行运行

```bash
pip install pytest pytest-benchmark sh
pytest runner/test_runner_benchmark.py --benchmark-only -v
```
