# JSON Schema 性能测试

zerodep jsonschema 与 [`allof-merge`](https://www.npmjs.com/package/allof-merge)（JavaScript）的性能对比。

!!! info "测试环境"
    - **CPU：** x86_64 Linux
    - **Python：** 3.12
    - **Node.js：** 22（用于 allof-merge）
    - **工具：** pytest-benchmark 5.2.3（报告均值）
    - **参考库：** allof-merge 0.6.8（通过持久化 Node.js 进程）
    - **最后更新：** 2026-04-25

## 实现方式

| 实现 | 文件/包 | 描述 |
|------|---------|------|
| **zerodep** | `jsonschema.py` | 仅标准库的 JSON Schema 展平器（完整管线） |
| **allof-merge** | *（参考库）* | JavaScript 的 `$ref` + `allOf` 解析库 |

## 测试 Schema

基准测试使用从简单到大规模合成的五个复杂度层级：

| 层级 | 描述 |
|------|------|
| Tiny | 简单对象，无组合关键字（直通基准） |
| Small | 单个 `anyOf` nullable 模式 |
| Medium | `$ref` + `allOf` + `anyOf` 组合 |
| Large | 多个 `$ref` + 嵌套 `allOf` + `oneOf` |
| XLarge | 合成：50 个字段、10 个 `$defs`、混合 `allOf`/`anyOf`/`oneOf` |

## 性能对比

| 层级 | zerodep | allof-merge (JS) | 比率 |
|------|---------|-------------------|------|
| Tiny | 19.8 us | 104 us | **快 5.3 倍** |
| Small | 35.7 us | 143 us | **快 4.0 倍** |
| Medium | 103.8 us | 236 us | **快 2.3 倍** |
| Large | 292.5 us | 486 us | **快 1.7 倍** |
| XLarge | 1.96 ms | 4.92 ms | **快 2.5 倍** |

!!! note "公平对比"
    JS 基准测试使用持久化 Node.js 进程（与 readability 模式相同），消除了子进程启动开销。仅测量实际的 `merge()` 调用耗时。zerodep 运行完整的 4 阶段管线（`flatten_schema`），而 allof-merge 仅执行 `$ref` + `allOf` 解析。

## 正确性验证

除 57 个独立单元测试外，13 个跨实现正确性测试验证了 zerodep（仅阶段 1+2）与 allof-merge 的结构等价性：

- 所有 5 个层级的**结构匹配**
- **allOf 完全解析**（无残留 `allOf` 关键字）
- zerodep 在所有上下文中**完全解析 `$ref`**

## 要点总结

- **zerodep 在所有复杂度层级快 1.7-5.3 倍**，即使 zerodep 运行了更完整的管线
- **zerodep 功能更多** —— 还简化了 `anyOf`/`oneOf` 并剥离不支持的键，allof-merge 不做这些
- **零依赖** —— zerodep 仅需标准库，allof-merge 需要 Node.js + npm
- **正确性** —— 在共享的 `$ref` + `allOf` 范围内，输出与 allof-merge 结构等价

## 自行运行

```bash
# 安装 JS 依赖
cd jsonschema && npm install

# 运行基准测试
pip install pytest pytest-benchmark
pytest jsonschema/test_jsonschema_benchmark.py --benchmark-only -v
```

---

## 最新 CI 结果

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/jsonschema.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> 每次发布时通过 [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml) 自动更新。
