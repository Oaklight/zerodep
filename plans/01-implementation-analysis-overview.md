# Zerodep 当前实现总览分析

## 核心判断

- `zerodep` 不是简单的一组工具脚本，而是一套围绕“零依赖、单文件、可复制分发”构建出来的实现体系。
- 当前实现最大的成功点在于产品形态非常清晰：模块可以单独复制使用，仓库也提供了从维护到分发的完整链路。
- 当前实现最大的长期压力点不是功能不够，而是为了保住“单文件”这个核心承诺，复杂度被压进了每个模块内部。

一句话概括：

> 这个仓库现在的主要问题不是代码质量差，而是“成功地把复杂度压缩进了单文件”。

## 仓库级架构

### 分发层

`zerodep.py:1` 是整个仓库的分发中枢，负责：

- 扫描模块目录
- 读取源码中的 frontmatter 元数据
- 生成 `manifest.json`
- 解析模块依赖
- 从远程源拉取文件
- 走本地缓存兜底
- 将模块复制到用户项目中

其中：

- 元数据读取由 `_extract_frontmatter()` 完成，见 `zerodep.py:209`
- 模块发现由 `_scan_modules()` 完成，见 `zerodep.py:140`

也就是说，仓库内部是 monorepo 维护方式，仓库外部是单文件分发方式。

### 模块层

每个功能模块基本遵循以下结构：

- `<module>/<module>.py`
- `<module>/test_*_correctness.py`
- `<module>/test_*_benchmark.py`

这套结构让模块既能独立维护，也能统一测试。

### 可选依赖层

部分模块会可选地使用同仓库的其他模块，例如：

- `config/config.py:1`
- `vcs/vcs.py:1`
- `sse/sse.py:1`

这些依赖不是硬编码打包关系，而是 guarded import + fallback。

这符合仓库目标：

- 用户只复制一个文件时，功能仍然尽量可用
- 用户复制多个文件时，模块之间能获得增强能力

## 为什么这个设计是成立的

### 1. 分发成本极低

用户直接复制：

- `cache/cache.py`
- `runner/runner.py`
- `httpclient/httpclient.py`

就能用，而不需要安装包、不需要引入第三方依赖。

### 2. 仓库目标高度统一

`README.md:1`、`pyproject.toml:1`、`zerodep.py:1` 的目标是一致的：

- 用 stdlib 实现常见能力
- 保持零依赖
- 保持单文件可复制

### 3. 模块独立性很强

仓库没有强制性的共享内部核心层，因此大多数模块可以被单独理解、单独复制、单独测试。

## 代价：复杂度被压进单文件

为了保住“单文件可复制”这个目标，很多正常项目里会抽到公共层的能力，在这里被重复写进不同模块：

- sibling import/fallback
- 环境变量和终端能力检测
- 子进程执行
- sync/async 双接口
- 资源清理
- 错误类型设计
- 策略校验

这不是偶然，也不是失误，而是架构选择带来的代价。

## 当前最明显的重复模式

### 1. 可选 sibling import 模式重复出现

代表位置：

- `config/config.py:33`
- `vcs/vcs.py:29`
- `sse/sse.py:62`

共同点：

- 计算同级模块目录
- 临时写入 `sys.path`
- 做 `ImportError` 兜底
- 设置 `_HAS_*` 标志位

问题在于：

- 写法不完全统一
- 可读性和可审计性一般
- `sys.path` 修改属于全局副作用，长期看比较脆弱

### 2. 子进程执行模式重复出现

代表位置：

- `runner/runner.py:350`
- `runner/runner.py:520`
- `vcs/vcs.py:252`

共同点：

- 命令解析
- 超时控制
- 编码/解码
- 返回码校验
- 失败包装

问题在于：

- `runner` 和 `vcs` 各自维护子进程语义
- 行为整体合理，但仓库层面缺少统一规范

### 3. 终端颜色能力检测重复出现

代表位置：

- `structlog/structlog.py:159`
- `prompt/prompt.py:146`

共同点：

- `FORCE_COLOR`
- `NO_COLOR`
- `isatty()`
- `TERM=dumb`

这是一个很典型的“适合先标准化、但不一定需要共享运行时代码”的重复 pattern。

### 4. sync/async 双实现重复出现

代表位置：

- `runner/runner.py:350`
- `runner/runner.py:520`
- `httpclient/httpclient.py:392`
- `httpclient/httpclient.py:846`
- `httpclient/httpclient.py:936`

这是当前复杂度膨胀最主要的来源之一。

### 5. 清理路径大量使用 best-effort

代表位置：

