---
title: 安装与获取
---

# 安装与获取

## 工作原理

zerodep 的每个模块都是独立的单 `.py` 文件，零外部依赖。你只需将所需的文件复制到项目目录中并 `import` 即可——运行时无需任何包管理器。这使得 zerodep 非常适合受限环境、引导脚本以及对供应链安全敏感的项目。

## 使用 CLI 工具（推荐）

获取模块最简单的方式是通过 `zerodep` CLI：

```bash
pip install zerodep
zerodep add yaml retry
```

这会将 `yaml.py` 和 `retry.py` 下载到当前目录，并自动解析模块间的依赖关系。CLI 还支持缓存、多源回退和离线模式。

完整的命令参考请查看 [CLI 工具](cli.md)。

## 手动下载

如果你不想安装 CLI，也可以直接下载单个模块文件：

```bash
curl -O https://raw.githubusercontent.com/Oaklight/zerodep/master/yaml/yaml.py
```

或者克隆整个仓库后复制所需文件：

```bash
git clone https://github.com/Oaklight/zerodep.git
cp zerodep/yaml/yaml.py ./
```

## 依赖解析

部分 zerodep 模块依赖于其他 zerodep 模块。完整的依赖关系如下：

| 模块 | 依赖 |
|------|------|
| `a2a` | `jsonrpc` |
| `acp` | `jsonrpc` |
| `config` | `dotenv`、`yaml`、`jsonx` |
| `frontmatter` | `yaml` |
| `skills` | `frontmatter`、`search` |
| `sse` | `httpclient` |
| `vcs` | `diff` |

其余所有模块均完全独立，无模块间依赖。

**使用 CLI 时**，依赖会被自动解析和拉取——你只需 `zerodep add sse`，`sse.py` 和 `httpclient.py` 就会一起出现。

**手动下载时**，你需要自行获取依赖。请检查每个模块文件顶部的 `# /// zerodep` frontmatter 注释块中的 `deps` 列表。

## 项目集成方式

### 扁平结构（默认）

将 `.py` 文件直接复制到项目根目录：

```bash
zerodep add yaml retry
```

```
my-project/
├── main.py
├── yaml.py
└── retry.py
```

### Vendor 目录

使用 `-d` 将模块放入专用目录：

```bash
zerodep add yaml retry -d vendor/
```

```
my-project/
├── main.py
└── vendor/
    ├── yaml.py
    └── retry.py
```

然后通过 `from vendor.yaml import ...` 导入，或将 `vendor/` 添加到 Python 路径。

### 嵌套结构（子目录）

使用 `--nested` 镜像仓库的目录布局：

```bash
zerodep add yaml retry --nested
```

```
my-project/
├── main.py
├── yaml/
│   └── yaml.py
└── retry/
    └── retry.py
```

当模块包含变体文件时（如 `aes/aes.py` 和 `aes/aes_python.py`），这种方式特别有用。`-d` 和 `--nested` 可以组合使用（如 `zerodep add sse -d lib/ --nested`）。
