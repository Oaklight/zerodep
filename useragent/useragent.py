# /// zerodep
# version = "0.1.1"
# deps = []
# tier = "simple"
# category = "network"
# note = "Install/update via: https://zerodep.readthedocs.io/en/latest/guide/cli/"
# ///

"""Lightweight User-Agent generator for Chrome/Edge with Client Hints.

Part of zerodep: https://github.com/Oaklight/zerodep
Copyright (c) 2026 Peng Ding. MIT License.

Generates realistic browser UA strings and matching ``Sec-CH-UA-*`` headers.
Covers Windows, macOS, Linux (desktop) and Android (mobile) platforms with
Chrome and Edge browsers only -- this is intentionally minimal.

Inspired by `ua-generator <https://github.com/iamdual/ua-generator>`_ (Apache-2.0).

Zero external dependencies -- stdlib ``random`` only.

Basic usage::

    from useragent import generate

    ua = generate(browser="chrome", device="desktop")
    print(ua.text)        # full User-Agent string
    print(ua.headers.get())  # dict with UA + Client Hints headers
"""

from __future__ import annotations

import random
from typing import Sequence, Union

__all__ = ["UserAgent", "generate"]

__version__ = "0.1.0"

# ---------------------------------------------------------------------------
# Version data
# ---------------------------------------------------------------------------

# (major, build) pairs.  Patch is randomised at generation time.
# Sources:
#   Chrome -- https://chromereleases.googleblog.com/search/label/Stable%20updates
#   Edge   -- https://learn.microsoft.com/en-us/deployedge/microsoft-edge-release-schedule

_CHROME_VERSIONS: list[tuple[int, int]] = [
    (120, 6099),
    (121, 6167),
    (122, 6261),
    (123, 6312),
    (124, 6367),
    (125, 6422),
    (126, 6478),
    (127, 6533),
    (128, 6613),
    (129, 6668),
    (130, 6723),
    (131, 6778),
    (132, 6834),
    (133, 6943),
    (134, 6998),
    (135, 7049),
    (136, 7103),
    (137, 7151),
    (138, 7204),
    (139, 7258),
    (140, 7339),
    (141, 7390),
    (142, 7444),
    (143, 7499),
    (144, 7559),
    (145, 7632),
    (146, 7680),
]

_EDGE_VERSIONS: list[tuple[int, int]] = [
    (120, 2210),
    (121, 2277),
    (122, 2365),
    (123, 2420),
    (124, 2478),
    (125, 2535),
    (126, 2592),
    (127, 2651),
    (128, 2739),
    (129, 2792),
    (130, 2849),
    (131, 2903),
    (132, 2957),
    (133, 3065),
    (134, 3124),
    (135, 3179),
    (136, 3240),
    (137, 3296),
    (138, 3351),
    (139, 3405),
    (140, 3485),
    (141, 3537),
    (142, 3595),
    (143, 3650),
    (144, 3719),
    (145, 3800),
    (146, 3856),
]

# Windows NT versions: (nt_major, nt_minor, ch_platform_range)
_WINDOWS_VERSIONS: list[tuple[float, tuple[int, int]]] = [
    (10.0, (1, 10)),  # Windows 10
    (10.0, (13, 16)),  # Windows 11
]

# macOS versions: (major, minor, max_build)
_MACOS_VERSIONS: list[tuple[int, int, int]] = [
    (13, 6, 9),
    (13, 7, 8),
    (14, 4, 1),
    (14, 5, 0),
    (14, 6, 1),
    (14, 7, 8),
    (14, 8, 4),
    (15, 0, 1),
    (15, 1, 1),
    (15, 2, 1),
    (15, 3, 1),
    (15, 4, 1),
    (15, 5, 0),
    (15, 6, 1),
    (15, 7, 4),
    (26, 0, 1),
    (26, 1, 0),
    (26, 2, 0),
    (26, 3, 2),
]

# Android model strings (Samsung subset -- most common vendor)
_ANDROID_MODELS: tuple[str, ...] = (
    "SM-G991B",
    "SM-G996B",
    "SM-G998B",
    "SM-A526B",
    "SM-A536B",
    "SM-S901B",
    "SM-S906B",
    "SM-S908B",
    "SM-S911B",
    "SM-S916B",
    "SM-S918B",
    "SM-S921B",
    "SM-S926B",
    "SM-S928B",
    "SM-A546B",
    "SM-A556B",
    "SM-A346B",
    "SM-A256B",
    "SM-A156B",
    "SM-G781B",
)

_DESKTOP_PLATFORMS = ("windows", "macos", "linux")
_MOBILE_PLATFORMS = ("android",)
_ALL_PLATFORMS = _DESKTOP_PLATFORMS + _MOBILE_PLATFORMS

_WEBKIT = "537.36"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _pick_chrome_version() -> tuple[int, int, int, int]:
    """Return (major, minor=0, build, patch)."""
    major, build = random.choice(_CHROME_VERSIONS)
    return (major, 0, build, random.randint(0, 255))


