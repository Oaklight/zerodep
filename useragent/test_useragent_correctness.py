"""Correctness tests for the useragent module."""

from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))

from useragent import UserAgent, _fmt_ver, generate

# ---------------------------------------------------------------------------
# generate() — basic API
# ---------------------------------------------------------------------------


class TestGenerate:
    def test_returns_useragent(self):
        ua = generate()
        assert isinstance(ua, UserAgent)

    def test_browser_chrome(self):
        ua = generate(browser="chrome")
        assert ua.browser == "chrome"

    def test_browser_edge(self):
        ua = generate(browser="edge")
        assert ua.browser == "edge"

    def test_browser_list(self):
        ua = generate(browser=["chrome"])
        assert ua.browser == "chrome"
        ua = generate(browser=["edge"])
        assert ua.browser == "edge"

    def test_browser_list_multiple(self):
        browsers_seen: set[str] = set()
        for _ in range(200):
            ua = generate(browser=["chrome", "edge"])
            browsers_seen.add(ua.browser)
        assert browsers_seen == {"chrome", "edge"}

    def test_browser_default_covers_both(self):
        browsers_seen: set[str] = set()
        for _ in range(200):
            ua = generate()
            browsers_seen.add(ua.browser)
        assert browsers_seen == {"chrome", "edge"}

    def test_browser_invalid(self):
        import pytest

        with pytest.raises(ValueError, match="Unsupported browser"):
            generate(browser="firefox")

    def test_device_desktop(self):
        for _ in range(50):
            ua = generate(device="desktop")
            assert ua.platform in ("windows", "macos", "linux")

    def test_device_mobile(self):
        for _ in range(50):
            ua = generate(device="mobile")
            assert ua.platform == "android"

    def test_device_default_covers_all(self):
        platforms_seen: set[str] = set()
        for _ in range(500):
            ua = generate()
            platforms_seen.add(ua.platform)
        assert platforms_seen == {"windows", "macos", "linux", "android"}


# ---------------------------------------------------------------------------
# UserAgent — attributes
# ---------------------------------------------------------------------------


class TestUserAgentAttributes:
    def test_version_tuple(self):
        ua = generate(browser="chrome")
        assert isinstance(ua.version, tuple)
        assert len(ua.version) == 4
        assert all(isinstance(v, int) for v in ua.version)

    def test_version_range_chrome(self):
        ua = generate(browser="chrome")
        assert 120 <= ua.version[0] <= 146
        assert ua.version[1] == 0
        assert 0 <= ua.version[3] <= 255

    def test_version_range_edge(self):
        ua = generate(browser="edge")
        assert 120 <= ua.version[0] <= 146
        assert ua.version[1] == 0
        assert 0 <= ua.version[3] <= 99

    def test_text_is_string(self):
        ua = generate()
        assert isinstance(ua.text, str)
        assert len(ua.text) > 50

    def test_str_equals_text(self):
        ua = generate()
        assert str(ua) == ua.text

    def test_repr(self):
        ua = generate(browser="chrome")
        r = repr(ua)
        assert "UserAgent" in r
        assert "chrome" in r


# ---------------------------------------------------------------------------
# UA string format
# ---------------------------------------------------------------------------


