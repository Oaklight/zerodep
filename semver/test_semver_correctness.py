"""Correctness tests: zerodep semver vs packaging.version.

Compares our PEP 440 parser against the reference ``packaging`` library
to ensure behavioural parity for parsing, comparison, normalisation,
and property access.
"""

from __future__ import annotations

import os
import sys

import pytest

try:
    from packaging.version import InvalidVersion as PkgInvalidVersion
    from packaging.version import Version as PkgVersion
except ImportError:
    pytest.skip("packaging not installed", allow_module_level=True)

sys.path.insert(0, os.path.dirname(__file__))
from semver import InvalidVersion, Version, version_parse  # noqa: E402


# ── Helpers ──────────────────────────────────────────────────────────


def assert_same(version_str: str) -> None:
    """Assert that our Version matches packaging's for a given string."""
    ours = Version(version_str)
    theirs = PkgVersion(version_str)
    assert str(ours) == str(theirs), f"str mismatch for {version_str!r}"
    assert ours.is_prerelease == theirs.is_prerelease, (
        f"is_prerelease mismatch for {version_str!r}"
    )
    assert ours.is_devrelease == theirs.is_devrelease, (
        f"is_devrelease mismatch for {version_str!r}"
    )
    assert ours.is_postrelease == theirs.is_postrelease, (
        f"is_postrelease mismatch for {version_str!r}"
    )


# ── Test classes ─────────────────────────────────────────────────────


class TestParsing:
    """Basic version string parsing."""

    @pytest.mark.parametrize(
        "v",
        [
            "1.0",
            "1.0.0",
            "1.2.3",
            "0.0.1",
            "10.20.30",
            "1.0.0.0.0",
        ],
    )
    def test_simple_releases(self, v: str) -> None:
        assert_same(v)

    @pytest.mark.parametrize("v", ["1!1.0", "2!1.2.3", "0!1.0"])
    def test_epoch(self, v: str) -> None:
        assert_same(v)

    @pytest.mark.parametrize(
        "v",
        [
            "1.0a1",
            "1.0b2",
            "1.0rc1",
            "1.0alpha1",
            "1.0beta2",
            "1.0preview1",
            "1.0c1",
            "1.0pre1",
        ],
    )
    def test_pre_release(self, v: str) -> None:
        assert_same(v)

    @pytest.mark.parametrize("v", ["1.0.post1", "1.0.post0", "1.0-1"])
    def test_post_release(self, v: str) -> None:
        assert_same(v)

    @pytest.mark.parametrize("v", ["1.0.dev0", "1.0.dev5", "1.0a1.dev1"])
    def test_dev_release(self, v: str) -> None:
        assert_same(v)

    @pytest.mark.parametrize("v", ["1.0+local", "1.0+local.1", "1.0+abc.123"])
    def test_local_version(self, v: str) -> None:
        assert_same(v)


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

    def test_ordering_matches_packaging(self) -> None:
        ours = [Version(v) for v in self.ORDERED]
        theirs = [PkgVersion(v) for v in self.ORDERED]
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


class TestPrerelease:
    """is_prerelease property."""

    @pytest.mark.parametrize(
        "v",
        ["1.0a1", "1.0b1", "1.0rc1", "1.0.dev1", "1.0a1.dev0"],
    )
    def test_is_prerelease(self, v: str) -> None:
        assert Version(v).is_prerelease is True

    @pytest.mark.parametrize(
        "v",
        ["1.0", "1.0.post1", "1.0.post0"],
    )
    def test_is_not_prerelease(self, v: str) -> None:
        assert Version(v).is_prerelease is False


class TestDevrelease:
    """is_devrelease property."""

    @pytest.mark.parametrize("v", ["1.0.dev0", "1.0.dev5", "1.0a1.dev1"])
    def test_is_devrelease(self, v: str) -> None:
        assert Version(v).is_devrelease is True

    @pytest.mark.parametrize(
        "v",
        ["1.0", "1.0a1", "1.0b1", "1.0rc1", "1.0.post1"],
    )
    def test_is_not_devrelease(self, v: str) -> None:
        assert Version(v).is_devrelease is False


class TestStringNormalization:
    """str() output matches packaging's canonical form."""

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("1.0", "1.0"),
            ("1.0.0", "1.0.0"),
            ("1.0alpha1", "1.0a1"),
            ("1.0beta2", "1.0b2"),
            ("1.0preview1", "1.0rc1"),
            ("1.0c1", "1.0rc1"),
            ("1.0pre1", "1.0rc1"),
            ("1.0-1", "1.0.post1"),
            ("1.0.rev2", "1.0.post2"),
            ("v1.0", "1.0"),
            ("  1.0  ", "1.0"),
        ],
    )
    def test_normalization(self, raw: str, expected: str) -> None:
        assert str(Version(raw)) == expected
        assert str(Version(raw)) == str(PkgVersion(raw))


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
