"""Conformance gate: run the vendored TOON spec 4.4 fixtures.

The fixtures under ``toon/fixtures/spec/`` are the official conformance set of
the TOON specification, copied verbatim from ``toon-format/spec`` (see
``toon/fixtures/README.md`` for the pinned commit). They are the same set
``toon-format/toon-python`` runs in its own CI.

This gate pins the current conformance level so later work can only move it up.
Most cases fail today, so the expected failures are recorded in
``toon/conformance_baseline.json`` and the gate is a ratchet:

* every case *not* in the committed baseline must pass;
* every case *in* the committed baseline must still fail, so a fix that starts
  passing must be removed from the baseline;
* the committed baseline's ``failing`` set must be a **subset** of the baseline
  at the branch point, and ``passing_total`` must not decrease. Regenerating the
  baseline cannot absorb a regression, because the regenerated set would be
  rejected against the branch point. Growing the baseline is a deliberate act,
  not a routine command.

The branch point is read from ``origin/master`` (falling back to a local
``master``), using the merge base with HEAD when the history allows it. A
shallow or single-branch clone that has neither ref is fetched; if the fetch
fails the gate **fails**, it never skips. The case-running part needs no
network and no reference library, so only the baseline-integrity check touches
git.

When a stage fixes a section, run ``python toon/test_toon_conformance.py
--update-baseline`` to shrink the baseline, then commit both files together.
That command refuses to grow the ``failing`` set unless ``--allow-growth`` is
passed explicitly. The failure output names the spec section and the fixture ID
so the change is attributable to a section.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, os.path.dirname(__file__))
from toon import ToonDecodeError, decode, encode  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures" / "spec"
BASELINE_PATH = Path(__file__).parent / "conformance_baseline.json"

_REPO_ROOT = Path(__file__).resolve().parents[1]
_BASELINE_RELPATH = "toon/conformance_baseline.json"
_BASE_REF_CANDIDATES = ("origin/master", "master")


def _encode_options(case: dict[str, Any]) -> dict[str, Any]:
    """Map fixture encode options onto the module's option names."""
    options = case.get("options", {})
    return {
        "indent": options.get("indentSize", 2),
        "delimiter": options.get("delimiter", ","),
    }


def _decode_options(case: dict[str, Any]) -> dict[str, Any]:
    """Map fixture decode options onto the module's option names."""
    options = case.get("options", {})
    return {
        "indent": options.get("indentSize", 2),
        "strict": options.get("strict", True),
    }


def _key_order(value: Any) -> Any:
    """Nested key sequences, which ``==`` on dicts ignores (§2)."""
    if isinstance(value, dict):
        return [(key, _key_order(item)) for key, item in value.items()]
    if isinstance(value, list):
        return [_key_order(item) for item in value]
    return None


def _iter_cases() -> list[dict[str, Any]]:
    """Load every fixture case with a stable ID and its spec section."""
    cases: list[dict[str, Any]] = []
    for path in sorted(FIXTURES.glob("*/*.json")):
        category = path.parent.name
        document = json.loads(path.read_text(encoding="utf-8"))
        for index, case in enumerate(document["tests"]):
            cases.append(
                {
                    "id": f"{category}/{path.stem}[{index}]",
                    "category": category,
                    "section": str(case.get("specSection", "")).lstrip("§") or "-",
                    "name": case["name"],
                    "case": case,
                }
            )
    return cases


def _run(case: dict[str, Any], category: str) -> tuple[bool, str]:
    """Return ``(passed, detail)`` for one fixture case."""
    if category == "encode":
        try:
            output = encode(case["input"], _encode_options(case))
        except Exception as exc:  # noqa: BLE001 - any raise is a failure here
            if case.get("shouldError"):
                return True, ""
            return False, f"raised {type(exc).__name__}: {exc}"
        if case.get("shouldError"):
            return False, f"expected an error, got {output!r}"
        if output == case["expected"]:
            return True, ""
        return False, f"got {output!r}, want {case['expected']!r}"

    if case.get("shouldError"):
        try:
            decode(case["input"], _decode_options(case))
        except ToonDecodeError:
            return True, ""
        except Exception as exc:  # noqa: BLE001 - wrong exception type fails
            return False, f"raised {type(exc).__name__} (want ToonDecodeError)"
        return False, "expected ToonDecodeError, decoded successfully"
    try:
        result = decode(case["input"], _decode_options(case))
    except Exception as exc:  # noqa: BLE001 - any raise is a failure here
        return False, f"raised {type(exc).__name__}: {exc}"
    if result != case["expected"]:
        return False, f"got {result!r}, want {case['expected']!r}"
    if _key_order(result) != _key_order(case["expected"]):
        return False, "key order differs from expected (§2)"
    return True, ""


