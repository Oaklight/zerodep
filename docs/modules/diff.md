# Diff

Unified diff parser, patch applicator, and three-way merge -- zero dependencies, stdlib only, Python 3.10+.

> **Replaces:** `unidiff`, `patch`

## Overview

The Diff module provides structured parsing of unified diffs, patch application/reversal, and three-way merge with conflict detection. Built entirely on the standard library `difflib` module -- no third-party dependencies required.

| File | Description | Dependencies |
|------|-------------|--------------|
| `diff.py` | Pure Python implementation | None (stdlib only) |

The module uses `difflib.unified_diff` for generating diffs (with post-processing to add `\ No newline at end of file` markers), a state-machine parser for unified diff text, and a sweep-line algorithm over `difflib.SequenceMatcher` opcodes for three-way merging.

## How to Use in Your Project

Just copy the single `.py` file into your project:

```bash
cp diff/diff.py your_project/
```

Then import directly:

```python
from diff import make_diff, parse_patch, apply_patch, reverse_patch, merge3
```

## API Reference

### `make_diff(a, b, ...)`

Generate a unified diff string from two text inputs.

```python
def make_diff(
    a: str,
    b: str,
    filename_a: str = "a",
    filename_b: str = "b",
    context: int = 3,
) -> str
```

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `a` | `str` | -- | Original text. |
| `b` | `str` | -- | Modified text. |
| `filename_a` | `str` | `"a"` | Label for the source file in the diff header. |
| `filename_b` | `str` | `"b"` | Label for the target file in the diff header. |
| `context` | `int` | `3` | Number of context lines around each change. |

**Returns:** `str` -- Unified diff text. Empty string if no differences.

**Example:**

```python
from diff import make_diff

d = make_diff("hello\nworld\n", "hello\nbrave new world\n")
print(d)
# --- a
# +++ b
# @@ -1,2 +1,2 @@
#  hello
# -world
# +brave new world
```

### `parse_patch(patch_text)`

Parse unified diff text into a structured `Patch` object.

```python
def parse_patch(patch_text: str) -> Patch
```

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `patch_text` | `str` | -- | Unified diff text. |

**Returns:** `Patch` -- Structured patch with files and hunks.

**Raises:** `PatchParseError` -- If the diff text is malformed.

### `apply_patch(source, patch)`

Apply a patch to source text and return the result.

```python
def apply_patch(source: str, patch: Patch | PatchedFile) -> str
```

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `source` | `str` | -- | Original text to patch. |
| `patch` | `Patch` or `PatchedFile` | -- | Parsed patch or single-file patch to apply. |

**Returns:** `str` -- Patched text.

**Raises:** `PatchApplyError` -- If the source doesn't match the patch expectations.

### `reverse_patch(patch)`

Reverse a patch so it undoes the original change.

```python
def reverse_patch(patch: Patch) -> Patch
```

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `patch` | `Patch` | -- | Patch to reverse. |

**Returns:** `Patch` -- A new patch that undoes the original.

### `merge3(base, ours, theirs, ...)`

Perform a three-way merge with conflict detection.

```python
def merge3(
    base: str,
    ours: str,
    theirs: str,
    label_ours: str = "ours",
    label_theirs: str = "theirs",
) -> MergeResult
```

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `base` | `str` | -- | Common ancestor text. |
| `ours` | `str` | -- | Our modified version. |
| `theirs` | `str` | -- | Their modified version. |
| `label_ours` | `str` | `"ours"` | Label for conflict markers on our side. |
| `label_theirs` | `str` | `"theirs"` | Label for conflict markers on their side. |

**Returns:** `MergeResult` -- Contains `content` (merged text), `has_conflicts` (bool), and `conflicts` (list of `ConflictRegion`).

## Data Structures

### `Patch`

Container for one or more file diffs. Supports `len()`, iteration, and indexing.

- `files: list[PatchedFile]`

### `PatchedFile`

A single file's diff with metadata.

