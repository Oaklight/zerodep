# /// zerodep
# version = "0.2.2"
# deps = ["diff"]
# tier = "subsystem"
# category = "devtools"
# ///
"""VCS CLI wrapper — zero dependencies, stdlib only, Python 3.10+.

Part of zerodep: https://github.com/Oaklight/zerodep
Copyright (c) 2026 Peng Ding. MIT License.

Provides a uniform Python interface to version-control systems (Git,
Mercurial, Jujutsu) by shelling out to their CLI binaries.  Each backend
implements the :class:`VCSBackend` protocol so callers can write
VCS-agnostic tooling.

Quick start::

    from vcs import detect

    repo = detect(".")
    if repo is not None:
        print(repo.name, repo.current_branch())
        for fs in repo.status():
            print(fs.status, fs.path)

Requires Python 3.10+.
"""

from __future__ import annotations

import dataclasses
import os
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Any, Callable, Protocol, runtime_checkable

# ── Sentinel for injection parameters ──────────────────────────────────────


class _Unset:
    """Sentinel indicating 'use default sibling auto-discovery'."""

    _instance: _Unset | None = None

    def __new__(cls) -> _Unset:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "UNSET"


_UNSET = _Unset()


def _ensure_sibling_path(name: str) -> str:
    """Return the sibling module directory and prepend it to ``sys.path``."""
    sibling_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", name)
    if sibling_dir not in sys.path:
        sys.path.insert(0, sibling_dir)
    return sibling_dir


# ── Sibling diff module import (lazy) ───────────────────────────────────────


def _load_diff_merge3():
    """Load the sibling ``diff`` module's ``merge3`` function on demand."""
    _ensure_sibling_path("diff")
    try:
        from diff import merge3 as diff_merge3
    except (ImportError, AttributeError) as exc:
        raise NotImplementedError(
            "merge_file requires the sibling diff module. "
            "Place diff.py in a sibling directory or on sys.path."
        ) from exc
    return diff_merge3


# ── Exceptions ───────────────────────────────────────────────────────


class VCSError(Exception):
    """Base exception for all VCS operations."""


class BinaryNotFoundError(VCSError):
    """Raised when the VCS binary cannot be located.

    Attributes:
        binary_name: Name of the binary that was not found.
    """

    def __init__(self, binary_name: str) -> None:
        self.binary_name = binary_name
        super().__init__(f"VCS binary not found: {binary_name}")


class CommandError(VCSError):
    """Raised when a VCS command exits with an unexpected return code.

    Attributes:
        command: The full command list that was executed.
        returncode: Process exit code.
        stderr: Captured standard-error output.
        timeout: Timeout value in seconds if this was a timeout, else ``None``.
    """

    def __init__(
        self,
        command: list[str],
        returncode: int,
        stderr: str,
        *,
        timeout: float | None = None,
    ) -> None:
        self.command = command
        self.returncode = returncode
        self.stderr = stderr
        self.timeout = timeout
        cmd_str = " ".join(command)
        if timeout is not None:
            msg = f"Command timed out after {timeout}s: {cmd_str}"
        else:
            msg = f"Command failed (rc={returncode}): {cmd_str}\n{stderr.rstrip()}"
        super().__init__(msg)


class NotARepoError(VCSError):
    """Raised when the given path is not inside a repository.

    Attributes:
        path: Filesystem path that was tested.
    """

    def __init__(self, path: str) -> None:
        self.path = path
        super().__init__(f"Not a repository: {path}")


# ── Data Structures ──────────────────────────────────────────────────


@dataclasses.dataclass(frozen=True)
class FileStatus:
    """Status of a single file in the working tree.

    Attributes:
        path: Relative path of the file.
        status: Single-character status code (e.g. ``'M'``, ``'A'``,
            ``'D'``, ``'R'``, ``'?'``, ``'!'``).
        original_path: For renames/copies, the path before the operation.
    """

    path: str
    status: str
    original_path: str | None = None


@dataclasses.dataclass(frozen=True)
class Commit:
    """Metadata for a single commit.

    Attributes:
        hash: Full commit hash.
        short_hash: Abbreviated commit hash.
        author: Author name.
        date: Commit date in ISO 8601 format.
        message: First line of the commit message.
    """

    hash: str
    short_hash: str
    author: str
    date: str
    message: str


@dataclasses.dataclass(frozen=True)
class BlameLine:
    """Annotation for a single source line.

    Attributes:
        commit: Commit hash that last changed this line.
        author: Author of the commit.
        date: Commit date.
        line_no: 1-based line number.
        content: Actual text content of the line.
    """

    commit: str
    author: str
    date: str
    line_no: int
    content: str


@dataclasses.dataclass(frozen=True)
class WorkspaceInfo:
    """Information about a workspace (Git worktree / Jujutsu workspace).

    Attributes:
        path: Absolute path to the workspace directory.
        head: HEAD commit hash.
        branch: Branch name (Git) or bookmark (Jujutsu), ``None``
            for detached HEAD or unknown.
        is_main: Whether this is the main/default workspace.
    """

    path: str
    head: str
    branch: str | None = None
    is_main: bool = False


# ── Binary Discovery ─────────────────────────────────────────────────