def _pick_edge_version() -> tuple[int, int, int, int]:
    major, build = random.choice(_EDGE_VERSIONS)
    return (major, 0, build, random.randint(0, 99))


def _fmt_ver(v: tuple[int, ...], n: int = 4, sep: str = ".") -> str:
    """Format version tuple to string, padding with 0s up to *n* parts."""
    parts = list(v[:n])
    while len(parts) < n:
        parts.append(0)
    return sep.join(str(p) for p in parts)


def _pick_platform(device: str | None) -> str:
    if device == "desktop":
        return random.choice(_DESKTOP_PLATFORMS)
    if device == "mobile":
        return random.choice(_MOBILE_PLATFORMS)
    return random.choice(_ALL_PLATFORMS)


def _build_ua_string(
    browser: str,
    platform: str,
    ver: tuple[int, int, int, int],
) -> str:
    """Build a User-Agent string from browser/platform/version."""
    chrome_str = _fmt_ver(ver)

    if platform == "windows":
        nt = random.choice(_WINDOWS_VERSIONS)
        nt_str = f"{nt[0]:.1f}".replace(".0", ".0")  # "10.0"
        base = (
            f"Mozilla/5.0 (Windows NT {nt_str}; Win64; x64) "
            f"AppleWebKit/{_WEBKIT} (KHTML, like Gecko) "
            f"Chrome/{chrome_str} Safari/{_WEBKIT}"
        )
        if browser == "edge":
            base += f" Edg/{chrome_str}"
        return base

    if platform == "linux":
        tpl = random.choice(
            (
                f"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/{_WEBKIT} "
                f"(KHTML, like Gecko) Chrome/{chrome_str} Safari/{_WEBKIT}",
                f"Mozilla/5.0 (X11; Ubuntu; Linux x86_64) AppleWebKit/{_WEBKIT} "
                f"(KHTML, like Gecko) Chrome/{chrome_str} Safari/{_WEBKIT}",
            )
        )
        if browser == "edge":
            tpl += f" Edg/{chrome_str}"
        return tpl

    if platform == "macos":
        mv = random.choice(_MACOS_VERSIONS)
        build = random.randint(0, mv[2]) if mv[2] > 0 else 0
        mac_str = f"{mv[0]}_{mv[1]}"
        if build:
            mac_str += f"_{build}"
        base = (
            f"Mozilla/5.0 (Macintosh; Intel Mac OS X {mac_str}) "
            f"AppleWebKit/{_WEBKIT} (KHTML, like Gecko) "
            f"Chrome/{chrome_str} Safari/{_WEBKIT}"
        )
        if browser == "edge":
            base += f" Edg/{chrome_str}"
        return base

    if platform == "android":
        android_ver = random.randint(12, 16)
        model = random.choice(_ANDROID_MODELS)
        base = (
            f"Mozilla/5.0 (Linux; Android {android_ver}; {model}) "
            f"AppleWebKit/{_WEBKIT} (KHTML, like Gecko) "
            f"Chrome/{chrome_str} Mobile Safari/{_WEBKIT}"
        )
        if browser == "edge":
            base += f" EdgA/{chrome_str}"
        return base

    raise ValueError(f"Unsupported platform: {platform}")


# ---------------------------------------------------------------------------
# Client Hints serialization
# ---------------------------------------------------------------------------


def _ch_bool(val: bool) -> str:
    return "?1" if val else "?0"


def _ch_string(val: str) -> str:
    return f'"{val}"'


def _ch_brand_list(brands: list[dict[str, str]]) -> str:
    return ", ".join(f'"{b["brand"]}";v="{b["version"]}"' for b in brands)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


