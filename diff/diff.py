# /// zerodep
# version = "0.3.0"
# deps = []
# tier = "simple"
# category = "devtools"
# note = "Install/update via: https://zerodep.readthedocs.io/en/latest/guide/cli/"
# ///

"""Unified diff parser, patch applicator, and three-way merge — zero dependencies, stdlib only, Python 3.10+.

Part of zerodep: https://github.com/Oaklight/zerodep
Copyright (c) 2026 Peng Ding. MIT License.

Provides structured parsing of unified diffs, patch application/reversal,
and three-way merge with conflict detection.  Built entirely on the
standard library ``difflib`` module.

Generate and round-trip a patch::

    from diff import make_diff, parse_patch, apply_patch, reverse_patch

    a = "hello\\nworld\\n"
    b = "hello\\nbrave new world\\n"

    patch_text = make_diff(a, b)
    patch = parse_patch(patch_text)
    assert apply_patch(a, patch) == b

    rev = reverse_patch(patch)
    assert apply_patch(b, rev) == a

Three-way merge::

    from diff import merge3

    result = merge3(base, ours, theirs)
    if result.has_conflicts:
        print("Conflicts found!")
    print(result.content)
"""

from __future__ import annotations

import dataclasses
import difflib
import re
from collections.abc import Sequence

__all__ = [
    # Exceptions
    "DiffError",
    "PatchParseError",
    "PatchApplyError",
    # Data structures
    "Hunk",
    "PatchedFile",
    "Patch",
    "ConflictRegion",
    "MergeResult",
    # Diff generation
    "make_diff",
    # Patch operations
    "parse_patch",
    "apply_patch",
    "reverse_patch",
    # Three-way merge
    "merge3",
]

# ── Exceptions ──────────────────────────────────────────────────────


class DiffError(Exception):
    """Base exception for all diff/patch operations."""


class PatchParseError(DiffError):
    """Raised when patch text has invalid or malformed format.

    Attributes:
        line_no: 1-based line number where the error was detected.
        detail: Human-readable description of the issue.
    """

    def __init__(self, line_no: int, detail: str) -> None:
        self.line_no = line_no
        self.detail = detail
        super().__init__(f"line {line_no}: {detail}")


class PatchApplyError(DiffError):
    """Raised when a patch cannot be applied to the given source.

    Attributes:
        hunk_index: 0-based index of the failing hunk.
        expected: The line content expected by the patch.
        actual: The line content found in the source.
        source_line_no: 1-based line number in the source.
    """

    def __init__(
        self,
        hunk_index: int,
        expected: str,
        actual: str,
        source_line_no: int,
    ) -> None:
        self.hunk_index = hunk_index
        self.expected = expected
        self.actual = actual
        self.source_line_no = source_line_no
        super().__init__(
            f"hunk {hunk_index}: source line {source_line_no}: "
            f"expected {expected!r}, got {actual!r}"
        )


# ── Data Structures ─────────────────────────────────────────────────


@dataclasses.dataclass
class Hunk:
    """A single contiguous changed region in a unified diff.

    Attributes:
        src_start: 1-based starting line in the source file.
        src_len: Number of source lines covered by this hunk.
        tgt_start: 1-based starting line in the target file.
        tgt_len: Number of target lines covered by this hunk.
        lines: Sequence of ``(tag, content)`` pairs where *tag* is one of
            ``' '`` (context), ``'-'`` (deletion), or ``'+'`` (addition)
            and *content* includes the trailing newline.
    """

    src_start: int
    src_len: int
    tgt_start: int
    tgt_len: int
    lines: list[tuple[str, str]]


@dataclasses.dataclass
class PatchedFile:
    """All hunks for a single file in a patch.

    Attributes:
        source_file: Source filename (``/dev/null`` for newly added files).
        target_file: Target filename (``/dev/null`` for deleted files).
        hunks: Ordered list of :class:`Hunk` instances.
    """

    source_file: str | None
    target_file: str | None
    hunks: list[Hunk]

    @property
    def is_added(self) -> bool:
        """True when the patch creates a new file."""
        return self.source_file is not None and self.source_file.endswith("/dev/null")

    @property
    def is_deleted(self) -> bool:
        """True when the patch deletes a file."""
        return self.target_file is not None and self.target_file.endswith("/dev/null")


@dataclasses.dataclass
class Patch:
    """A collection of :class:`PatchedFile` instances parsed from unified diff text.

    Supports ``len()``, iteration, and indexing.
    """

    files: list[PatchedFile]

    def __len__(self) -> int:
        return len(self.files)

    def __iter__(self):
        return iter(self.files)

    def __getitem__(self, index: int) -> PatchedFile:
        return self.files[index]