def _find_binary(name: str) -> str:
    """Locate a VCS binary on the system.

    Resolution order:

    1. Environment variable ``ZERODEP_{NAME}_PATH`` (upper-cased).
    2. ``shutil.which`` (cross-platform PATH search).
    3. Windows-only fallback: common installation directories.

    Args:
        name: Binary name, e.g. ``"git"``, ``"hg"``, ``"jj"``.

    Returns:
        Absolute path to the binary.

    Raises:
        BinaryNotFoundError: If the binary cannot be found anywhere.
    """
    # 1. Explicit env override
    env_key = f"ZERODEP_{name.upper()}_PATH"
    env_path = os.environ.get(env_key)
    if env_path and os.path.isfile(env_path):
        return env_path

    # 2. Standard PATH lookup
    found = shutil.which(name)
    if found:
        return found

    # 3. Windows fallback directories
    if os.name == "nt":
        _WINDOWS_DIRS: dict[str, list[str]] = {
            "git": [
                os.path.join(
                    os.environ.get("ProgramFiles", r"C:\Program Files"),
                    "Git",
                    "bin",
                    "git.exe",
                ),
                os.path.join(
                    os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
                    "Git",
                    "bin",
                    "git.exe",
                ),
                os.path.join(
                    os.environ.get("LOCALAPPDATA", ""),
                    "Programs",
                    "Git",
                    "bin",
                    "git.exe",
                ),
            ],
            "hg": [
                os.path.join(
                    os.environ.get("ProgramFiles", r"C:\Program Files"),
                    "Mercurial",
                    "hg.exe",
                ),
            ],
        }
        for candidate in _WINDOWS_DIRS.get(name, []):
            if candidate and os.path.isfile(candidate):
                return candidate

    raise BinaryNotFoundError(name)


# ── Subprocess Helper ────────────────────────────────────────────────


def _run(
    cmd: list[str],
    *,
    cwd: str | None = None,
    input: str | None = None,  # noqa: A002
    timeout: float = 30.0,
    encoding: str = "utf-8",
    allowed_returncodes: tuple[int, ...] = (0,),
) -> subprocess.CompletedProcess[str]:
    """Run a subprocess and return its completed result.

    Args:
        cmd: Command and arguments list.
        cwd: Working directory for the subprocess.
        input: String to pass on stdin.
        timeout: Maximum seconds to wait.
        encoding: Text encoding for stdout/stderr.
        allowed_returncodes: Tuple of acceptable exit codes.

    Returns:
        The :class:`subprocess.CompletedProcess` result.

    Raises:
        VCSError: On timeout.
        CommandError: If the exit code is not in *allowed_returncodes*.
    """
    kwargs: dict = {
        "capture_output": True,
        "text": True,
        "encoding": encoding,
        "cwd": cwd,
        "input": input,
        "timeout": timeout,
    }
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

    try:
        result = subprocess.run(cmd, **kwargs)  # noqa: S603
    except subprocess.TimeoutExpired as exc:
        raise CommandError(
            cmd,
            -1,
            (exc.stderr or "").strip() if isinstance(exc.stderr, str) else "",
            timeout=timeout,
        ) from exc

    if result.returncode not in allowed_returncodes:
        raise CommandError(cmd, result.returncode, result.stderr)

    return result


# ── VCSBackend Protocol ──────────────────────────────────────────────


@runtime_checkable
class VCSBackend(Protocol):
    """Protocol that every VCS backend must satisfy."""

    @property
    def name(self) -> str:
        """Short name of the VCS (e.g. ``"git"``)."""
        ...

    def is_repo(self, path: str) -> bool:
        """Return ``True`` if *path* is inside a repository."""
        ...

    def diff(self, *paths: str, staged: bool = False) -> str:
        """Return a unified diff of uncommitted changes.

        Args:
            *paths: Restrict diff to these paths.
            staged: If ``True``, diff only staged (index) changes.
        """
        ...

    def diff_files(self, path_a: str, path_b: str) -> str:
        """Return a diff between two arbitrary files.

        Args:
            path_a: First file path.
            path_b: Second file path.
        """
        ...

    def apply(self, patch: str) -> None:
        """Apply a unified diff patch to the working tree.

        Args:
            patch: Patch text (unified diff format).
        """
        ...

    def status(self) -> list[FileStatus]:
        """Return the list of changed files in the working tree."""
        ...

    def log(self, n: int = 10) -> list[Commit]:
        """Return the last *n* commits.

        Args:
            n: Maximum number of commits to return.
        """
        ...

    def blame(self, path: str) -> list[BlameLine]:
        """Return per-line annotation for a file.

        Args:
            path: Path to the file (relative to repo root).
        """
        ...

    def current_branch(self) -> str:
        """Return the name of the current branch or bookmark."""
        ...

    def merge_file(self, base: str, ours: str, theirs: str) -> str:
        """Three-way merge of file contents.

        Args:
            base: Common-ancestor file content.
            ours: Content from the first branch.
            theirs: Content from the second branch.

        Returns:
            Merged file content (may contain conflict markers).
        """
        ...

    def workspace_add(
        self,
        path: str,
        *,
        branch: str | None = None,
        rev: str | None = None,
    ) -> str:
        """Create a new workspace at *path*.

        Args:
            path: Directory for the new workspace.
            branch: Branch to create (Git) or bookmark (Jujutsu).
            rev: Starting revision/commit.

        Returns:
            Absolute path to the created workspace.
        """
        ...

    def workspace_remove(self, path: str, *, force: bool = False) -> None:
        """Remove a workspace.

        Args:
            path: Path to the workspace directory.
            force: Force removal even with uncommitted changes.
        """
        ...

    def workspace_list(self) -> list[WorkspaceInfo]:
        """List all workspaces.

        Returns:
            List of :class:`WorkspaceInfo` entries.
        """
        ...

    def branches(self) -> list[str]:
        """List all branch names or bookmarks.

        Returns:
            List of branch/bookmark name strings.
        """
        ...

    def create_branch(self, name: str, *, rev: str | None = None) -> None:
        """Create a new branch or bookmark.

        Args:
            name: Branch/bookmark name.
            rev: Starting point (defaults to current HEAD).
        """
        ...

    def switch(self, target: str) -> None:
        """Switch to a branch or revision.

        Args:
            target: Branch name or revision identifier.
        """
        ...

    def commit(self, message: str, *, paths: list[str] | None = None) -> str:
        """Create a commit/change.

        Args:
            message: Commit message.
            paths: Files to stage and commit (Git-specific).

        Returns:
            Commit hash of the new commit.
        """
        ...

    def rev_parse(self, rev: str) -> str:
        """Resolve a revision string to a full commit hash.

        Args:
            rev: Revision string (branch name, tag, ``"HEAD"``, etc.).

        Returns:
            Full commit hash.
        """
        ...


