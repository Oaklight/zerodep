"""Correctness tests: zerodep jsonx (JSONC + JSONL) vs commentjson."""

import io
import json
import os
import sys

import pytest

# ── Import commentjson for comparison ──

try:
    import commentjson as _cj
except ImportError:
    pytest.skip("commentjson not installed", allow_module_level=True)

# Import our implementation
sys.path.insert(0, os.path.dirname(__file__))
from jsonx import (  # noqa: E402
    JSONCDecodeError,
    dump,
    dump_lines,
    dumps,
    dumps_lines,
    load,
    load_lines,
    loads,
    loads_lines,
)

# ── Helpers ──


def assert_same(jsonc_text: str) -> None:
    """Assert that our loads and commentjson.loads produce the same result."""
    ours = loads(jsonc_text)
    theirs = _cj.loads(jsonc_text)
    assert ours == theirs, f"Mismatch:\n  ours:   {ours!r}\n  theirs: {theirs!r}"


# ── Test: basic JSON (no comments) ──


class TestBasicJSON:
    @pytest.mark.parametrize(
        "text,expected",
        [
            ('{"a": 1}', {"a": 1}),
            ("[1, 2, 3]", [1, 2, 3]),
            ('"hello"', "hello"),
            ("42", 42),
            ("3.14", 3.14),
            ("true", True),
            ("false", False),
            ("null", None),
        ],
        ids=[
            "object",
            "array",
            "string",
            "int",
            "float",
            "true",
            "false",
            "null",
        ],
    )
    def test_basic_types(self, text: str, expected: object) -> None:
        assert loads(text) == expected

    def test_nested(self) -> None:
        text = '{"a": {"b": [1, 2, {"c": true}]}}'
        assert_same(text)

    def test_empty_object(self) -> None:
        assert loads("{}") == {}

    def test_empty_array(self) -> None:
        assert loads("[]") == []


# ── Test: single-line // comments ──


class TestSingleLineComments:
    def test_comment_at_end_of_line(self) -> None:
        text = '{"a": 1, // this is a comment\n"b": 2}'
        assert_same(text)

    def test_comment_on_own_line(self) -> None:
        text = '{\n// comment line\n"a": 1\n}'
        assert_same(text)

    def test_multiple_comments(self) -> None:
        text = """{
// first comment
"a": 1, // inline
// another comment
"b": 2
}"""
        assert_same(text)

    def test_comment_after_value(self) -> None:
        text = '{"key": "value" // comment\n}'
        assert_same(text)

    def test_double_slash_in_string_preserved(self) -> None:
        text = '{"url": "https://example.com"}'
        assert loads(text) == {"url": "https://example.com"}


# ── Test: hash # comments ──


class TestHashComments:
    def test_hash_comment_at_end(self) -> None:
        text = '{"a": 1 # comment\n}'
        assert_same(text)

    def test_hash_comment_on_own_line(self) -> None:
        text = '{\n# comment\n"a": 1\n}'
        assert_same(text)

    def test_hash_in_string_preserved(self) -> None:
        text = '{"color": "#ff0000"}'
        assert loads(text) == {"color": "#ff0000"}


# ── Test: block /* */ comments ──


class TestBlockComments:
    def test_inline_block_comment(self) -> None:
        text = '{"a": /* comment */ 1}'
        assert loads(text) == {"a": 1}

    def test_multiline_block_comment(self) -> None:
        text = """{
/* this is
   a multiline
   comment */
"a": 1
}"""
        assert loads(text) == {"a": 1}

    def test_block_comment_between_entries(self) -> None:
        text = '{"a": 1, /* comment */ "b": 2}'
        assert loads(text) == {"a": 1, "b": 2}

    def test_block_comment_in_array(self) -> None:
        text = "[1, /* skip */ 2, 3]"
        assert loads(text) == [1, 2, 3]


# ── Test: trailing commas ──


class TestTrailingCommas:
    def test_trailing_comma_in_object(self) -> None:
        text = '{"a": 1, "b": 2,}'
        assert_same(text)

    def test_trailing_comma_in_array(self) -> None:
        text = "[1, 2, 3,]"
        assert_same(text)

    def test_nested_trailing_commas(self) -> None:
        text = '{"a": [1, 2,], "b": {"c": 3,},}'
        assert_same(text)

    def test_trailing_comma_with_whitespace(self) -> None:
        text = '{"a": 1 ,  }'
        assert_same(text)

    def test_trailing_comma_with_newline(self) -> None:
        text = '{\n"a": 1,\n}'
        assert_same(text)


