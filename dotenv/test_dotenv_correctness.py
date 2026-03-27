"""Correctness tests: zerodep dotenv vs python-dotenv."""

import io
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import dotenv_values, find_dotenv, get_key, load_dotenv, set_key, unset_key

ref_dotenv = pytest.importorskip("dotenv", reason="python-dotenv not installed")


# ── Helpers ──


def _ours(content: str) -> dict[str, str | None]:
    return dotenv_values(stream=io.StringIO(content))


def _theirs(content: str) -> dict[str, str | None]:
    return ref_dotenv.dotenv_values(stream=io.StringIO(content))


# ── Test vectors ──

SIMPLE_CASES = [
    pytest.param("KEY=value", id="simple"),
    pytest.param("KEY=", id="empty_value"),
    pytest.param("KEY=value with spaces", id="spaces_in_value"),
    pytest.param("KEY=123", id="numeric_value"),
    pytest.param("  KEY=value  ", id="surrounding_whitespace"),
    pytest.param("KEY = value", id="spaces_around_equals"),
    pytest.param("MY_VAR=hello", id="underscore_key"),
    pytest.param("_PRIVATE=secret", id="leading_underscore"),
]

QUOTED_CASES = [
    pytest.param("KEY='single quoted'", id="single_quoted"),
    pytest.param('KEY="double quoted"', id="double_quoted"),
    pytest.param("KEY='has spaces'", id="single_quoted_spaces"),
    pytest.param('KEY="has spaces"', id="double_quoted_spaces"),
    pytest.param(r'KEY="escaped \"quote\""', id="escaped_quotes"),
    pytest.param(r'KEY="line\nbreak"', id="escaped_newline"),
    pytest.param(r'KEY="tab\there"', id="escaped_tab"),
    pytest.param(r'KEY="back\\slash"', id="escaped_backslash"),
    pytest.param("KEY='no $interpolation'", id="single_no_interpolation"),
    pytest.param("KEY=''", id="empty_single_quoted"),
    pytest.param('KEY=""', id="empty_double_quoted"),
]

COMMENT_CASES = [
    pytest.param("# this is a comment\nKEY=value", id="comment_line"),
    pytest.param("KEY=value # inline comment", id="inline_comment"),
    pytest.param("KEY='value # not a comment'", id="hash_in_single_quotes"),
    pytest.param('KEY="value # not a comment"', id="hash_in_double_quotes"),
    pytest.param("# comment only", id="comment_only"),
    pytest.param("", id="empty"),
    pytest.param("\n\n\n", id="blank_lines"),
]

EXPORT_CASES = [
    pytest.param("export KEY=value", id="export_simple"),
    pytest.param("export KEY='quoted'", id="export_single_quoted"),
    pytest.param('export KEY="quoted"', id="export_double_quoted"),
    pytest.param("export  KEY=value", id="export_extra_space"),
]

MULTILINE_CASES = [
    pytest.param('KEY="line1\nline2"', id="escaped_newlines"),
    pytest.param('KEY="line1\nline2\nline3"', id="three_lines_escaped"),
]

INTERPOLATION_CASES = [
    pytest.param("BASE=/app\nPATH=$BASE/bin", id="simple_dollar"),
    pytest.param("BASE=/app\nPATH=${BASE}/bin", id="braced"),
    pytest.param("A=1\nB=2\nC=$A-$B", id="multiple_refs"),
    pytest.param("KEY=$MISSING", id="missing_var"),
    pytest.param("KEY=${MISSING:-default}", id="default_value"),
]

MULTI_ENTRY_CASES = [
    pytest.param("A=1\nB=2\nC=3", id="three_entries"),
    pytest.param("A=1\n\nB=2\n# comment\nC=3", id="mixed_with_comments"),
    pytest.param("A=first\nA=second", id="duplicate_keys"),
]


# ── Test classes ──


class TestSimpleParsing:
    @pytest.mark.parametrize("content", SIMPLE_CASES)
    def test_matches_reference(self, content: str):
        assert _ours(content) == _theirs(content)


class TestQuotedValues:
    @pytest.mark.parametrize("content", QUOTED_CASES)
    def test_matches_reference(self, content: str):
        assert _ours(content) == _theirs(content)


class TestComments:
    @pytest.mark.parametrize("content", COMMENT_CASES)
    def test_matches_reference(self, content: str):
        assert _ours(content) == _theirs(content)


