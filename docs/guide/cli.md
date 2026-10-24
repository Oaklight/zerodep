# CLI 工具

`zerodep` CLI 自动化模块发现、依赖解析和文件拷贝——类似一个轻量级的单文件模块版 `pip`。

## 安装

### 直接运行（无需安装）

```bash
# 从仓库下载 zerodep.py
curl -O https://raw.githubusercontent.com/Oaklight/zerodep/master/zerodep.py

# 直接使用
python zerodep.py list
```

### 通过 pip 安装

```bash
pip install zerodep
zerodep list
```

## 命令

### `zerodep list`

列出所有可用模块及其版本和描述。

```bash
# 只看一个分类
zerodep list --category serialization

# 机器可读输出
zerodep list --json
```

```bash
$ zerodep list
  Module      Version  Description
  ----------  -----    ----------------------------------------
  aes         0.1.0    Pure-Python AES encryption: ECB, CBC, CTR, and GCM modes
  dotenv      0.1.0    .env file parser and loader
  httpclient  0.1.0    Zero-dependency sync + async HTTP REST client
  scheduler   0.1.0    Zero-dependency in-process task scheduler with cron support
  sse         0.1.0    Zero-dependency SSE (Server-Sent Events) client
  ...

  20 modules available
```

### `zerodep search <term> [...]`

在模块名称、描述、分类、层级和依赖中搜索；所有关键词都要命中，不区分大小写。

```bash
$ zerodep search http
  httpclient  0.6.1  Zero-dependency sync + async HTTP REST client
  httpserver  0.6.1  Zero-dependency async HTTP server with decorator-based routing
  sse         0.4.1  Zero-dependency SSE (Server-Sent Events) client and event encoder

  3 module(s) matched

# 供脚本使用
zerodep search http --json
```

### `zerodep info <module>`

显示模块详情，包括文件、版本和依赖树。

```bash
$ zerodep info sse
Module:      sse
Version:     0.1.0
Description: Zero-dependency SSE (Server-Sent Events) client
Files:       sse/sse.py
Dependencies: httpclient
  (transitive: httpclient)
```

### `zerodep add <module> [...]`

将模块文件拷贝到你的项目中。依赖会自动解析并一起拉取。

```bash
# 拷贝 scheduler.py 到当前目录
zerodep add scheduler

# 拷贝 sse 及其依赖 httpclient 到 lib/ 目录
zerodep add sse -d lib/

# 拷贝多个模块
zerodep add retry dotenv yaml

# 使用子目录结构（sse/sse.py, httpclient/httpclient.py）
zerodep add sse --nested

# 跳过依赖——仅拷贝请求的模块
zerodep add sse --no-deps

# 跳过确认提示
zerodep add scheduler -y

# 覆盖已有文件，不提示
zerodep add scheduler -f

# 不写入 zerodep.lock.json
zerodep add scheduler --no-lock

# 只显示计划，不拷贝任何文件
zerodep add sse --dry-run
```

