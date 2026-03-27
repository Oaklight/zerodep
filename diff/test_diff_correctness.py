"""Correctness tests: zerodep diff vs unidiff."""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from diff import (
    ConflictRegion,
    DiffError,
    Patch,
    PatchApplyError,
    PatchedFile,
    PatchParseError,
    apply_patch,
    make_diff,
    merge3,
    parse_patch,
    reverse_patch,
)

unidiff = pytest.importorskip("unidiff", reason="unidiff not installed")


# ── Helpers ──────────────────────────────────────────────────────────


def _assert_round_trip(a: str, b: str) -> None:
    """Verify make_diff → parse_patch → apply_patch reproduces *b*,
    and reverse_patch reproduces *a*."""
    diff_text = make_diff(a, b)
    if a == b:
        assert diff_text == ""
        return
    patch = parse_patch(diff_text)
    assert apply_patch(a, patch) == b

    rev = reverse_patch(patch)
    assert apply_patch(b, rev) == a


def _compare_structure(our_patch: Patch, ref_patchset) -> None:
    """Compare structural equivalence with unidiff.PatchSet."""
    assert len(our_patch.files) == len(ref_patchset)
    for ours, theirs in zip(our_patch.files, ref_patchset):
        assert len(ours.hunks) == len(theirs)
        for our_hunk, ref_hunk in zip(ours.hunks, theirs):
            assert our_hunk.src_start == ref_hunk.source_start
            assert our_hunk.src_len == ref_hunk.source_length
            assert our_hunk.tgt_start == ref_hunk.target_start
            assert our_hunk.tgt_len == ref_hunk.target_length


# ── Test Data ────────────────────────────────────────────────────────

SIMPLE_A = "hello\nworld\n"
SIMPLE_B = "hello\nbrave new world\n"

MULTI_LINE_A = "line1\nline2\nline3\nline4\nline5\n"
MULTI_LINE_B = "line1\nmodified\nline3\ninserted\nline4\nline5\n"

LONG_A = "".join(f"line{i}\n" for i in range(100))
LONG_B_LINES = list(f"line{i}\n" for i in range(100))
LONG_B_LINES[10] = "CHANGED10\n"
LONG_B_LINES[50] = "CHANGED50\n"
LONG_B_LINES[90] = "CHANGED90\n"
LONG_B = "".join(LONG_B_LINES)

ROUND_TRIP_CASES = [
    pytest.param(SIMPLE_A, SIMPLE_B, id="simple"),
    pytest.param(MULTI_LINE_A, MULTI_LINE_B, id="multi_line"),
    pytest.param(LONG_A, LONG_B, id="long_multi_hunk"),
    pytest.param("", "new content\n", id="empty_to_content"),
    pytest.param("old content\n", "", id="content_to_empty"),
    pytest.param("same\n", "same\n", id="identical"),
    pytest.param("no newline", "also no newline", id="no_trailing_newline"),
    pytest.param("hello\nworld", "hello\nworld\n", id="add_trailing_newline"),
    pytest.param("hello\nworld\n", "hello\nworld", id="remove_trailing_newline"),
    pytest.param("一\n二\n三\n", "一\n贰\n三\n", id="unicode_cjk"),
    pytest.param("a\nb\n", "a\nx\ny\nb\n", id="insert_multiple"),
    pytest.param("a\nx\ny\nb\n", "a\nb\n", id="delete_multiple"),
    pytest.param("a\n", "b\n", id="single_line_change"),
]


# ── TestMakeDiff ─────────────────────────────────────────────────────


class TestMakeDiff:
    def test_simple_change(self):
        d = make_diff(SIMPLE_A, SIMPLE_B)
        assert "--- a" in d
        assert "+++ b" in d
        assert "-world" in d
        assert "+brave new world" in d

    def test_custom_filenames(self):
        d = make_diff(SIMPLE_A, SIMPLE_B, filename_a="old.txt", filename_b="new.txt")
        assert "--- old.txt" in d
        assert "+++ new.txt" in d

    def test_no_differences(self):
        assert make_diff("same\n", "same\n") == ""

    def test_empty_inputs(self):
        d = make_diff("", "new\n")
        assert "+new" in d

    def test_context_parameter(self):
        d1 = make_diff(LONG_A, LONG_B, context=1)
        d3 = make_diff(LONG_A, LONG_B, context=3)
        # Fewer context lines → shorter diff.
        assert len(d1) < len(d3)

    def test_no_trailing_newline_marker(self):
        d = make_diff("hello", "world")
        assert "\\ No newline at end of file" in d