class UserAgent:
    """A generated user-agent with matching Client Hints headers.

    Attributes:
        browser: Browser name (``"chrome"`` or ``"edge"``).
        platform: Platform name (``"windows"``, ``"macos"``, ``"linux"``,
            or ``"android"``).
        version: 4-tuple ``(major, minor, build, patch)``.
        text: The full User-Agent string.
        headers: A :class:`_Headers` instance for Client Hints.

    Example::

        ua = generate(browser=["chrome", "edge"])
        ua.headers.accept_ch("Sec-CH-UA-Platform-Version")
        headers = ua.headers.get()
    """

    def __init__(
        self,
        *,
        browser: str,
        platform: str,
        version: tuple[int, int, int, int],
        ua_string: str,
    ) -> None:
        self.browser = browser
        self.platform = platform
        self.version = version
        self.text = ua_string
        self.headers = _Headers(self)

    # -- Client Hints data methods --

    def _is_mobile(self) -> bool:
        return self.platform in _MOBILE_PLATFORMS

    def _ch_platform_name(self) -> str:
        mapping = {
            "windows": "Windows",
            "macos": "macOS",
            "linux": "Linux",
            "android": "Android",
        }
        return mapping.get(self.platform, self.platform.title())

    def _ch_platform_version(self) -> str:
        if self.platform == "windows":
            lo, hi = random.choice(_WINDOWS_VERSIONS)[1]
            return f"{random.randint(lo, hi)}.0.0"
        if self.platform == "macos":
            mv = random.choice(_MACOS_VERSIONS)
            return f"{mv[0]}.{mv[1]}.{random.randint(0, max(mv[2], 1))}"
        if self.platform == "android":
            return f"{random.randint(12, 16)}.0.0"
        # Linux
        return ""

    def _ch_brands(self, full_version: bool = False) -> list[dict[str, str]]:
        ver_str = _fmt_ver(self.version) if full_version else str(self.version[0])
        filler_ver = "99.0.0.0" if full_version else "99"
        brands: list[dict[str, str]] = [{"brand": "Not A(Brand", "version": filler_ver}]
        if self.browser == "chrome":
            brands.append({"brand": "Chromium", "version": ver_str})
            brands.append({"brand": "Google Chrome", "version": ver_str})
        elif self.browser == "edge":
            brands.append({"brand": "Chromium", "version": ver_str})
            brands.append({"brand": "Microsoft Edge", "version": ver_str})
        return brands

    def _ch_architecture(self) -> str:
        if self.platform in ("android",):
            return "arm"
        if self.platform == "macos":
            return random.choice(("arm", "x86", "arm", "arm"))
        return "x86"

    def _ch_bitness(self) -> str:
        if self.platform == "android":
            return random.choice(("32", "64", "32", "32"))
        return "64"

    def _ch_model(self) -> str:
        if self.platform == "android":
            return random.choice(_ANDROID_MODELS)
        return ""

    def __str__(self) -> str:
        return self.text

    def __repr__(self) -> str:
        return f"UserAgent(browser={self.browser!r}, platform={self.platform!r})"


class _Headers:
    """Lazy header builder matching the ``ua_generator.Headers`` interface."""

    def __init__(self, ua: UserAgent) -> None:
        self._ua = ua
        self._headers: dict[str, str] = {}
        self._initialised = False

    def _reset(self) -> None:
        self._initialised = True
        self._headers = {"user-agent": self._ua.text}
        # Low-entropy hints (always included for Chromium)
        self._add("sec-ch-ua")
        self._add("sec-ch-ua-mobile")
        self._add("sec-ch-ua-platform")

    def _add(self, key: str) -> None:
        ua = self._ua
        if key == "sec-ch-ua":
            self._headers[key] = _ch_brand_list(ua._ch_brands(full_version=False))
        elif key == "sec-ch-ua-full-version-list":
            self._headers[key] = _ch_brand_list(ua._ch_brands(full_version=True))
        elif key == "sec-ch-ua-platform":
            self._headers[key] = _ch_string(ua._ch_platform_name())
        elif key == "sec-ch-ua-platform-version":
            self._headers[key] = _ch_string(ua._ch_platform_version())
        elif key == "sec-ch-ua-mobile":
            self._headers[key] = _ch_bool(ua._is_mobile())
        elif key == "sec-ch-ua-arch":
            self._headers[key] = _ch_string(ua._ch_architecture())
        elif key == "sec-ch-ua-bitness":
            self._headers[key] = _ch_string(ua._ch_bitness())
        elif key == "sec-ch-ua-model":
            self._headers[key] = _ch_string(ua._ch_model())

    def accept_ch(self, val: str) -> None:
        """Process an ``Accept-CH`` header value and populate matching hints.

        Args:
            val: Comma-separated list of hint names
                (e.g. ``"Sec-CH-UA-Platform-Version, Sec-CH-UA-Arch"``).
        """
        self._reset()
        for hint in val.split(","):
            self._add(hint.strip().lower())

    def get(self) -> dict[str, str]:
        """Return all generated headers as a dict."""
        if not self._initialised:
            self._reset()
        return self._headers


def generate(
    *,
    browser: Union[str, Sequence[str]] | None = None,
    device: str | None = None,
) -> UserAgent:
    """Generate a random User-Agent with matching Client Hints.

    Args:
        browser: Browser name or list of names to pick from.
            Supported: ``"chrome"``, ``"edge"``. Defaults to both.
        device: Device type -- ``"desktop"`` or ``"mobile"``.
            Defaults to random selection across all platforms.

    Returns:
        A :class:`UserAgent` instance.

    Raises:
        ValueError: If *browser* is not ``"chrome"`` or ``"edge"``.
    """
    # Resolve browser
    if browser is None:
        chosen_browser = random.choice(("chrome", "edge"))
    elif isinstance(browser, str):
        chosen_browser = browser
    else:
        chosen_browser = random.choice(list(browser))

    if chosen_browser not in ("chrome", "edge"):
        raise ValueError(f"Unsupported browser: {chosen_browser!r}")

    # Resolve platform
    platform = _pick_platform(device)

    # Pick version
    if chosen_browser == "chrome":
        ver = _pick_chrome_version()
    else:
        ver = _pick_edge_version()

    ua_string = _build_ua_string(chosen_browser, platform, ver)
    return UserAgent(
        browser=chosen_browser, platform=platform, version=ver, ua_string=ua_string
    )
