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
zerodep 0.1.0
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