# ── Git Backend ──────────────────────────────────────────────────────


class Git:
    """Git CLI backend.

    Args:
        repo_path: Path to the repository (defaults to ``"."``).
        binary: Explicit path to the ``git`` binary; discovered
            automatically if ``None``.
        encoding: Text encoding for command I/O.
        timeout: Default subprocess timeout in seconds.
    """

    def __init__(
        self,
        repo_path: str = ".",
        *,
        binary: str | None = None,
        encoding: str = "utf-8",
        timeout: float = 30.0,
    ) -> None:
        self._binary = binary or _find_binary("git")
        self._repo = os.path.abspath(repo_path)
        self._encoding = encoding
        self._timeout = timeout

    # -- helpers --

    def _git(
        self,
        *args: str,
        allowed_returncodes: tuple[int, ...] = (0,),
        input: str | None = None,  # noqa: A002
    ) -> subprocess.CompletedProcess[str]:
        """Run a git sub-command inside the repository.

        Args:
            *args: Arguments after ``git``.
            allowed_returncodes: Acceptable exit codes.
            input: Text to pass via stdin.

        Returns:
            Completed process result.
        """
        cmd = [self._binary, *args]
        return _run(
            cmd,
            cwd=self._repo,
            input=input,
            timeout=self._timeout,
            encoding=self._encoding,
            allowed_returncodes=allowed_returncodes,
        )

    # -- protocol implementation --

    @property
    def name(self) -> str:
        """Return ``"git"``."""
        return "git"

    def is_repo(self, path: str) -> bool:
        """Check whether *path* is inside a git repository.

        Args:
            path: Directory to test.

        Returns:
            ``True`` if *path* is a git working tree or bare repo.
        """
        git_dir = os.path.join(path, ".git")
        if os.path.isdir(git_dir) or os.path.isfile(git_dir):
            return True
        try:
            _run(
                [self._binary, "-C", path, "rev-parse", "--git-dir"],
                timeout=self._timeout,
                encoding=self._encoding,
            )
            return True
        except (VCSError, OSError):
            return False

    def diff(self, *paths: str, staged: bool = False) -> str:
        """Return a unified diff of uncommitted changes.

        Args:
            *paths: Restrict diff to these paths.
            staged: If ``True``, show only staged changes.

        Returns:
            Diff text (may be empty).
        """
        cmd: list[str] = ["diff"]
        if staged:
            cmd.append("--staged")
        if paths:
            cmd.append("--")
            cmd.extend(paths)
        result = self._git(*cmd, allowed_returncodes=(0, 1))
        return result.stdout

    def diff_files(self, path_a: str, path_b: str) -> str:
        """Return a diff between two arbitrary files.

        Args:
            path_a: First file path.
            path_b: Second file path.

        Returns:
            Diff text.
        """
        result = self._git(
            "diff", "--no-index", "--", path_a, path_b, allowed_returncodes=(0, 1)
        )
        return result.stdout

    def apply(self, patch: str) -> None:
        """Apply a unified diff patch via ``git apply``.

        Args:
            patch: Patch text.
        """
        self._git("apply", "-", input=patch)

    def status(self) -> list[FileStatus]:
        """Return the list of changed files via ``git status --porcelain``.

        Returns:
            List of :class:`FileStatus` entries.
        """
        result = self._git("status", "--porcelain=v1")
        entries: list[FileStatus] = []
        for line in result.stdout.splitlines():
            if len(line) < 4:
                continue
            xy = line[:2]
            rest = line[3:]
            # Pick the most informative status character:
            # index status (X) or work-tree status (Y).
            status_char = xy[0] if xy[0] != " " else xy[1]
            if status_char == "R" and " -> " in rest:
                old, new = rest.split(" -> ", 1)
                entries.append(FileStatus(path=new, status="R", original_path=old))
            elif " -> " in rest and xy[0] == "R":
                old, new = rest.split(" -> ", 1)
                entries.append(FileStatus(path=new, status="R", original_path=old))
            else:
                entries.append(FileStatus(path=rest, status=status_char))
        return entries

    def log(self, n: int = 10) -> list[Commit]:
        """Return the last *n* commits.

        Args:
            n: Maximum number of commits.

        Returns:
            List of :class:`Commit` entries, newest first.
        """
        fmt = "%H%n%h%n%an%n%aI%n%s"
        result = self._git("log", f"--format={fmt}", "-n", str(n))
        lines = result.stdout.strip().splitlines()
        commits: list[Commit] = []
        for i in range(0, len(lines) - 4, 5):
            commits.append(
                Commit(
                    hash=lines[i],
                    short_hash=lines[i + 1],
                    author=lines[i + 2],
                    date=lines[i + 3],
                    message=lines[i + 4],
                )
            )
        return commits

    def blame(self, path: str) -> list[BlameLine]:
        """Return per-line blame annotation via ``git blame --porcelain``.

        Args:
            path: File path relative to the repository root.

        Returns:
            List of :class:`BlameLine` entries, one per source line.
        """
        result = self._git("blame", "--porcelain", path)
        blame_lines: list[BlameLine] = []
        current_hash = ""
        current_author = ""
        current_date = ""
        current_lineno = 0
        for raw in result.stdout.splitlines():
            # Header line: <hash> <orig-line> <final-line> [<num-lines>]
            m = re.match(r"^([0-9a-f]{40})\s+\d+\s+(\d+)", raw)
            if m:
                current_hash = m.group(1)
                current_lineno = int(m.group(2))
                continue
            if raw.startswith("author "):
                current_author = raw[7:]
            elif raw.startswith("author-time "):
                current_date = raw[12:]
            elif raw.startswith("\t"):
                blame_lines.append(
                    BlameLine(
                        commit=current_hash,
                        author=current_author,
                        date=current_date,
                        line_no=current_lineno,
                        content=raw[1:],
                    )
                )
        return blame_lines

    def current_branch(self) -> str:
        """Return the current branch name.

        Falls back to the short HEAD hash when in detached-HEAD state.

        Returns:
            Branch name or abbreviated commit hash.
        """
        result = self._git("branch", "--show-current")
        branch = result.stdout.strip()
        if branch:
            return branch
        # Detached HEAD — return short hash
        result = self._git("rev-parse", "--short", "HEAD")
        return result.stdout.strip()

    def merge_file(self, base: str, ours: str, theirs: str) -> str:
        """Three-way merge of file contents via ``git merge-file``.

        Writes the three versions to temporary files, runs
        ``git merge-file -p``, and returns the merged output.  Conflict
        markers are included when the merge is non-clean.

        Args:
            base: Common-ancestor file content.
            ours: Content from the first branch.
            theirs: Content from the second branch.

        Returns:
            Merged file content (may contain conflict markers).
        """
        tmp_base = tmp_ours = tmp_theirs = None
        try:
            tmp_base = tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".base",
                delete=False,
                encoding=self._encoding,
            )
            tmp_base.write(base)
            tmp_base.close()

            tmp_ours = tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".ours",
                delete=False,
                encoding=self._encoding,
            )
            tmp_ours.write(ours)
            tmp_ours.close()

            tmp_theirs = tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".theirs",
                delete=False,
                encoding=self._encoding,
            )
            tmp_theirs.write(theirs)
            tmp_theirs.close()

            result = self._git(
                "merge-file",
                "-p",
                tmp_ours.name,
                tmp_base.name,
                tmp_theirs.name,
                allowed_returncodes=(0, 1),
            )
            return result.stdout
        finally:
            for tmp in (tmp_base, tmp_ours, tmp_theirs):
                if tmp is not None:
                    # Tier 3: best-effort silent — temp file cleanup
                    try:
                        os.unlink(tmp.name)
                    except OSError:
                        pass

    # -- workspace / branch / commit operations --

    def workspace_add(
        self,
        path: str,
        *,
        branch: str | None = None,
        rev: str | None = None,
    ) -> str:
        """Create a new workspace via ``git worktree add``.

        Args:
            path: Directory for the new workspace.
            branch: If given, create this branch in the new workspace.
            rev: Starting commit-ish.

        Returns:
            Absolute path to the created workspace.
        """
        abs_path = os.path.abspath(path)
        cmd: list[str] = ["worktree", "add"]
        if branch:
            cmd.extend(["-b", branch])
        cmd.append(abs_path)
        if rev:
            cmd.append(rev)
        self._git(*cmd)
        return abs_path

    def workspace_remove(self, path: str, *, force: bool = False) -> None:
        """Remove a workspace via ``git worktree remove``.

        Args:
            path: Path to the workspace directory.
            force: Force removal even with uncommitted changes.
        """
        abs_path = os.path.abspath(path)
        cmd: list[str] = ["worktree", "remove"]
        if force:
            cmd.append("--force")
        cmd.append(abs_path)
        self._git(*cmd)

    def workspace_list(self) -> list[WorkspaceInfo]:
        """List all workspaces via ``git worktree list --porcelain``.

        Returns:
            List of :class:`WorkspaceInfo` entries.
        """
        result = self._git("worktree", "list", "--porcelain")
        workspaces: list[WorkspaceInfo] = []
        path = ""
        head = ""
        branch: str | None = None
        for line in result.stdout.splitlines():
            if line.startswith("worktree "):
                # Flush previous entry
                if path:
                    workspaces.append(
                        WorkspaceInfo(
                            path=path,
                            head=head,
                            branch=branch,
                            is_main=len(workspaces) == 0,
                        )
                    )
                path = line[9:]
                head = ""
                branch = None
            elif line.startswith("HEAD "):
                head = line[5:]
            elif line.startswith("branch "):
                branch = line[7:].removeprefix("refs/heads/")
            elif line == "detached":
                branch = None
        # Flush last entry
        if path:
            workspaces.append(
                WorkspaceInfo(
                    path=path,
                    head=head,
                    branch=branch,
                    is_main=len(workspaces) == 0,
                )
            )
        return workspaces

    def branches(self) -> list[str]:
        """List all branches via ``git branch``.

        Returns:
            List of branch name strings.
        """
        result = self._git("branch", "--format=%(refname:short)")
        return [b.strip() for b in result.stdout.splitlines() if b.strip()]

    def create_branch(self, name: str, *, rev: str | None = None) -> None:
        """Create a new branch via ``git branch``.

        Args:
            name: Branch name.
            rev: Starting commit-ish (defaults to HEAD).
        """
        cmd: list[str] = ["branch", name]
        if rev:
            cmd.append(rev)
        self._git(*cmd)

    def switch(self, target: str) -> None:
        """Switch to a branch or revision via ``git switch``.

        Falls back to ``git switch --detach`` for non-branch revisions.

        Args:
            target: Branch name or revision identifier.
        """
        try:
            self._git("switch", target)
        except CommandError:
            self._git("switch", "--detach", target)

    def commit(self, message: str, *, paths: list[str] | None = None) -> str:
        """Create a commit via ``git commit``.

        If *paths* is given, stages those files first.  Otherwise commits
        whatever is already staged.

        Args:
            message: Commit message.
            paths: Files to stage before committing.

        Returns:
            Full commit hash of the new commit.
        """
        if paths:
            self._git("add", "--", *paths)
        self._git("commit", "-m", message)
        result = self._git("rev-parse", "HEAD")
        return result.stdout.strip()

    def rev_parse(self, rev: str) -> str:
        """Resolve a revision string via ``git rev-parse``.

        Args:
            rev: Revision string.

        Returns:
            Full commit hash.
        """
        result = self._git("rev-parse", rev)
        return result.stdout.strip()