@dataclasses.dataclass
class ConflictRegion:
    """A region where concurrent edits conflict in a three-way merge.

    Attributes:
        base_start: 0-based start index in the base lines.
        base_end: 0-based exclusive end index in the base lines.
        ours: Lines from the *ours* side.
        theirs: Lines from the *theirs* side.
    """

    base_start: int
    base_end: int
    ours: list[str]
    theirs: list[str]


@dataclasses.dataclass
class MergeResult:
    """Result of a three-way merge.

    Attributes:
        content: The merged text.  When conflicts exist the text includes
            conflict markers (``<<<<<<<``, ``=======``, ``>>>>>>>``).
        has_conflicts: ``True`` when at least one conflict was detected.
        conflicts: List of :class:`ConflictRegion` instances.
    """

    content: str
    has_conflicts: bool
    conflicts: list[ConflictRegion]


# ── Internal Constants ──────────────────────────────────────────────

_HUNK_HEADER_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
_NO_NEWLINE_MARKER = "\\ No newline at end of file"


# ── Diff Generation ─────────────────────────────────────────────────


def make_diff(
    a: str,
    b: str,
    filename_a: str = "a",
    filename_b: str = "b",
    context: int = 3,
) -> str:
    """Generate a unified diff between two strings.

    Args:
        a: Original text.
        b: Modified text.
        filename_a: Label for the original file in the diff header.
        filename_b: Label for the modified file in the diff header.
        context: Number of context lines around each change.

    Returns:
        A unified diff string, or an empty string if *a* and *b* are identical.
    """
    a_lines = a.splitlines(True)
    b_lines = b.splitlines(True)
    raw = list(
        difflib.unified_diff(
            a_lines,
            b_lines,
            fromfile=filename_a,
            tofile=filename_b,
            n=context,
        )
    )
    # difflib does not emit "\ No newline at end of file" markers.
    # Insert them after any diff body line that lacks a trailing newline.
    result: list[str] = []
    for line in raw:
        result.append(line)
        if line and not line.endswith("\n") and line[0] in (" ", "-", "+"):
            result.append("\n" + _NO_NEWLINE_MARKER + "\n")
    return "".join(result)


# ── Patch Parser ────────────────────────────────────────────────────


def _strip_filename_prefix(name: str) -> str:
    """Remove the leading ``a/`` or ``b/`` prefix from diff filenames."""
    if len(name) > 2 and name[1] == "/" and name[0] in ("a", "b"):
        return name[2:]
    return name


def parse_patch(patch_text: str) -> Patch:
    """Parse unified diff text into a structured :class:`Patch`.

    Args:
        patch_text: The unified diff text.

    Returns:
        A :class:`Patch` containing one :class:`PatchedFile` per file.

    Raises:
        PatchParseError: If the diff text is malformed.
    """
    files: list[PatchedFile] = []
    current_file: PatchedFile | None = None
    current_hunk: Hunk | None = None
    remaining_src = 0
    remaining_tgt = 0
    source_name: str | None = None

    raw_lines = patch_text.splitlines(True)

    for line_no_0, raw in enumerate(raw_lines):
        line_no = line_no_0 + 1
        # Strip trailing newline for comparisons but keep it for content.
        stripped = raw.rstrip("\n").rstrip("\r")

        # --- source file header
        if stripped.startswith("--- "):
            source_name = _strip_filename_prefix(stripped[4:].strip())
            current_hunk = None
            continue

        # +++ target file header
        if stripped.startswith("+++ "):
            target_name = _strip_filename_prefix(stripped[4:].strip())
            current_file = PatchedFile(
                source_file=source_name,
                target_file=target_name,
                hunks=[],
            )
            files.append(current_file)
            source_name = None
            current_hunk = None
            continue

        # @@ hunk header
        m = _HUNK_HEADER_RE.match(stripped)
        if m:
            if current_file is None:
                raise PatchParseError(line_no, "hunk header before file header")
            src_start = int(m.group(1))
            src_len = int(m.group(2)) if m.group(2) is not None else 1
            tgt_start = int(m.group(3))
            tgt_len = int(m.group(4)) if m.group(4) is not None else 1
            current_hunk = Hunk(
                src_start=src_start,
                src_len=src_len,
                tgt_start=tgt_start,
                tgt_len=tgt_len,
                lines=[],
            )
            current_file.hunks.append(current_hunk)
            remaining_src = src_len
            remaining_tgt = tgt_len
            continue

        # "\ No newline at end of file"
        if stripped.startswith("\\"):
            if current_hunk and current_hunk.lines:
                tag, content = current_hunk.lines[-1]
                current_hunk.lines[-1] = (tag, content.rstrip("\n"))
            continue

        # Hunk body lines
        if current_hunk is not None and (remaining_src > 0 or remaining_tgt > 0):
            if not raw:
                continue
            tag = raw[0]
            content = raw[1:]
            if tag == " ":
                current_hunk.lines.append((" ", content))
                remaining_src -= 1
                remaining_tgt -= 1
            elif tag == "-":
                current_hunk.lines.append(("-", content))
                remaining_src -= 1
            elif tag == "+":
                current_hunk.lines.append(("+", content))
                remaining_tgt -= 1
            else:
                # Tolerate unknown prefix (e.g. diff preamble) outside a hunk,
                # but if we're inside a hunk this is unexpected.
                raise PatchParseError(
                    line_no,
                    f"unexpected line prefix {tag!r} inside hunk body",
                )
            continue

        # Lines outside hunks (diff --git preamble, index, mode, etc.)

    return Patch(files=files)


