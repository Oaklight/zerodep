"""Correctness tests: zerodep vcs module."""

import os
import shutil
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from vcs import (
    BinaryNotFoundError,
    BlameLine,
    CommandError,
    Commit,
    FileStatus,
    Git,
    NotARepoError,
    VCSError,
    detect,
)

# ── Fixtures ─────────────────────────────────────────────────────────

HAS_GIT = shutil.which("git") is not None
HAS_HG = shutil.which("hg") is not None
HAS_JJ = shutil.which("jj") is not None

skip_no_git = pytest.mark.skipif(not HAS_GIT, reason="git not installed")
skip_no_hg = pytest.mark.skipif(not HAS_HG, reason="hg not installed")
skip_no_jj = pytest.mark.skipif(not HAS_JJ, reason="jj not installed")


_GIT_ENV = {
    **os.environ,
    "GIT_AUTHOR_NAME": "Test User",
    "GIT_AUTHOR_EMAIL": "test@test.com",
    "GIT_COMMITTER_NAME": "Test User",
    "GIT_COMMITTER_EMAIL": "test@test.com",
    "GIT_CONFIG_NOSYSTEM": "1",
    "HOME": "/dev/null",  # Prevent reading global config.
}


def _git(tmp_path, *args):
    """Run a git command in the temp repo with controlled env."""
    return subprocess.run(
        ["git", "-C", str(tmp_path), *args],
        check=True,
        capture_output=True,
        env={**_GIT_ENV, "HOME": str(tmp_path)},
    )


@pytest.fixture
def git_repo(tmp_path):
    """Create a temporary git repo with an initial commit."""
    subprocess.run(
        ["git", "init", str(tmp_path)],
        check=True,
        capture_output=True,
        env=_GIT_ENV,
    )
    _git(tmp_path, "config", "user.email", "test@test.com")
    _git(tmp_path, "config", "user.name", "Test User")
    f = tmp_path / "file.txt"
    f.write_text("line1\nline2\nline3\n")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "initial commit")
    return tmp_path


# ── TestDetect ───────────────────────────────────────────────────────


@skip_no_git
class TestDetect:
    def test_detect_git_repo(self, git_repo):
        backend = detect(str(git_repo))
        assert backend is not None
        assert backend.name == "git"

    def test_detect_subdirectory(self, git_repo):
        sub = git_repo / "subdir"
        sub.mkdir()
        backend = detect(str(sub))
        assert backend is not None
        assert backend.name == "git"

    def test_detect_non_repo(self, tmp_path):
        backend = detect(str(tmp_path))
        assert backend is None


# ── TestGitStatus ────────────────────────────────────────────────────


@skip_no_git
class TestGitStatus:
    def test_clean(self, git_repo):
        g = Git(str(git_repo))
        assert g.status() == []

    def test_modified_file(self, git_repo):
        (git_repo / "file.txt").write_text("modified\n")
        g = Git(str(git_repo))
        statuses = g.status()
        paths = [s.path for s in statuses]
        assert "file.txt" in paths
        modified = [s for s in statuses if s.path == "file.txt"][0]
        assert modified.status == "M"

    def test_untracked_file(self, git_repo):
        (git_repo / "new.txt").write_text("new\n")
        g = Git(str(git_repo))
        statuses = g.status()
        untracked = [s for s in statuses if s.path == "new.txt"]
        assert len(untracked) == 1
        assert untracked[0].status == "?"

    def test_added_file(self, git_repo):
        (git_repo / "added.txt").write_text("added\n")
        _git(git_repo, "add", "added.txt")
        g = Git(str(git_repo))
        statuses = g.status()
        added = [s for s in statuses if s.path == "added.txt"]
        assert len(added) == 1
        assert added[0].status == "A"

    def test_deleted_file(self, git_repo):
        (git_repo / "file.txt").unlink()
        g = Git(str(git_repo))
        statuses = g.status()
        deleted = [s for s in statuses if s.path == "file.txt"]
        assert len(deleted) == 1
        assert deleted[0].status == "D"


# ── TestGitDiff ──────────────────────────────────────────────────────


@skip_no_git
class TestGitDiff:
    def test_no_changes(self, git_repo):
        g = Git(str(git_repo))
        assert g.diff() == ""

    def test_unstaged_diff(self, git_repo):
        (git_repo / "file.txt").write_text("changed\n")
        g = Git(str(git_repo))
        d = g.diff()
        assert "-line1" in d
        assert "+changed" in d

    def test_staged_diff(self, git_repo):
        (git_repo / "file.txt").write_text("staged\n")
        _git(git_repo, "add", "file.txt")
        g = Git(str(git_repo))
        # Unstaged should be empty now.
        assert g.diff() == ""
        # Staged should show changes.
        d = g.diff(staged=True)
        assert "+staged" in d

    def test_diff_specific_path(self, git_repo):
        (git_repo / "file.txt").write_text("changed\n")
        (git_repo / "other.txt").write_text("other\n")
        g = Git(str(git_repo))
        d = g.diff("file.txt")
        assert "file.txt" in d
        assert "other" not in d

    def test_diff_files(self, git_repo):
        f1 = git_repo / "a.txt"
        f2 = git_repo / "b.txt"
        f1.write_text("hello\n")
        f2.write_text("world\n")
        g = Git(str(git_repo))
        d = g.diff_files(str(f1), str(f2))
        assert "-hello" in d
        assert "+world" in d


