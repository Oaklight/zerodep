"""Benchmark: zerodep readability vs readability-lxml vs Mozilla JS."""

import json
import os
import shutil
import subprocess
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from readability import extract, is_probably_readable  # noqa: E402

# ── readability-lxml reference ──

try:
    from importlib.metadata import version as _pkg_version

    _pkg_version("readability-lxml")
    _HAS_REFERENCE = True
except Exception:
    _HAS_REFERENCE = False


def _load_reference_document_class():
    """Load readability-lxml's Document class, working around name clash."""
    import importlib

    saved_path = sys.path[:]
    saved_modules = {
        k: sys.modules.pop(k)
        for k in list(sys.modules)
        if k == "readability" or k.startswith("readability.")
    }
    try:
        this_dir = os.path.dirname(__file__)
        this_abs = os.path.abspath(this_dir)
        sys.path = [p for p in sys.path if os.path.abspath(p) != this_abs]
        mod = importlib.import_module("readability")
        return mod.Document
    finally:
        sys.path = saved_path
        for k in list(sys.modules):
            if k == "readability" or k.startswith("readability."):
                del sys.modules[k]
        sys.modules.update(saved_modules)


if _HAS_REFERENCE:
    _RefDocument = _load_reference_document_class()
else:
    _RefDocument = None


# ── Test data: Mozilla fixtures by size tier ──

_TEST_PAGES_DIR = os.path.join(os.path.dirname(__file__), "test-pages")


def _load_source(name: str) -> str:
    """Load source HTML for a fixture."""
    path = os.path.join(_TEST_PAGES_DIR, name, "source.html")
    with open(path, encoding="utf-8") as f:
        return f.read()


# Categorize fixtures by source HTML size.
_SMALL_FIXTURES = ["rtl-1", "basic-tags-cleaning", "003-metadata-preferred"]
_MEDIUM_FIXTURES = ["001", "ars-1"]
_LARGE_FIXTURES = ["cnn", "bbc-1", "guardian-1"]

# Preload HTML to avoid I/O during benchmarks.
_FIXTURE_CACHE: dict[str, str] = {}


def _get_fixture(name: str) -> str:
    """Get cached fixture HTML."""
    if name not in _FIXTURE_CACHE:
        _FIXTURE_CACHE[name] = _load_source(name)
    return _FIXTURE_CACHE[name]


def _pick_available(names: list[str]) -> str | None:
    """Return the first available fixture name, or None."""
    for name in names:
        path = os.path.join(_TEST_PAGES_DIR, name, "source.html")
        if os.path.isfile(path):
            return name
    return None


# ── Benchmark helpers ──


def _zd_extract(html: str) -> None:
    extract(html)


def _zd_is_readable(html: str) -> None:
    is_probably_readable(html)


def _ref_extract(html: str) -> None:
    doc = _RefDocument(html)
    doc.summary()


# ── Mozilla Readability.js via persistent Node.js process ──

_BENCH_SERVER_JS = os.path.join(os.path.dirname(__file__), "bench_server.js")
_NODE_MODULES = os.path.join(os.path.dirname(__file__), "node_modules")
_HAS_NODE = shutil.which("node") is not None and os.path.isdir(_NODE_MODULES)


class _JsEngine:
    """Persistent Node.js process for Mozilla Readability benchmarks."""

    def __init__(self):
        self._proc = subprocess.Popen(
            ["node", _BENCH_SERVER_JS],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.path.dirname(__file__),
        )
        # Wait for ready signal.
        line = self._proc.stdout.readline()
        ready = json.loads(line)
        if not ready.get("ready"):
            raise RuntimeError("bench_server.js did not start")
        # Cache for synthetic HTML temp files.
        self._tmpdir = tempfile.mkdtemp(prefix="readability_bench_")
        self._tmpfiles: dict[int, str] = {}

    def parse_file(self, path: str) -> None:
        """Run Readability on a file (result discarded, timing by pytest)."""
        self._proc.stdin.write(json.dumps({"file": path}).encode() + b"\n")
        self._proc.stdin.flush()
        line = self._proc.stdout.readline()
        resp = json.loads(line)
        if not resp.get("ok"):
            raise RuntimeError(f"JS error: {resp.get('error')}")

    def parse_html(self, html: str) -> None:
        """Run Readability on inline HTML via a temp file."""
        key = id(html)
        if key not in self._tmpfiles:
            path = os.path.join(self._tmpdir, f"{key}.html")
            with open(path, "w", encoding="utf-8") as f:
                f.write(html)
            self._tmpfiles[key] = path
        self.parse_file(self._tmpfiles[key])

    def close(self):
        try:
            self._proc.stdin.write(b'{"cmd":"quit"}\n')
            self._proc.stdin.flush()
            self._proc.wait(timeout=5)
        except Exception:
            self._proc.kill()
        # Cleanup temp files.
        import shutil as _shutil

        _shutil.rmtree(self._tmpdir, ignore_errors=True)


@pytest.fixture(scope="module")
def js_engine():
    """Module-scoped fixture: persistent Node.js benchmark process."""
    if not _HAS_NODE:
        pytest.skip("Node.js or npm dependencies not available")
    engine = _JsEngine()
    yield engine
    engine.close()


# ── Small fixtures (~1-3 KB) ──


_SMALL = _pick_available(_SMALL_FIXTURES)


@pytest.mark.skipif(_SMALL is None, reason="No small fixture available")
class TestSmall:
    def test_zerodep(self, benchmark):
        html = _get_fixture(_SMALL)
        benchmark(_zd_extract, html)

    @pytest.mark.skipif(not _HAS_REFERENCE, reason="readability-lxml missing")
    def test_readability_lxml(self, benchmark):
        html = _get_fixture(_SMALL)
        benchmark(_ref_extract, html)

    @pytest.mark.skipif(not _HAS_NODE, reason="Node.js or npm deps missing")
    def test_mozilla_js(self, benchmark, js_engine):
        path = os.path.join(_TEST_PAGES_DIR, _SMALL, "source.html")
        benchmark(js_engine.parse_file, path)


