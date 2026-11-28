"""Repair tests: contract, generated damage, and bounded exhaustive checks.

The exhaustive and property tests replace hand-written case lists: they cover
every short input over a token alphabet and every truncation point of a sample
document, instead of a sample of them.
"""

import itertools
import json
import os
import random
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
from jsonx import (  # noqa: E402
    JSONCDecodeError,
    JSONRepairError,
    RepairReport,
    loads,
    repair,
)


def _json_value(rng, depth=0):
    kinds = ["int", "float", "str", "bool", "none"]
    if depth < 3:
        kinds += ["list", "dict"]
    kind = rng.choice(kinds)
    if kind == "int":
        return rng.randint(-(10**6), 10**6)
    if kind == "float":
        return rng.random() * 10**3
    if kind == "str":
        return "".join(rng.choice('ab"\\\n\té') for _ in range(rng.randrange(8)))
    if kind == "bool":
        return rng.choice([True, False])
    if kind == "none":
        return None
    if kind == "list":
        return [_json_value(rng, depth + 1) for _ in range(rng.randrange(4))]
    return {f"k{i}": _json_value(rng, depth + 1) for i in range(rng.randrange(4))}


DOC = json.dumps(
    {"items": [{"id": i, "name": f"n{i}"} for i in range(30)], "ok": True},
    separators=(",", ":"),
)


# ── Contract ─────────────────────────────────────────────────────────────────


def test_valid_json_is_returned_unchanged_with_a_clean_report():
    text = '{"a": [1, 2.5, "x", true, null]}'
    value, report = repair(text)
    assert value == json.loads(text)
    assert report.total == 0
    assert not report


def test_repair_accepts_bytes_and_counts_replaced_bytes():
    value, report = repair(b'{"a": 1, "b": "\xff"}')
    assert value["a"] == 1
    assert report.replaced_characters == 1
    assert "�" in value["b"]


def test_repair_rejects_other_types():
    with pytest.raises(TypeError):
        repair(42)


def test_nothing_recoverable_raises_and_carries_the_report():
    with pytest.raises(JSONRepairError) as info:
        repair("total garbage")
    assert isinstance(info.value.report, RepairReport)


def test_empty_input_raises():
    with pytest.raises(JSONRepairError):
        repair("")


def test_deep_nesting_raises_repair_error_not_recursion_error():
    with pytest.raises(JSONRepairError):
        repair("[" * 600)


def test_each_repair_kind_is_counted():
    cases = {
        '{"a": 1 "b": 2}': "missing_comma",
        '{"a" 1}': "missing_colon",
        '{"a": 1': "unclosed",
        '{"a": "x': "unterminated_string",
        '{"a": 1]': "stray_closer",
        '{"a": }': "missing_value",
        '{"a": @}': "skipped_token",
        '{"a": 1} tail': "trailing_garbage",
    }
    for text, kind in cases.items():
        _, report = repair(text)
        assert kind in report.counts, (text, report)


def test_comments_and_trailing_commas_are_tolerated():
    value, report = repair('{"a": 1, /* c */ "b": [1, 2,], // x\n "c": 3}')
    assert value == {"a": 1, "b": [1, 2], "c": 3}
    assert report.total == 0


# ── Real damaged bodies ──────────────────────────────────────────────────────

_FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures", "repair")
_REAL_DAMAGE = sorted(name for name in os.listdir(_FIXTURES) if name.endswith(".json"))


@pytest.mark.parametrize("name", _REAL_DAMAGE)
def test_real_damaged_body_is_recovered(name):
    with open(os.path.join(_FIXTURES, name), encoding="utf-8") as fp:
        text = fp.read()
    value, report = repair(text)
    assert isinstance(value, dict)
    assert len(value) == 2
    assert report.total > 0
    assert loads(text, repair=True) == value
    assert json.dumps(value, sort_keys=True)


# ── loads(repair=True) ───────────────────────────────────────────────────────


def test_loads_with_repair_recovers_a_damaged_document():
    assert loads('{"a": 1 "b": 2', repair=True) == {"a": 1, "b": 2}


