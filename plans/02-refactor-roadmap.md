# Zerodep 重构路线图

## 目标

这份路线图的目标不是把仓库改造成一个传统 package，而是在不破坏核心承诺的前提下，降低维护成本。

必须保留的核心承诺：

- 单文件模块
- 仅使用 stdlib
- 可复制到外部项目直接使用
- 模块之间可以可选组合，但不强制绑定成内部共享运行时

核心原则可以概括为一句话：

> 在仓库层面标准化 pattern，但不要在运行时强行引入共享核心依赖。

## 当前问题的本质

当前仓库不是“代码烂”，而是“重复结构太多，但还没有足够仓库级规范”。

最明显的重复模式包括：

- sibling import / `sys.path` fallback：`config/config.py:33`、`vcs/vcs.py:29`、`sse/sse.py:62`
- subprocess 执行与二进制发现：`runner/runner.py:350`、`runner/runner.py:1090`、`vcs/vcs.py:180`
- 终端颜色能力检测：`structlog/structlog.py:159`、`prompt/prompt.py:146`
- sync/async 双路径结构：`runner/runner.py:350`、`runner/runner.py:520`、`httpclient/httpclient.py:392`
- cleanup best-effort 逻辑：`httpclient/httpclient.py:624` 及其周边 close/pool 路径

## 重构原则

## 1. 保住单文件契约

不要引入必须被所有模块 import 的公共 runtime core。

不建议做的事情：

- 建一个 `zerodep/_core`
- 把所有模块改成“薄包装 + 共享内部库”
- 让复制出来的单文件无法脱离仓库独立使用

## 2. 先标准化写法，再考虑抽象

对于当前仓库，最优先的不是“消灭重复代码”，而是“让重复代码采用同一种写法”。

也就是：

- 相同问题尽量用相同结构解决
- 相同能力尽量用相同命名
- 相同 fallback 尽量给出相同错误语义

这会明显降低维护成本，而不会破坏单文件设计。

## 3. 大模块优先做内部整形，而不是跨模块抽象

对 `httpclient`、`runner`、`scheduler` 这类模块，最有价值的不是先抽公共 helper，
而是先把模块内部结构理顺：

- 阶段边界更清楚
- 状态机更容易推理
- sync/async 对照关系更明显
- cleanup 路径更可审计

## 4. 把重复 pattern 当成“仓库资产”维护

仓库应该明确维护一套 canonical patterns：

- 可选 sibling import
- subprocess 执行
- sync/async API 镜像结构
- 终端能力检测
- cleanup 分类
- 错误类型设计

这些不一定变成共享代码，但一定要变成共享约定。

## 该标准化什么

## A. sibling import 模式

当前出现位置：

- `config/config.py:33`
- `vcs/vcs.py:29`
- `sse/sse.py:62`

建议统一的内容：

- 目录定位写法
- `sys.path.insert(0, ...)` 的使用条件
- 捕获哪些异常
- `_HAS_*` flag 的命名方式
- 对用户抛出的 fallback 错误文案风格

目标：

- 不做共享 helper
- 但让所有 optional import block 看起来像同一个作者写的

## B. subprocess 执行模式

当前出现位置：

- `runner/runner.py:350`
- `runner/runner.py:520`
- `vcs/vcs.py:252`

建议统一的内容：

- binary lookup 顺序
- timeout 文案
- allowed returncodes 约定
- timeout 后的清理方式
- encoding 默认值
- 哪些异常需要 wrap，哪些直接透出

边界很重要：

- 不建议强制让 `vcs` 依赖 `runner`
- 更合理的做法是：让 `runner` 成为参考实现，`vcs` 逐步对齐行为语义

## C. 终端颜色能力检测

当前出现位置：

- `structlog/structlog.py:159`
- `prompt/prompt.py:146`

建议统一：

- `FORCE_COLOR`
- `NO_COLOR`
- `isatty()`
- `TERM=dumb`

这是一个低风险高收益的标准化点。

## D. cleanup 策略

当前痛点主要在：

- `httpclient/httpclient.py:624`
- `httpclient/httpclient.py:846`
- `runner/runner.py:281`
- `runner/runner.py:488`

建议建立三类 cleanup 语义：

- **必须成功，否则抛错**
- **best-effort，但最好可观测**
- **best-effort，可以静默**

这样可以避免以后大家都习惯性写 `except Exception: pass`。

## E. 错误类型设计约定

当前已有不错基础：

- `runner/runner.py:60`
- `scheduler/scheduler.py:54`
- `httpclient/httpclient.py:660`
- `vcs/vcs.py:52`
- `validate/validate.py:214`

建议统一的不是继承树，而是风格：

- 模块内优先定义领域异常
- 异常名尽量避免和常见 built-in 语义重叠过多
- 错误消息统一带最小必要上下文，例如：
  - command
  - URL
  - timeout
  - job id
  - path

