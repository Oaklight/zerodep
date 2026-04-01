"""Correctness tests: zerodep filelock."""

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))


from filelock import FileLock


class TestBasicLocking:
    """Basic lock/unlock semantics."""

    def test_lock_creates_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = Path(tmpdir) / ".lock"
            lock = FileLock(lock_path)
            lock.lock()
            assert lock_path.exists()
            lock.unlock()
            lock.close()

    def test_context_manager(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = Path(tmpdir) / ".lock"
            lock = FileLock(lock_path)
            with lock:
                assert lock_path.exists()
            lock.close()

    def test_try_lock_succeeds_when_free(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = Path(tmpdir) / ".lock"
            lock = FileLock(lock_path)
            assert lock.try_lock() is True
            lock.unlock()
            lock.close()

    def test_path_property(self):
        p = Path("/tmp/.test.lock")
        lock = FileLock(p)
        assert lock.path == p

    def test_accepts_str_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = os.path.join(tmpdir, ".lock")
            lock = FileLock(lock_path)
            lock.lock()
            assert Path(lock_path).exists()
            lock.unlock()
            lock.close()


class TestContention:
    """Two FileLock instances competing for the same file."""

    def test_try_lock_fails_when_held(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = Path(tmpdir) / ".lock"
            holder_fd = os.open(str(lock_path), os.O_RDWR | os.O_CREAT, 0o644)

            if sys.platform == "win32":
                import msvcrt

                os.write(holder_fd, b"\x00")
                os.lseek(holder_fd, 0, os.SEEK_SET)
                msvcrt.locking(holder_fd, msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(holder_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)

            try:
                lock = FileLock(lock_path)
                assert lock.try_lock() is False
                lock.close()
            finally:
                if sys.platform == "win32":
                    os.lseek(holder_fd, 0, os.SEEK_SET)
                    msvcrt.locking(holder_fd, msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(holder_fd, fcntl.LOCK_UN)
                os.close(holder_fd)

    def test_unlock_releases_for_others(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = Path(tmpdir) / ".lock"
            lock_a = FileLock(lock_path)
            lock_b = FileLock(lock_path)

            lock_a.lock()
            assert lock_b.try_lock() is False

            lock_a.unlock()
            assert lock_b.try_lock() is True

            lock_b.unlock()
            lock_a.close()
            lock_b.close()

    def test_close_releases_lock(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = Path(tmpdir) / ".lock"
            lock_a = FileLock(lock_path)
            lock_b = FileLock(lock_path)

            lock_a.lock()
            assert lock_b.try_lock() is False

            lock_a.close()
            assert lock_b.try_lock() is True

            lock_b.unlock()
            lock_b.close()


class TestEdgeCases:
    """Edge-case and safety tests."""

    def test_creates_parent_directories(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = Path(tmpdir) / "sub" / "dir" / ".lock"
            lock = FileLock(lock_path)
            lock.lock()
            assert lock_path.exists()
            lock.unlock()
            lock.close()

    def test_double_close_is_safe(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = Path(tmpdir) / ".lock"
            lock = FileLock(lock_path)
            lock.lock()
            lock.close()
            lock.close()  # should not raise

    def test_unlock_without_lock_is_safe(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = Path(tmpdir) / ".lock"
            lock = FileLock(lock_path)
            lock.unlock()  # no fd yet, should not raise

    def test_reacquire_after_unlock(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = Path(tmpdir) / ".lock"
            lock = FileLock(lock_path)
            lock.lock()
            lock.unlock()
            lock.lock()  # re-acquire same lock
            lock.unlock()
            lock.close()

    def test_reacquire_after_close(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = Path(tmpdir) / ".lock"
            lock = FileLock(lock_path)
            lock.lock()
            lock.close()
            lock.lock()  # re-open fd and acquire
            lock.unlock()
            lock.close()
