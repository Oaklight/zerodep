"""Conformance gate: run the vendored TOON spec 4.4 fixtures.

The fixtures under ``toon/fixtures/spec/`` are the official conformance set of
the TOON specification, copied verbatim from ``toon-format/spec`` (see
``toon/fixtures/README.md`` for the pinned commit). They are the same set
``toon-format/toon-python`` runs in its own CI.

This gate pins the current conformance level so later work can only move it up.
Most cases fail today, so the expected failures are recorded in
``toon/conformance_baseline.json`` and the gate is a ratchet:

* every case *not* in the baseline must pass;
* every case *in* the baseline must still fail, so a fix that starts passing
  must be removed from the baseline (it can only shrink);
* the total pass count must never drop below the recorded number.

When a stage fixes a section, run ``python toon/test_toon_conformance.py
--update-baseline`` to shrink the baseline, then commit both files together.
The failure output names the spec section and the fixture ID so the change is
attributable to a section.

The gate needs no network and no reference library: the fixtures are vendored
and the only import is the module under test.
"""

from __future__ import annotations

import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, os.path.dirname(__file__))
from toon import ToonDecodeError, decode, encode  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures" / "spec"
BASELINE_PATH = Path(__file__).parent / "conformance_baseline.json"


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
        for section in sorted(
            buckets[category],
            key=lambda s: (-(buckets[category][s][0] - buckets[category][s][1]), s),
        ):
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


if __name__ == "__main__":
    if "--update-baseline" in sys.argv:
        BASELINE_PATH.write_text(
            json.dumps(_build_baseline(), indent=2) + "\n", encoding="utf-8"
        )
        print(f"wrote {BASELINE_PATH}")
    elif "--report" in sys.argv:
        print(_section_table())
    else:
        pytest.main([__file__, "-v"])
