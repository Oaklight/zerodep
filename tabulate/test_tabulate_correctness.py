"""Correctness tests: zerodep tabulate vs reference tabulate."""

import os
import sys

import pytest

# Our tabulate.py shadows the reference 'tabulate' package.
# Import the reference library first via path manipulation.
_this_dir = os.path.dirname(__file__)

_saved_path = sys.path[:]
sys.path = [
    p
    for p in sys.path
    if os.path.abspath(p)
    not in (
        os.path.abspath(_this_dir),
        os.path.abspath(os.path.join(_this_dir, "..")),
    )
]

_cached_tabulate = sys.modules.pop("tabulate", None)

try:
    import tabulate as _ref_tabulate_mod

    if not hasattr(_ref_tabulate_mod, "tabulate"):
        raise ImportError("Not the real tabulate")
    _ref_tabulate = _ref_tabulate_mod.tabulate
except ImportError:
    pytest.skip("tabulate not installed", allow_module_level=True)
finally:
    sys.path = _saved_path
    sys.modules.pop("tabulate", None)
    if _cached_tabulate is not None:
        sys.modules["tabulate"] = _cached_tabulate

sys.path.insert(0, _this_dir)
from tabulate import tabulate as our_tabulate  # noqa: E402

# ── Helpers ──


def _ref(data, **kwargs):
    return _ref_tabulate(data, **kwargs)


def _ours(data, **kwargs):
    return our_tabulate(data, **kwargs)


# ── Plain format ──


class TestPlainFormat:
    def test_list_of_lists(self):
        data = [["Alice", 24], ["Bob", 30]]
        assert _ours(data, tablefmt="plain") == _ref(data, tablefmt="plain")

    def test_with_headers(self):
        data = [["Alice", 24], ["Bob", 30]]
        assert _ours(data, headers=["Name", "Age"], tablefmt="plain") == _ref(
            data, headers=["Name", "Age"], tablefmt="plain"
        )

    def test_empty(self):
        assert _ours([], tablefmt="plain") == _ref([], tablefmt="plain")

    def test_single_row(self):
        data = [["only", "row"]]
        assert _ours(data, tablefmt="plain") == _ref(data, tablefmt="plain")

    def test_single_column(self):
        data = [["a"], ["b"], ["c"]]
        assert _ours(data, tablefmt="plain") == _ref(data, tablefmt="plain")

    def test_numbers_only(self):
        data = [[1, 2.5], [3, 4.0]]
        assert _ours(data, tablefmt="plain") == _ref(data, tablefmt="plain")


# ── Simple format (default) ──


class TestSimpleFormat:
    def test_basic(self):
        data = [["Alice", 24], ["Bob", 30]]
        assert _ours(data, headers=["Name", "Age"]) == _ref(
            data, headers=["Name", "Age"]
        )

    def test_no_headers(self):
        data = [["Alice", 24], ["Bob", 30]]
        assert _ours(data) == _ref(data)

    def test_no_headers_explicit(self):
        data = [["Alice", 24], ["Bob", 30]]
        assert _ours(data, tablefmt="simple") == _ref(data, tablefmt="simple")

    def test_with_none(self):
        data = [["Alice", None], ["Bob", 30]]
        assert _ours(data, headers=["Name", "Age"], tablefmt="simple") == _ref(
            data, headers=["Name", "Age"], tablefmt="simple"
        )

    def test_many_columns(self):
        data = [["a", "b", "c", "d", "e"]]
        assert _ours(data, tablefmt="simple") == _ref(data, tablefmt="simple")


# ── Grid format ──