# ── TestParsePatch ───────────────────────────────────────────────────


class TestParsePatch:
    @pytest.mark.parametrize("a,b", ROUND_TRIP_CASES)
    def test_parseable(self, a, b):
        d = make_diff(a, b)
        if d == "":
            return
        patch = parse_patch(d)
        assert len(patch.files) >= 1

    def test_structure_matches_unidiff(self):
        d = make_diff(LONG_A, LONG_B, context=3)
        ours = parse_patch(d)
        ref = unidiff.PatchSet(d)
        _compare_structure(ours, ref)

    def test_single_hunk(self):
        d = make_diff(SIMPLE_A, SIMPLE_B)
        p = parse_patch(d)
        assert len(p.files) == 1
        assert len(p[0].hunks) == 1

    def test_multi_hunk(self):
        d = make_diff(LONG_A, LONG_B, context=1)
        p = parse_patch(d)
        assert len(p[0].hunks) == 3

    def test_new_file(self):
        d = make_diff("", "new\n", filename_a="/dev/null", filename_b="new.txt")
        p = parse_patch(d)
        assert p[0].is_added

    def test_deleted_file(self):
        d = make_diff("old\n", "", filename_a="old.txt", filename_b="/dev/null")
        p = parse_patch(d)
        assert p[0].is_deleted

    def test_hunk_header_before_file_header(self):
        with pytest.raises(PatchParseError, match="hunk header before file header"):
            parse_patch("@@ -1,1 +1,1 @@\n content\n")

    def test_hunk_line_counts(self):
        d = make_diff(MULTI_LINE_A, MULTI_LINE_B)
        p = parse_patch(d)
        hunk = p[0].hunks[0]
        # Verify line counts match actual content.
        src_count = sum(1 for t, _ in hunk.lines if t in (" ", "-"))
        tgt_count = sum(1 for t, _ in hunk.lines if t in (" ", "+"))
        assert src_count == hunk.src_len
        assert tgt_count == hunk.tgt_len


# ── TestApplyPatch ───────────────────────────────────────────────────


class TestApplyPatch:
    @pytest.mark.parametrize("a,b", ROUND_TRIP_CASES)
    def test_round_trip(self, a, b):
        _assert_round_trip(a, b)

    def test_apply_patched_file(self):
        """Can pass a PatchedFile directly."""
        d = make_diff(SIMPLE_A, SIMPLE_B)
        p = parse_patch(d)
        result = apply_patch(SIMPLE_A, p[0])
        assert result == SIMPLE_B

    def test_wrong_source_raises(self):
        d = make_diff(SIMPLE_A, SIMPLE_B)
        p = parse_patch(d)
        with pytest.raises(PatchApplyError):
            apply_patch("completely\ndifferent\n", p)

    def test_multi_file_patch_raises(self):
        d1 = make_diff("a\n", "b\n", filename_a="file1", filename_b="file1")
        d2 = make_diff("c\n", "d\n", filename_a="file2", filename_b="file2")
        combined = d1 + d2
        p = parse_patch(combined)
        assert len(p.files) == 2
        with pytest.raises(DiffError, match="2 files"):
            apply_patch("a\n", p)

    def test_empty_patch(self):
        p = Patch(files=[])
        assert apply_patch("unchanged\n", p) == "unchanged\n"


# ── TestReversePatch ─────────────────────────────────────────────────


class TestReversePatch:
    @pytest.mark.parametrize("a,b", ROUND_TRIP_CASES)
    def test_reverse_round_trip(self, a, b):
        _assert_round_trip(a, b)

    def test_metadata_swap(self):
        d = make_diff(SIMPLE_A, SIMPLE_B, filename_a="old.py", filename_b="new.py")
        p = parse_patch(d)
        rev = reverse_patch(p)
        assert rev[0].source_file == "new.py"
        assert rev[0].target_file == "old.py"
        for hunk, rev_hunk in zip(p[0].hunks, rev[0].hunks):
            assert hunk.src_start == rev_hunk.tgt_start
            assert hunk.tgt_start == rev_hunk.src_start
            assert hunk.src_len == rev_hunk.tgt_len
            assert hunk.tgt_len == rev_hunk.src_len

    def test_tag_inversion(self):
        d = make_diff("a\n", "b\n")
        p = parse_patch(d)
        rev = reverse_patch(p)
        original_tags = [t for t, _ in p[0].hunks[0].lines]
        reversed_tags = [t for t, _ in rev[0].hunks[0].lines]
        for ot, rt in zip(original_tags, reversed_tags):
            if ot == "+":
                assert rt == "-"
            elif ot == "-":
                assert rt == "+"
            else:
                assert rt == " "


