"""Benchmark: cold-start (import + first-call) overhead for zerodep modules.

Measures true cold import and first-call time via subprocess, so there is no
warm bytecode cache or pre-initialized state from the test runner.  Each
invocation spawns a fresh Python process -- Python startup overhead cancels
out when comparing zerodep vs reference library.

Modules that require network, servers, or complex setup (httpclient,
httpserver, websocket, cdp, sse, s3, ratelimit, runner, scheduler,
persistdict) are excluded.
"""

import functools
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.abspath(__file__))
PYTHON = sys.executable

# -------------------------------------------------------------------
# Module registry
# Each entry: (name, subdir, import_stmt, first_call_snippet | None)
# -------------------------------------------------------------------

ZERODEP_MODULES = [
    ("yaml", "yaml", "import yaml", "yaml.load('key: value\\nlist:\\n  - 1\\n  - 2')"),
    (
        "dotenv",
        "dotenv",
        "import dotenv",
        "dotenv.dotenv_values(stream=__import__('io').StringIO('K=V\\nA=B'))",
    ),
    (
        "semver",
        "semver",
        "import semver",
        "semver.version_parse('1.2.3-alpha.1+build.42')",
    ),
    (
        "xml",
        "xml",
        "import xml as xmlmod",
        "xmlmod.parse('<root><a>1</a><b>2</b></root>')",
    ),
    (
        "jsonx",
        "jsonx",
        "import jsonx",
        'jsonx.loads(\'{"key": /* comment */ "value"}\')',
    ),
    ("soup", "soup", "import soup", "soup.Soup('<html><body><p>hi</p></body></html>')"),
    (
        "multipart",
        "multipart",
        "import multipart",
        "multipart.encode_multipart(fields={'f': 'val'})",
    ),
    (
        "frontmatter",
        "frontmatter",
        "import frontmatter",
        "frontmatter.loads('---\\ntitle: t\\n---\\nbody')",
    ),
    (
        "validate",
        "validate",
        "import validate",
        "validate.validate({'x': 'a', 'y': 1}, "
        "validate.create_struct("
        "'P', {'x': (str, ...), 'y': (int, ...)}))",
    ),
    (
        "markdown",
        "markdown",
        "import markdown",
        "markdown.render('# Hello\\n\\nparagraph **bold**')",
    ),
    ("diff", "diff", "import diff", "diff.make_diff('a\\nb\\n', 'a\\nc\\n')"),
    (
        "aes",
        "aes",
        "import aes",
        "aes.aes_cbc_encrypt(b'sixteen byte key', b'\\0'*16, b'hello world 1234')",
    ),
    ("qr", "qr", "import qr", "qr.QrCode.encode_text('hello', qr.QrCode.Ecc.LOW)"),
    ("protobuf", "protobuf", "import protobuf", "protobuf.encode_varint(300)"),
    (
        "tabulate",
        "tabulate",
        "import tabulate",
        "tabulate.tabulate([['a', 1], ['b', 2]], headers=['Name', 'Val'])",
    ),
    ("structlog", "structlog", "import structlog", "structlog.get_logger('test')"),
    ("cache", "cache", "import cache", "cache.LRUCache(maxsize=128)"),
    (
        "readability",
        "readability",
        "import readability",
        "readability.is_probably_readable("
        "'<html><body>' + '<p>word </p>'*50 + '</body></html>')",
    ),
    (
        "jsonschema",
        "jsonschema",
        "import jsonschema",
        "jsonschema.resolve_refs("
        "{'type': 'object', "
        "'properties': {'a': {'type': 'string'}}})",
    ),
    (
        "sparse_search",
        "sparse_search",
        "import sparse_search",
        "idx = sparse_search.SparseIndex(); "
        "idx.add('d1', 'hello world'); idx.search('hello')",
    ),
    ("useragent", "useragent", "import useragent", "useragent.generate()"),
    (
        "jsonrpc",
        "jsonrpc",
        "import jsonrpc",
        "jsonrpc.JSONRPCRequest(method='echo', params={'msg': 'hi'}).to_dict()",
    ),
    (
        "png",
        "png",
        "import png",
        "png.encode_png(png.Image(2, 2, b'\\xff\\x00\\x00' * 4, mode='RGB'))",
    ),
    ("config", "config", "import config", None),
    ("retry", "retry", "import retry", None),
]

# -------------------------------------------------------------------
# Reference libraries
# Each entry: (label, import_stmt, first_call_snippet | None)
# -------------------------------------------------------------------