class TestUAStringFormat:
    def test_chrome_windows(self):
        for _ in range(20):
            ua = generate(browser="chrome", device="desktop")
            if ua.platform == "windows":
                assert "Windows NT 10.0" in ua.text
                assert "Chrome/" in ua.text
                assert "Safari/537.36" in ua.text
                assert "Edg/" not in ua.text
                break

    def test_edge_windows(self):
        for _ in range(20):
            ua = generate(browser="edge", device="desktop")
            if ua.platform == "windows":
                assert "Windows NT 10.0" in ua.text
                assert "Chrome/" in ua.text
                assert "Edg/" in ua.text
                break

    def test_chrome_macos(self):
        for _ in range(20):
            ua = generate(browser="chrome", device="desktop")
            if ua.platform == "macos":
                assert "Macintosh" in ua.text
                assert "Intel Mac OS X" in ua.text
                assert "Chrome/" in ua.text
                assert "Edg/" not in ua.text
                break

    def test_chrome_linux(self):
        for _ in range(20):
            ua = generate(browser="chrome", device="desktop")
            if ua.platform == "linux":
                assert "X11" in ua.text
                assert "Linux x86_64" in ua.text
                assert "Chrome/" in ua.text
                break

    def test_edge_linux_has_edg(self):
        for _ in range(20):
            ua = generate(browser="edge", device="desktop")
            if ua.platform == "linux":
                assert "Edg/" in ua.text
                break

    def test_chrome_android(self):
        ua = generate(browser="chrome", device="mobile")
        assert ua.platform == "android"
        assert "Android" in ua.text
        assert "Mobile" in ua.text
        assert "SM-" in ua.text
        assert "EdgA/" not in ua.text

    def test_edge_android(self):
        ua = generate(browser="edge", device="mobile")
        assert "EdgA/" in ua.text

    def test_version_in_ua_string(self):
        ua = generate(browser="chrome")
        ver_str = _fmt_ver(ua.version)
        assert f"Chrome/{ver_str}" in ua.text


# ---------------------------------------------------------------------------
# Headers — default (no accept_ch)
# ---------------------------------------------------------------------------


class TestHeadersDefault:
    def test_default_headers_keys(self):
        ua = generate(browser="chrome")
        h = ua.headers.get()
        assert "user-agent" in h
        assert "sec-ch-ua" in h
        assert "sec-ch-ua-mobile" in h
        assert "sec-ch-ua-platform" in h

    def test_default_no_high_entropy(self):
        ua = generate()
        h = ua.headers.get()
        assert "sec-ch-ua-platform-version" not in h
        assert "sec-ch-ua-arch" not in h
        assert "sec-ch-ua-bitness" not in h
        assert "sec-ch-ua-model" not in h

    def test_user_agent_matches_text(self):
        ua = generate()
        h = ua.headers.get()
        assert h["user-agent"] == ua.text

    def test_mobile_hint_desktop(self):
        ua = generate(browser="chrome", device="desktop")
        h = ua.headers.get()
        assert h["sec-ch-ua-mobile"] == "?0"

    def test_mobile_hint_mobile(self):
        ua = generate(browser="chrome", device="mobile")
        h = ua.headers.get()
        assert h["sec-ch-ua-mobile"] == "?1"


# ---------------------------------------------------------------------------
# Headers — sec-ch-ua brand list
# ---------------------------------------------------------------------------


class TestBrandList:
    def test_chrome_brands(self):
        ua = generate(browser="chrome")
        h = ua.headers.get()
        ch_ua = h["sec-ch-ua"]
        assert "Google Chrome" in ch_ua
        assert "Chromium" in ch_ua
        assert "Not A(Brand" in ch_ua

    def test_edge_brands(self):
        ua = generate(browser="edge")
        h = ua.headers.get()
        ch_ua = h["sec-ch-ua"]
        assert "Microsoft Edge" in ch_ua
        assert "Chromium" in ch_ua
        assert "Google Chrome" not in ch_ua

    def test_platform_hint_values(self):
        mapping = {
            "windows": '"Windows"',
            "macos": '"macOS"',
            "linux": '"Linux"',
            "android": '"Android"',
        }
        for _ in range(200):
            ua = generate()
            h = ua.headers.get()
            expected = mapping[ua.platform]
            assert h["sec-ch-ua-platform"] == expected


# ---------------------------------------------------------------------------
# Headers — accept_ch (high-entropy hints)
# ---------------------------------------------------------------------------


