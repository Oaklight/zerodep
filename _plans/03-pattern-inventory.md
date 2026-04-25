# Zerodep 重复模式清单

## 目的

这份文档不是为了“消灭重复代码”，而是为了把当前仓库里已经明显重复出现的实现模式整理成一套可维护的约定。

对 `zerodep` 来说，重复本身并不是原罪。

因为仓库的核心目标是：

- 单文件
- 零依赖
- 可复制
- 可选组合

在这种前提下，很多正常项目里会抽成共享基础库的东西，在这里本来就会重复。

所以这份文档的目标是：

> 让重复变成“有规范的重复”，而不是“每个模块各写一套”。

## 使用方式

后续如果新增模块，或者给现有模块加能力，优先检查是否命中了以下 pattern：

1. optional sibling import
2. subprocess 执行
3. terminal color detection
4. sync/async API 镜像
5. cleanup 语义
6. 错误类型设计
7. 大模块的内部层次划分

如果命中，就优先沿用已有模板和约定，而不是重新设计一遍。

---

## Pattern 1：Optional Sibling Import

### 典型出现位置

- `config/config.py:33`
- `vcs/vcs.py:29`
- `sse/sse.py:62`

### 问题定义

单个模块复制出去时，不能强依赖仓库内其他模块。

但如果用户同时复制了多个模块，又希望这些模块之间能自动增强能力。

因此需要一种模式：

- sibling module 存在时启用增强能力
- sibling module 不存在时保持可运行或给出明确错误

### 推荐结构

建议统一成以下逻辑顺序：

1. 计算 sibling 目录
2. 确保目录只在必要时插入 `sys.path`
3. 尝试 import 目标标识符
4. 设置 `_HAS_*` 能力标记
5. 在真正需要该能力时再抛用户可理解的错误

### 推荐命名

- 路径变量：`_yaml_dir`、`_diff_dir`、`_httpclient_dir`
- 能力开关：`_HAS_YAML`、`_HAS_DIFF_MODULE`、`_HAS_DOTENV`
- 导入目标重命名：`from yaml import load as _yaml_load`

### 推荐原则

- 避免在模块顶层做过度复杂的 fallback 分支
- `ImportError` 只负责能力探测，不直接做业务处理
- 真正依赖该能力的地方再抛更明确的错误

### 不推荐做法

- 在多个位置重复插入 `sys.path`
- `_HAS_*` 命名风格不统一
- 顶层 import 失败后静默降级，但后续真正使用时没有明确错误

### Canonical Recipe

可作为仓库级模板理解：

- 顶层只做“探测 + 标记”
- 运行期做“能力判断 + 用户提示”
- import block 尽量短、机械、统一

---

## Pattern 2：Subprocess 执行

### 典型出现位置

- `runner/runner.py:350`
- `runner/runner.py:520`
- `vcs/vcs.py:252`

### 问题定义

仓库内多个模块都需要：

- 调外部命令
- 控制 timeout
- 处理编码
- 检查返回码
- 在失败时包装出更易理解的异常

### 推荐结构

建议统一为以下阶段：

1. 命令规范化
2. 策略校验（allowlist/blocklist）
3. 环境构建
4. 启动进程
5. 收集 stdout/stderr
6. timeout/terminate/kill 处理
7. 结果对象封装
8. 非零退出包装

### 参考实现

目前最完整的参考实现是：

- `runner/runner.py:350`
- `runner/runner.py:520`

### 推荐原则

- 将 `runner` 视为 subprocess 语义的参考实现
- 其他模块不一定依赖 `runner`，但应该尽量对齐语义
- timeout 错误消息要带：
  - command
  - timeout 值
- 非零退出错误要带：
  - returncode
  - command
  - 关键 stderr

### 不推荐做法

- 不同模块对 timeout 用完全不同语义
- 有的模块吞 stderr，有的模块全抛，风格混乱
- 二进制发现逻辑在多个模块中顺序不一致

### Canonical Recipe

- `runner` 是子进程行为语义的“参考模块”
- `vcs` 等模块应尽量靠近它，而不是各自发明一套命令执行模型

---

## Pattern 3：Terminal Color Detection

### 典型出现位置