- `httpclient/httpclient.py:624`
- `httpclient/httpclient.py:846`
- `runner/runner.py:281`
- `runner/runner.py:488`

这类写法在网络、连接池、close、terminate 场景下是现实且合理的。

但问题在于：

- 哪些应该静默吞掉
- 哪些应该 warning
- 哪些应该视为状态异常

目前还没有形成全仓库的一致约定。

## 按模块看当前实现状态

## `zerodep.py`

优点：

- 产品闭环完整
- CLI 实用
- frontmatter + manifest 方案很聪明

风险：

- 一个文件同时承担 fetch/cache/manifest/resolver/CLI 多种职责
- `master` 分支写死在 `zerodep.py:28`

判断：

- 好用，但已经是“仓库基础设施级文件”，不再是简单脚本

## `config/config.py`

优点：

- 配置源优先级清晰
- cast 和多格式支持很实用
- 对 sibling 模块缺失有兜底

风险：

- `sys.path` 侵入式修改
- 查找、加载、cast、flatten、source precedence 都挤在一个模块里

判断：

- 产品价值高，内部耦合偏高

## `runner/runner.py`

优点：

- 很像仓库里的底层基础设施模块
- sync/async/streaming 覆盖完整
- 超时、执行策略、错误包装都比较成熟

风险：

- 同步异步逻辑重复明显
- 流式输出和超时清理组合起来后，边界复杂度很高

判断：

- 应该按“核心模块”对待，而不是普通模块

## `scheduler/scheduler.py`

优点：

- 结构相对工整：cron、trigger、job、scheduler 分层明确
- 事件模型是加分项

风险：

- 线程调度器 + async job 是双并发模型
- listener 与 shutdown 的语义需要更明确

判断：

- 在复杂模块里算比较整齐，但并发语义是重点风险点

## `httpclient/httpclient.py`

优点：

- stdlib-only 前提下能力非常强
- 支持连接池、streaming、auth、proxy、multipart、decompress
- 有明显的资源卫生意识

风险：

- 复杂度极高
- 多类状态机耦合在一个文件里
- cleanup 路径里部分异常被静默吞掉

判断：

- 这是仓库里最值得深挖、也最值得谨慎重构的模块之一

## `vcs/vcs.py`

优点：

- `VCSBackend` 协议抽象比较成熟，见 `vcs/vcs.py:296`
- Git / Hg / JJ 的差异处理比较诚实
- 用户接口层体验不错

风险：

- 后端协议面宽，长期维护成本高
- 子进程逻辑与 `runner` 重复
- 对 `diff` 的 sibling import 延续了仓库的脆弱模式

判断：

- 架构上是成熟的，但后端分化会逐步抬高维护成本

## 测试姿态

这个仓库的测试覆盖广度其实是很强的。

`pyproject.toml:72` 中覆盖了大量模块的测试路径，且多数模块同时有：

- correctness tests
- benchmark tests

这与仓库“对标现有库实现”的定位高度一致。

### 当前更像“压力点”的不是缺测试，而是难测边界

主要包括：

- sync/async 一致性
- timeout/cancel 行为
- 资源回收
- 连接池复用与失效
- sibling import fallback
- 跨平台 subprocess 行为

## 当前最核心的架构风险

### 1. `sys.path` 修改带来的全局副作用

这是最明显的架构脆弱点。

### 2. 重复 pattern 还没沉淀成仓库级规范

现在重复已经足够明显，但还没有 canonical recipe。

### 3. 大单文件正在演化成“压缩后的子系统”

代表模块：

- `httpclient/httpclient.py:1`
- `runner/runner.py:1`
- `scheduler/scheduler.py:1`
- `cache/cache.py:1`
- `vcs/vcs.py:1`
- `yaml/yaml.py:1`

### 4. API 面扩张速度开始超过规范化速度

模块越多，后续越需要靠文档和模式治理，而不是靠临时记忆维持一致性。

## 总结

当前实现总体是强的、清晰的、自洽的。

它最大的优点是：

- 产品目标清楚
- 单文件分发价值真实存在
- 很多模块已经达到“可用且有替代意义”的程度

它当前最大的债务是：

- 重复结构越来越明显
- 大模块已经开始具备子系统复杂度
- 仓库需要从“功能扩展阶段”进入“模式治理阶段”

建议阅读顺序：

1. `plans/01-implementation-analysis-overview.md:1`
2. `plans/02-refactor-roadmap.md:1`
3. `plans/04-runtime-concurrency-deep-dive.md:1`
4. `plans/05-httpclient-deep-dive.md:1`
