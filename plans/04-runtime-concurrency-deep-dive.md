# 运行时与并发深挖

这份文档聚焦两个模块：

- `runner/runner.py`
- `scheduler/scheduler.py`

它们有一个共同点：

- 都不是简单工具函数集合
- 都已经具备“运行时子系统”的特征
- 都涉及生命周期、超时、cleanup、并发语义和边界行为

如果说 `httpclient` 是网络与连接状态机的高复杂度模块，
那么 `runner` 和 `scheduler` 则分别代表：

- 进程执行运行时
- 应用内任务调度运行时

## 一、总判断

### `runner`

`runner` 已经不是“执行 subprocess 的辅助工具”，而是一套比较完整的命令执行框架。

它覆盖了：

- sync 执行
- async 执行
- streaming sync
- streaming async
- timeout
- 进程终止升级策略
- 环境隔离
- 命令 allow/block policy

核心位置包括：

- 同步执行：`runner/runner.py:350`
- 异步执行：`runner/runner.py:520`
- sync streaming：`runner/runner.py:794`
- async streaming：`runner/runner.py:896`
- 命令发现：`runner/runner.py:1090`

### `scheduler`

`scheduler` 也不是简单的 cron helper，而是一个应用内调度器。

它覆盖了：

- cron 表达式解析
- interval / cron / once trigger
- 后台线程循环
- job 注册与状态管理
- listener 事件投递
- async job 支持

核心位置包括：

- cron 解析：`scheduler/scheduler.py:225`
- trigger 定义：`scheduler/scheduler.py:386`
- job / event 模型：`scheduler/scheduler.py:550`
- scheduler 主体：`scheduler/scheduler.py:621`
- 主循环与 shutdown：`scheduler/scheduler.py:894`

## 二、`runner` 的结构分析

## 1. 设计优点

### API 面完整

`runner` 提供了四种主要使用方式：

- 同步一次性执行
- 异步一次性执行
- 同步流式读取
- 异步流式读取

这对用户非常友好，因为不同运行场景基本都覆盖到了。

### 生命周期意识很强

`runner` 不是简单调用 `subprocess.run()`，而是系统性考虑了：

- timeout
- graceful terminate
- kill escalation
- partial output
- cleanup after exception

典型位置：

- `_terminate_with_escalation()`：`runner/runner.py:281`
- `_async_terminate_with_escalation()`：`runner/runner.py:296`

### 结果模型明确

`RunResult` 定义在 `runner/runner.py:107`，把：

- command
- returncode
- stdout
- stderr
- duration
- pid

统一收口，接口体验是成熟的。

## 2. 复杂度来源

### sync / async 双路径重复

最明显的复杂度来自：

- `run()`：`runner/runner.py:350`
- `run_async()`：`runner/runner.py:520`

它们在语义上应该对齐，但目前是两套并行实现。

这带来三个问题：

#### 1. 行为对齐成本高

一旦以后要修：

- timeout 行为
- partial output 语义
- callback 行为
- cleanup 细节

就需要同时检查 sync 和 async 两套路径。

#### 2. reviewer 心智负担高

任何对执行路径的修改，都不能只看一个函数。

#### 3. 容易出现微妙漂移

哪怕功能层面看起来一致，也可能在这些细节上逐步分叉：

- 错误消息
- timeout 后的输出保留策略
- 异常包装层次
- 清理时机

### streaming 再次乘法式放大复杂度

`runner` 不仅有 sync/async 两套执行路径，还有 sync/async 两套 streaming 抽象：

- `stream()`：`runner/runner.py:794`
- `AsyncStreamHandle`：`runner/runner.py:896`

这意味着它实际上维护的是四种生命周期模型：

- sync non-streaming
- async non-streaming
- sync streaming
- async streaming

这已经是典型的“运行时框架”复杂度，不再是普通 helper 复杂度。

## 3. 当前最值得关注的语义点

### timeout 语义整体是清楚的

这是 `runner` 做得比较好的部分。

同步与异步路径都体现出清晰的目标：

- 超时后优先 terminate
- 超过宽限期再 kill
- 将 timeout 包装成领域异常

这比很多轻量库要成熟。

### callback + streaming 的组合要重点看