# ── Patch Application ───────────────────────────────────────────────


def apply_patch(source: str, patch: Patch | PatchedFile) -> str:
    """Apply a parsed patch to source text.

    Args:
        source: The original text to patch.
        patch: A :class:`Patch` (must contain exactly one file) or a
            single :class:`PatchedFile`.

    Returns:
        The patched text.

    Raises:
        PatchApplyError: If a context or deletion line does not match
            the source.
        DiffError: If a :class:`Patch` contains more than one file.
    """
    if isinstance(patch, Patch):
        if len(patch.files) == 0:
            return source
        if len(patch.files) != 1:
            raise DiffError(
                f"patch contains {len(patch.files)} files; "
                "pass a single PatchedFile instead"
            )
        pf = patch.files[0]
    else:
        pf = patch

    # Handle file creation from /dev/null.
    if pf.is_added:
        lines: list[str] = []
        for hunk in pf.hunks:
            for tag, content in hunk.lines:
                if tag == "+":
                    lines.append(content)
        return "".join(lines)

    # Handle file deletion.
    if pf.is_deleted:
        return ""

    source_lines = source.splitlines(True)
    output: list[str] = []
    src_idx = 0  # current position in source_lines (0-based)

    for hunk_i, hunk in enumerate(pf.hunks):
        hunk_start = hunk.src_start - 1  # convert to 0-based

        # Copy unchanged lines before this hunk.
        output.extend(source_lines[src_idx:hunk_start])

        src_pos = hunk_start
        for tag, content in hunk.lines:
            if tag == " ":
                # Context: must match source.
                if src_pos >= len(source_lines):
                    raise PatchApplyError(hunk_i, content, "<EOF>", src_pos + 1)
                actual = source_lines[src_pos]
                if actual != content:
                    raise PatchApplyError(hunk_i, content, actual, src_pos + 1)
                output.append(actual)
                src_pos += 1
            elif tag == "-":
                # Deletion: verify and skip.
                if src_pos >= len(source_lines):
                    raise PatchApplyError(hunk_i, content, "<EOF>", src_pos + 1)
                actual = source_lines[src_pos]
                if actual != content:
                    raise PatchApplyError(hunk_i, content, actual, src_pos + 1)
                src_pos += 1
            elif tag == "+":
                # Addition.
                output.append(content)

        src_idx = src_pos

    # Copy remaining lines after the last hunk.
    output.extend(source_lines[src_idx:])
    return "".join(output)


# ── Patch Reversal ──────────────────────────────────────────────────


def reverse_patch(patch: Patch) -> Patch:
    """Create a reversed copy of *patch*.

    Applying the reversed patch to the target reproduces the original source::

        assert apply_patch(b, reverse_patch(parse_patch(make_diff(a, b)))) == a

    Args:
        patch: The patch to reverse.

    Returns:
        A new :class:`Patch` with swapped source/target and inverted changes.
    """
    _TAG_SWAP = {"+": "-", "-": "+", " ": " "}

    new_files: list[PatchedFile] = []
    for pf in patch.files:
        new_hunks: list[Hunk] = []
        for hunk in pf.hunks:
            new_lines = [(_TAG_SWAP[tag], content) for tag, content in hunk.lines]
            new_hunks.append(
                Hunk(
                    src_start=hunk.tgt_start,
                    src_len=hunk.tgt_len,
                    tgt_start=hunk.src_start,
                    tgt_len=hunk.src_len,
                    lines=new_lines,
                )
            )
        new_files.append(
            PatchedFile(
                source_file=pf.target_file,
                target_file=pf.source_file,
                hunks=new_hunks,
            )
        )
    return Patch(files=new_files)