- `source_file: str | None` -- Source filename (or `"/dev/null"` for new files).
- `target_file: str | None` -- Target filename (or `"/dev/null"` for deletions).
- `hunks: list[Hunk]`
- `is_added` / `is_deleted` -- Properties indicating new/deleted files.

### `Hunk`

A contiguous region of changes.

- `src_start`, `src_len` -- Source region (1-based start).
- `tgt_start`, `tgt_len` -- Target region (1-based start).
- `lines: list[tuple[str, str]]` -- List of `(tag, content)` where tag is `" "`, `"+"`, or `"-"`.

### `MergeResult`

- `content: str` -- Merged text (with conflict markers if conflicts exist).
- `has_conflicts: bool`
- `conflicts: list[ConflictRegion]`

### `ConflictRegion`

- `base_start`, `base_end` -- 0-based line range in the base.
- `ours: list[str]`, `theirs: list[str]` -- Conflicting lines from each side.

## Usage Examples

### Round-Trip Patch

```python
from diff import make_diff, parse_patch, apply_patch, reverse_patch

a = "line1\nline2\nline3\n"
b = "line1\nmodified\nline3\n"

# Generate diff
diff_text = make_diff(a, b)

# Parse and apply
patch = parse_patch(diff_text)
assert apply_patch(a, patch) == b

# Reverse and apply to get back to original
rev = reverse_patch(patch)
assert apply_patch(b, rev) == a
```

### Three-Way Merge

```python
from diff import merge3

base = "line1\nline2\nline3\nline4\nline5\n"
ours = "line1\nmodified\nline3\nline4\nline5\n"
theirs = "line1\nline2\nline3\nline4\nchanged\n"

result = merge3(base, ours, theirs)
assert not result.has_conflicts
print(result.content)
# line1
# modified
# line3
# line4
# changed
```

### Conflict Detection

```python
from diff import merge3

base = "line1\nline2\nline3\n"
ours = "line1\nours\nline3\n"
theirs = "line1\ntheirs\nline3\n"

result = merge3(base, ours, theirs)
assert result.has_conflicts
assert len(result.conflicts) == 1
print(result.content)
# line1
# <<<<<<< ours
# ours
# =======
# theirs
# >>>>>>> theirs
# line3
```

### Multi-File Patch Parsing

```python
from diff import make_diff, parse_patch

d1 = make_diff("a\n", "b\n", filename_a="file1.txt", filename_b="file1.txt")
d2 = make_diff("c\n", "d\n", filename_a="file2.txt", filename_b="file2.txt")
combined = d1 + d2

patch = parse_patch(combined)
assert len(patch.files) == 2
print(patch[0].source_file)  # file1.txt
print(patch[1].source_file)  # file2.txt
```

## Exceptions

| Exception | When Raised |
|-----------|-------------|
| `DiffError` | Base class for all diff errors. |
| `PatchParseError` | Malformed diff text (with `line_no` and `detail`). |
| `PatchApplyError` | Source text doesn't match patch expectations (with `hunk_index`, `expected`, `actual`). |

## Not Supported

- Binary diff handling
- Git extended diff headers (`index`, `mode`, `rename from/to`)
- Fuzzy/offset patch matching (exact context match required)
- Combined diffs (merge commits)

## Notes and Caveats

!!! info "difflib-Based Generation"
    `make_diff()` uses `difflib.unified_diff` from the standard library with post-processing to insert `\ No newline at end of file` markers. The generated diffs are compatible with standard tools like `git apply` and `patch`.

!!! info "Strict Application"
    `apply_patch()` requires exact context line matching. Unlike `git apply` which supports offset and fuzz, this implementation will raise `PatchApplyError` if context lines don't match exactly. This ensures correctness at the cost of flexibility.

- **Python version:** Requires Python 3.10+ (uses `X | Y` union type syntax).
- **Performance:** ~8-9x faster than `unidiff` for patch parsing.
- **Round-trip invariant:** `apply_patch(a, parse_patch(make_diff(a, b))) == b` holds for all valid inputs.

## Benchmark

Benchmarked against `unidiff` across three diff sizes (small, medium, large).

See [Diff Benchmark](../benchmarks/diff.md) for detailed results.