# ── Mercurial Backend ────────────────────────────────────────────────


class Mercurial:
    """Mercurial (``hg``) CLI backend.

    Args:
        repo_path: Path to the repository (defaults to ``"."``).
        binary: Explicit path to the ``hg`` binary; discovered
            automatically if ``None``.
        encoding: Text encoding for command I/O.
        timeout: Default subprocess timeout in seconds.
        merge_func: Three-way merge callable ``(base, ours, theirs) -> result``.
            Defaults to ``_UNSET`` (auto-discover sibling ``diff`` module).
            Pass ``None`` to disable ``merge_file()``, or a custom callable
            whose return value has a ``.content`` attribute (or is a plain
            ``str``).
    """

    def __init__(
        self,
        repo_path: str = ".",
        *,
        binary: str | None = None,
        encoding: str = "utf-8",
        timeout: float = 30.0,
        merge_func: Callable[[str, str, str], Any] | None | _Unset = _UNSET,
    ) -> None:
        self._binary = binary or _find_binary("hg")
        self._repo = os.path.abspath(repo_path)
        self._encoding = encoding
        self._timeout = timeout
        self._merge_func = merge_func

    def _hg(
        self,
        *args: str,
        allowed_returncodes: tuple[int, ...] = (0,),
        input: str | None = None,  # noqa: A002
    ) -> subprocess.CompletedProcess[str]:
        """Run a Mercurial sub-command inside the repository."""
        cmd = [self._binary, *args]
        return _run(
            cmd,
            cwd=self._repo,
            input=input,
            timeout=self._timeout,
            encoding=self._encoding,
            allowed_returncodes=allowed_returncodes,
        )

    @property
    def name(self) -> str:
        """Return ``"hg"``."""
        return "hg"

    def is_repo(self, path: str) -> bool:
        """Check whether *path* is inside a Mercurial repository.

        Args:
            path: Directory to test.

        Returns:
            ``True`` if *path* contains an ``.hg`` directory.
        """
        return os.path.isdir(os.path.join(path, ".hg"))

    def diff(self, *paths: str, staged: bool = False) -> str:
        """Return a unified diff of uncommitted changes.

        Args:
            *paths: Restrict diff to these paths.
            staged: Ignored — Mercurial has no staging area.

        Returns:
            Diff text.
        """
        cmd: list[str] = ["diff"]
        if paths:
            cmd.extend(paths)
        result = self._hg(*cmd)
        return result.stdout

    def diff_files(self, path_a: str, path_b: str) -> str:
        """Not supported by Mercurial CLI.

        Raises:
            NotImplementedError: Always.
        """
        raise NotImplementedError("hg does not support diffing arbitrary files")

    def apply(self, patch: str) -> None:
        """Apply a patch via ``hg import --no-commit``.

        Args:
            patch: Patch text.
        """
        self._hg("import", "--no-commit", "-", input=patch)

    def status(self) -> list[FileStatus]:
        """Return the list of changed files via ``hg status``.

        Returns:
            List of :class:`FileStatus` entries.
        """
        result = self._hg("status")
        entries: list[FileStatus] = []
        for line in result.stdout.splitlines():
            if len(line) < 3:
                continue
            status_char = line[0]
            path = line[2:]
            entries.append(FileStatus(path=path, status=status_char))
        return entries

    def log(self, n: int = 10) -> list[Commit]:
        """Return the last *n* commits.

        Args:
            n: Maximum number of commits.

        Returns:
            List of :class:`Commit` entries, newest first.
        """
        template = (
            "{node}\\n{short(node)}\\n{author|user}\\n"
            "{date|isodate}\\n{desc|firstline}\\n\\x00"
        )
        result = self._hg("log", "--template", template, "-l", str(n))
        commits: list[Commit] = []
        for block in result.stdout.split("\x00"):
            block = block.strip()
            if not block:
                continue
            lines = block.splitlines()
            if len(lines) < 5:
                continue
            commits.append(
                Commit(
                    hash=lines[0],
                    short_hash=lines[1],
                    author=lines[2],
                    date=lines[3],
                    message=lines[4],
                )
            )
        return commits

    def blame(self, path: str) -> list[BlameLine]:
        """Return per-line blame via ``hg annotate``.

        Args:
            path: File path relative to the repository root.

        Returns:
            List of :class:`BlameLine` entries.
        """
        result = self._hg("annotate", "-u", "-d", "-n", "-c", path)
        blame_lines: list[BlameLine] = []
        line_no = 0
        for raw in result.stdout.splitlines():
            line_no += 1
            # Format: <changeset> <user> <date> <lineno>: <content>
            m = re.match(
                r"^\s*([0-9a-f]+)\s+(.+?)\s+"
                r"(\S+ \S+(?: [+-]\d+)?)\s+(\d+):\s?(.*)",
                raw,
            )
            if m:
                blame_lines.append(
                    BlameLine(
                        commit=m.group(1),
                        author=m.group(2).strip(),
                        date=m.group(3),
                        line_no=int(m.group(4)),
                        content=m.group(5),
                    )
                )
        return blame_lines

    def current_branch(self) -> str:
        """Return the current Mercurial branch name.

        Returns:
            Branch name string.
        """
        result = self._hg("branch")
        return result.stdout.strip()

    def merge_file(self, base: str, ours: str, theirs: str) -> str:
        """Three-way merge using the sibling ``diff`` module.

        Uses an injected ``merge_func`` if provided at construction time,
        otherwise falls back to sibling ``diff.merge3`` auto-discovery.

        Args:
            base: Common-ancestor file content.
            ours: Content from the first branch.
            theirs: Content from the second branch.

        Returns:
            Merged file content (may contain conflict markers).

        Raises:
            NotImplementedError: If the sibling ``diff`` module is
                not available and no ``merge_func`` was injected,
                or if ``merge_func=None`` was passed explicitly.
        """
        merge3 = self._resolve_merge_func()
        result = merge3(base, ours, theirs)
        return result.content if hasattr(result, "content") else result

    def _resolve_merge_func(self) -> Callable[[str, str, str], Any]:
        """Return the merge callable, resolving sibling fallback if needed."""
        if isinstance(self._merge_func, _Unset):
            return _load_diff_merge3()
        if self._merge_func is None:
            raise NotImplementedError(
                "merge_file disabled: merge_func=None was passed explicitly"
            )
        return self._merge_func

    def workspace_add(
        self,
        path: str,
        *,
        branch: str | None = None,
        rev: str | None = None,
    ) -> str:
        """Not supported by Mercurial.

        Raises:
            NotImplementedError: Always.
        """
        raise NotImplementedError("hg does not support workspaces")

    def workspace_remove(self, path: str, *, force: bool = False) -> None:
        """Not supported by Mercurial.

        Raises:
            NotImplementedError: Always.
        """
        raise NotImplementedError("hg does not support workspaces")

    def workspace_list(self) -> list[WorkspaceInfo]:
        """Not supported by Mercurial.

        Raises:
            NotImplementedError: Always.
        """
        raise NotImplementedError("hg does not support workspaces")

    def branches(self) -> list[str]:
        """Not supported — Mercurial branches have different semantics.

        Raises:
            NotImplementedError: Always.
        """
        raise NotImplementedError("hg branches have different semantics; not supported")

    def create_branch(self, name: str, *, rev: str | None = None) -> None:
        """Not supported — Mercurial branches have different semantics.

        Raises:
            NotImplementedError: Always.
        """
        raise NotImplementedError("hg branches have different semantics; not supported")

    def switch(self, target: str) -> None:
        """Not supported by Mercurial.

        Raises:
            NotImplementedError: Always.
        """
        raise NotImplementedError("hg does not support switch")

    def commit(self, message: str, *, paths: list[str] | None = None) -> str:
        """Not supported by Mercurial.

        Raises:
            NotImplementedError: Always.
        """
        raise NotImplementedError("hg commit is not supported via this interface")

    def rev_parse(self, rev: str) -> str:
        """Not supported by Mercurial.

        Raises:
            NotImplementedError: Always.
        """
        raise NotImplementedError("hg does not support rev-parse via this interface")