class TestExportPrefix:
    @pytest.mark.parametrize("content", EXPORT_CASES)
    def test_matches_reference(self, content: str):
        assert _ours(content) == _theirs(content)


class TestMultilineValues:
    @pytest.mark.parametrize("content", MULTILINE_CASES)
    def test_matches_reference(self, content: str):
        assert _ours(content) == _theirs(content)


class TestInterpolation:
    @pytest.mark.parametrize("content", INTERPOLATION_CASES)
    def test_matches_reference(self, content: str):
        assert _ours(content) == _theirs(content)


class TestMultiEntry:
    @pytest.mark.parametrize("content", MULTI_ENTRY_CASES)
    def test_matches_reference(self, content: str):
        assert _ours(content) == _theirs(content)


class TestLoadDotenv:
    def test_sets_environ(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("ZERODEP_TEST_KEY=hello\n")
        load_dotenv(env_file)
        assert os.environ.get("ZERODEP_TEST_KEY") == "hello"
        os.environ.pop("ZERODEP_TEST_KEY", None)

    def test_no_override_by_default(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("ZERODEP_TEST_OVR=new\n")
        os.environ["ZERODEP_TEST_OVR"] = "old"
        load_dotenv(env_file, override=False)
        assert os.environ["ZERODEP_TEST_OVR"] == "old"
        os.environ.pop("ZERODEP_TEST_OVR", None)

    def test_override_true(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("ZERODEP_TEST_OVR2=new\n")
        os.environ["ZERODEP_TEST_OVR2"] = "old"
        load_dotenv(env_file, override=True)
        assert os.environ["ZERODEP_TEST_OVR2"] == "new"
        os.environ.pop("ZERODEP_TEST_OVR2", None)

    def test_missing_file_returns_false(self, tmp_path):
        assert load_dotenv(tmp_path / "nonexistent") is False


class TestDotenvValues:
    def test_returns_dict(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("A=1\nB=2\n")
        result = dotenv_values(env_file)
        assert result == {"A": "1", "B": "2"}

    def test_does_not_modify_environ(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("ZERODEP_NOTOUCH=val\n")
        dotenv_values(env_file)
        assert "ZERODEP_NOTOUCH" not in os.environ


class TestFindDotenv:
    def test_finds_in_current_dir(self, tmp_path, monkeypatch):
        env_file = tmp_path / ".env"
        env_file.write_text("K=V\n")
        monkeypatch.chdir(tmp_path)
        result = find_dotenv(usecwd=True)
        assert result == str(env_file)

    def test_not_found_returns_empty(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = find_dotenv(filename=".env.nonexistent", usecwd=True)
        assert result == ""

    def test_raise_error(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        with pytest.raises(IOError):
            find_dotenv(
                filename=".env.nonexistent",
                raise_error_if_not_found=True,
                usecwd=True,
            )


class TestSetUnsetKey:
    def test_set_key_creates_file(self, tmp_path):
        env_file = tmp_path / ".env"
        ok, key, val = set_key(env_file, "NEW_KEY", "new_value")
        assert ok
        assert env_file.read_text().strip() == 'NEW_KEY="new_value"'

    def test_set_key_updates_existing(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("A=old\nB=keep\n")
        set_key(env_file, "A", "new")
        content = env_file.read_text()
        assert 'A="new"' in content
        assert "B=keep" in content

    def test_unset_key_removes(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("A=1\nB=2\nC=3\n")
        ok, key = unset_key(env_file, "B")
        assert ok
        content = env_file.read_text()
        assert "A=1" in content
        assert "B=" not in content
        assert "C=3" in content

    def test_get_key(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("FOO=bar\nBAZ=qux\n")
        assert get_key(env_file, "FOO") == "bar"
        assert get_key(env_file, "BAZ") == "qux"
        assert get_key(env_file, "MISSING") is None


class TestEdgeCases:
    def test_utf8_bom(self):
        content = "\ufeffKEY=value"
        assert _ours(content) == {"KEY": "value"}

    def test_windows_line_endings(self):
        content = "A=1\r\nB=2\r\n"
        assert _ours(content) == _theirs(content)

    def test_no_trailing_newline(self):
        content = "KEY=value"
        assert _ours(content) == _theirs(content)
