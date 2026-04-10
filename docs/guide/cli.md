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
```

**确认提示** — 默认情况下，`add` 会显示执行计划并请求确认：

```
Will copy:
  sse.py                    -> sse.py  [sse]
  httpclient.py             -> httpclient.py  [httpclient (dependency)]
Target: /home/user/my-project
Continue? [Y/n]
```

### `zerodep update <module> [...]`

重新获取并覆盖已有模块文件。等同于 `add --force --yes`。

```bash
zerodep update sse
```

### `zerodep outdated`

检查本地 zerodep 文件是否有上游内容变更。将每个本地文件的内容哈希与 manifest 对比，忽略仅元数据变更（如版本号更新）。

```bash
$ zerodep outdated
Module  Local Ver  Latest Ver  Status
------  ---------  ----------  ----------
semver  0.3.0      0.4.0       up-to-date
yaml    0.3.0      0.4.0       outdated
```

- **up-to-date** — 文件内容与上游一致（元数据可能不同）
- **outdated** — 文件有实质性的上游内容变更

仅检查当前目录中存在的文件；本地不存在的模块会被跳过。

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

### `zerodep dep-graph`

显示模块依赖关系。无参数时显示所有有依赖关系的模块表格；指定模块名时显示详细的依赖信息，包括传递性影响分析。

```bash
# 所有有依赖关系的模块
$ zerodep dep-graph
Module       Depends on           Depended on by
-----------  -------------------  -------------------
config       dotenv, jsonc, yaml  (none)
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
zerodep 2026.4.0
```

## 全局选项

| 选项 | 说明 |
|------|------|
| `--offline` | 仅使用缓存文件，不访问网络 |
| `--local` | 使用本地 `manifest.json`，不从远程获取 |

## 网络行为

CLI 使用多源回退链获取文件：

```
GitHub raw → jsDelivr CDN → Fastly CDN → 本地缓存
```

1. 优先尝试 `raw.githubusercontent.com`
2. 回退到 `cdn.jsdelivr.net` 镜像
3. 回退到 `fastly.jsdelivr.net` 镜像
4. 如果全部失败，使用本地缓存（会发出警告）
5. 使用 `--offline` 时完全跳过网络，仅使用缓存

获取的文件缓存在 `~/.zerodep/cache/`，供离线使用。

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
