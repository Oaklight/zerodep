# VCS 版本控制

Git/Mercurial/Jujutsu CLI 封装 —— 零依赖，仅使用标准库，支持 Python 3.10+。

## 概述

VCS 模块通过调用 CLI 二进制文件，提供版本控制系统的统一 Python 接口。每个后端都实现了 `VCSBackend` 协议，支持编写与 VCS 无关的工具代码。跨平台二进制发现机制兼容 Linux、macOS 和 Windows。

| 文件 | 说明 | 依赖 |
|------|------|------|
| `vcs.py` | VCS CLI 封装 | 无（仅标准库） |

模块支持三种 VCS 后端：

| 后端 | 二进制 | 覆盖范围 |
|------|--------|----------|
| **Git** | `git` | 完整（diff、status、log、blame、apply、merge-file、branch） |
| **Mercurial** | `hg` | 核心子集（diff、status、log、blame、branch） |
| **Jujutsu** | `jj` | 核心子集（diff、status、log、blame、branch） |

## 如何在项目中使用

只需将单个 `.py` 文件复制到你的项目中：

```bash
cp vcs/vcs.py your_project/
```

然后直接导入：

```python
from vcs import detect, Git
```

## API 参考

### `detect(path)`

自动检测指定目录的 VCS 后端。

```python
def detect(path: str = ".") -> VCSBackend | None
```

从 `path` 向上遍历检查 `.git/`、`.hg/` 或 `.jj/` 目录。如果对应的二进制可用，返回相应的后端实例；未找到仓库时返回 `None`。

**示例：**

```python
from vcs import detect

repo = detect(".")
if repo is not None:
    print(repo.name)           # "git"、"hg" 或 "jj"
    print(repo.current_branch())
```

### `VCSBackend` 协议

所有后端都实现此协议：

```python
class VCSBackend(Protocol):
    name: str
    def is_repo(self, path: str) -> bool: ...
    def diff(self, *paths: str, staged: bool = False) -> str: ...
    def diff_files(self, path_a: str, path_b: str) -> str: ...
    def apply(self, patch: str) -> None: ...
    def status(self) -> list[FileStatus]: ...
    def log(self, n: int = 10) -> list[Commit]: ...
    def blame(self, path: str) -> list[BlameLine]: ...
    def current_branch(self) -> str: ...
    def merge_file(self, base: str, ours: str, theirs: str) -> str: ...
```

### Git 后端

最完整的后端。通过传递仓库路径创建：

```python
from vcs import Git

g = Git("/path/to/repo")
```

#### `status()`

返回工作区的 `FileStatus` 对象列表。

```python
statuses = g.status()
for s in statuses:
    print(s.status, s.path)  # 例如 "M file.txt"、"? new.txt"
```

状态码：`M`（修改）、`A`（新增）、`D`（删除）、`R`（重命名）、`?`（未跟踪）。

#### `diff(*paths, staged=False)`

返回工作区变更的 unified diff 文本。

```python
d = g.diff()                    # 所有未暂存的变更
d = g.diff(staged=True)         # 仅暂存的变更
d = g.diff("src/main.py")      # 指定文件
```

#### `diff_files(path_a, path_b)`

对比两个任意文件（不一定是被跟踪的）。

```python
d = g.diff_files("/tmp/old.txt", "/tmp/new.txt")
```

#### `log(n=10)`

返回最近的提交，以 `Commit` 对象列表形式。

```python
commits = g.log(n=5)
for c in commits:
    print(c.short_hash, c.author, c.message)
```

#### `blame(path)`

返回按行的 blame 信息，以 `BlameLine` 对象列表形式。

```python
lines = g.blame("README.md")
for bl in lines:
    print(f"{bl.commit[:8]} {bl.author:>15}  {bl.content}", end="")
```

#### `apply(patch)`

将 unified diff 补丁应用到工作区。

```python
g.apply(diff_text)
```

#### `current_branch()`

返回当前分支名，或在 detached HEAD 时返回短提交哈希。

```python
branch = g.current_branch()  # "main"、"feature/xyz" 等
```

#### `merge_file(base, ours, theirs)`

使用 `git merge-file` 进行文本内容的三路合并。

```python
result = g.merge_file(base_text, our_text, their_text)
```

## 数据结构

### `FileStatus`

冻结的 dataclass，表示文件状态。

- `path: str` -- 相对路径。
- `status: str` -- 单字符状态码（`'M'`、`'A'`、`'D'`、`'R'`、`'?'`、`'!'`）。
- `original_path: str | None` -- 重命名时的原始路径。

### `Commit`

冻结的 dataclass，表示提交元数据。

- `hash: str` -- 完整提交哈希。
- `short_hash: str` -- 缩写哈希。
- `author: str` -- 作者姓名。
- `date: str` -- ISO 8601 日期字符串。
- `message: str` -- 提交消息主题。

### `BlameLine`

冻结的 dataclass，表示按行的 blame 信息。

- `commit: str` -- 提交哈希。
- `author: str` -- 作者姓名。
- `date: str` -- 提交日期。
- `line_no: int` -- 1-based 行号。
- `content: str` -- 行内容。

## 异常

| 异常 | 触发条件 |
|------|----------|
| `VCSError` | 所有 VCS 错误的基类。 |
| `BinaryNotFoundError` | 系统中未找到 VCS 二进制文件（包含 `binary_name`）。 |
| `CommandError` | VCS 命令以意外返回码退出（包含 `command`、`returncode`、`stderr`）。 |
| `NotARepoError` | 路径不在仓库内（包含 `path`）。 |

## 跨平台二进制发现

模块使用三级策略定位 VCS 二进制文件：

1. **环境变量覆盖：** `ZERODEP_GIT_PATH`、`ZERODEP_HG_PATH`、`ZERODEP_JJ_PATH`
2. **`shutil.which()`：** 标准 PATH 查找（所有平台通用）
3. **Windows 回退：** 检查常见安装目录（如 `C:\Program Files\Git\bin\git.exe`）

macOS Homebrew 路径（`/opt/homebrew/bin`、`/usr/local/bin`）包含在搜索范围内。

## 跨模块集成

Mercurial 和 Jujutsu 后端可选使用兄弟模块 `diff/diff.py` 的 `merge3()` 函数来实现 `merge_file()`。如果 diff 模块不可用，这些后端的 `merge_file()` 将抛出 `NotImplementedError`。

## 注意事项

!!! info "基于子进程"
    所有 VCS 操作通过调用 CLI 二进制文件执行。这意味着系统上必须安装对应的 VCS 工具。模块不嵌入或捆绑任何 VCS 实现。

!!! info "Windows 支持"
    在 Windows 上，子进程调用使用 `CREATE_NO_WINDOW` 以防止控制台窗口闪烁。二进制发现包含常见的 Windows 安装路径。

- **Python 版本：** 需要 Python 3.10+。
- **无性能测试：** 由于所有操作基于子进程，性能主要取决于进程启动和 CLI 执行时间，而非 Python 代码。
- **Git 最为完整：** Mercurial 和 Jujutsu 后端覆盖核心操作，但缺少一些 Git 特有的功能如 `diff_files` 和原生 `merge_file`。