# ── Test: comments + trailing commas combined ──


class TestCombined:
    def test_comment_and_trailing_comma(self) -> None:
        text = """{
"a": 1, // first
"b": 2, // second
}"""
        assert loads(text) == {"a": 1, "b": 2}

    def test_full_config_style(self) -> None:
        text = """{
// Database config
"host": "localhost",
"port": 5432,
"options": {
    "ssl": true,
    "timeout": 30, // seconds
},
}"""
        expected = {
            "host": "localhost",
            "port": 5432,
            "options": {"ssl": True, "timeout": 30},
        }
        assert loads(text) == expected

    def test_hash_comment_and_trailing_comma(self) -> None:
        text = """{
# comment
"a": [1, 2, 3,],
}"""
        assert loads(text) == {"a": [1, 2, 3]}


# ── Test: string edge cases ──


class TestStringEdgeCases:
    def test_escaped_quote_in_string(self) -> None:
        text = r'{"key": "value with \"quote\""}'
        assert_same(text)

    def test_backslash_in_string(self) -> None:
        text = r'{"path": "C:\\Users\\test"}'
        assert_same(text)

    def test_comment_like_content_in_string(self) -> None:
        text = '{"code": "x // not a comment", "more": "/* also not */"}'
        expected = {"code": "x // not a comment", "more": "/* also not */"}
        assert loads(text) == expected

    def test_url_with_double_slash(self) -> None:
        text = '{"url": "http://example.com/path"}'
        assert loads(text) == {"url": "http://example.com/path"}

    def test_unicode_in_string(self) -> None:
        text = '{"emoji": "\\u2764", "cn": "\\u4f60\\u597d"}'
        assert_same(text)

    def test_newline_in_string(self) -> None:
        text = '{"line": "a\\nb"}'
        assert loads(text) == {"line": "a\nb"}


# ── Test: load from file ──


class TestLoad:
    def test_load_from_stream(self) -> None:
        text = '{"a": 1, // comment\n"b": 2}'
        fp = io.StringIO(text)
        assert load(fp) == {"a": 1, "b": 2}

    def test_load_from_file(self, tmp_path: object) -> None:
        import pathlib

        p = pathlib.Path(str(tmp_path)) / "test.jsonc"
        p.write_text('{\n// config\n"key": "value",\n}')
        with open(p) as f:
            result = load(f)
        assert result == {"key": "value"}


# ── Test: dump/dumps (pass-through) ──


class TestDump:
    def test_dumps_basic(self) -> None:
        data = {"a": 1, "b": [2, 3]}
        assert dumps(data) == json.dumps(data)

    def test_dumps_with_indent(self) -> None:
        data = {"a": 1}
        assert dumps(data, indent=2) == json.dumps(data, indent=2)

    def test_dumps_sort_keys(self) -> None:
        data = {"b": 2, "a": 1}
        assert dumps(data, sort_keys=True) == json.dumps(data, sort_keys=True)

    def test_dump_to_stream(self) -> None:
        data = {"a": 1}
        ours = io.StringIO()
        theirs = io.StringIO()
        dump(data, ours)
        json.dump(data, theirs)
        assert ours.getvalue() == theirs.getvalue()


# ── Test: error handling ──


class TestErrors:
    def test_invalid_json_raises(self) -> None:
        with pytest.raises(JSONCDecodeError):
            loads("{invalid}")

    def test_unclosed_string_raises(self) -> None:
        with pytest.raises(JSONCDecodeError):
            loads('{"key": "unclosed}')

    def test_error_is_json_decode_error(self) -> None:
        with pytest.raises(json.JSONDecodeError):
            loads("{bad}")


# ── Test: edge cases ──


class TestEdgeCases:
    def test_empty_with_comments(self) -> None:
        text = "// just a comment\n{}"
        assert loads(text) == {}

    def test_only_whitespace_around_value(self) -> None:
        text = "  \n  42  \n  "
        assert loads(text) == 42

    def test_deeply_nested(self) -> None:
        text = '{"a": {"b": {"c": {"d": [1, 2, 3,],},},},}'
        expected = {"a": {"b": {"c": {"d": [1, 2, 3]}}}}
        assert loads(text) == expected

    def test_large_array_with_comments(self) -> None:
        items = [f"  {i}, // item {i}" for i in range(100)]
        text = "[\n" + "\n".join(items) + "\n]"
        assert loads(text) == list(range(100))

    def test_comment_at_very_end(self) -> None:
        text = '{"a": 1}\n// trailing comment'
        assert loads(text) == {"a": 1}

    def test_block_comment_at_start(self) -> None:
        text = '/* header comment */\n{"a": 1}'
        assert loads(text) == {"a": 1}

    def test_consecutive_block_comments(self) -> None:
        text = '{"a": /* c1 */ /* c2 */ 1}'
        assert loads(text) == {"a": 1}