# ── TestMerge3 ───────────────────────────────────────────────────────

BASE = "line1\nline2\nline3\nline4\nline5\n"


class TestMerge3:
    def test_no_changes(self):
        m = merge3(BASE, BASE, BASE)
        assert not m.has_conflicts
        assert m.content == BASE

    def test_ours_only(self):
        ours = "line1\nmodified\nline3\nline4\nline5\n"
        m = merge3(BASE, ours, BASE)
        assert not m.has_conflicts
        assert m.content == ours

    def test_theirs_only(self):
        theirs = "line1\nline2\nline3\nline4\nchanged\n"
        m = merge3(BASE, BASE, theirs)
        assert not m.has_conflicts
        assert m.content == theirs

    def test_both_non_overlapping(self):
        ours = "line1\nmodified2\nline3\nline4\nline5\n"
        theirs = "line1\nline2\nline3\nline4\nmodified5\n"
        m = merge3(BASE, ours, theirs)
        assert not m.has_conflicts
        assert m.content == "line1\nmodified2\nline3\nline4\nmodified5\n"

    def test_both_identical_change(self):
        ours = "line1\nsame_change\nline3\nline4\nline5\n"
        theirs = "line1\nsame_change\nline3\nline4\nline5\n"
        m = merge3(BASE, ours, theirs)
        assert not m.has_conflicts
        assert m.content == ours

    def test_conflict(self):
        ours = "line1\nours2\nline3\nline4\nline5\n"
        theirs = "line1\ntheirs2\nline3\nline4\nline5\n"
        m = merge3(BASE, ours, theirs)
        assert m.has_conflicts
        assert len(m.conflicts) == 1
        assert "<<<<<<< ours" in m.content
        assert "=======" in m.content
        assert ">>>>>>> theirs" in m.content

    def test_conflict_custom_labels(self):
        ours = "line1\nA\nline3\nline4\nline5\n"
        theirs = "line1\nB\nline3\nline4\nline5\n"
        m = merge3(BASE, ours, theirs, label_ours="HEAD", label_theirs="feature")
        assert "<<<<<<< HEAD" in m.content
        assert ">>>>>>> feature" in m.content

    def test_conflict_region_fields(self):
        ours = "line1\nours2\nline3\nline4\nline5\n"
        theirs = "line1\ntheirs2\nline3\nline4\nline5\n"
        m = merge3(BASE, ours, theirs)
        c = m.conflicts[0]
        assert isinstance(c, ConflictRegion)
        assert "ours2\n" in c.ours
        assert "theirs2\n" in c.theirs

    def test_empty_base_both_add(self):
        m = merge3("", "hello\n", "world\n")
        # Both sides add to empty base at the same position — conflict
        # if the changes overlap, otherwise clean merge.
        # With difflib's SequenceMatcher, both additions target the same
        # empty range in base, so it depends on overlap detection.
        # Either outcome is acceptable; verify content is well-formed.
        assert isinstance(m.content, str)
        assert "hello" in m.content
        assert "world" in m.content

    def test_one_side_empty(self):
        m = merge3(BASE, BASE, BASE)
        assert m.content == BASE


# ── TestEdgeCases ────────────────────────────────────────────────────


class TestEdgeCases:
    def test_windows_line_endings(self):
        a = "hello\r\nworld\r\n"
        b = "hello\r\nchanged\r\n"
        _assert_round_trip(a, b)

    def test_large_file(self):
        a = "".join(f"line {i}\n" for i in range(500))
        lines = list(f"line {i}\n" for i in range(500))
        lines[100] = "CHANGED\n"
        lines[250] = "ALSO CHANGED\n"
        lines[400] = "AND THIS\n"
        b = "".join(lines)
        _assert_round_trip(a, b)

    def test_patch_iteration(self):
        d = make_diff("a\n", "b\n")
        p = parse_patch(d)
        assert len(p) == 1
        for f in p:
            assert isinstance(f, PatchedFile)
        assert isinstance(p[0], PatchedFile)

    def test_single_line_no_newline(self):
        _assert_round_trip("hello", "world")

    def test_empty_to_empty(self):
        assert make_diff("", "") == ""