class TestAcceptCH:
    def test_accept_ch_platform_version(self):
        ua = generate(browser="chrome")
        ua.headers.accept_ch("Sec-CH-UA-Platform-Version")
        h = ua.headers.get()
        assert "sec-ch-ua-platform-version" in h
        # Value is quoted string with version-like content
        val = h["sec-ch-ua-platform-version"]
        assert val.startswith('"')
        assert val.endswith('"')

    def test_accept_ch_full_version_list(self):
        ua = generate(browser="chrome")
        ua.headers.accept_ch("Sec-CH-UA-Full-Version-List")
        h = ua.headers.get()
        val = h["sec-ch-ua-full-version-list"]
        # Full version list has x.y.z.w format
        assert re.search(r"\d+\.\d+\.\d+\.\d+", val)

    def test_accept_ch_arch(self):
        ua = generate(browser="chrome", device="desktop")
        ua.headers.accept_ch("Sec-CH-UA-Arch")
        h = ua.headers.get()
        arch = h["sec-ch-ua-arch"]
        assert arch in ('"x86"', '"arm"')

    def test_accept_ch_bitness(self):
        ua = generate(browser="chrome", device="desktop")
        ua.headers.accept_ch("Sec-CH-UA-Bitness")
        h = ua.headers.get()
        assert h["sec-ch-ua-bitness"] == '"64"'

    def test_accept_ch_bitness_mobile(self):
        ua = generate(browser="chrome", device="mobile")
        ua.headers.accept_ch("Sec-CH-UA-Bitness")
        h = ua.headers.get()
        assert h["sec-ch-ua-bitness"] in ('"32"', '"64"')

    def test_accept_ch_model_desktop(self):
        ua = generate(browser="chrome", device="desktop")
        ua.headers.accept_ch("Sec-CH-UA-Model")
        h = ua.headers.get()
        assert h["sec-ch-ua-model"] == '""'

    def test_accept_ch_model_mobile(self):
        ua = generate(browser="chrome", device="mobile")
        ua.headers.accept_ch("Sec-CH-UA-Model")
        h = ua.headers.get()
        model = h["sec-ch-ua-model"]
        assert model.startswith('"SM-')

    def test_accept_ch_multiple(self):
        ua = generate(browser="chrome")
        ua.headers.accept_ch(
            "Sec-CH-UA-Platform-Version, Sec-CH-UA-Arch, Sec-CH-UA-Bitness"
        )
        h = ua.headers.get()
        assert "sec-ch-ua-platform-version" in h
        assert "sec-ch-ua-arch" in h
        assert "sec-ch-ua-bitness" in h

    def test_accept_ch_resets_headers(self):
        ua = generate(browser="chrome")
        ua.headers.get()
        # accept_ch resets and rebuilds
        ua.headers.accept_ch("Sec-CH-UA-Arch")
        h2 = ua.headers.get()
        # Low-entropy hints still present after reset
        assert "sec-ch-ua" in h2
        assert "sec-ch-ua-mobile" in h2
        assert "sec-ch-ua-platform" in h2
        assert "sec-ch-ua-arch" in h2

    def test_accept_ch_unknown_hint_ignored(self):
        ua = generate(browser="chrome")
        ua.headers.accept_ch("Sec-CH-UA-Nonexistent")
        h = ua.headers.get()
        assert "sec-ch-ua-nonexistent" not in h


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class TestFmtVer:
    def test_four_parts(self):
        assert _fmt_ver((1, 2, 3, 4)) == "1.2.3.4"

    def test_padding(self):
        assert _fmt_ver((1,)) == "1.0.0.0"
        assert _fmt_ver((1, 2)) == "1.2.0.0"

    def test_custom_n(self):
        assert _fmt_ver((1, 2, 3, 4), n=2) == "1.2"

    def test_custom_sep(self):
        assert _fmt_ver((1, 2, 3, 4), sep="-") == "1-2-3-4"


# ---------------------------------------------------------------------------
# Determinism with seed
# ---------------------------------------------------------------------------


class TestDeterminism:
    def test_seeded_reproducibility(self):
        import random

        random.seed(42)
        ua1 = generate(browser="chrome", device="desktop")

        random.seed(42)
        ua2 = generate(browser="chrome", device="desktop")

        assert ua1.text == ua2.text
        assert ua1.browser == ua2.browser
        assert ua1.platform == ua2.platform
        assert ua1.version == ua2.version