REFERENCE_LIBS = {
    "yaml": (
        "PyYAML",
        "import yaml",
        "yaml.safe_load('key: value\\nlist:\\n  - 1\\n  - 2')",
    ),
    "dotenv": (
        "python-dotenv",
        "from dotenv import dotenv_values",
        "dotenv_values(stream=__import__('io').StringIO('K=V\\nA=B'))",
    ),
    "semver": (
        "packaging",
        "from packaging.version import Version",
        "Version('1.2.3a1')",
    ),
    "xml": (
        "xmltodict",
        "import xmltodict",
        "xmltodict.parse('<root><a>1</a><b>2</b></root>')",
    ),
    "jsonx": (
        "commentjson",
        "import commentjson",
        'commentjson.loads(\'{"key": "value"}\')',
    ),
    "soup": (
        "beautifulsoup4",
        "from bs4 import BeautifulSoup",
        "BeautifulSoup('<html><body><p>hi</p></body></html>', 'html.parser')",
    ),
    "multipart": (
        "python-multipart",
        "from multipart.multipart import parse_options_header",
        "parse_options_header('text/plain; charset=utf-8')",
    ),
    "frontmatter": (
        "python-frontmatter",
        "import frontmatter",
        "frontmatter.loads('---\\ntitle: t\\n---\\nbody')",
    ),
    "validate": (
        "pydantic",
        "from pydantic import BaseModel",
        "type('M', (BaseModel,), "
        "{'__annotations__': {'name': str, 'age': int}})"
        "(name='a', age=1)",
    ),
    "markdown": (
        "mistune",
        "import mistune",
        "mistune.html('# Hello\\n\\nparagraph **bold**')",
    ),
    "diff": (
        "unidiff",
        "import unidiff",
        "unidiff.PatchSet('')",
    ),
    "aes": (
        "pycryptodome",
        "from Crypto.Cipher import AES",
        "AES.new(b'sixteen byte key', AES.MODE_CBC, "
        "iv=b'\\0'*16).encrypt(b'hello world 1234')",
    ),
    "qr": (
        "qrcode",
        "import qrcode",
        "qrcode.make('https://example.com')",
    ),
    "tabulate": (
        "tabulate",
        "from tabulate import tabulate",
        "tabulate([['a', 1], ['b', 2]], headers=['Name', 'Val'])",
    ),
    "structlog": (
        "structlog",
        "import structlog",
        "structlog.get_logger('test')",
    ),
    "cache": (
        "cachetools",
        "import cachetools",
        "cachetools.LRUCache(maxsize=128)",
    ),
    "readability": (
        "readability-lxml",
        "from readability import Document",
        "Document('<html><body>' + '<p>word </p>'*50 + '</body></html>')",
    ),
    "jsonschema": (
        "jsonschema-lib",
        "import jsonschema",
        "jsonschema.validate({'a': 'x'}, "
        "{'type': 'object', "
        "'properties': {'a': {'type': 'string'}}})",
    ),
    "sparse_search": (
        "rank-bm25",
        "from rank_bm25 import BM25Okapi",
        "BM25Okapi([['hello', 'world'], ['foo', 'bar']]).get_scores(['hello'])",
    ),
    "useragent": (
        "ua-generator",
        "from ua_generator import generate",
        "generate()",
    ),
    "jsonrpc": (
        "jsonrpcserver",
        "from jsonrpcserver import Success, method, serve",
        None,
    ),
    "png": (
        "Pillow",
        "from PIL import Image",
        "Image.frombytes('RGB', (2, 2), b'\\xff\\x00\\x00' * 4)",
    ),
    "protobuf": (
        "protobuf-lib",
        "from google.protobuf import json_format",
        None,
    ),
    "config": (
        "python-decouple",
        "from decouple import config",
        None,
    ),
    "retry": (
        "tenacity",
        "import tenacity",
        None,
    ),
}


def _run_snippet(code: str) -> None:
    subprocess.run(
        [PYTHON, "-c", code],
        capture_output=True,
        check=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )


def _make_zerodep_code(mod_dir: str, import_stmt: str, call: str | None) -> str:
    lines = [
        f"import sys; sys.path.insert(0, {mod_dir!r})",
        import_stmt,
    ]
    if call:
        lines.append(call)
    return "; ".join(lines)


def _make_ref_code(import_stmt: str, call: str | None) -> str:
    lines = [import_stmt]
    if call:
        lines.append(call)
    return "; ".join(lines)


@functools.lru_cache(maxsize=None)
def _check_ref_available(name: str) -> bool:
    if name not in REFERENCE_LIBS:
        return False
    _, ref_imp, _ = REFERENCE_LIBS[name]
    try:
        subprocess.run(
            [PYTHON, "-c", ref_imp],
            capture_output=True,
            check=True,
            timeout=10,
        )
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False


# -------------------------------------------------------------------
# Cold import benchmarks
# -------------------------------------------------------------------

_import_params = []
for _name, _subdir, _imp, _ in ZERODEP_MODULES:
    _mod_dir = os.path.join(ROOT, _subdir)
    _import_params.append(
        pytest.param(
            _make_zerodep_code(_mod_dir, _imp, None),
            id=f"zerodep-{_name}",
        )
    )
    if _name in REFERENCE_LIBS and _check_ref_available(_name):
        _ref_label, _ref_imp, _ = REFERENCE_LIBS[_name]
        _import_params.append(
            pytest.param(
                _make_ref_code(_ref_imp, None),
                id=f"ref-{_name}-{_ref_label}",
            )
        )


class TestColdImport:
    """Measure import-only time via subprocess (no warm cache)."""

    @pytest.mark.parametrize("code", _import_params)
    def test_cold_import(self, benchmark, code):
        benchmark(_run_snippet, code)


# -------------------------------------------------------------------
# Cold first-call benchmarks
# -------------------------------------------------------------------

_call_params = []
for _name, _subdir, _imp, _call in ZERODEP_MODULES:
    if _call is None:
        continue
    _mod_dir = os.path.join(ROOT, _subdir)
    _call_params.append(
        pytest.param(
            _make_zerodep_code(_mod_dir, _imp, _call),
            id=f"zerodep-{_name}",
        )
    )
    if _name in REFERENCE_LIBS and _check_ref_available(_name):
        _ref_label, _ref_imp, _ref_call = REFERENCE_LIBS[_name]
        if _ref_call is not None:
            _call_params.append(
                pytest.param(
                    _make_ref_code(_ref_imp, _ref_call),
                    id=f"ref-{_name}-{_ref_label}",
                )
            )


class TestColdFirstCall:
    """Measure import + first call via subprocess (no warm cache)."""

    @pytest.mark.parametrize("code", _call_params)
    def test_cold_first_call(self, benchmark, code):
        benchmark(_run_snippet, code)
