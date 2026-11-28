"""Correctness tests: zerodep semver vs packaging.version.

Compares our PEP 440 parser against the reference ``packaging`` library.
The version corpus is generated from a bounded grammar (epoch × release ×
pre × post × dev × local) instead of a hand-written list, so parity is
checked over every combination in the grammar rather than selected samples.
"""

from __future__ import annotations

import itertools
import os
import sys

import pytest

try:
    from packaging.version import InvalidVersion as PkgInvalidVersion
    from packaging.version import Version as PkgVersion
except ImportError:
    pytest.skip("packaging not installed", allow_module_level=True)

sys.path.insert(0, os.path.dirname(__file__))
from semver import InvalidVersion, Version, version_parse  # noqa: E402, I001


# ── Helpers ──────────────────────────────────────────────────────────


def _parity_error(version_str: str) -> list[tuple[str, object, object]] | None:
    """Return the fields where our Version disagrees with packaging, if any."""
    ours = Version(version_str)
    theirs = PkgVersion(version_str)
    pairs = [
        ("str", str(ours), str(theirs)),
        ("is_prerelease", ours.is_prerelease, theirs.is_prerelease),
        ("is_devrelease", ours.is_devrelease, theirs.is_devrelease),
        ("is_postrelease", ours.is_postrelease, theirs.is_postrelease),
    ]
    mismatches = [pair for pair in pairs if pair[1] != pair[2]]
    return mismatches or None


def assert_same(version_str: str) -> None:
    """Assert that our Version matches packaging's for a given string."""
    mismatches = _parity_error(version_str)
    assert not mismatches, f"parity mismatch for {version_str!r}: {mismatches!r}"


# ── Generated corpus ─────────────────────────────────────────────────

_RELEASES = ("1.0", "1.2.3", "0.0.1", "10.20.30")
_EPOCHS = ("", "1!", "2!")
_PRES = ("", "a1", "rc1")
_POSTS = ("", ".post1")
_DEVS = ("", ".dev0")
_LOCALS = ("", "+local", "+abc.123")


def _generated_versions() -> list[str]:
    """Every combination of the bounded PEP 440 grammar."""
    return [
        f"{epoch}{release}{pre}{post}{dev}{local}"
        for epoch, release, pre, post, dev, local in itertools.product(
            _EPOCHS, _RELEASES, _PRES, _POSTS, _DEVS, _LOCALS
        )
    ]


def _generated_aliases() -> list[tuple[str, str]]:
    """Non-canonical spellings paired with their canonical form."""
    cases: list[tuple[str, str]] = []

    pre_aliases = {
        "alpha": "a",
        "beta": "b",
        "preview": "rc",
        "pre": "rc",
        "c": "rc",
    }
    for alias, canonical in pre_aliases.items():
        for number in (1, 2, 3):
            cases.append((f"1.0{alias}{number}", f"1.0{canonical}{number}"))

    for number in (1, 2):
        cases.append((f"1.0-{number}", f"1.0.post{number}"))
        cases.append((f"1.0rev{number}", f"1.0.post{number}"))
        cases.append((f"1.0.r{number}", f"1.0.post{number}"))

    cases.extend(
        [
            ("v1.0", "1.0"),
            ("  1.0  ", "1.0"),
            ("1.0.0", "1.0.0"),
            # Golden values pin the contract independently of packaging.
            ("1.0alpha1", "1.0a1"),
            ("1.0preview1", "1.0rc1"),
        ]
    )
    return cases


# ── Test classes ─────────────────────────────────────────────────────


class TestParsing:
    def test_generated_versions_match_packaging(self):
        mismatches = []
        for version in _generated_versions():
            error = _parity_error(version)
            if error:
                mismatches.append((version, error))
        assert not mismatches, f"parity mismatches: {mismatches!r}"


class TestOrdering:
    """PEP 440 ordering: dev < alpha < beta < rc < release < post."""

    ORDERED = [
        "1.0.dev0",
        "1.0.dev1",
        "1.0a1.dev0",
        "1.0a1",
        "1.0a2",
        "1.0b1",
        "1.0b2",
        "1.0rc1",
        "1.0rc2",
        "1.0",
        "1.0.post0",
        "1.0.post1",
    ]

    def test_full_ordering(self) -> None:
        parsed = [Version(v) for v in self.ORDERED]
        for i in range(len(parsed)):
            for j in range(i + 1, len(parsed)):
                assert parsed[i] < parsed[j], (
                    f"Expected {self.ORDERED[i]} < {self.ORDERED[j]}"
                )

    def test_generated_order_matches_packaging(self) -> None:
        versions = _generated_versions()
        ours = [Version(v) for v in versions]
        theirs = [PkgVersion(v) for v in versions]
        assert [str(v) for v in sorted(ours)] == [str(v) for v in sorted(theirs)]

    def test_epoch_trumps_release(self) -> None:
        assert Version("1!0.1") > Version("999.999")

    def test_post_after_release(self) -> None:
        assert Version("1.0.post1") > Version("1.0")

    def test_dev_before_release(self) -> None:
        assert Version("1.0.dev1") < Version("1.0")