# ── Medium fixtures (~12-55 KB) ──


_MEDIUM = _pick_available(_MEDIUM_FIXTURES)


@pytest.mark.skipif(_MEDIUM is None, reason="No medium fixture available")
class TestMedium:
    def test_zerodep(self, benchmark):
        html = _get_fixture(_MEDIUM)
        benchmark(_zd_extract, html)

    @pytest.mark.skipif(not _HAS_REFERENCE, reason="readability-lxml missing")
    def test_readability_lxml(self, benchmark):
        html = _get_fixture(_MEDIUM)
        benchmark(_ref_extract, html)

    @pytest.mark.skipif(not _HAS_NODE, reason="Node.js or npm deps missing")
    def test_mozilla_js(self, benchmark, js_engine):
        path = os.path.join(_TEST_PAGES_DIR, _MEDIUM, "source.html")
        benchmark(js_engine.parse_file, path)


# ── Large fixtures (~250-1100 KB) ──


_LARGE = _pick_available(_LARGE_FIXTURES)


@pytest.mark.skipif(_LARGE is None, reason="No large fixture available")
class TestLarge:
    def test_zerodep(self, benchmark):
        html = _get_fixture(_LARGE)
        benchmark(_zd_extract, html)

    @pytest.mark.skipif(not _HAS_REFERENCE, reason="readability-lxml missing")
    def test_readability_lxml(self, benchmark):
        html = _get_fixture(_LARGE)
        benchmark(_ref_extract, html)

    @pytest.mark.skipif(not _HAS_NODE, reason="Node.js or npm deps missing")
    def test_mozilla_js(self, benchmark, js_engine):
        path = os.path.join(_TEST_PAGES_DIR, _LARGE, "source.html")
        benchmark(js_engine.parse_file, path)


# ── is_probably_readable benchmark ──


@pytest.mark.skipif(_MEDIUM is None, reason="No medium fixture available")
class TestIsProbablyReadable:
    def test_zerodep(self, benchmark):
        html = _get_fixture(_MEDIUM)
        benchmark(_zd_is_readable, html)


# ── Synthetic benchmark: generated article ──


def _make_article_html(n_paragraphs: int) -> str:
    """Generate a synthetic article HTML with *n_paragraphs*."""
    lines = [
        "<!DOCTYPE html>",
        '<html lang="en"><head>',
        "<title>Benchmark Article | Test Site</title>",
        '<meta property="og:title" content="Benchmark Article">',
        '<meta name="author" content="Bench Author">',
        "</head><body>",
        '<nav><a href="/">Home</a> <a href="/about">About</a></nav>',
        "<article>",
    ]
    for i in range(n_paragraphs):
        lines.append(
            f"<p>Paragraph {i}: Lorem ipsum dolor sit amet, consectetur "
            f"adipiscing elit, sed do eiusmod tempor incididunt ut labore "
            f"et dolore magna aliqua. Ut enim ad minim veniam, quis "
            f"nostrud exercitation ullamco laboris nisi ut aliquip ex ea "
            f"commodo consequat. Duis aute irure dolor in reprehenderit "
            f"in voluptate velit esse cillum dolore eu fugiat nulla "
            f"pariatur.</p>"
        )
    lines.extend(
        [
            "</article>",
            '<aside class="sidebar"><ul>',
            '<li><a href="/1">Link 1</a></li>',
            '<li><a href="/2">Link 2</a></li>',
            "</ul></aside>",
            "<footer><p>Copyright 2024</p></footer>",
            "</body></html>",
        ]
    )
    return "\n".join(lines)


SYNTH_SMALL = _make_article_html(5)
SYNTH_MEDIUM = _make_article_html(30)
SYNTH_LARGE = _make_article_html(200)


class TestSyntheticSmall:
    def test_zerodep(self, benchmark):
        benchmark(_zd_extract, SYNTH_SMALL)

    @pytest.mark.skipif(not _HAS_REFERENCE, reason="readability-lxml missing")
    def test_readability_lxml(self, benchmark):
        benchmark(_ref_extract, SYNTH_SMALL)

    @pytest.mark.skipif(not _HAS_NODE, reason="Node.js or npm deps missing")
    def test_mozilla_js(self, benchmark, js_engine):
        benchmark(js_engine.parse_html, SYNTH_SMALL)


class TestSyntheticMedium:
    def test_zerodep(self, benchmark):
        benchmark(_zd_extract, SYNTH_MEDIUM)

    @pytest.mark.skipif(not _HAS_REFERENCE, reason="readability-lxml missing")
    def test_readability_lxml(self, benchmark):
        benchmark(_ref_extract, SYNTH_MEDIUM)

    @pytest.mark.skipif(not _HAS_NODE, reason="Node.js or npm deps missing")
    def test_mozilla_js(self, benchmark, js_engine):
        benchmark(js_engine.parse_html, SYNTH_MEDIUM)


class TestSyntheticLarge:
    def test_zerodep(self, benchmark):
        benchmark(_zd_extract, SYNTH_LARGE)

    @pytest.mark.skipif(not _HAS_REFERENCE, reason="readability-lxml missing")
    def test_readability_lxml(self, benchmark):
        benchmark(_ref_extract, SYNTH_LARGE)

    @pytest.mark.skipif(not _HAS_NODE, reason="Node.js or npm deps missing")
    def test_mozilla_js(self, benchmark, js_engine):
        benchmark(js_engine.parse_html, SYNTH_LARGE)