# ── Test: JSONL (JSON Lines) ──


class TestLoadsLines:
    def test_basic_multiline(self) -> None:
        text = '{"a":1}\n{"b":2}\n{"c":3}'
        assert loads_lines(text) == [{"a": 1}, {"b": 2}, {"c": 3}]

    def test_empty_lines_skipped(self) -> None:
        text = '{"a":1}\n\n\n{"b":2}'
        assert loads_lines(text) == [{"a": 1}, {"b": 2}]

    def test_comment_lines_skipped(self) -> None:
        text = '// header\n{"a":1}\n# comment\n{"b":2}\n// footer'
        assert loads_lines(text) == [{"a": 1}, {"b": 2}]

    def test_inline_comments_stripped(self) -> None:
        text = '{"a":1} // first\n{"b":2} # second'
        assert loads_lines(text) == [{"a": 1}, {"b": 2}]

    def test_mixed_types(self) -> None:
        text = '42\n"hello"\n[1,2,3]\ntrue\nnull'
        assert loads_lines(text) == [42, "hello", [1, 2, 3], True, None]

    def test_trailing_commas_per_line(self) -> None:
        text = '{"a":1,}\n{"b":[2,3,],}'
        assert loads_lines(text) == [{"a": 1}, {"b": [2, 3]}]

    def test_empty_input(self) -> None:
        assert loads_lines("") == []

    def test_only_comments(self) -> None:
        assert loads_lines("// a\n# b\n") == []

    def test_single_line(self) -> None:
        assert loads_lines('{"x":99}') == [{"x": 99}]

    def test_whitespace_only_lines(self) -> None:
        text = '  \n{"a":1}\n   \n{"b":2}\n  '
        assert loads_lines(text) == [{"a": 1}, {"b": 2}]

    def test_error_on_bad_line(self) -> None:
        text = '{"a":1}\n{bad}\n{"c":3}'
        with pytest.raises(JSONCDecodeError):
            loads_lines(text)


class TestLoadLines:
    def test_from_stream(self) -> None:
        text = '{"a":1}\n{"b":2}'
        fp = io.StringIO(text)
        assert load_lines(fp) == [{"a": 1}, {"b": 2}]

    def test_from_file(self, tmp_path: object) -> None:
        import pathlib

        p = pathlib.Path(str(tmp_path)) / "data.jsonl"
        p.write_text('{"x":1}\n{"y":2}\n')
        with open(p) as f:
            assert load_lines(f) == [{"x": 1}, {"y": 2}]


class TestDumpsLines:
    def test_basic(self) -> None:
        objs = [{"a": 1}, {"b": 2}]
        result = dumps_lines(objs)
        assert result == '{"a": 1}\n{"b": 2}'

    def test_roundtrip(self) -> None:
        original = [{"id": i, "val": i * 2} for i in range(5)]
        text = dumps_lines(original)
        recovered = loads_lines(text)
        assert recovered == original

    def test_empty_list(self) -> None:
        assert dumps_lines([]) == ""

    def test_single_item(self) -> None:
        assert dumps_lines([42]) == "42"

    def test_sort_keys(self) -> None:
        result = dumps_lines([{"b": 2, "a": 1}], sort_keys=True)
        assert result == '{"a": 1, "b": 2}'


class TestDumpLines:
    def test_to_stream(self) -> None:
        objs = [{"a": 1}, {"b": 2}]
        fp = io.StringIO()
        dump_lines(objs, fp)
        assert fp.getvalue() == '{"a": 1}\n{"b": 2}\n'

    def test_roundtrip_file(self, tmp_path: object) -> None:
        import pathlib

        p = pathlib.Path(str(tmp_path)) / "out.jsonl"
        original = [{"x": 1}, {"y": 2}, {"z": 3}]
        with open(p, "w") as f:
            dump_lines(original, f)
        with open(p) as f:
            recovered = load_lines(f)
        assert recovered == original
