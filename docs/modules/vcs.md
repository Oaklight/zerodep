# VCS

Git/Mercurial/Jujutsu CLI wrapper -- zero dependencies, stdlib only, Python 3.10+.

## Overview

The VCS module provides a uniform Python interface to version-control systems by shelling out to their CLI binaries. Each backend implements the `VCSBackend` protocol, enabling VCS-agnostic tooling. Cross-platform binary discovery handles Linux, macOS, and Windows.

| File | Description | Dependencies |
|------|-------------|--------------|
| `vcs.py` | VCS CLI wrapper | None (stdlib only) |

The module supports three VCS backends:

| Backend | Binary | Coverage |
|---------|--------|----------|
| **Git** | `git` | Full (diff, status, log, blame, apply, merge-file, branch) |
| **Mercurial** | `hg` | Core subset (diff, status, log, blame, branch) |
| **Jujutsu** | `jj` | Core subset (diff, status, log, blame, branch) |

## How to Use in Your Project

Just copy the single `.py` file into your project:

```bash
cp vcs/vcs.py your_project/
```

Then import directly:

```python
from vcs import detect, Git
```

## API Reference

### `detect(path)`

Auto-detect the VCS backend for a given directory.

```python
def detect(path: str = ".") -> VCSBackend | None
```

Walks upward from `path` checking for `.git/`, `.hg/`, or `.jj/` directories. Returns the corresponding backend instance if the binary is available, or `None` if no repository is found.

**Example:**

```python
from vcs import detect

repo = detect(".")
if repo is not None:
    print(repo.name)           # "git", "hg", or "jj"
    print(repo.current_branch())
```

### `VCSBackend` Protocol

All backends implement this protocol:

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

### Git Backend

The most complete backend. Created by passing a repository path:

```python
from vcs import Git

g = Git("/path/to/repo")
```

#### `status()`

Returns a list of `FileStatus` objects for the working tree.

```python
statuses = g.status()
for s in statuses:
    print(s.status, s.path)  # e.g. "M file.txt", "? new.txt"
```

Status codes: `M` (modified), `A` (added), `D` (deleted), `R` (renamed), `?` (untracked).

#### `diff(*paths, staged=False)`

Returns unified diff text for working tree changes.

```python
d = g.diff()                    # All unstaged changes
d = g.diff(staged=True)         # Staged changes only
d = g.diff("src/main.py")      # Specific file
```

#### `diff_files(path_a, path_b)`

Diff two arbitrary files (not necessarily tracked).

```python
d = g.diff_files("/tmp/old.txt", "/tmp/new.txt")
```

#### `log(n=10)`

Returns recent commits as `Commit` objects.

```python
commits = g.log(n=5)
for c in commits:
    print(c.short_hash, c.author, c.message)
```

#### `blame(path)`

Returns per-line blame information as `BlameLine` objects.

```python
lines = g.blame("README.md")
for bl in lines:
    print(f"{bl.commit[:8]} {bl.author:>15}  {bl.content}", end="")
```

#### `apply(patch)`

Apply a unified diff patch to the working tree.

```python
g.apply(diff_text)
```

#### `current_branch()`

Returns the current branch name, or the short commit hash for detached HEAD.

```python
branch = g.current_branch()  # "main", "feature/xyz", etc.
```

#### `merge_file(base, ours, theirs)`

Three-way merge of text content using `git merge-file`.

```python
result = g.merge_file(base_text, our_text, their_text)
```

## Data Structures

### `FileStatus`

Frozen dataclass representing a file's status.

- `path: str` -- Relative path.
- `status: str` -- Single-character code (`'M'`, `'A'`, `'D'`, `'R'`, `'?'`, `'!'`).
- `original_path: str | None` -- For renames, the original path.

### `Commit`

Frozen dataclass for commit metadata.

- `hash: str` -- Full commit hash.
- `short_hash: str` -- Abbreviated hash.
- `author: str` -- Author name.
- `date: str` -- ISO 8601 date string.
- `message: str` -- Commit message subject.

### `BlameLine`

Frozen dataclass for per-line blame information.

- `commit: str` -- Commit hash.
- `author: str` -- Author name.
- `date: str` -- Commit date.
- `line_no: int` -- 1-based line number.
- `content: str` -- Line content.

## Exceptions

| Exception | When Raised |
|-----------|-------------|
| `VCSError` | Base class for all VCS errors. |
| `BinaryNotFoundError` | VCS binary not found on the system (with `binary_name`). |
| `CommandError` | VCS command exited with unexpected return code (with `command`, `returncode`, `stderr`). |
| `NotARepoError` | Path is not inside a repository (with `path`). |

## Cross-Platform Binary Discovery

The module uses a three-tier strategy to locate VCS binaries:

1. **Environment variable override:** `ZERODEP_GIT_PATH`, `ZERODEP_HG_PATH`, `ZERODEP_JJ_PATH`
2. **`shutil.which()`:** Standard PATH lookup (works on all platforms)
3. **Windows fallback:** Checks common install directories (e.g. `C:\Program Files\Git\bin\git.exe`)

macOS Homebrew paths (`/opt/homebrew/bin`, `/usr/local/bin`) are included in the search.

## Cross-Module Integration

The Mercurial and Jujutsu backends optionally use the sibling `diff/diff.py` module's `merge3()` function for `merge_file()`. If the diff module is not available, `merge_file()` raises `NotImplementedError` for those backends.

## Notes and Caveats

!!! info "Subprocess-Based"
    All VCS operations shell out to the CLI binary. This means the corresponding VCS tool must be installed on the system. The module does not embed or bundle any VCS implementation.

!!! info "Windows Support"
    On Windows, subprocess calls use `CREATE_NO_WINDOW` to prevent console window flashing. Binary discovery includes common Windows installation paths.

- **Python version:** Requires Python 3.10+.
- **No benchmark:** Since all operations are subprocess-based, performance is dominated by process startup and CLI execution time rather than Python code.
- **Git is most complete:** Mercurial and Jujutsu backends cover core operations but lack some Git-specific features like `diff_files` and native `merge_file`.