在 `run()` 和 `run_async()` 的 callback 模式下：

- 输出仍然会被捕获
- 同时会逐行回调

这很方便，但也是边界最多的地方，因为它涉及：

- pipe 读取顺序
- callback 异常传播
- timeout 触发时的 partial output
- reader 线程 / 协程的收尾顺序

### `StreamHandle` / `AsyncStreamHandle` 是隐藏复杂度中心

很多用户看到 `stream()` 会以为只是“拿到一个可迭代对象”。

实际上这里面有非常强的生命周期要求：

- 什么时候进程算结束
- 什么时候 returncode 有效
- 提前退出上下文时如何清理
- stdout/stderr 是否都被消费

这部分需要更明确的内部语义约定。

## 三、`runner` 的并发/生命周期风险点

## 1. 线程 + pipe 读取的边界复杂度

在 sync streaming 路径中，`runner` 使用后台线程读取 stdout/stderr，见 `runner/runner.py:731`、`runner/runner.py:748` 一带。

风险不一定是立即 bug，而是维护上的高脆弱性：

- 管道关闭顺序
- reader 线程结束顺序
- 主线程退出时 join 语义
- partial read 的一致性

## 2. async streaming 依赖事件循环时机

`AsyncStreamHandle` 在 `runner/runner.py:896` 之后的逻辑依赖：

- event loop 持续可用
- stdout/stderr 读取协程的消费顺序
- `await self._proc.wait()` 的时机

如果未来扩展功能，很容易碰到：

- 某一端流已关闭，另一端未完全消费
- 用户只消费 stdout，不消费 stderr
- 提前取消迭代时 returncode 与 cleanup 语义变得微妙

## 3. policy 检查是优点，但也形成“执行前状态机”

`_check_command_policy()` 在 `runner/runner.py:244` 很有价值。

但它意味着执行前已经有一层额外语义：

- 命令是否允许
- basename 如何解析
- allowlist / blocklist 优先级

这是好事，但也说明 `runner` 已经不只是 subprocess wrapper，而是 policy-aware runtime。

## 四、`scheduler` 的结构分析

## 1. 设计优点

### 分层比较好

`scheduler` 是当前几个复杂模块里，内部分层比较清晰的一个：

- cron parser
- triggers
- job model
- event model
- scheduler runtime

这比把所有逻辑混在一起的实现方式要健康得多。

### trigger 抽象是对的

抽象出：

- `IntervalTrigger`
- `CronTrigger`
- `OnceTrigger`

是很好的做法。

因为 scheduler 的真正复杂度不在“怎么 sleep”，而在“什么时候该触发”。

### 事件模型是加分项

`JobEvent` 和 `EventType` 在 `scheduler/scheduler.py:550` 一带，让调度器不只是“执行任务”，而是能与外部系统形成集成点。

## 2. 复杂度来源

### 线程调度器 + async job 是双模型并存

`scheduler` 的核心运行时是后台线程，见：

- `self._thread`：`scheduler/scheduler.py:684`
- `start()`：`scheduler/scheduler.py:894`
- `_run_loop()`：`scheduler/scheduler.py:915`

但它又支持 async job，这意味着它必须跨越：

- 线程模型
- 事件循环模型

这是整个模块最核心的复杂度来源。

### cron 语义本身就很容易出边界问题

`parse_cron()` 和 `_cron_next_fire_time()` 在：

- `scheduler/scheduler.py:225`
- `scheduler/scheduler.py:271`

整体思路是合理的，但 cron 从来都属于“看起来简单、边界很多”的领域，尤其是：

- day-of-month / day-of-week 的 OR 语义
- 时间推进
- 月份跨越
- timezone

因此这里天然是维护热点。

## 3. 当前最值得关注的语义点

### `_emit()` 的策略是运行安全优先

`scheduler` 在 `_emit()` 中捕获 listener 异常并写日志，见 `scheduler/scheduler.py:874`。

这在调度器里是合理的，因为：

- 监听器失败不应该把 scheduler 主循环拖垮

但代价是：

- listener 错误不再向上传播
- 某些集成错误会更隐蔽

这不是 bug，但应该在文档中明确这是一种设计选择。

### shutdown 语义值得更清楚