class TestGridFormat:
    def test_basic(self):
        data = [["Alice", 24], ["Bob", 30]]
        assert _ours(data, headers=["Name", "Age"], tablefmt="grid") == _ref(
            data, headers=["Name", "Age"], tablefmt="grid"
        )

    def test_no_headers(self):
        data = [["Alice", 24], ["Bob", 30]]
        assert _ours(data, tablefmt="grid") == _ref(data, tablefmt="grid")

    def test_single_row(self):
        data = [["one", "two", "three"]]
        assert _ours(data, headers=["A", "B", "C"], tablefmt="grid") == _ref(
            data, headers=["A", "B", "C"], tablefmt="grid"
        )

    def test_wide_values(self):
        data = [["a very long string", 1], ["short", 999999]]
        assert _ours(data, headers=["Text", "Num"], tablefmt="grid") == _ref(
            data, headers=["Text", "Num"], tablefmt="grid"
        )


# ── Pipe format ──


class TestPipeFormat:
    def test_basic(self):
        data = [["Alice", 24], ["Bob", 30]]
        assert _ours(data, headers=["Name", "Age"], tablefmt="pipe") == _ref(
            data, headers=["Name", "Age"], tablefmt="pipe"
        )

    def test_alignment_markers_left(self):
        data = [["a", "b"]]
        result = _ours(data, headers=["X", "Y"], tablefmt="pipe", stralign="left")
        ref = _ref(data, headers=["X", "Y"], tablefmt="pipe", stralign="left")
        assert result == ref

    def test_alignment_markers_right(self):
        data = [[1, 2]]
        result = _ours(data, headers=["X", "Y"], tablefmt="pipe")
        ref = _ref(data, headers=["X", "Y"], tablefmt="pipe")
        assert result == ref

    def test_alignment_markers_center(self):
        data = [["a", "b"]]
        result = _ours(
            data,
            headers=["X", "Y"],
            tablefmt="pipe",
            colalign=("center", "center"),
        )
        ref = _ref(
            data,
            headers=["X", "Y"],
            tablefmt="pipe",
            colalign=("center", "center"),
        )
        assert result == ref


# ── GitHub format ──


class TestGithubFormat:
    def test_basic(self):
        data = [["Alice", 24], ["Bob", 30]]
        assert _ours(data, headers=["Name", "Age"], tablefmt="github") == _ref(
            data, headers=["Name", "Age"], tablefmt="github"
        )

    def test_single_column(self):
        data = [["a"], ["b"]]
        assert _ours(data, headers=["X"], tablefmt="github") == _ref(
            data, headers=["X"], tablefmt="github"
        )

    def test_many_rows(self):
        data = [[i, i * 2] for i in range(10)]
        assert _ours(data, headers=["N", "2N"], tablefmt="github") == _ref(
            data, headers=["N", "2N"], tablefmt="github"
        )


# ── Orgtbl format ──


class TestOrgtblFormat:
    def test_basic(self):
        data = [["Alice", 24], ["Bob", 30]]
        assert _ours(data, headers=["Name", "Age"], tablefmt="orgtbl") == _ref(
            data, headers=["Name", "Age"], tablefmt="orgtbl"
        )

    def test_no_headers(self):
        data = [["Alice", 24], ["Bob", 30]]
        assert _ours(data, tablefmt="orgtbl") == _ref(data, tablefmt="orgtbl")


# ── Pretty format ──


class TestPrettyFormat:
    def test_basic(self):
        data = [["Alice", 24], ["Bob", 30]]
        assert _ours(data, headers=["Name", "Age"], tablefmt="pretty") == _ref(
            data, headers=["Name", "Age"], tablefmt="pretty"
        )

    def test_no_headers(self):
        data = [["Alice", 24], ["Bob", 30]]
        assert _ours(data, tablefmt="pretty") == _ref(data, tablefmt="pretty")


# ── Headers ──


