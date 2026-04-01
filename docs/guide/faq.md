---
title: 常见问题
---

# 常见问题

## 支持哪些 Python 版本？

zerodep 要求 **Python 3.10+**。代码中使用了 `match/case` 语句、`X | Y` 联合类型语法等 3.10+ 的语言特性，不支持更早的 Python 版本。

## 如何更新模块？

运行 `zerodep update <module>` 即可从 manifest 拉取最新版本。也可以手动从仓库重新下载 `.py` 文件替换项目中的旧版本。

## 可以同时使用多个模块吗？

可以。部分模块之间存在依赖关系，例如 `sse` 依赖 `httpclient`，`a2a` 依赖 `jsonrpc`。使用 `zerodep add` 时，CLI 会自动解析依赖并一并下载所需的全部文件。

## 如何处理模块间的依赖？

当模块 A 依赖模块 B 时，两个 `.py` 文件都必须存在于项目中。`zerodep add` 命令会自动解析依赖图并下载所有必需的模块。如果手动复制文件，请检查每个模块 frontmatter 中的 `dependencies` 字段。

## 这些模块可以用于生产环境吗？

每个模块都经过与参考库的正确性测试（例如 `yaml` 对比 PyYAML，`jsonc` 对比 `json5`），并提供性能基准测试数据。但它们毕竟是仅依赖标准库的重新实现——请根据测试覆盖率和基准测试结果，结合自身需求进行评估后再决定是否用于生产环境。

## 为什么不发布到 PyPI？

zerodep 的核心理念是**零依赖、单文件模块**。发布到 PyPI 会引入打包、版本管理和依赖管理的额外开销，与这一理念相悖。CLI 已经提供了类似 `pip` 的体验（`zerodep add`、`zerodep update`、`zerodep list`），无需引入这些额外机制。

## 如何参与贡献？

欢迎参与贡献！请访问 [GitHub 仓库](https://github.com/Oaklight/zerodep) 提交 Issue 或 Pull Request。在贡献新模块或修改现有模块之前，请阅读[内部约定](internals.md)页面，了解编码规范、frontmatter 格式、测试要求和命名规则。