# Evaluated once at import: 564 cases, all in-process.
CASES = _iter_cases()
RESULTS = {item["id"]: _run(item["case"], item["category"]) for item in CASES}
BASELINE = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
BASELINE_FAILING = frozenset(BASELINE["failing"])


def _format_failures(title: str, cases: list[dict[str, Any]]) -> str:
    lines = [title]
    for item in cases:
        detail = RESULTS[item["id"]][1]
        lines.append(
            f"  §{item['section']}  {item['id']}  {item['name']}\n      {detail}"
        )
    return "\n".join(lines)


def _git(*args: str) -> subprocess.CompletedProcess[str]:
    """Run git in the repository root without raising on a non-zero exit."""
    try:
        return subprocess.run(
            ["git", "-C", str(_REPO_ROOT), *args],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:  # pragma: no cover - git is required
        raise AssertionError(
            "the conformance ratchet needs git to read the baseline at the "
            f"branch point, but git could not be run: {exc}"
        ) from exc


def _has_commit(ref: str) -> bool:
    return _git("rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}").returncode == 0


def _resolve_base_commit() -> tuple[str, bool]:
    """Return ``(base_commit, base_has_baseline)`` for the branch point.

    Prefers a local ``origin/master`` or ``master``; the merge base with HEAD is
    used when the history allows it, otherwise the ref tip. When neither ref
    exists (a shallow or single-branch clone) ``origin master`` is fetched. A
    failed fetch raises, so the gate never silently turns itself off.
    """
    ref = next((r for r in _BASE_REF_CANDIDATES if _has_commit(r)), None)
    if ref is None:
        fetch = _git("fetch", "--quiet", "origin", "master")
        if fetch.returncode != 0 or not _has_commit("origin/master"):
            raise AssertionError(
                "cannot resolve a base ref to ratchet against: neither "
                f"{' nor '.join(_BASE_REF_CANDIDATES)} exists and "
                "`git fetch origin master` failed "
                f"({fetch.stderr.strip() or 'no output'})."
            )
        ref = "origin/master"

    merge_base = _git("merge-base", "HEAD", ref)
    if merge_base.returncode == 0 and merge_base.stdout.strip():
        base = merge_base.stdout.strip()
    else:
        # Shallow history: the fork point is unavailable, so the ref tip is the
        # closest thing to the branch point we can name.
        base = _git("rev-parse", f"{ref}^{{commit}}").stdout.strip() or ref

    shown = _git("show", f"{base}:{_BASELINE_RELPATH}")
    if shown.returncode != 0:
        stderr = shown.stderr.lower()
        if "does not exist" in stderr or "but not in" in stderr:
            return base, False
        raise AssertionError(
            f"could not read {_BASELINE_RELPATH} at {base}: {shown.stderr.strip()}"
        )
    return base, True


# Resolved lazily so a failure lands on the test, not on collection.
_BASE_CACHE: tuple[str, dict[str, Any] | None] | None = None


def _base_baseline() -> tuple[str, dict[str, Any] | None]:
    global _BASE_CACHE
    if _BASE_CACHE is None:
        base, has_baseline = _resolve_base_commit()
        if not has_baseline:
            _BASE_CACHE = (base, None)
        else:
            shown = _git("show", f"{base}:{_BASELINE_RELPATH}")
            _BASE_CACHE = (base, json.loads(shown.stdout))
    return _BASE_CACHE


def test_fixture_totals_match_baseline() -> None:
    """The vendored fixture set must match the pinned baseline."""
    counts = dict(Counter(item["category"] for item in CASES))
    assert counts == BASELINE["case_counts"], (
        "fixture totals changed; refresh the vendored set and the baseline"
    )


def test_no_new_failures() -> None:
    """Every case that is not in the baseline must pass."""
    new = [
        item
        for item in CASES
        if not RESULTS[item["id"]][0] and item["id"] not in BASELINE_FAILING
    ]
    assert not new, _format_failures(
        f"{len(new)} conformance case(s) fail but are not in the baseline:",
        new,
    )


def test_baseline_entries_still_fail() -> None:
    """A baseline entry that now passes must be removed (ratchet only shrinks)."""
    fixed = [
        item
        for item in CASES
        if RESULTS[item["id"]][0] and item["id"] in BASELINE_FAILING
    ]
    assert not fixed, _format_failures(
        f"{len(fixed)} baseline case(s) now pass; run "
        "`python toon/test_toon_conformance.py --update-baseline`:",
        fixed,
    )


def test_pass_count_never_drops() -> None:
    """The total pass count must not fall below the recorded floor."""
    passing = sum(1 for ok, _ in RESULTS.values() if ok)
    assert passing >= BASELINE["passing_total"], (
        f"conformance pass count dropped to {passing} "
        f"(floor is {BASELINE['passing_total']})"
    )


def test_baseline_entries_exist_in_fixtures() -> None:
    """Every baseline ID must name a real fixture case."""
    known = {item["id"] for item in CASES}
    missing = sorted(BASELINE_FAILING - known)
    assert not missing, f"baseline names unknown fixture IDs: {missing}"


def test_no_regression_against_base() -> None:
    """The committed baseline may only shrink relative to the branch point.

    This is what stops a regression from being absorbed by regenerating the
    baseline: the regenerated ``failing`` set would no longer be a subset of the
    one at the branch point, and this test rejects it. It needs the base ref,
    and it fails rather than skips when the ref cannot be resolved.
    """
    base, base_baseline = _base_baseline()
    if base_baseline is None:
        # The commit that introduces the gate has nothing to compare against;
        # from the next commit on this check is live.
        return
    if dict(base_baseline["case_counts"]) != dict(BASELINE["case_counts"]):
        # The vendored fixture set changed, so failing IDs are not comparable
        # across the two sets and a subset check would be meaningless. This is
        # a deliberate, visible change, not a regression to catch here.
        return
    base_failing = frozenset(base_baseline["failing"])
    grown = sorted(BASELINE_FAILING - base_failing)
    assert not grown, (
        f"the committed baseline adds {len(grown)} failing case(s) that "
        f"{base[:12]} does not have; the ratchet may only shrink. Fix the "
        "regression rather than committing the regenerated baseline:\n"
        + "\n".join(f"  {case_id}" for case_id in grown[:40])
    )
    assert BASELINE["passing_total"] >= base_baseline["passing_total"], (
        f"passing_total dropped to {BASELINE['passing_total']} from "
        f"{base_baseline['passing_total']} at {base[:12]}"
    )


def _section_table() -> str:
    """Pass/fail per spec section, encode and decode separately."""
    buckets: dict[str, dict[str, list[int]]] = defaultdict(
        lambda: defaultdict(lambda: [0, 0])
    )
    for item in CASES:
        bucket = buckets[item["category"]][item["section"]]
        bucket[0] += 1
        if RESULTS[item["id"]][0]:
            bucket[1] += 1
    lines = []
    for category in ("encode", "decode"):
        total = [0, 0]
        lines.append(f"== {category}")
        ordered = sorted(
            buckets[category],
            key=lambda s: (-(buckets[category][s][0] - buckets[category][s][1]), s),
        )
        for section in ordered:
            count, passed = buckets[category][section]
            total[0] += count
            total[1] += passed
            detail = f"{passed:>3}/{count:<3} pass ({count - passed} fail)"
            lines.append(f"  §{section:<5} {detail}")
        lines.append(f"  total  {total[1]}/{total[0]} pass")
    return "\n".join(lines)


def _build_baseline() -> dict[str, Any]:
    failing = sorted(item["id"] for item in CASES if not RESULTS[item["id"]][0])
    passing = sum(1 for ok, _ in RESULTS.values() if ok)
    return {
        "spec_version": BASELINE["spec_version"],
        "upstream_commit": BASELINE["upstream_commit"],
        "case_counts": dict(Counter(item["category"] for item in CASES)),
        "passing_total": passing,
        "failing": failing,
    }


def _update_baseline(allow_growth: bool) -> int:
    """Write a fresh baseline, refusing to grow the failing set by default."""
    fresh = _build_baseline()
    if BASELINE_PATH.exists() and not allow_growth:
        current = set(json.loads(BASELINE_PATH.read_text(encoding="utf-8"))["failing"])
        grown = sorted(set(fresh["failing"]) - current)
        if grown:
            print(
                f"refusing to grow the baseline: {len(grown)} case(s) would be "
                "added to `failing`. Fix the regression, or pass --allow-growth "
                "if the growth is deliberate:\n  " + "\n  ".join(grown[:40])
            )
            return 1
    BASELINE_PATH.write_text(json.dumps(fresh, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {BASELINE_PATH}")
    return 0


if __name__ == "__main__":
    if "--update-baseline" in sys.argv:
        raise SystemExit(_update_baseline("--allow-growth" in sys.argv))
    elif "--report" in sys.argv:
        print(_section_table())
    else:
        pytest.main([__file__, "-v"])