class TestHeaders:
    def test_firstrow(self):
        data = [["Name", "Age"], ["Alice", 24], ["Bob", 30]]
        assert _ours(data, headers="firstrow") == _ref(data, headers="firstrow")

    def test_firstrow_grid(self):
        data = [["Name", "Age"], ["Alice", 24], ["Bob", 30]]
        assert _ours(data, headers="firstrow", tablefmt="grid") == _ref(
            data, headers="firstrow", tablefmt="grid"
        )

    def test_keys_list_of_dicts(self):
        data = [{"name": "Alice", "age": 24}, {"name": "Bob", "age": 30}]
        assert _ours(data, headers="keys") == _ref(data, headers="keys")

    def test_keys_list_of_dicts_grid(self):
        data = [{"name": "Alice", "age": 24}, {"name": "Bob", "age": 30}]
        assert _ours(data, headers="keys", tablefmt="grid") == _ref(
            data, headers="keys", tablefmt="grid"
        )

    def test_explicit_headers(self):
        data = [["Alice", 24], ["Bob", 30]]
        assert _ours(data, headers=["Name", "Age"]) == _ref(
            data, headers=["Name", "Age"]
        )

    def test_no_headers(self):
        data = [["Alice", 24], ["Bob", 30]]
        assert _ours(data) == _ref(data)

    def test_headers_longer_than_data(self):
        data = [["a", "b"]]
        result = _ours(data, headers=["X", "Y", "Z"])
        ref = _ref(data, headers=["X", "Y", "Z"])
        assert result == ref


# ── Alignment ──


class TestAlignment:
    def test_numalign_right(self):
        data = [["Alice", 24], ["Bob", 3000]]
        assert _ours(data, headers=["Name", "Num"], numalign="right") == _ref(
            data, headers=["Name", "Num"], numalign="right"
        )

    def test_numalign_left(self):
        data = [["Alice", 24], ["Bob", 3000]]
        assert _ours(data, headers=["Name", "Num"], numalign="left") == _ref(
            data, headers=["Name", "Num"], numalign="left"
        )

    def test_numalign_center(self):
        data = [["Alice", 24], ["Bob", 3000]]
        assert _ours(data, headers=["Name", "Num"], numalign="center") == _ref(
            data, headers=["Name", "Num"], numalign="center"
        )

    def test_stralign_left(self):
        data = [["Alice", 24], ["Bob", 30]]
        assert _ours(data, headers=["Name", "Age"], stralign="left") == _ref(
            data, headers=["Name", "Age"], stralign="left"
        )

    def test_stralign_right(self):
        data = [["Alice", 24], ["Bob", 30]]
        assert _ours(data, headers=["Name", "Age"], stralign="right") == _ref(
            data, headers=["Name", "Age"], stralign="right"
        )

    def test_stralign_center(self):
        data = [["Alice", 24], ["Bob", 30]]
        assert _ours(data, headers=["Name", "Age"], stralign="center") == _ref(
            data, headers=["Name", "Age"], stralign="center"
        )

    def test_colalign_override(self):
        data = [["Alice", 24, "NY"], ["Bob", 30, "LA"]]
        assert _ours(
            data,
            headers=["Name", "Age", "City"],
            colalign=("left", "center", "right"),
        ) == _ref(
            data,
            headers=["Name", "Age", "City"],
            colalign=("left", "center", "right"),
        )

    def test_colalign_partial(self):
        data = [["Alice", 24, "NY"], ["Bob", 30, "LA"]]
        assert _ours(
            data,
            headers=["Name", "Age", "City"],
            colalign=("right",),
        ) == _ref(
            data,
            headers=["Name", "Age", "City"],
            colalign=("right",),
        )

    def test_colalign_grid(self):
        data = [["a", 1], ["bb", 22]]
        assert _ours(
            data,
            headers=["Text", "Num"],
            tablefmt="grid",
            colalign=("center", "left"),
        ) == _ref(
            data,
            headers=["Text", "Num"],
            tablefmt="grid",
            colalign=("center", "left"),
        )


# ── Number formatting ──