# ── Jujutsu Backend ──────────────────────────────────────────────────


class Jujutsu:
    """Jujutsu (``jj``) CLI backend.

    Args:
        repo_path: Path to the repository (defaults to ``"."``).
        binary: Explicit path to the ``jj`` binary; discovered
            automatically if ``None``.
        encoding: Text encoding for command I/O.
        timeout: Default subprocess timeout in seconds.
        merge_func: Three-way merge callable ``(base, ours, theirs) -> result``.
            Defaults to ``_UNSET`` (auto-discover sibling ``diff`` module).
            Pass ``None`` to disable ``merge_file()``, or a custom callable
            whose return value has a ``.content`` attribute (or is a plain
            ``str``).
    """

    def __init__(
        self,
        repo_path: str = ".",
        *,
        binary: str | None = None,
        encoding: str = "utf-8",
        timeout: float = 30.0,
        merge_func: Callable[[str, str, str], Any] | None | _Unset = _UNSET,
    ) -> None:
        self._binary = binary or _find_binary("jj")
        self._repo = os.path.abspath(repo_path)
        self._encoding = encoding
        self._timeout = timeout
        self._merge_func = merge_func

    def _jj(
        self,
        *args: str,
        allowed_returncodes: tuple[int, ...] = (0,),
        input: str | None = None,  # noqa: A002
    ) -> subprocess.CompletedProcess[str]:
        """Run a Jujutsu sub-command inside the repository."""
        cmd = [self._binary, *args]
        return _run(
            cmd,
            cwd=self._repo,
            input=input,
            timeout=self._timeout,
            encoding=self._encoding,
            allowed_returncodes=allowed_returncodes,
        )

    @property
    def name(self) -> str:
        """Return ``"jj"``."""
        return "jj"

    def is_repo(self, path: str) -> bool:
        """Check whether *path* is inside a Jujutsu repository.

        Args:
            path: Directory to test.

        Returns:
            ``True`` if *path* contains a ``.jj`` directory.
        """
        return os.path.isdir(os.path.join(path, ".jj"))

    def diff(self, *paths: str, staged: bool = False) -> str:
        """Return a diff of uncommitted changes.

        Jujutsu has no staging area, so *staged* is ignored.

        Args:
            *paths: Restrict diff to these paths.
            staged: Ignored.

        Returns:
            Diff text.
        """
        cmd: list[str] = ["diff"]
        if paths:
            cmd.extend(paths)
        result = self._jj(*cmd)
        return result.stdout

    def diff_files(self, path_a: str, path_b: str) -> str:
        """Not supported by Jujutsu CLI.

        Raises:
            NotImplementedError: Always.
        """
        raise NotImplementedError("jj does not support diffing arbitrary files")

    def apply(self, patch: str) -> None:
        """Not supported by Jujutsu CLI.

        Raises:
            NotImplementedError: Always.
        """
        raise NotImplementedError("jj does not support applying patches via CLI")

    def status(self) -> list[FileStatus]:
        """Return the list of changed files via ``jj status``.

        Returns:
            List of :class:`FileStatus` entries.
        """
        result = self._jj("status")
        entries: list[FileStatus] = []
        # jj status output: "M path" / "A path" / "D path" / etc.
        for line in result.stdout.splitlines():
            m = re.match(r"^([MADR?!])\s+(.+)$", line)
            if m:
                entries.append(FileStatus(path=m.group(2), status=m.group(1)))
        return entries

    def log(self, n: int = 10) -> list[Commit]:
        """Return the last *n* commits.

        Args:
            n: Maximum number of commits.

        Returns:
            List of :class:`Commit` entries, newest first.
        """
        template = (
            'commit_id ++ "\\n" ++ '
            'commit_id.short() ++ "\\n" ++ '
            'if(author, author.name(), "") ++ "\\n" ++ '
            'if(author, author.timestamp(), "") ++ "\\n" ++ '
            'if(description, description.first_line(), "") ++ "\\n" ++ '
            '"\\x00"'
        )
        result = self._jj("log", "-n", str(n), "--no-graph", "-T", template)
        commits: list[Commit] = []
        for block in result.stdout.split("\x00"):
            block = block.strip()
            if not block:
                continue
            lines = block.splitlines()
            if len(lines) < 5:
                continue
            commits.append(
                Commit(
                    hash=lines[0],
                    short_hash=lines[1],
                    author=lines[2],
                    date=lines[3],
                    message=lines[4],
                )
            )
        return commits

    def blame(self, path: str) -> list[BlameLine]:
        """Return per-line annotation via ``jj file annotate``.

        Args:
            path: File path relative to the repository root.

        Returns:
            List of :class:`BlameLine` entries.
        """
        result = self._jj("file", "annotate", path)
        blame_lines: list[BlameLine] = []
        line_no = 0
        for raw in result.stdout.splitlines():
            line_no += 1
            # jj file annotate format: <change_id> <committer> <date> <line>
            m = re.match(r"^(\S+)\s+(\S+)\s+(\S+)\s?(.*)", raw)
            if m:
                blame_lines.append(
                    BlameLine(
                        commit=m.group(1),
                        author=m.group(2),
                        date=m.group(3),
                        line_no=line_no,
                        content=m.group(4),
                    )
                )
        return blame_lines

    def current_branch(self) -> str:
        """Return the current bookmark or change ID.

        Returns:
            First bookmark pointing to ``@``, or the change ID.
        """
        result = self._jj("bookmark", "list", "--pointing-to", "@")
        first = result.stdout.strip().splitlines()
        if first and first[0].strip():
            # Bookmark line format: "name: <change-id>"
            return first[0].split(":")[0].strip()
        # No bookmark — return change ID
        result = self._jj("log", "-r", "@", "--no-graph", "-T", "change_id.short()")
        return result.stdout.strip()

    def merge_file(self, base: str, ours: str, theirs: str) -> str:
        """Three-way merge using the sibling ``diff`` module.

        Uses an injected ``merge_func`` if provided at construction time,
        otherwise falls back to sibling ``diff.merge3`` auto-discovery.

        Args:
            base: Common-ancestor file content.
            ours: Content from the first branch.
            theirs: Content from the second branch.

        Returns:
            Merged file content (may contain conflict markers).

        Raises:
            NotImplementedError: If the sibling ``diff`` module is
                not available and no ``merge_func`` was injected,
                or if ``merge_func=None`` was passed explicitly.
        """
        merge3 = self._resolve_merge_func()
        result = merge3(base, ours, theirs)
        return result.content if hasattr(result, "content") else result

    def _resolve_merge_func(self) -> Callable[[str, str, str], Any]:
        """Return the merge callable, resolving sibling fallback if needed."""
        if isinstance(self._merge_func, _Unset):
            return _load_diff_merge3()
        if self._merge_func is None:
            raise NotImplementedError(
                "merge_file disabled: merge_func=None was passed explicitly"
            )
        return self._merge_func

    # -- workspace / bookmark / commit operations --

    def workspace_add(
        self,
        path: str,
        *,
        branch: str | None = None,
        rev: str | None = None,
    ) -> str:
        """Create a new workspace via ``jj workspace add``.

        The workspace name defaults to the basename of *path* (Jujutsu
        convention).  If *branch* is given, a bookmark is created in the
        new workspace pointing to its working-copy change.

        Args:
            path: Directory for the new workspace.
            branch: If given, create a bookmark in the new workspace.
            rev: Starting revision.

        Returns:
            Absolute path to the created workspace.
        """
        abs_path = os.path.abspath(path)
        cmd: list[str] = ["workspace", "add", abs_path]
        if rev:
            cmd.extend(["-r", rev])
        self._jj(*cmd)
        if branch:
            # Create a bookmark in the new workspace context
            _run(
                [self._binary, "bookmark", "create", branch],
                cwd=abs_path,
                timeout=self._timeout,
                encoding=self._encoding,
            )
        return abs_path

    def workspace_remove(self, path: str, *, force: bool = False) -> None:
        """Remove a workspace via ``jj workspace forget``.

        Derives the workspace name from the directory basename (Jujutsu
        default naming convention), then removes the directory.

        Args:
            path: Path to the workspace directory.
            force: Unused — ``jj workspace forget`` always succeeds for
                registered workspaces.
        """
        abs_path = os.path.abspath(path)
        ws_name = os.path.basename(abs_path)
        self._jj("workspace", "forget", ws_name)
        if os.path.isdir(abs_path):
            shutil.rmtree(abs_path)

    def workspace_list(self) -> list[WorkspaceInfo]:
        """List all workspaces via ``jj workspace list``.

        Only the default workspace has a known path (``repo_path``);
        other workspace paths are not exposed by ``jj workspace list``.

        Returns:
            List of :class:`WorkspaceInfo` entries.
        """
        result = self._jj("workspace", "list")
        workspaces: list[WorkspaceInfo] = []
        for line in result.stdout.splitlines():
            # Format: "name: change_id_short commit_id_short ..."
            m = re.match(r"^(\S+):\s+(\S+)\s+(\S+)", line)
            if m:
                ws_name = m.group(1)
                commit_short = m.group(3)
                path = self._repo if ws_name == "default" else ""
                workspaces.append(
                    WorkspaceInfo(
                        path=path,
                        head=commit_short,
                        branch=None,
                        is_main=ws_name == "default",
                    )
                )
        return workspaces

    def branches(self) -> list[str]:
        """List all bookmarks via ``jj bookmark list``.

        Returns:
            List of bookmark name strings.
        """
        result = self._jj("bookmark", "list")
        names: list[str] = []
        for line in result.stdout.splitlines():
            # Format: "name: change_id commit_id ..."
            m = re.match(r"^(\S+):", line)
            if m:
                names.append(m.group(1))
        return names

    def create_branch(self, name: str, *, rev: str | None = None) -> None:
        """Create a bookmark via ``jj bookmark create``.

        Args:
            name: Bookmark name.
            rev: Target revision (defaults to ``@``).
        """
        cmd: list[str] = ["bookmark", "create", name]
        if rev:
            cmd.extend(["-r", rev])
        self._jj(*cmd)

    def switch(self, target: str) -> None:
        """Switch working copy via ``jj new``.

        Creates a new change on top of *target*, analogous to how
        ``git switch`` positions the working copy for new commits.

        Args:
            target: Bookmark name or revision identifier.
        """
        self._jj("new", target)

    def commit(self, message: str, *, paths: list[str] | None = None) -> str:
        """Finalize the current change via ``jj commit``.

        The *paths* argument is ignored — Jujutsu auto-tracks all
        working-copy changes.

        Args:
            message: Change description.
            paths: Ignored.

        Returns:
            Full commit hash of the finalized change.
        """
        self._jj("commit", "-m", message)
        # The committed change is now @- (parent of current)
        result = self._jj("log", "-r", "@-", "--no-graph", "-T", "commit_id")
        return result.stdout.strip()

    def rev_parse(self, rev: str) -> str:
        """Resolve a revision string to a full commit hash.

        Args:
            rev: Revision string (bookmark, change ID, etc.).

        Returns:
            Full commit hash.
        """
        result = self._jj("log", "-r", rev, "--no-graph", "-T", "commit_id")
        return result.stdout.strip()