## 不该标准化成共享运行时的东西

## 1. 不要做统一内部 core

如果为了消灭重复而牺牲可复制性，那就偏离了仓库初衷。

## 2. 不要为了降行数而机械拆文件

LOC 高不一定意味着必须拆分。

真正该关注的是：

- 生命周期是否清晰
- 状态是否容易推理
- 边界是否容易测试

## 3. 不要过度追求“零重复”

对这个仓库来说，适度重复是健康的。

问题不是重复本身，而是重复没有规范。

## 优先级分层

## Tier 1：低风险高收益规范化

这是最值得先做的一层。

### 1. 建立 pattern inventory

建议后续补一个：

- `plans/03-pattern-inventory.md`

内容专门记录：

- sibling import 模板
- subprocess 模板
- color detection 模板
- sync/async 镜像结构模板
- cleanup 分类模板
- error taxonomy 风格模板

### 2. 统一 optional import block

优先模块：

- `config`
- `vcs`
- `sse`

### 3. 统一颜色能力检测

优先模块：

- `structlog`
- `prompt`
- 必要时看 `ansi`

### 4. 统一 cleanup 段落的内部风格

目标不是加很多注释，而是让 cleanup 段：

- 结构一致
- 异常处理层级一致
- 可观测性一致

## Tier 2：核心大模块内部整形

## 1. `httpclient` 内部分层整形

目标文件：

- `httpclient/httpclient.py:1`

重点：

- request building
- connection acquisition
- transport execution
- response parsing
- streaming lifecycle
- pool return / discard

这是最复杂、也最值得谨慎推进的重构点。

## 2. `runner` 内部结构整形

目标文件：

- `runner/runner.py:1`

重点：

- sync/async 结构对齐
- streaming 生命周期更清楚
- timeout/cleanup 语义统一

## 3. `scheduler` 并发模型梳理

目标文件：

- `scheduler/scheduler.py:1`

重点：

- thread + async 的互动语义
- listener 行为
- shutdown 路径
- race condition 风险点

## Tier 3：仓库级治理机制

### 1. 贡献规范文档

即使没有正式的 contributor guide，也应该有一份短文档说明：

- 如何写 sibling import
- 什么时候允许重复
- `_HAS_*` 怎么命名
- 异常怎么设计
- sync/async API 应该怎么镜像

### 2. 文档同步清单

建议把以下文件纳入同一套维护检查：

- `README.md:1`
- `pyproject.toml:72`
- `Makefile:1`
- `manifest.json:1`

### 3. 按复杂度给模块分层

建议内部先做一个认知分层：

- **简单工具模块**：`ansi`、`dotenv`、`jsonc`、`prompt`
- **中等功能模块**：`markdown`、`frontmatter`、`tabulate`、`validate`
- **子系统模块**：`httpclient`、`runner`、`scheduler`、`cache`、`vcs`、`yaml`

这样后续新增功能时，不同类型模块就能采用不同的审查标准。

## 30/60/90 计划

## 30 天内

- 完成 `plans/` 分析文档基线
- 增加 `pattern-inventory`
- 统一 `config` / `vcs` / `sse` 的 sibling import 模式
- 统一 `structlog` / `prompt` 的颜色能力检测
- 检查 `README` / `Makefile` / pytest 路径是否漂移

## 60 天内

- 整理 `runner` 内部结构
- 梳理 `scheduler` 并发模型
- 开始 `httpclient` 生命周期与 cleanup 审计
- 建立错误消息风格约定

## 90 天内

- 完成 `httpclient` 内部整形第一轮
- 正式识别并标记 subsystem 级模块
- 增加面向边界行为的测试：
  - resource cleanup
  - timeout/cancel
  - pool reuse/invalidation
  - sibling import fallback

## 现在最值得做的事

如果只看 ROI，建议顺序是：

1. 先把重复 pattern 记录下来
2. 先标准化最简单、最通用的重复 pattern
3. 把 `runner`、`scheduler`、`httpclient` 明确按 subsystem 对待
4. 重构以“内部清晰化”为优先，而不是以“抽公共代码”为优先

## 推荐文档组织

建议当前 `plans/` 下的阅读顺序：

1. `plans/01-implementation-analysis-overview.md:1`
2. `plans/02-refactor-roadmap.md:1`
3. `plans/04-runtime-concurrency-deep-dive.md:1`
4. `plans/05-httpclient-deep-dive.md:1`

后续建议新增：

- `plans/03-pattern-inventory.md:1`

## 最终立场

对 `zerodep` 来说，正确的重构方向不是“更框架化”，而是“更有纪律”。

也就是：

- 相同 pattern 用相同写法
- 相同问题用相同约定
- 大模块内部边界更清楚
- 生命周期更可推理
- 明确哪些重复是有意保留的

这样既不会破坏单文件哲学，也能明显降低后续维护成本。