class TestNumberFormatting:
    def test_floatfmt_default(self):
        data = [[1.23456789], [9.87654321]]
        assert _ours(data) == _ref(data)

    def test_floatfmt_2f(self):
        data = [[1.23456789], [9.87654321]]
        assert _ours(data, floatfmt=".2f") == _ref(data, floatfmt=".2f")

    def test_floatfmt_4f(self):
        data = [[3.14159265]]
        assert _ours(data, floatfmt=".4f") == _ref(data, floatfmt=".4f")

    def test_integers_stay_integer(self):
        data = [[42], [100]]
        assert _ours(data) == _ref(data)

    def test_mixed_int_float(self):
        data = [[1, 2.5], [3, 4.0]]
        assert _ours(data) == _ref(data)

    def test_none_values(self):
        data = [[1, None], [None, 2]]
        assert _ours(data) == _ref(data)

    def test_bool_values(self):
        data = [[True, False], [False, True]]
        assert _ours(data) == _ref(data)

    def test_inf_values(self):
        data = [[float("inf"), float("-inf")]]
        assert _ours(data) == _ref(data)

    def test_nan_values(self):
        data = [[float("nan")]]
        # nan != nan so compare strings
        assert _ours(data) == _ref(data)

    def test_scientific_format(self):
        data = [[1.23456789]]
        assert _ours(data, floatfmt=".2e") == _ref(data, floatfmt=".2e")


# ── Data types ──


class TestDataTypes:
    def test_list_of_lists(self):
        data = [["a", 1], ["b", 2]]
        assert _ours(data) == _ref(data)

    def test_list_of_tuples(self):
        data = [("a", 1), ("b", 2)]
        assert _ours(data) == _ref(data)

    def test_list_of_dicts(self):
        data = [{"x": 1, "y": 2}, {"x": 3, "y": 4}]
        assert _ours(data, headers="keys") == _ref(data, headers="keys")

    def test_list_of_dicts_missing_keys(self):
        data = [{"x": 1, "y": 2}, {"x": 3, "z": 5}]
        assert _ours(data, headers="keys") == _ref(data, headers="keys")

    def test_dict_of_lists(self):
        data = {"Name": ["Alice", "Bob"], "Age": [24, 30]}
        assert _ours(data, headers="keys") == _ref(data, headers="keys")

    def test_dict_of_lists_uneven(self):
        data = {"A": [1, 2, 3], "B": [10, 20]}
        assert _ours(data, headers="keys") == _ref(data, headers="keys")


# ── Missing values ──


class TestMissingValues:
    def test_none_default(self):
        data = [["Alice", None], [None, 30]]
        assert _ours(data) == _ref(data)

    def test_none_custom(self):
        data = [["Alice", None], [None, 30]]
        assert _ours(data, missingval="N/A") == _ref(data, missingval="N/A")

    def test_none_with_headers(self):
        data = [["Alice", None], [None, 30]]
        assert _ours(data, headers=["Name", "Age"], missingval="-") == _ref(
            data, headers=["Name", "Age"], missingval="-"
        )


# ── Show index ──


class TestShowIndex:
    def test_showindex_true(self):
        data = [["Alice", 24], ["Bob", 30]]
        assert _ours(data, showindex=True) == _ref(data, showindex=True)

    def test_showindex_with_headers(self):
        data = [["Alice", 24], ["Bob", 30]]
        assert _ours(data, headers=["Name", "Age"], showindex=True) == _ref(
            data, headers=["Name", "Age"], showindex=True
        )

    def test_showindex_custom(self):
        data = [["Alice", 24], ["Bob", 30]]
        assert _ours(data, showindex=["a", "b"]) == _ref(data, showindex=["a", "b"])

    def test_showindex_grid(self):
        data = [["Alice", 24], ["Bob", 30]]
        assert _ours(
            data,
            headers=["Name", "Age"],
            showindex=True,
            tablefmt="grid",
        ) == _ref(
            data,
            headers=["Name", "Age"],
            showindex=True,
            tablefmt="grid",
        )


# ── Edge cases ──