# ── Auto-Detection ───────────────────────────────────────────────────

_BACKENDS: list[tuple[str, str, type]] = [
    (".git", "git", Git),
    (".hg", "hg", Mercurial),
    (".jj", "jj", Jujutsu),
]


def detect(
    path: str = ".",
    *,
    merge_func: Callable[[str, str, str], Any] | None | _Unset = _UNSET,
) -> VCSBackend | None:
    """Auto-detect the VCS backend for the given path.

    Walks upward from *path* to the filesystem root looking for
    ``.git/``, ``.hg/``, or ``.jj/`` directories.  Returns the first
    backend whose marker directory is found **and** whose binary is
    available on the system, or ``None`` if no VCS is detected.

    Args:
        path: Starting directory (defaults to ``"."``).
        merge_func: Forwarded to ``Mercurial`` / ``Jujutsu`` constructors.
            See their docstrings for semantics.  Ignored for ``Git``
            (which uses ``git merge-file`` directly).

    Returns:
        An instantiated backend, or ``None``.
    """
    current = os.path.abspath(path)
    while True:
        for marker, binary_name, cls in _BACKENDS:
            marker_path = os.path.join(current, marker)
            if os.path.isdir(marker_path) or os.path.isfile(marker_path):
                try:
                    _find_binary(binary_name)
                except BinaryNotFoundError:
                    continue
                if cls is Git:
                    return cls(current)
                return cls(current, merge_func=merge_func)
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return None