# ── TestGitLog ───────────────────────────────────────────────────────


@skip_no_git
class TestGitLog:
    def test_log_count(self, git_repo):
        g = Git(str(git_repo))
        commits = g.log(n=5)
        assert len(commits) == 1  # Only initial commit.

    def test_commit_fields(self, git_repo):
        g = Git(str(git_repo))
        commits = g.log(n=1)
        c = commits[0]
        assert isinstance(c, Commit)
        assert len(c.hash) == 40
        assert len(c.short_hash) > 0
        assert c.author == "Test User"
        assert c.message == "initial commit"
        assert "T" in c.date  # ISO 8601 format.

    def test_multiple_commits(self, git_repo):
        (git_repo / "file.txt").write_text("v2\n")
        _git(git_repo, "add", ".")
        _git(git_repo, "commit", "-m", "second commit")
        g = Git(str(git_repo))
        commits = g.log(n=5)
        assert len(commits) == 2
        assert commits[0].message == "second commit"
        assert commits[1].message == "initial commit"


# ── TestGitBlame ─────────────────────────────────────────────────────


@skip_no_git
class TestGitBlame:
    def test_blame_fields(self, git_repo):
        g = Git(str(git_repo))
        lines = g.blame("file.txt")
        assert len(lines) == 3
        for bl in lines:
            assert isinstance(bl, BlameLine)
            assert bl.author == "Test User"
        assert lines[0].line_no == 1
        assert "line1" in lines[0].content
        assert "line2" in lines[1].content
        assert "line3" in lines[2].content


# ── TestGitBranch ────────────────────────────────────────────────────


@skip_no_git
class TestGitBranch:
    def test_main_branch(self, git_repo):
        g = Git(str(git_repo))
        branch = g.current_branch()
        # Default branch could be "master" or "main".
        assert branch in ("master", "main")

    def test_new_branch(self, git_repo):
        _git(git_repo, "checkout", "-b", "feature")
        g = Git(str(git_repo))
        assert g.current_branch() == "feature"


# ── TestGitApply ─────────────────────────────────────────────────────


@skip_no_git
class TestGitApply:
    def test_apply_patch(self, git_repo):
        g = Git(str(git_repo))
        # Create a diff.
        (git_repo / "file.txt").write_text("patched\nline2\nline3\n")
        d = g.diff()
        # Restore original.
        _git(git_repo, "checkout", "file.txt")
        assert (git_repo / "file.txt").read_text() == "line1\nline2\nline3\n"
        # Apply the patch.
        g.apply(d)
        assert (git_repo / "file.txt").read_text() == "patched\nline2\nline3\n"


# ── TestGitMergeFile ─────────────────────────────────────────────────


@skip_no_git
class TestGitMergeFile:
    def test_clean_merge(self, git_repo):
        g = Git(str(git_repo))
        # Changes must be far enough apart to avoid adjacent-line conflict.
        base = "line1\nline2\nline3\nline4\nline5\n"
        ours = "line1\nmodified\nline3\nline4\nline5\n"
        theirs = "line1\nline2\nline3\nline4\nchanged\n"
        result = g.merge_file(base, ours, theirs)
        assert "modified" in result
        assert "changed" in result
        assert "<<<" not in result

    def test_conflict_merge(self, git_repo):
        g = Git(str(git_repo))
        base = "line1\nline2\nline3\n"
        ours = "line1\nours\nline3\n"
        theirs = "line1\ntheirs\nline3\n"
        result = g.merge_file(base, ours, theirs)
        assert "<<<<<<<" in result or "ours" in result


# ── TestExceptions ───────────────────────────────────────────────────


class TestExceptions:
    def test_binary_not_found_error(self):
        err = BinaryNotFoundError("nonexistent")
        assert err.binary_name == "nonexistent"
        assert "nonexistent" in str(err)

    def test_command_error(self):
        err = CommandError(["git", "bad"], 128, "fatal: error")
        assert err.returncode == 128
        assert err.stderr == "fatal: error"
        assert "128" in str(err)

    def test_not_a_repo_error(self):
        err = NotARepoError("/tmp/nowhere")
        assert err.path == "/tmp/nowhere"

    @skip_no_git
    def test_command_error_raised(self, git_repo):
        g = Git(str(git_repo))
        with pytest.raises(CommandError):
            g._git("nonexistent-subcommand")

    def test_vcs_error_hierarchy(self):
        assert issubclass(BinaryNotFoundError, VCSError)
        assert issubclass(CommandError, VCSError)
        assert issubclass(NotARepoError, VCSError)


# ── TestDataStructures ───────────────────────────────────────────────


class TestDataStructures:
    def test_file_status_frozen(self):
        fs = FileStatus(path="test.py", status="M")
        with pytest.raises(AttributeError):
            fs.path = "other.py"  # ty: ignore[invalid-assignment]

    def test_commit_frozen(self):
        c = Commit(
            hash="abc123",
            short_hash="abc",
            author="Test",
            date="2026-01-01",
            message="msg",
        )
        with pytest.raises(AttributeError):
            c.message = "changed"  # ty: ignore[invalid-assignment]

    def test_blame_line_frozen(self):
        bl = BlameLine(
            commit="abc123",
            author="Test",
            date="2026-01-01",
            line_no=1,
            content="hello\n",
        )
        with pytest.raises(AttributeError):
            bl.content = "changed"  # ty: ignore[invalid-assignment]