- `structlog/structlog.py:159`
- `prompt/prompt.py:146`

### 问题定义

终端模块需要统一判断：

- 是否应该输出 ANSI 颜色
- 环境变量是否强制开启/关闭颜色
- 当前流是否真的是 TTY

### 推荐优先级

建议统一判断顺序：

1. `FORCE_COLOR` → 强制开启
2. `NO_COLOR` → 强制关闭
3. `isatty()` → 非 TTY 关闭
4. `TERM=dumb` → 关闭
5. 否则开启

### 推荐原则

- 所有终端相关模块使用同一优先级顺序
- 判断逻辑保持极短，避免各模块自行扩展特殊分支
- 如果未来 `ansi` 模块也包含类似能力，应把它视为文档参考实现

### 不推荐做法

- 一个模块把 `NO_COLOR` 放前面，另一个模块把 `FORCE_COLOR` 放前面
- 一个模块要求 TTY，另一个模块默认强开颜色

### Canonical Recipe

颜色能力判断不一定要抽成共享 helper，但应当成为仓库内统一写法。

当前建议以 `ansi/ansi.py:261` 作为参考实现，其他终端相关模块尽量与它保持一致，例如：

- `structlog/structlog.py:158`
- `prompt/prompt.py:134`

颜色集合本身也建议与 `ansi/ansi.py:71` 和 `ansi/ansi.py:82` 保持一致，默认对齐：

- 标准 8 色
- bright 8 色

对于上层终端模块，如果没有非常明确的产品理由，不应单独发明新的 named-color 集合。

进一步的能力分层建议如下：

- `ansi` 负责完整颜色表达能力，覆盖 named colors、bright colors、256 色、hex、RGB、前景和背景
- `prompt` 作为交互层，默认沿用 16 色 named colors；如确有需要，可以局部支持更灵活的前景色表达（例如 hex 前景）
- `structlog` 作为日志渲染层，默认保持固定 16 色映射，不主动扩展为通用配色系统

也就是说：

- `ansi` 是颜色能力上限的参考实现
- `prompt` 可以按交互需要局部借用 `ansi` 的表达模型
- `structlog` 不必为了能力对齐而机械补齐 hex / 256 色，除非后续明确有更强的 renderer 可配置需求

---

## Pattern 4：Sync / Async API 镜像

### 典型出现位置

- `runner/runner.py:350`
- `runner/runner.py:520`
- `httpclient/httpclient.py:392`
- `httpclient/httpclient.py:846`
- `httpclient/httpclient.py:936`

### 问题定义

对于网络、子进程、streaming 这类模块，用户通常希望同时拥有：

- sync API
- async API

但这会显著增加维护成本。

### 推荐结构

建议在设计时保持以下对应关系：

- sync 路径与 async 路径在命名上对齐
- 阶段划分对齐
- 错误语义尽量对齐
- cleanup 时机尽量对齐

### 推荐原则

- 同步和异步不是“两个独立产品”，而是“一份语义、两套执行路径”
- 设计时优先保证语义对齐，而不是只保证功能都能跑
- 文件内 section 顺序也尽量镜像，方便 reviewer 横向对比

### 不推荐做法

- sync/async 逐步演化成两套风格完全不同的实现
- timeout、error、cleanup 语义明显分叉
- 一个路径支持 pooling/streaming，另一个路径只是功能上勉强对上

### Canonical Recipe

- 以“语义镜像”作为目标
- 允许实现细节不同，但不允许用户行为模型严重漂移

---

## Pattern 5：Cleanup 语义

### 典型出现位置

- `httpclient/httpclient.py:624`
- `httpclient/httpclient.py:846`
- `runner/runner.py:281`
- `runner/runner.py:488`

### 问题定义

在网络、进程、streaming、连接池场景中，cleanup 经常是 best-effort 的。

但如果没有统一约定，就容易变成：

- 到处都是 `except Exception: pass`
- 出问题时完全没有可观测性
- 模块之间 cleanup 风格严重分叉

### 建议分类

把 cleanup 分成三类：

#### 1. 必须成功，否则抛错

适用于：

- 影响外部可见一致性的关键状态切换
- 失败会导致对象处于不可信状态的路径

#### 2. Best-effort，但应可观测