class TestComparison:
    """Comparison operators and built-in functions."""

    def test_equal(self) -> None:
        assert Version("1.0") == Version("1.0")
        assert Version("1.0.0") == Version("1.0")

    def test_not_equal(self) -> None:
        assert Version("1.0") != Version("2.0")

    def test_gt(self) -> None:
        assert Version("2.0") > Version("1.0")

    def test_gte(self) -> None:
        assert Version("1.0") >= Version("1.0")
        assert Version("2.0") >= Version("1.0")

    def test_lt(self) -> None:
        assert Version("1.0") < Version("2.0")

    def test_lte(self) -> None:
        assert Version("1.0") <= Version("1.0")
        assert Version("1.0") <= Version("2.0")

    def test_max(self) -> None:
        versions = [Version("1.0"), Version("3.0"), Version("2.0")]
        assert max(versions) == Version("3.0")

    def test_min(self) -> None:
        versions = [Version("1.0"), Version("3.0"), Version("2.0")]
        assert min(versions) == Version("1.0")

    def test_sorted(self) -> None:
        raw = ["3.0", "1.0", "2.0b1", "2.0"]
        assert [str(v) for v in sorted(Version(x) for x in raw)] == [
            "1.0",
            "2.0b1",
            "2.0",
            "3.0",
        ]

    def test_not_implemented_for_non_version(self) -> None:
        v = Version("1.0")
        assert v.__eq__("1.0") is NotImplemented
        assert v.__lt__("1.0") is NotImplemented


class TestStringNormalization:
    """str() output matches packaging's canonical form."""

    def test_generated_aliases(self):
        mismatches = []
        for raw, expected in _generated_aliases():
            got = str(Version(raw))
            if got != expected or got != str(PkgVersion(raw)):
                mismatches.append((raw, expected, got, str(PkgVersion(raw))))
        assert not mismatches, f"normalization mismatches: {mismatches!r}"


class TestInvalidVersion:
    """Unparseable strings should raise InvalidVersion."""

    @pytest.mark.parametrize(
        "v",
        [
            "not a version",
            "1.0.0.0.0.0.0.0lol",
            "",
            "french toast",
            "1.0.0.0.0.0.0.0.0.z.1",
        ],
    )
    def test_invalid(self, v: str) -> None:
        with pytest.raises(InvalidVersion):
            Version(v)
        with pytest.raises(PkgInvalidVersion):
            PkgVersion(v)


class TestHash:
    """Hash behaviour."""

    def test_equal_versions_same_hash(self) -> None:
        assert hash(Version("1.0")) == hash(Version("1.0"))
        assert hash(Version("1.0.0")) == hash(Version("1.0"))

    def test_usable_as_dict_key(self) -> None:
        d: dict[Version, str] = {Version("1.0"): "one"}
        assert d[Version("1.0")] == "one"
        assert d[Version("1.0.0")] == "one"

    def test_usable_in_set(self) -> None:
        s = {Version("1.0"), Version("1.0.0"), Version("2.0")}
        assert len(s) == 2


class TestProperties:
    """Property accessors."""

    def test_epoch(self) -> None:
        assert Version("1.0").epoch == 0
        assert Version("2!1.0").epoch == 2

    def test_release(self) -> None:
        assert Version("1.2.3").release == (1, 2, 3)

    def test_pre(self) -> None:
        assert Version("1.0a1").pre == ("a", 1)
        assert Version("1.0").pre is None

    def test_post(self) -> None:
        assert Version("1.0.post2").post == 2
        assert Version("1.0").post is None

    def test_dev(self) -> None:
        assert Version("1.0.dev3").dev == 3
        assert Version("1.0").dev is None

    def test_local(self) -> None:
        assert Version("1.0+local.1").local == "local.1"
        assert Version("1.0").local is None

    def test_major_minor_micro(self) -> None:
        v = Version("1.2.3")
        assert v.major == 1
        assert v.minor == 2
        assert v.micro == 3

    def test_major_only(self) -> None:
        v = Version("5")
        assert v.major == 5
        assert v.minor == 0
        assert v.micro == 0

    def test_base_version(self) -> None:
        assert Version("1.0a1.dev2+local").base_version == "1.0"
        assert Version("2!3.4.5").base_version == "2!3.4.5"

    def test_public(self) -> None:
        assert Version("1.0+local").public == "1.0"
        assert Version("1.0a1.dev2+local").public == "1.0a1.dev2"

    def test_is_postrelease(self) -> None:
        assert Version("1.0.post1").is_postrelease is True
        assert Version("1.0").is_postrelease is False


class TestVersionParse:
    """version_parse() convenience function."""

    def test_basic(self) -> None:
        v = version_parse("1.2.3")
        assert isinstance(v, Version)
        assert str(v) == "1.2.3"

    def test_invalid_raises(self) -> None:
        with pytest.raises(InvalidVersion):
            version_parse("not valid")


class TestEdgeCases:
    """Edge cases and regression tests."""

    def test_leading_v(self) -> None:
        assert str(Version("v1.0")) == "1.0"
        assert Version("v1.0") == Version("1.0")

    def test_whitespace(self) -> None:
        assert str(Version("  1.0  ")) == "1.0"

    def test_zero_epoch(self) -> None:
        # 0! is valid but should not appear in canonical form
        assert str(Version("0!1.0")) == "1.0"

    def test_repr(self) -> None:
        assert repr(Version("1.0")) == "<Version('1.0')>"

    def test_deeply_nested_release(self) -> None:
        v = Version("1.2.3.4.5.6")
        assert v.release == (1, 2, 3, 4, 5, 6)
        assert str(v) == "1.2.3.4.5.6"

    def test_implicit_pre_number(self) -> None:
        # "1.0a" should be treated as "1.0a0"
        assert str(Version("1.0a")) == "1.0a0"
        assert str(Version("1.0a")) == str(PkgVersion("1.0a"))

    def test_local_with_mixed_segments(self) -> None:
        v = Version("1.0+abc.123.def")
        assert v.local == "abc.123.def"
