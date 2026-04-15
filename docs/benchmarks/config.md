# Config 性能测试

zerodep config 与 [`python-decouple`](https://pypi.org/project/python-decouple/) 的同场景性能对比。

!!! info "测试环境"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **工具:** pytest-benchmark 5.2.3（报告均值）
    - **对标库:** python-decouple 3.8
    - **最后更新:** 2026-04-15

## 实现

| 实现 | 文件/包 | 说明 |
|------|---------|------|
| **zerodep** | `config.py` | 仅标准库的统一配置加载器 |
| **python-decouple** | *（参考库）* | 流行的 12-factor 配置库 |

## 测试项目

| 测试 | 说明 |
|------|------|
| 环境变量查找 | 从 `os.environ` 查找单个键 |
| Dotenv 查找 | 从预加载的 `.env` 文件（50 条）中查找键 |
| 整型转换 | 环境变量查找 + `cast=int` |
| 布尔转换 | 环境变量查找 + `cast=bool` |
| CSV | 环境变量查找 + `cast=Csv()` |

## 性能对比（均值）

| 测试 | zerodep | python-decouple | 加速比 |
|------|---------|-----------------|--------|
| 环境变量查找 | 0.8 μs | 1.4 μs | **快 1.8 倍** |
| Dotenv 查找 | 0.8 μs | 1.5 μs | **快 1.9 倍** |
| 整型转换 | 1.0 μs | 1.8 μs | **快 1.8 倍** |
| 布尔转换 | 1.1 μs | 2.3 μs | **快 2.2 倍** |
| CSV | 2.2 μs | 11.2 μs | **快 5.0 倍** |

## 附加基准测试（仅 zerodep）

| 测试 | 均值 | 说明 |
|------|------|------|
| 嵌套 JSON 查找 | 1.7 μs | 从 JSON 配置文件中查找嵌套键 |
| Config 初始化（仅环境变量） | 0.5 μs | 不加载文件构造 `Config()` |
| Config 初始化（含 JSON） | 38.9 μs | 加载 JSON 配置文件构造 `Config()` |
| Config 初始化（含 .env） | 759.8 μs | 加载 .env 文件（50 条）构造 `Config()` |

## 要点总结

- **一致更快** -- zerodep config 在所有可比操作中比 python-decouple 快 1.8 到 5.0 倍。
- **CSV 解析优势** -- 最大加速比（5.0 倍）出现在 CSV 转换中，zerodep 更简洁的实现避免了 python-decouple 的额外开销。
- **轻量初始化** -- 不加载文件的 `Config` 构造仅需约 0.5 μs；JSON 配置加载增加约 39 μs，.env 加载约 760 μs。
- **额外功能零开销** -- zerodep 在保持更好性能的同时，增加了配置文件支持（JSON/YAML/TOML/INI）、嵌套键和前缀支持。

## 自行运行

```bash
pip install pytest pytest-benchmark python-decouple
pytest config/test_config_benchmark.py --benchmark-only -v
```

---

## 最新 CI 结果

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/config.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> 每次发版时通过 [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml) 自动更新。