class TestEdgeCases:
    def test_empty_data(self):
        assert _ours([]) == _ref([])

    def test_empty_rows(self):
        data = [[], []]
        assert _ours(data) == _ref(data)

    def test_single_cell(self):
        data = [["hello"]]
        assert _ours(data) == _ref(data)

    def test_unicode_basic(self):
        data = [["cafe\u0301", 1], ["\u00e9l\u00e8ve", 2]]
        assert _ours(data) == _ref(data)

    def test_cjk_characters(self):
        data = [["\u4f60\u597d", 1], ["\u4e16\u754c", 2]]
        assert _ours(data, headers=["Text", "Num"]) == _ref(
            data, headers=["Text", "Num"]
        )

    def test_mixed_cjk_ascii(self):
        data = [["\u4e1c\u4eacTokyo", 1], ["NYC", 2]]
        assert _ours(data, headers=["City", "ID"]) == _ref(data, headers=["City", "ID"])

    def test_wide_emoji(self):
        # Some emoji are wide characters
        data = [["\U0001f600", "smile"]]
        assert _ours(data) == _ref(data)

    def test_single_dict(self):
        # Reference tabulate doesn't support single dicts (raises TypeError).
        # Verify our implementation produces a sensible table.
        data = {"name": "Alice", "age": 24}
        result = _ours(data)
        assert "name" in result
        assert "Alice" in result

    def test_large_numbers(self):
        data = [[10**15, 3.14159]]
        assert _ours(data) == _ref(data)

    def test_negative_numbers(self):
        data = [[-1, -2.5], [3, -4.0]]
        assert _ours(data) == _ref(data)

    def test_zero_values(self):
        data = [[0, 0.0], [0, 0]]
        assert _ours(data) == _ref(data)

    def test_empty_strings(self):
        data = [["", "b"], ["c", ""]]
        assert _ours(data) == _ref(data)

    def test_multiline_not_special(self):
        # Single-line strings that contain no newlines
        data = [["hello world", 1]]
        assert _ours(data) == _ref(data)


# ── Format-specific cross-checks ──


class TestCrossFormatConsistency:
    """Verify that our output matches the reference across all formats."""

    FORMATS = ["plain", "simple", "grid", "pipe", "orgtbl", "pretty", "github"]

    def test_all_formats_basic(self):
        data = [["Alice", 24], ["Bob", 30]]
        for fmt in self.FORMATS:
            assert _ours(data, headers=["Name", "Age"], tablefmt=fmt) == _ref(
                data, headers=["Name", "Age"], tablefmt=fmt
            ), f"Mismatch for format {fmt!r}"

    def test_all_formats_no_headers(self):
        data = [["Alice", 24], ["Bob", 30]]
        for fmt in self.FORMATS:
            assert _ours(data, tablefmt=fmt) == _ref(data, tablefmt=fmt), (
                f"Mismatch for format {fmt!r}"
            )

    def test_all_formats_numbers(self):
        data = [[1, 2.5, 3], [10, 20.1, 300]]
        for fmt in self.FORMATS:
            assert _ours(data, headers=["A", "B", "C"], tablefmt=fmt) == _ref(
                data, headers=["A", "B", "C"], tablefmt=fmt
            ), f"Mismatch for format {fmt!r}"

    def test_all_formats_with_index(self):
        data = [["Alice", 24], ["Bob", 30]]
        for fmt in self.FORMATS:
            assert _ours(
                data,
                headers=["Name", "Age"],
                showindex=True,
                tablefmt=fmt,
            ) == _ref(
                data,
                headers=["Name", "Age"],
                showindex=True,
                tablefmt=fmt,
            ), f"Mismatch for format {fmt!r}"

    def test_all_formats_floatfmt(self):
        data = [[3.14159, 2.71828]]
        # The reference "pretty" format ignores floatfmt, so exclude it.
        fmts = [f for f in self.FORMATS if f != "pretty"]
        for fmt in fmts:
            assert _ours(
                data,
                headers=["Pi", "E"],
                tablefmt=fmt,
                floatfmt=".2f",
            ) == _ref(
                data,
                headers=["Pi", "E"],
                tablefmt=fmt,
                floatfmt=".2f",
            ), f"Mismatch for format {fmt!r}"