# ── Three-Way Merge ─────────────────────────────────────────────────


def _extract_changes(
    opcodes: Sequence[tuple[str, int, int, int, int]],
    other_lines: list[str],
) -> list[tuple[int, int, list[str]]]:
    """Convert SequenceMatcher opcodes to ``(base_start, base_end, replacement)``."""
    changes: list[tuple[int, int, list[str]]] = []
    for tag, i1, i2, j1, j2 in opcodes:
        if tag != "equal":
            changes.append((i1, i2, other_lines[j1:j2]))
    return changes


def merge3(
    base: str,
    ours: str,
    theirs: str,
    label_ours: str = "ours",
    label_theirs: str = "theirs",
) -> MergeResult:
    """Perform a three-way merge.

    Args:
        base: The common ancestor text.
        ours: Text from the first branch.
        theirs: Text from the second branch.
        label_ours: Label for conflict markers on the *ours* side.
        label_theirs: Label for conflict markers on the *theirs* side.

    Returns:
        A :class:`MergeResult` with the merged content and any conflicts.
    """
    base_lines = base.splitlines(True)
    ours_lines = ours.splitlines(True)
    theirs_lines = theirs.splitlines(True)

    sm_ours = difflib.SequenceMatcher(None, base_lines, ours_lines)
    sm_theirs = difflib.SequenceMatcher(None, base_lines, theirs_lines)

    ours_changes = _extract_changes(sm_ours.get_opcodes(), ours_lines)
    theirs_changes = _extract_changes(sm_theirs.get_opcodes(), theirs_lines)

    merged: list[str] = []
    conflicts: list[ConflictRegion] = []
    base_pos = 0
    oi = 0  # index into ours_changes
    ti = 0  # index into theirs_changes

    base_len = len(base_lines)

    while base_pos <= base_len:
        o_change = ours_changes[oi] if oi < len(ours_changes) else None
        t_change = theirs_changes[ti] if ti < len(theirs_changes) else None

        if o_change is None and t_change is None:
            # No more changes — emit remaining base.
            merged.extend(base_lines[base_pos:])
            break

        o_start = o_change[0] if o_change else base_len + 1
        t_start = t_change[0] if t_change else base_len + 1

        # Emit base lines before the next change.
        next_start = min(o_start, t_start)
        if next_start > base_pos:
            merged.extend(base_lines[base_pos:next_start])
            base_pos = next_start

        if o_change is not None and t_change is not None:
            o_s, o_e, o_rep = o_change
            t_s, t_e, t_rep = t_change

            if o_e <= t_s:
                # No overlap: ours first.
                merged.extend(o_rep)
                base_pos = o_e
                oi += 1
            elif t_e <= o_s:
                # No overlap: theirs first.
                merged.extend(t_rep)
                base_pos = t_e
                ti += 1
            else:
                # Overlapping ranges.
                union_start = min(o_s, t_s)
                union_end = max(o_e, t_e)

                if o_rep == t_rep:
                    # Identical changes — clean merge.
                    merged.extend(o_rep)
                else:
                    # Conflict.
                    conflicts.append(
                        ConflictRegion(
                            base_start=union_start,
                            base_end=union_end,
                            ours=list(o_rep),
                            theirs=list(t_rep),
                        )
                    )
                    merged.append(f"<<<<<<< {label_ours}\n")
                    merged.extend(o_rep)
                    merged.append("=======\n")
                    merged.extend(t_rep)
                    merged.append(f">>>>>>> {label_theirs}\n")

                base_pos = union_end
                oi += 1
                ti += 1
                # Skip additional changes from either side within the union.
                while oi < len(ours_changes) and ours_changes[oi][0] < union_end:
                    oi += 1
                while ti < len(theirs_changes) and theirs_changes[ti][0] < union_end:
                    ti += 1
        elif o_change is not None and o_start == base_pos:
            merged.extend(o_change[2])
            base_pos = o_change[1]
            oi += 1
        elif t_change is not None and t_start == base_pos:
            merged.extend(t_change[2])
            base_pos = t_change[1]
            ti += 1
        else:
            # Safety: should not reach here.
            break  # pragma: no cover

    return MergeResult(
        content="".join(merged),
        has_conflicts=len(conflicts) > 0,
        conflicts=conflicts,
    )