`shutdown()` 在 `scheduler/scheduler.py:904` 的行为总体合理：

- 标记停止
- 设置 event
- 可选等待线程退出

但使用者最关心的问题通常是：

- shutdown 时已经在执行的 job 怎么办
- listener 是否还会收到剩余事件
- async job 是否会被等完

这些语义如果没有明确说明，维护时就容易出现假设冲突。

### `run_job()` 绕过 trigger 是实用但需要小心的功能

`run_job()` 见 `scheduler/scheduler.py:843`。

这是个很好用的功能，但它也引入了额外语义：

- 手动执行是否影响下一次调度
- 与正常调度触发是否共享同一条状态路径
- 错误/事件行为是否完全一致

这是以后很值得重点验证的地方。

## 五、`scheduler` 的并发风险点

## 1. 锁粒度与 job 状态更新

`scheduler` 用 `threading.Lock()` 管理 `_jobs`，见 `scheduler/scheduler.py:684`。

这是必要的，但后续要小心：

- job 取出后在锁外执行
- 执行期间 job 状态是否仍然可信
- listener 是否可能观察到中间态

这类问题不是代码明显错误，而是典型的并发维护风险。

## 2. async job 运行时机

`scheduler` 支持 async job，通常意味着它需要在某处临时建立或使用事件循环。

这种设计的常见风险是：

- loop 生命周期和线程生命周期耦合
- shutdown 时 async job 的尾部行为不够稳定
- 某些异常只会出现在特定 loop 状态下

## 3. misfire 与 late execution 语义

`scheduler` 有 `misfire_grace_time`，见 `scheduler/scheduler.py:599` 一带。

这是很有价值的能力，但也说明模块内部不仅在处理“是否执行”，还在处理“迟到多久还算有效”。

这类语义越多，越需要文档和测试把边界钉牢。

## 六、两个模块放在一起看时的共同模式

`runner` 和 `scheduler` 有几个共同点：

### 1. 都是运行时模块，不只是工具模块

它们都管理：

- 生命周期
- 状态转换
- timeout / shutdown
- 错误包装
- 外部副作用

### 2. 都已经进入 subsystem 复杂度

不能再按“小工具文件”的标准看待。

### 3. 都适合先做内部清晰化，而不是先抽公共代码

更合理的重构方向是：

- 先把状态边界写清楚
- 先把 sync/async 结构对齐
- 先把 cleanup 策略统一
- 再考虑要不要抽模式文档

而不是先做共享 runtime helper。

## 七、重构建议

## 对 `runner`

### 优先级最高的事

1. 明确 sync/async 语义对照表
2. 明确 streaming handle 生命周期
3. 对 cleanup 与 partial output 规则做仓库级描述

### 最值得重构的位置

- `run()` / `run_async()` 的结构对齐
- `stream()` / `AsyncStreamHandle` 的生命周期说明
- callback + timeout 路径的一致性审计

## 对 `scheduler`

### 优先级最高的事

1. 写清楚 thread + async 的运行模型
2. 写清楚 shutdown 语义
3. 审计 listener / event 投递的可见性边界

### 最值得重构的位置

- `_run_loop()` 的状态叙事清晰化
- async job 执行路径的边界说明
- misfire / manual run / pause-resume 之间的关系

## 八、结论

### 对 `runner` 的结论

`runner` 是一个设计成熟、功能完整、但复杂度已经明显进入“运行时框架级”的模块。

它最值得关注的不是功能缺失，而是：

- sync/async 是否持续对齐
- streaming 生命周期是否持续清楚
- cleanup 与 partial output 是否持续可预测

### 对 `scheduler` 的结论

`scheduler` 的分层其实不错，但它背后的复杂度来自并发模型，而不是 API 数量。

它最值得关注的不是 cron 语法支持够不够，而是：

- 线程与 async 的语义是否明确
- shutdown 与 listener 的行为是否稳定
- job 状态与事件是否可推理

### 总结性判断

如果要排序：

- `runner` 的风险更偏“生命周期复杂度”
- `scheduler` 的风险更偏“并发语义复杂度”

两者都不应该继续按“普通单文件工具模块”的标准扩展功能，
而应该按“单文件运行时子系统”的标准管理。