适用于：

- close 失败不影响主逻辑结果
- 但失败说明存在资源卫生问题
- 可以考虑 warning / debug logging / ResourceWarning

#### 3. Best-effort，可以静默

适用于：

- 二次 close
- 兜底回收
- 明确无害、且高频发生的关闭失败

### 推荐原则

- `except Exception: pass` 只能用于第 3 类
- 第 2 类最好至少有 warning 信号
- cleanup 段内部结构尽量一致：
  - 先标记状态
  - 再尝试释放资源
  - 再做兜底

### Canonical Recipe

不要追求所有 cleanup 都抛错，也不要习惯性全吞掉。

关键是：

- 分清 cleanup 的严重级别
- 不同级别用不同策略

---

## Pattern 6：错误类型设计

### 典型出现位置

- `runner/runner.py:60`
- `scheduler/scheduler.py:54`
- `httpclient/httpclient.py:660`
- `vcs/vcs.py:52`
- `validate/validate.py:214`

### 问题定义

复杂模块如果直接把底层 stdlib 异常暴露给用户，会导致：

- 用户不知道哪里出了问题
- 错误消息上下文不够
- 模块 API 不稳定

### 推荐结构

- 每个复杂模块尽量有自己的异常族
- 模块内错误应当反映领域语义，而不是底层实现细节

### 推荐原则

错误消息尽量包含最小必要上下文：

- 命令执行类：command、returncode、stderr
- 网络类：URL、host、timeout、status code
- 调度类：job id、trigger、scheduled time
- 配置类：key、source、expected cast

### 不推荐做法

- 不同模块中同类错误表达风格完全不一致
- 对用户抛出过于底层的 stdlib 异常
- 消息没有上下文，只写 “failed” 或 “invalid”

### Canonical Recipe

异常设计不是要统一继承树，而是要统一“信息密度”和“领域语义”。

---

## Pattern 7：大模块内部层次划分

### 典型出现位置

- `httpclient/httpclient.py:1`
- `runner/runner.py:1`
- `scheduler/scheduler.py:1`
- `cache/cache.py:1`
- `vcs/vcs.py:1`
- `yaml/yaml.py:1`

### 问题定义

这些模块虽然仍然是单文件，但本质上已经是“压缩后的子系统”。

风险不只是 LOC，而是：

- 状态机多
- 生命周期长
- helper 之间耦合强
- 修改一个分支容易影响另一个分支

### 推荐结构

大模块内部应优先划清这些层次：

1. public API
2. domain model / data structure
3. parser / builder / executor
4. transport / runtime / storage core
5. cleanup / lifecycle
6. exception family

### 推荐原则

- 大模块先做“内部整形”，再考虑是否做跨模块抽象
- section 顺序要稳定
- 命名要能反映职责，而不是只反映技术细节

### Canonical Recipe

把“大单文件”当作“单文件子系统”对待，维护方式要比普通工具模块更严格。

---

## 按优先级的 pattern 治理建议

> 以下用 ✅ 标注已完成项、🔄 标注进行中。最后更新：2026-03-30。

## 第一优先级

最应该先统一的：

1. ✅ Optional sibling import — 已统一模式（`a196e45`）+ 懒加载（`240d6b5`、`262674a`）
2. ✅ Terminal color detection — 已对齐 structlog/prompt（`87ef4dc`）
3. ✅ Cleanup 语义分级 — 三级分类标准化完成

原因：

- 风险低
- 收益高
- 影响面广
- 不容易引发行为回归

## 第二优先级

接下来治理的：

1. Subprocess 执行约定
2. Error taxonomy 风格
3. Sync/async 镜像结构

## 第三优先级

最后处理的：

1. 大模块的系统性内部整形
2. `httpclient` / `runner` / `scheduler` 的深度结构调整

原因：

- 改动风险更高
- 需要更深入测试和更明确设计文档

## 最后结论

`zerodep` 当前真正需要的，不是“去重复工具”，而是“重复模式治理”。

也就是说：

- 允许重复
- 但重复必须可预测
- 允许单文件独立实现
- 但实现模式必须越来越统一

如果这份 pattern inventory 能持续维护，后续新增模块和现有模块重构的成本都会明显下降。