def test_loads_without_repair_still_raises():
    with pytest.raises(JSONCDecodeError):
        loads('{"a": 1 "b": 2')


def test_loads_with_repair_still_parses_jsonc():
    assert loads('{"a": 1,}', repair=True) == {"a": 1}


def test_loads_with_repair_rejects_hooks():
    with pytest.raises(ValueError):
        loads("{}", repair=True, object_hook=lambda d: d)


def test_loads_with_repair_raises_repair_error_when_nothing_is_left():
    with pytest.raises(JSONRepairError):
        loads("garbage", repair=True)


# ── Bounded exhaustive check ─────────────────────────────────────────────────

_ALPHABET = '{}[]:,"a1 \\'


def test_every_short_input_either_repairs_or_raises_repair_error():
    seen_value = False
    for length in range(5):
        for chars in itertools.product(_ALPHABET, repeat=length):
            text = "".join(chars)
            try:
                value, report = repair(text)
            except JSONRepairError as exc:
                assert isinstance(exc.report, RepairReport)
                continue
            seen_value = True
            assert isinstance(report, RepairReport)
            # Whatever came back must be a value json can serialize: repair
            # never leaks a sentinel or a decoder-internal type.
            assert json.dumps(value) is not None
    assert seen_value


# ── Generated valid documents ────────────────────────────────────────────────


def test_repair_agrees_with_json_on_generated_valid_documents():
    rng = random.Random(20261128)
    for _ in range(300):
        obj = _json_value(rng)
        text = json.dumps(obj)
        value, report = repair(text)
        assert value == json.loads(text)
        assert report.total == 0


# ── Truncation: every prefix, not a sample ───────────────────────────────────


def _compatible(part, whole):
    """True when *part* is *whole*, or a truncated copy of it."""
    if isinstance(whole, str) and isinstance(part, str):
        return whole.startswith(part)
    if isinstance(whole, bool) or isinstance(part, bool) or part is None:
        return part == whole
    if isinstance(whole, int) and isinstance(part, int):
        return str(whole).startswith(str(part))
    if isinstance(whole, dict) and isinstance(part, dict):
        return all(k in whole and _compatible(v, whole[k]) for k, v in part.items())
    if isinstance(whole, list) and isinstance(part, list):
        return len(part) <= len(whole) and all(
            _compatible(p, w) for p, w in zip(part, whole)
        )
    return part == whole


def test_every_truncation_keeps_the_prefix_it_parsed():
    original = json.loads(DOC)["items"]
    for cut in range(1, len(DOC) + 1):
        value, _ = repair(DOC[:cut])
        assert isinstance(value, dict)
        items = value.get("items", [])
        assert len(items) <= len(original)
        for i, item in enumerate(items):
            # Only the element the cut lands in may be partial; the ones
            # before it are complete and identical.
            if i < len(items) - 1:
                assert item == original[i], (cut, i)
            else:
                assert _compatible(item, original[i]), (cut, item)


# ── Spliced documents: deletions keep the rest readable ──────────────────────


def _splice(text, rng, rate=0.01):
    out = []
    i = 0
    while i < len(text):
        if rng.random() < rate:
            i += rng.randint(1, 12)
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def test_spliced_documents_keep_most_elements_in_order():
    original = json.loads(DOC)["items"]
    ids = {item["id"] for item in original}
    rng = random.Random(7)
    kept = []
    for _ in range(40):
        value, _ = repair(_splice(DOC, rng))
        items = value.get("items", []) if isinstance(value, dict) else []
        got = [
            item["id"]
            for item in items
            if isinstance(item, dict) and isinstance(item.get("id"), int)
        ]
        # A splice can merge two elements, so ids may repeat or merge, but
        # every one of them must be an id that was in the document.
        assert all(i in ids for i in got), got
        kept.append(len(got))
    assert sum(kept) / len(kept) >= 0.7 * len(original), kept


def test_repair_output_round_trips_and_stays_stable():
    rng = random.Random(3)
    value, _ = repair(_splice(DOC, rng))
    once = json.dumps(value, sort_keys=True)
    again, report = repair(once)
    assert again == json.loads(once)
    assert report.total == 0
