"""Tests for VCS merge_func injection API."""

from __future__ import annotations

import dataclasses
import unittest


@dataclasses.dataclass
class _FakeMergeResult:
    content: str


def _fake_merge3(base: str, ours: str, theirs: str) -> _FakeMergeResult:
    """Trivial merge that concatenates inputs."""
    return _FakeMergeResult(content=f"{base}|{ours}|{theirs}")


def _raw_merge(base: str, ours: str, theirs: str) -> str:
    """Merge func that returns a plain string (no .content)."""
    return f"{base}+{ours}+{theirs}"


class TestMercurialMergeInjection(unittest.TestCase):
    """Test merge_func injection on Mercurial backend."""

    def _make_hg(self, **kwargs):
        # Mercurial.__init__ calls _find_binary("hg") which may raise
        # if hg is not installed. We patch it to avoid that.
        from unittest.mock import patch

        with patch("vcs._find_binary", return_value="/usr/bin/hg"):
            from vcs import Mercurial

            return Mercurial("/tmp", **kwargs)

    def test_custom_merge_func_with_content_attr(self):
        hg = self._make_hg(merge_func=_fake_merge3)
        result = hg.merge_file("base", "ours", "theirs")
        self.assertEqual(result, "base|ours|theirs")

    def test_custom_merge_func_returns_plain_string(self):
        hg = self._make_hg(merge_func=_raw_merge)
        result = hg.merge_file("a", "b", "c")
        self.assertEqual(result, "a+b+c")

    def test_merge_func_none_raises(self):
        hg = self._make_hg(merge_func=None)
        with self.assertRaises(NotImplementedError) as ctx:
            hg.merge_file("a", "b", "c")
        self.assertIn("merge_func=None", str(ctx.exception))

    def test_default_uses_sibling_fallback(self):
        """When merge_func is _UNSET, _load_diff_merge3 is called."""
        from unittest.mock import patch

        mock_merge = _fake_merge3
        with patch("vcs._find_binary", return_value="/usr/bin/hg"):
            from vcs import Mercurial

            hg = Mercurial("/tmp")
        with patch("vcs._load_diff_merge3", return_value=mock_merge):
            result = hg.merge_file("x", "y", "z")
        self.assertEqual(result, "x|y|z")


class TestJujutsuMergeInjection(unittest.TestCase):
    """Test merge_func injection on Jujutsu backend."""

    def _make_jj(self, **kwargs):
        from unittest.mock import patch

        with patch("vcs._find_binary", return_value="/usr/bin/jj"):
            from vcs import Jujutsu

            return Jujutsu("/tmp", **kwargs)

    def test_custom_merge_func(self):
        jj = self._make_jj(merge_func=_fake_merge3)
        result = jj.merge_file("base", "ours", "theirs")
        self.assertEqual(result, "base|ours|theirs")

    def test_merge_func_none_raises(self):
        jj = self._make_jj(merge_func=None)
        with self.assertRaises(NotImplementedError):
            jj.merge_file("a", "b", "c")


class TestDetectMergeForward(unittest.TestCase):
    """Test that detect() forwards merge_func to backends."""

    def test_detect_forwards_merge_func_to_hg(self):
        import os
        import tempfile
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, ".hg"))
            with patch("vcs._find_binary", return_value="/usr/bin/hg"):
                from vcs import detect

                repo = detect(tmp, merge_func=_fake_merge3)
            self.assertIsNotNone(repo)
            self.assertEqual(repo._merge_func, _fake_merge3)  # type: ignore[union-attr]


if __name__ == "__main__":
    unittest.main()
