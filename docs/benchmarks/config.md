# Config 性能测试

zerodep config 与 [`python-decouple`](https://pypi.org/project/python-decouple/) 的同场景性能对比。

!!! info "测试环境"
    - **CPU：** x86_64 Linux
    - **Python：** 3.10.20
    - **工具：** pytest-benchmark 5.2.3（报告中位数）

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

## 性能对比（中位数）

| 测试 | zerodep | python-decouple | 加速比 |
|------|---------|-----------------|--------|
| 环境变量查找 | 657 ns | 977 ns | **快 1.5 倍** |
| Dotenv 查找 | 650 ns | 938 ns | **快 1.4 倍** |
| 整型转换 | 788 ns | 1,223 ns | **快 1.6 倍** |
| 布尔转换 | 869 ns | 1,437 ns | **快 1.7 倍** |
| CSV | 1,816 ns | 9,509 ns | **快 5.2 倍** |

## 附加基准测试（仅 zerodep）

| 测试 | 中位数 | 说明 |
|------|--------|------|
| 嵌套 JSON 查找 | 1,177 ns | 从 JSON 配置文件中查找嵌套键 |
| Config 初始化（仅环境变量） | 319 ns | 不加载文件构造 `Config()` |
| Config 初始化（含 JSON） | 19,360 ns | 加载 JSON 配置文件构造 `Config()` |
| Config 初始化（含 .env） | 95,706 ns | 加载 .env 文件（50 条）构造 `Config()` |

## 要点总结

- **一致更快** -- zerodep config 在所有可比操作中比 python-decouple 快 1.4 到 5.2 倍。
- **CSV 解析优势** -- 最大加速比（5.2 倍）出现在 CSV 转换中，zerodep 更简洁的实现避免了 python-decouple 的额外开销。
- **轻量初始化** -- 不加载文件的 `Config` 构造仅需约 319 ns；JSON 配置加载增加约 19 us，.env 加载约 96 us。
- **额外功能零开销** -- zerodep 在保持更好性能的同时，增加了配置文件支持（JSON/YAML/TOML/INI）、嵌套键和前缀支持。

## 自行运行

```bash
pip install pytest pytest-benchmark python-decouple
pytest config/test_config_benchmark.py --benchmark-only -v
```