每次安装都会在拷贝文件旁记录 `zerodep.lock.json`（见[源版本锁定与锁文件](#源版本锁定与锁文件)）。

`add` 会拒绝覆盖与锁文件记录不一致的文件；对于锁文件出现之前的旧安装，则拒绝覆盖与上游不一致的文件。加 `--force` 才会替换。作为依赖拉取的模块会以 `"requested": false` 记录。

**确认提示** — 默认情况下，`add` 会显示执行计划并请求确认：

```
Will copy:
  sse.py                    -> sse.py  [sse]
  httpclient.py             -> httpclient.py  [httpclient (dependency)]
Target: /home/user/my-project
Continue? [Y/n]
```

### `zerodep update <module> [...]`

将已安装的模块更新到当前源版本。每个模块都会与 `zerodep.lock.json` 对比，因此本地修改不会被静默覆盖。

```bash
# 更新单个模块（会自动拉取上游新增的依赖）
zerodep update sse

# 更新所有需要处理的模块
zerodep update --all

# 只预览改动，不写任何文件
zerodep update --all --diff

# CI 门禁：有需要处理的模块时退出 1
zerodep update --all --check

# 覆盖本地修改或未验证的模块
zerodep update sse --force

# 不把结果写入锁文件
zerodep update sse --no-lock

# 只显示将要更新的内容，不写入
zerodep update --all --dry-run
```

| 状态 | 含义 | 不加 `--force` 时 `update` 的行为 |
|------|------|-----------------------------------|
| `up-to-date` | 安装内容与锁文件和上游都一致 | 无需处理 |
| `outdated` | 上游有变更，本地文件未被修改 | 覆盖更新 |
| `locally-modified` | 本地内容与锁文件记录不同 | **跳过**，退出 1 |
| `conflict` | 上游有变更，且本地文件被修改 | **跳过**，退出 1 |
| `missing` | 锁文件记录的文件被删除 | 重新安装 |
| `unverified` | 无锁文件记录，且内容与上游不同 | **跳过**，退出 1 |
| `upstream-removed` | 该模块已不再发布 | **跳过**，给出警告 |

只要有模块被跳过，命令就以 1 退出，CI 不会把"拒绝更新"误判为成功。`--diff` 只读，并且仍会为被跳过的模块输出 diff，因此执行 `--force` 前可以先看清楚地改了什么。

#### 迁移没有锁文件的旧安装

锁文件出现之前，安装没有基线，旧副本与"旧副本且被本地修改过"无法区分。因此这类文件一律报告为 `unverified`，不会自动更新——`add` 和 `update` 都必须加 `--force`。一次性迁移步骤：

```bash
zerodep status                  # 查看哪些模块是 unverified
zerodep update sse --diff       # 逐个查看改动
zerodep update sse --force      # 采用上游内容并写入锁文件
# 或者接受所有 unverified 模块都被重写：
zerodep update --all --force
```

之后锁文件存在，后续更新只会替换仍与记录一致的文件。

### `zerodep status`

列出所有已安装模块的安装版本、最新版本和状态（与 `update` 使用同一套状态）。

```bash
$ zerodep status
Module      Installed  Latest  State
----------  ---------  ------  ----------------
httpclient  0.6.1      0.6.1   up-to-date
jsonx       1.0.0      1.0.2   outdated
yaml        0.3.1      0.3.1   locally-modified
```

```bash
zerodep status --json         # 机器可读输出，并附带各状态计数
zerodep status --exit-code    # 只要存在非最新状态就退出 1
```

`status` 还会提示未安装的依赖。手工放进 vendor 目录、锁文件里没有记录的模块同样会被列出。

### `zerodep remove <module> [...]`

删除已安装模块的文件并同步更新锁文件。仅因它而被拉取的依赖会被建议移除；仍被它需要的依赖会被提示。

```bash
# 先看会删除什么
zerodep remove sse --dry-run

# 直接删除，跳过确认
zerodep remove sse -y

# 删除被本地修改过的模块
zerodep remove sse --force

# 机器可读结果
zerodep remove sse -y --json
```

`remove` 默认拒绝删除与锁文件记录不一致的已跟踪文件（需要 `--force`），并在仍被其他已安装模块依赖时给出警告。`--json` 需要配合 `--yes`（或 `--force`），因为它无法交互确认。

### `zerodep outdated`

列出本地 zerodep 文件及其与上游的对比结果。状态词与 `status` 相同；有锁文件时能区分上游变更和本地修改，没有锁文件时任何内容差异都报告为 `unverified`。

```bash
$ zerodep outdated
Module  Local Ver  Latest Ver  Status
------  ---------  ----------  ----------------
semver  0.3.0      0.4.0       unverified
yaml    0.3.1      0.3.1       up-to-date
```

- **up-to-date** — 内容与上游一致（元数据可能不同）
- **unverified** — 没有锁文件记录且内容与上游不同；可能只是旧版本，也可能被修改过，或两者兼有
- **outdated** / **locally-modified** / **conflict** / **missing** / **upstream-removed** — 含义见 `update` 一节

`--json` 输出机器可读结果，`--exit-code` 在任何模块非最新时以 1 退出。只检查目标目录中存在的文件。

### `zerodep version-check`

检查哪些模块在其声明版本后有代码修改。将每个模块当前源码的内容哈希与其声明版本对应的 git tag 进行对比。

```bash
$ zerodep version-check
Module       Version  Status
-----------  -------  -----------------------------
aes          0.4.0    up-to-date
cache        0.2.0    up-to-date
config       0.3.0    modified (needs version bump)
yaml         0.3.0    up-to-date
...
```

这是维护者命令——在发布前运行，确保所有修改过的模块都已更新版本号。

使用 `--strict` 可在有模块需要 bump 时以退出码 1 退出（适用于 CI）：

```bash
$ zerodep version-check --strict
# 全部最新时退出 0，有模块需要 bump 时退出 1
```

### `zerodep release-check`

执行打发布 tag 前必须通过的全部检查：模块版本是否与已声明的版本 tag 一致、manifest 是否最新、`pyproject.toml` 与 `zerodep.py` 的 CalVer 版本是否一致、模块源码是否只导入标准库与同项目模块、frontmatter 的 `deps` 是否与实际同项目导入一致、每个需要参考实现的 benchmark 是否有对应的 `bench-*` extra、每个测试文件是否已接入 Makefile、生成的文档模块索引（在挂载了 docs worktree 时）以及工作区是否干净。任一检查失败都会以退出码 1 结束。

Release 工作流调用的正是同一条命令，因此本地检查与 CI 不会出现偏差。

```bash
$ zerodep release-check
Check            Result  Detail
---------------  ------  ---------------------------------------------
module-versions  ok      49 modules match their declared versions
manifest         ok      manifest.json matches the source tree
project-version  ok      2026.10.23.1 is CalVer and matches zerodep.py
docs-index       ok      docs module index matches the manifest
working-tree     ok      no uncommitted tracked changes

release-check passed
```

迭代过程中可使用 `--allow-dirty` 跳过工作区检查。

两项可选检查不重复实现，而是委托给项目自身的工具：

```bash
# 运行 pre-commit 钩子（ruff、ruff-format、ty、complexipy）
zerodep release-check --with-lint

# 只测试指定模块（逗号分隔）
zerodep release-check --with-tests httpclient,httpserver

# 运行全部正确性测试
zerodep release-check --with-tests
```

使用 `--version X` 可额外校验即将打出的版本号：必须是 CalVer（`YYYY.M.D` / `YYYY.M.D.N`），且 `vX` tag 尚不存在。Release 工作流会传入它计算出的版本号，因此手动触发时传入任意版本字符串会在这里失败，而不会打出一个名不副实的 tag。

manifest 检查只比较描述源码树的字段（`files`、`version`、`content_hash`、`deps`、`tier`、`category`、`description`），忽略 `generated` 与每个模块的 `last_updated`——它们来自提交时间戳，在历史被压缩或重写时会变化。注意：未挂载 docs worktree 时会跳过 `docs-index` 检查（CI 中即是如此），因此文档门禁只在维护者本地运行。

### 目录类命令作用于哪棵树

读取或改写模块源码的命令——`manifest`、`bump`、`new`、`version-check`、
`dep-graph`、`dep-check` 与 `release-check`——都作用于一个“目录”（catalog），
即包含 `manifest.json` 的 checkout。它们从当前目录逐级向上查找；若都找不到，
则退回到 CLI 自身所在的目录（当该目录本身是 checkout 时）。

因此，pip 安装的 CLI 在 checkout 内可以直接使用，无需 `python -m zerodep`：

```bash
cd ~/projects/zerodep
zerodep release-check        # 检查这个 checkout，而不是 site-packages

cd httpclient
zerodep version-check        # 仍然解析到上层的 checkout
```

以 `manifest.json` 作为标记，是因为它本身就是目录清单——只含 `pyproject.toml`
的目录属于别的项目，而不是本目录。不在任何目录内时，命令会拒绝执行而不是瞎猜：

```
error: version-check inspects the zerodep source tree, but no manifest.json is
above /home/me/other-project and this CLI is not part of a checkout
(/usr/lib/python3/site-packages).
  Run it from a checkout: cd /path/to/zerodep && python -m zerodep version-check
```

没有这道防线时，`site-packages` 里的每个目录都像是 zerodep 模块，这正是该命令
过去会报告的内容。若同时存在两个目录（CLI 属于一个 checkout，而你站在另一个
checkout 里），命令会在写入前指明它使用的是哪棵树。

### `zerodep bump`

自动检测变更模块并 bump 其 frontmatter 版本号。默认执行 patch bump；可使用 `--minor` 或 `--major` 进行更大幅度的版本递增。

```bash
# 自动检测并 patch bump 所有变更模块
$ zerodep bump
Module       Old    New
-----------  -----  -----
config       0.3.0  0.3.1
yaml         0.3.0  0.3.1

bumped 2 module(s) (patch)
regenerating manifest.json ...
Generated manifest.json with 34 modules

# 对指定模块进行 minor bump
$ zerodep bump --minor config yaml

# major bump
$ zerodep bump --major config
```

Bump 完成后会自动重新生成 manifest。此命令被 [Release 工作流](https://github.com/Oaklight/zerodep/actions/workflows/release.yml) 用于在打 tag 前 bump 版本号。

### `zerodep new`

生成新模块目录的脚手架模板文件。

```bash
# 使用默认值创建新模块（tier=simple, category=utility）
$ zerodep new mymodule

# 指定分类和层级
$ zerodep new mymodule --category network --tier subsystem

# 带依赖
$ zerodep new mymodule --deps httpclient yaml

# 从已有 Python 文件创建模块
$ zerodep new mymodule --from ~/projects/other/mymodule.py

# 从已有文件创建，同时覆盖分类和层级
$ zerodep new mymodule --from ./mymodule.py --category text --tier medium
```

使用 `--from` 时，命令会：

- 将源文件复制到新模块目录中
- 如果源文件没有 zerodep frontmatter，自动注入（保留 shebang/encoding 声明）
- 如果已有 frontmatter 则复用；`--category`、`--tier`、`--deps` 可以覆盖
- 检测到第三方 import 时输出警告（zerodep 模块必须仅使用标准库）

不使用 `--from` 时，创建空的脚手架：

```
mymodule/
├── mymodule.py               # 包含 frontmatter 和版权信息的模块文件
└── test_mymodule_correctness.py  # 测试文件脚手架
```

可用分类：`agent`、`data`、`network`、`text`、`search`、`config`、`cli`、`security`、`utility`。
可用层级：`simple`、`medium`、`subsystem`。

### `zerodep dep-graph`

显示模块依赖关系。无参数时显示所有有依赖关系的模块表格；指定模块名时显示详细的依赖信息，包括传递性影响分析。

```bash
# 所有有依赖关系的模块
$ zerodep dep-graph
Module       Depends on           Depended on by
-----------  -------------------  -------------------
config       dotenv, jsonx, yaml  (none)
frontmatter  yaml                 skills
yaml         (none)               config, frontmatter
...

# 单个模块详情
$ zerodep dep-graph yaml
Module: yaml (v0.3.0)
  Depends on: (none)
  Depended on by: config, frontmatter
  Transitively affects: config, frontmatter, skills
```

### `zerodep dep-check`

自动检测变更模块，并运行这些模块及其所有下游依赖的正确性测试。确保某个模块的变更不会破坏依赖它的其他模块。

```bash
# 自动检测变更模块
$ zerodep dep-check

Changed modules: yaml
Affected downstream: config, frontmatter, skills
Total modules to test: 4

Module       Changed  Test  Detail
-----------  -------  ----  ------
config       no       pass
frontmatter  no       pass
skills       no       pass
yaml         yes      pass

4 passed

# 检查指定模块
$ zerodep dep-check yaml config
```

测试失败时退出码为 1——适用于 CI 流水线和发布前检查。

### `zerodep manifest`

从本地模块源文件重新生成 `manifest.json`。这是维护者命令——在仓库中添加或更新模块后运行。

```bash
$ zerodep manifest
Generated manifest.json with 20 modules
Modules with dependencies:
  sse -> httpclient
  vcs -> diff
```

详见 [Manifest 清单](manifest.md) 了解清单格式。

### `zerodep version`

输出 CLI 版本号。

```bash
$ zerodep version
zerodep 2026.4.11
```

## 全局选项

| 选项 | 说明 |
|------|------|
| `--offline` | 仅使用缓存文件，不访问网络 |
| `--local` | 使用本地 `manifest.json` 和模块源码，不从远程获取 |
| `--ref <ref>` | 从指定的 release tag、分支或提交安装（默认：最新 release，缓存一小时） |

全局选项必须写在子命令之前：`zerodep --ref master add sse`。

## 网络行为

CLI 从解析出的源版本（默认是最新 release，而不是会移动的 `master` 分支）使用多源回退链获取文件：

```
GitHub raw → jsDelivr CDN → Fastly CDN → 本地缓存
```

1. 优先尝试 `raw.githubusercontent.com`
2. 回退到 `cdn.jsdelivr.net` 镜像
3. 回退到 `fastly.jsdelivr.net` 镜像
4. 如果全部失败，使用本地缓存（会发出警告）
5. 使用 `--offline` 时完全跳过网络，仅使用缓存

获取的文件按 ref 缓存在 `~/.zerodep/cache/`，供离线使用。写入任何文件之前，都会用 manifest 校验其内容哈希；校验失败会中止整个操作，不会留下半安装的模块。

## 源版本锁定与锁文件

`zerodep add` 会在安装目录旁写入 `zerodep.lock.json`，记录源仓库与确切 ref、每个模块的版本和上游内容哈希、每个已安装文件的 sha256，以及该模块是显式请求的还是作为依赖拉取的。

```json
{
  "lock_version": 1,
  "source": {"repo": "Oaklight/zerodep", "ref": "v2026.10.23"},
  "modules": {
    "sse": {
      "version": "0.4.1",
      "upstream_hash": "b7937446…",
      "requested": true,
      "files": {"sse.py": "3f216fb3…"}
    }
  }
}
```

请把锁文件与 vendor 的模块一起提交。它让 `update` 能区分"上游变了"和"我改过这个文件"，也固定了项目实际安装的来源版本。使用 `--no-lock` 可以关闭。

## 依赖解析

使用 `add` 命令时，CLI 会进行拓扑排序的依赖解析：

```
zerodep add sse
→ 读取 manifest.json
→ sse 依赖 httpclient
→ 解析结果: [httpclient, sse]（依赖优先）
→ 拷贝两个文件
```

使用 `--no-deps` 可跳过依赖解析，仅拷贝明确请求的模块。

## 使用示例

### 快速开始

```bash
# 创建新项目并拉入所需模块
mkdir my-tool && cd my-tool
zerodep add yaml dotenv structlog
# 现在你有了 yaml.py, dotenv.py, structlog.py——可以直接 import
```

### 作为库的 vendor 依赖

```bash
# 以子目录结构拷贝到 vendor/ 目录
zerodep add retry httpclient -d vendor/ --nested
# 结果: vendor/retry/retry.py, vendor/httpclient/httpclient.py
```

### 隔离网络环境

```bash
# 在有网络的机器上——填充缓存
zerodep add scheduler yaml dotenv -y
# 文件缓存在 ~/.zerodep/cache/

# 在隔离网络的机器上——拷贝缓存目录，然后：
zerodep add scheduler yaml dotenv --offline -y
```
