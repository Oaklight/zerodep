# /// zerodep
# version = "0.4.0"
# deps = []
# tier = "medium"
# category = "devtools"
# note = "Install/update via zerodep CLI (https://zerodep.readthedocs.io/en/latest/guide/cli/). Manual copy may miss deps."
# ///

"""Dependency detection and verification — zero dependencies, stdlib only, Python 3.10+.

Part of zerodep: https://github.com/Oaklight/zerodep
Copyright (c) 2026 Peng Ding. MIT License.

Parse dependency information from Python source code, requirements files,
and free-text compatibility strings.  Verify that binaries, Python packages,
and environment variables are present on the current system.

Analyze imports in Python source::

    from depdetect import parse_imports, analyze_source

    # Raw import names (third-party only, stdlib filtered out)
    imports = parse_imports("import requests\\nimport os\\n")
    # → {"requests"}

    # Resolved to pip-installable names
    pip_names = analyze_source("import yaml\\nimport PIL\\n")
    # → {"pyyaml", "pillow"}

Check system dependencies::

    from depdetect import check_binary, check_python_package, get_binary_version

    path = check_binary("git")          # "/usr/bin/git" or None
    ver = get_binary_version("git")     # "2.43.0" or None
    ok = check_python_package("requests")  # True / False

Parse and verify requirements::

    from depdetect import parse_requirements, check_requirements

    reqs = parse_requirements("requests>=2.28\\npillow>=10.0\\n")
    report = check_requirements(reqs)
    print(report.summary())

Requires Python 3.10+.
"""

from __future__ import annotations

import ast
import importlib.metadata
import importlib.util
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Any

__all__ = [
    # Exceptions
    "DepdetectError",
    # Data classes
    "Requirement",
    "DependencyStatus",
    "DependencyReport",
    # Parsing
    "parse_imports",
    "parse_requirements",
    "parse_compatibility",
    "parse_tool_hints",
    # Name resolution
    "resolve_pip_name",
    # Detection
    "check_binary",
    "check_python_package",
    "check_env_var",
    "get_binary_version",
    # High-level
    "check_requirements",
    "analyze_source",
]


# ── Constants ──

_SUBPROCESS_TIMEOUT: float = 5.0
_IS_WINDOWS: bool = os.name == "nt"

# Cross-platform alias mapping: logical name → candidate binary names.
_BINARY_ALIASES: dict[str, list[str]] = {
    "python": ["python3", "python"],
    "libreoffice": ["libreoffice", "soffice"],
    "node.js": ["node"],
    "nodejs": ["node"],
}

# pip distribution name → Python import name.
_PIP_TO_IMPORT: dict[str, str] = {
    "beautifulsoup4": "bs4",
    "dateutil": "dateutil",
    "opencv-python": "cv2",
    "opencv-python-headless": "cv2",
    "pillow": "PIL",
    "pymupdf": "fitz",
    "python-dateutil": "dateutil",
    "python-dotenv": "dotenv",
    "python-magic": "magic",
    "pyyaml": "yaml",
    "scikit-learn": "sklearn",
}

# Python import name → pip distribution name (static fallback).
_IMPORT_TO_PIP: dict[str, str] = {
    "PIL": "pillow",
    "bs4": "beautifulsoup4",
    "cv2": "opencv-python",
    "dateutil": "python-dateutil",
    "dotenv": "python-dotenv",
    "fitz": "pymupdf",
    "magic": "python-magic",
    "sklearn": "scikit-learn",
    "yaml": "pyyaml",
}

# Binaries that need a flag other than ``--version``.
_VERSION_FLAG: dict[str, list[str]] = {
    "java": ["-version"],
    "ffmpeg": ["-version"],
}

# Noise words to skip in compatibility string parsing.
_COMPAT_NOISE: frozenset[str] = frozenset(
    {"or", "and", "requires", "needs", "with", "on", "the", "a", "an", "for", "is"}
)

# Known runtime names (map to category "runtime" in parse_compatibility).
_RUNTIME_NAMES: frozenset[str] = frozenset(
    {"python", "python3", "node", "node.js", "nodejs", "ruby", "java", "go", "perl"}
)

_VERSION_RE = re.compile(r"(\d+(?:\.\d+)+)")

_REQ_RE = re.compile(
    r"^([A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?)"  # package name
    r"(?:\[([^\]]+)\])?"  # optional extras
    r"(?:\s*(~=|==|!=|<=|>=|<|>)\s*([^\s,;#]+))?"  # optional version spec
)

_COMPAT_RE = re.compile(
    r"([A-Za-z][A-Za-z0-9._+-]*)"  # name
    r"\s*"
    r"(>=|<=|>|<|==|~=)?\s*"  # optional operator
    r"(\d+(?:\.\d+)*)?"  # optional version
    r"\+?"  # optional trailing +
)

_TOOL_HINT_PAREN_RE = re.compile(r"\(([^)]+)\)")
_TOOL_HINT_BINARY_RE = re.compile(r"([a-zA-Z][a-zA-Z0-9_-]*):")

# Module-level cache for the dynamic import→pip mapping.
_import_to_pip_cache: dict[str, str] | None = None


# ── Exceptions ──


class DepdetectError(Exception):
    """Base exception for dependency detection errors."""


# ── Data Classes ──


@dataclass(frozen=True, slots=True)
class Requirement:
    """A parsed dependency requirement.

    Attributes:
        name: Package or binary name.
        category: One of ``"binary"``, ``"python"``, ``"env"``, ``"runtime"``.
        op: Version comparison operator (``">="``, ``"=="``, etc.) or ``None``.
        version: Required version string, or ``None``.
        extras: Extras specifier for Python packages (e.g. ``"security"``).
    """

    name: str
    category: str = "python"
    op: str | None = None
    version: str | None = None
    extras: str | None = None


@dataclass(frozen=True, slots=True)
class DependencyStatus:
    """Result of checking a single dependency.

    Attributes:
        name: Dependency name.
        category: One of ``"binary"``, ``"python"``, ``"env"``, ``"runtime"``.
        required: Version constraint string (e.g. ``">=3.10"``), or ``None``.
        found: Whether the dependency was found.
        found_version: Detected version string, or ``None``.
        path: Binary path for ``"binary"`` category, or ``None``.
        message: Human-readable status description.
    """

    name: str
    category: str
    required: str | None
    found: bool
    found_version: str | None = None
    path: str | None = None
    message: str = ""


@dataclass
class DependencyReport:
    """Aggregated results for multiple dependency checks.

    Attributes:
        dependencies: List of individual dependency check results.
    """

    dependencies: list[DependencyStatus] = field(default_factory=list)

    @property
    def satisfied(self) -> bool:
        """Whether all dependencies are found and version-compatible."""
        return all(d.found for d in self.dependencies)

    @property
    def missing(self) -> list[DependencyStatus]:
        """Dependencies that were not found or version-incompatible."""
        return [d for d in self.dependencies if not d.found]

    def summary(self) -> str:
        """Human-readable summary of all dependency checks."""
        lines: list[str] = []
        for d in self.dependencies:
            status = "OK" if d.found else "MISSING"
            ver = f" ({d.found_version})" if d.found_version else ""
            msg = f": {d.message}" if d.message else ""
            lines.append(f"[{status}] {d.name}{ver}{msg}")
        total = len(self.dependencies)
        ok = total - len(self.missing)
        lines.append(f"\n{ok}/{total} dependencies satisfied.")
        return "\n".join(lines)


# ── Internal Helpers ──


def _parse_version(v: str) -> tuple[int, ...]:
    """Parse a version string into a tuple of integers for comparison.

    Args:
        v: Version string like ``"2.43.0"`` or ``"3.10"``.

    Returns:
        Tuple of integers, e.g. ``(2, 43, 0)``.
    """
    return tuple(int(x) for x in re.findall(r"\d+", v))


def _compare_versions(found: str, op: str, required: str) -> bool:
    """Compare two version strings using the given operator.

    Args:
        found: The version that was detected.
        op: Comparison operator (``">="``, ``"=="``, etc.).
        required: The required version.

    Returns:
        ``True`` if the comparison is satisfied.
    """
    f = _parse_version(found)
    r = _parse_version(required)
    if op == ">=":
        return f >= r
    if op == ">":
        return f > r
    if op == "<=":
        return f <= r
    if op == "<":
        return f < r
    if op == "==":
        return f == r
    if op == "!=":
        return f != r
    if op == "~=":
        # Compatible release: ~=X.Y means >=X.Y, <(X+1).0
        return f >= r and f[: len(r) - 1] == r[: len(r) - 1]
    return True  # unknown operator — assume satisfied


def _subprocess_kwargs() -> dict[str, Any]:
    """Return platform-specific kwargs for subprocess.run."""
    kwargs: dict[str, Any] = {
        "capture_output": True,
        "text": True,
        "timeout": _SUBPROCESS_TIMEOUT,
    }
    if _IS_WINDOWS:
        CREATE_NO_WINDOW = 0x08000000
        kwargs["creationflags"] = CREATE_NO_WINDOW
    return kwargs


def _run_version_cmd(binary_path: str, name: str) -> str | None:
    """Run a binary with its version flag and extract a version number.

    Args:
        binary_path: Absolute path to the binary.
        name: Logical name (used to look up custom version flags).

    Returns:
        Version string like ``"2.43.0"``, or ``None``.
    """
    flag = _VERSION_FLAG.get(name.lower(), ["--version"])
    try:
        result = subprocess.run(  # noqa: S603
            [binary_path, *flag],
            **_subprocess_kwargs(),
        )
        output = result.stdout + result.stderr
        m = _VERSION_RE.search(output)
        return m.group(1) if m else None
    except (subprocess.TimeoutExpired, OSError, FileNotFoundError):
        return None


def _resolve_binary_candidates(name: str) -> list[str]:
    """Return candidate binary names for a logical name.

    Args:
        name: Logical binary name (e.g. ``"node.js"``).

    Returns:
        List of candidate binary names to try with :func:`shutil.which`.
    """
    key = name.lower()
    if key in _BINARY_ALIASES:
        return list(_BINARY_ALIASES[key])
    return [name]


def _resolve_import_name(pip_name: str) -> str:
    """Convert a pip distribution name to the Python import name.

    Args:
        pip_name: pip package name (e.g. ``"pillow"``).

    Returns:
        Import name (e.g. ``"PIL"``).
    """
    key = pip_name.lower()
    if key in _PIP_TO_IMPORT:
        return _PIP_TO_IMPORT[key]
    # Default convention: replace hyphens with underscores
    return pip_name.replace("-", "_")


def _build_import_to_pip_from_metadata() -> dict[str, str]:
    """Build import→pip mapping from installed package metadata.

    Uses ``importlib.metadata`` to inspect installed distributions and
    their ``top_level.txt`` files.  Works on Python 3.10+.

    Returns:
        Dict mapping import names to pip distribution names.
    """
    mapping: dict[str, str] = {}
    try:
        if sys.version_info >= (3, 11):
            # packages_distributions() returns {import_name: [dist_name, ...]}
            pkgs = importlib.metadata.packages_distributions()
            for import_name, dist_names in pkgs.items():
                if dist_names:
                    mapping[import_name] = dist_names[0]
        else:
            # Python 3.10: manual iteration
            for dist in importlib.metadata.distributions():
                dist_name = dist.metadata.get("Name", "")
                top_level = dist.read_text("top_level.txt")
                if top_level:
                    for line in top_level.strip().splitlines():
                        name = line.strip()
                        if name:
                            mapping[name] = dist_name
    except Exception:
        pass  # graceful degradation
    return mapping


def _get_import_to_pip_cache() -> dict[str, str]:
    """Return the cached import→pip mapping, building it on first access."""
    global _import_to_pip_cache  # noqa: PLW0603
    if _import_to_pip_cache is None:
        _import_to_pip_cache = _build_import_to_pip_from_metadata()
    return _import_to_pip_cache


# ── Parsing Functions ──


def parse_imports(
    source: str,
    *,
    file_path: str | None = None,
) -> set[str]:
    """Extract third-party import names from Python source code.

    Parses the source with :mod:`ast` and collects all ``import`` and
    ``from ... import`` statements.  Standard library modules (detected
    via ``sys.stdlib_module_names``) are filtered out, and only top-level
    package names are returned.

    Args:
        source: Python source code string.
        file_path: Optional file path for error messages.

    Returns:
        Set of top-level third-party package names (import names, not
        pip names).  Use :func:`resolve_pip_name` to convert.

    Raises:
        DepdetectError: If the source cannot be parsed.

    Example::

        parse_imports("import requests\\nfrom os.path import join\\n")
        # → {"requests"}
    """
    try:
        tree = ast.parse(source, filename=file_path or "<string>")
    except SyntaxError as exc:
        src = file_path or "<string>"
        raise DepdetectError(f"cannot parse {src}: {exc}") from exc

    stdlib = getattr(sys, "stdlib_module_names", frozenset())
    imports: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split(".")[0]
                if top not in stdlib:
                    imports.add(top)
        elif isinstance(node, ast.ImportFrom):
            # Skip relative imports
            if node.level and node.level > 0:
                continue
            if node.module:
                top = node.module.split(".")[0]
                if top not in stdlib:
                    imports.add(top)

    return imports


def parse_requirements(text: str) -> list[Requirement]:
    """Parse pip requirements.txt format into :class:`Requirement` objects.

    Handles version constraints (``>=``, ``==``, ``~=``, etc.), extras
    (``package[extra]``), comments, blank lines, and skips ``-r``/``-e``
    directives.

    Args:
        text: Contents of a requirements.txt file.

    Returns:
        List of parsed requirements with ``category="python"``.

    Example::

        parse_requirements("requests>=2.28.0\\npillow>=10.0\\n")
        # → [Requirement("requests", "python", ">=", "2.28.0"),
        #    Requirement("pillow", "python", ">=", "10.0")]
    """
    results: list[Requirement] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        # Skip empty lines, comments, -r/-c includes, -e editable installs
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        m = _REQ_RE.match(line)
        if m:
            name = m.group(1)
            extras = m.group(2)
            op = m.group(3)
            version = m.group(4)
            results.append(
                Requirement(
                    name=name,
                    category="python",
                    op=op,
                    version=version,
                    extras=extras,
                )
            )
    return results


def parse_compatibility(text: str) -> list[Requirement]:
    """Parse free-text compatibility notes into structured requirements.

    Best-effort extraction from strings like
    ``"Python 3.10+, Node.js >= 18, pandoc >= 3.0"``.  Noise words
    (``"or"``, ``"and"``, ``"requires"``, etc.) are filtered out.

    Args:
        text: Compatibility string (typically from SKILL.md frontmatter).

    Returns:
        List of parsed requirements.  May be incomplete for ambiguous input.

    Example::

        parse_compatibility("Python 3.10+, pandoc >= 3.0")
        # → [Requirement("Python", "runtime", ">=", "3.10"),
        #    Requirement("pandoc", "binary", ">=", "3.0")]
    """
    results: list[Requirement] = []
    for m in _COMPAT_RE.finditer(text):
        name = m.group(1)
        # Skip noise words
        if name.lower() in _COMPAT_NOISE:
            continue
        op = m.group(2)
        version = m.group(3)
        # If there's a trailing + in the original text and no explicit op,
        # treat as >=
        if version and not op:
            # Check if there's a + right after the version in the source
            end = m.end()
            if end <= len(text) and text[m.start(3) : end].endswith("+"):
                pass  # the + was already stripped by regex
            op = ">="

        # Infer category
        category = "runtime" if name.lower() in _RUNTIME_NAMES else "binary"

        results.append(
            Requirement(name=name, category=category, op=op, version=version)
        )
    return results


def parse_tool_hints(allowed_tools: str) -> list[str]:
    """Extract binary name hints from an ``allowed-tools`` string.

    Parses parenthesized parameters like ``Bash(git:* npm:*)`` to extract
    ``["git", "npm"]`` as binaries the skill expects to use via the shell.

    Args:
        allowed_tools: The ``allowed-tools`` field value from SKILL.md.

    Returns:
        List of binary names found in tool parameters.

    Example::

        parse_tool_hints("Bash(git:* docker:*) Read Write")
        # → ["git", "docker"]
    """
    binaries: list[str] = []
    for paren_match in _TOOL_HINT_PAREN_RE.finditer(allowed_tools):
        content = paren_match.group(1)
        for bin_match in _TOOL_HINT_BINARY_RE.finditer(content):
            binaries.append(bin_match.group(1))
    return binaries


# ── Name Resolution ──


def resolve_pip_name(import_name: str) -> str:
    """Resolve a Python import name to its pip distribution name.

    Uses a three-level fallback strategy:

    1. **Installed metadata** — queries ``importlib.metadata`` for the
       exact mapping from installed packages (cached after first call).
    2. **Static mapping** — covers ~30 high-frequency mismatches
       (e.g. ``PIL`` → ``pillow``, ``yaml`` → ``pyyaml``).
    3. **Heuristic** — replaces underscores with hyphens, which covers
       the majority of conventional packages.

    Args:
        import_name: The name used in ``import`` statements.

    Returns:
        The pip-installable package name.

    Example::

        resolve_pip_name("PIL")     # → "pillow"
        resolve_pip_name("yaml")    # → "pyyaml"
        resolve_pip_name("dotenv")  # → "python-dotenv"
    """
    # Level 1: dynamic metadata lookup
    cache = _get_import_to_pip_cache()
    if import_name in cache:
        return cache[import_name]

    # Level 2: static mapping
    if import_name in _IMPORT_TO_PIP:
        return _IMPORT_TO_PIP[import_name]

    # Level 3: heuristic
    return import_name.replace("_", "-")


# ── Detection Functions ──


def check_binary(name: str) -> str | None:
    """Check if a binary is available on the system PATH.

    Resolves aliases (e.g. ``"node.js"`` → ``"node"``) and returns
    the first matching path.  Uses :func:`shutil.which` which handles
    Windows ``PATHEXT`` automatically.

    Args:
        name: Binary name or alias.

    Returns:
        Absolute path to the binary, or ``None`` if not found.
    """
    for candidate in _resolve_binary_candidates(name):
        path = shutil.which(candidate)
        if path:
            return path
    return None


def check_python_package(name: str) -> bool:
    """Check if a Python package is importable in the current environment.

    Uses :func:`importlib.util.find_spec` to check availability without
    triggering the actual import.  Handles pip-to-import name mapping
    (e.g. ``"pillow"`` → ``"PIL"``).

    Args:
        name: Package name (pip distribution name or import name).

    Returns:
        ``True`` if the package can be imported.
    """
    import_name = _resolve_import_name(name)
    try:
        return importlib.util.find_spec(import_name) is not None
    except (ModuleNotFoundError, ValueError):
        return False


def check_env_var(name: str) -> bool:
    """Check if an environment variable is set and non-empty.

    Args:
        name: Environment variable name.

    Returns:
        ``True`` if the variable is set and has a non-empty value.
    """
    return bool(os.environ.get(name))


def get_binary_version(name: str) -> str | None:
    """Get the version string of an installed binary.

    Runs the binary with ``--version`` (or an appropriate flag) and
    extracts a dotted version number from the output.

    Args:
        name: Binary name or alias.

    Returns:
        Version string (e.g. ``"2.43.0"``), or ``None`` if the binary
        is not found or the version cannot be determined.
    """
    path = check_binary(name)
    if not path:
        return None
    return _run_version_cmd(path, name)


# ── High-Level Functions ──


def _check_one(req: Requirement) -> DependencyStatus:
    """Check a single requirement against the current system."""
    required_str = f"{req.op}{req.version}" if req.op and req.version else None

    if req.category == "binary":
        path = check_binary(req.name)
        if not path:
            return DependencyStatus(
                name=req.name,
                category=req.category,
                required=required_str,
                found=False,
                message=f"{req.name} not found on PATH",
            )
        found_version = _run_version_cmd(path, req.name)
        # Check version constraint
        if req.op and req.version and found_version:
            if not _compare_versions(found_version, req.op, req.version):
                return DependencyStatus(
                    name=req.name,
                    category=req.category,
                    required=required_str,
                    found=False,
                    found_version=found_version,
                    path=path,
                    message=f"{req.name} {found_version} !~ {required_str}",
                )
        return DependencyStatus(
            name=req.name,
            category=req.category,
            required=required_str,
            found=True,
            found_version=found_version,
            path=path,
            message=f"found at {path}",
        )

    if req.category == "python":
        found = check_python_package(req.name)
        if not found:
            return DependencyStatus(
                name=req.name,
                category=req.category,
                required=required_str,
                found=False,
                message=f"{req.name} not importable",
            )
        # Try to get installed version
        found_version = None
        try:
            found_version = importlib.metadata.version(req.name)
        except importlib.metadata.PackageNotFoundError:
            # Try with the import name mapped back
            import_name = _resolve_import_name(req.name)
            if import_name != req.name:
                try:
                    found_version = importlib.metadata.version(import_name)
                except importlib.metadata.PackageNotFoundError:
                    pass
        # Check version constraint
        if req.op and req.version and found_version:
            if not _compare_versions(found_version, req.op, req.version):
                return DependencyStatus(
                    name=req.name,
                    category=req.category,
                    required=required_str,
                    found=False,
                    found_version=found_version,
                    message=f"{req.name} {found_version} !~ {required_str}",
                )
        return DependencyStatus(
            name=req.name,
            category=req.category,
            required=required_str,
            found=True,
            found_version=found_version,
            message="importable",
        )

    if req.category == "env":
        found = check_env_var(req.name)
        return DependencyStatus(
            name=req.name,
            category=req.category,
            required=None,
            found=found,
            message="set" if found else f"{req.name} not set",
        )

    if req.category == "runtime":
        name_lower = req.name.lower()
        if name_lower in ("python", "python3"):
            vi = sys.version_info
            ver = f"{vi.major}.{vi.minor}.{vi.micro}"
            found = True
            if req.op and req.version:
                found = _compare_versions(ver, req.op, req.version)
            return DependencyStatus(
                name=req.name,
                category=req.category,
                required=required_str,
                found=found,
                found_version=ver,
                message="current interpreter"
                if found
                else f"Python {ver} !~ {required_str}",
            )
        # Other runtimes: treat like binary
        path = check_binary(req.name)
        if not path:
            return DependencyStatus(
                name=req.name,
                category=req.category,
                required=required_str,
                found=False,
                message=f"{req.name} not found on PATH",
            )
        found_version = _run_version_cmd(path, req.name)
        if req.op and req.version and found_version:
            if not _compare_versions(found_version, req.op, req.version):
                return DependencyStatus(
                    name=req.name,
                    category=req.category,
                    required=required_str,
                    found=False,
                    found_version=found_version,
                    path=path,
                    message=f"{req.name} {found_version} !~ {required_str}",
                )
        return DependencyStatus(
            name=req.name,
            category=req.category,
            required=required_str,
            found=True,
            found_version=found_version,
            path=path,
            message=f"found at {path}",
        )

    # Unknown category — report as not checkable
    return DependencyStatus(
        name=req.name,
        category=req.category,
        required=required_str,
        found=False,
        message=f"unknown category: {req.category}",
    )


def check_requirements(requirements: list[Requirement]) -> DependencyReport:
    """Check a list of requirements against the current system.

    Dispatches each requirement to the appropriate detection function
    based on its :attr:`~Requirement.category`, performs version comparison
    if a constraint is specified, and aggregates results into a report.

    Args:
        requirements: List of requirements to check.

    Returns:
        A :class:`DependencyReport` with one :class:`DependencyStatus`
        per requirement.

    Example::

        reqs = [
            Requirement("git", "binary"),
            Requirement("requests", "python", ">=", "2.28"),
        ]
        report = check_requirements(reqs)
        if not report.satisfied:
            print(report.summary())
    """
    statuses: list[DependencyStatus] = []
    for req in requirements:
        statuses.append(_check_one(req))
    return DependencyReport(dependencies=statuses)


def analyze_source(
    source: str,
    *,
    file_path: str | None = None,
) -> set[str]:
    """Analyze Python source code for third-party dependencies.

    Combines :func:`parse_imports` (AST-based import extraction) with
    :func:`resolve_pip_name` (import→pip name resolution) to produce
    a set of pip-installable package names.

    Args:
        source: Python source code string.
        file_path: Optional path for error messages.

    Returns:
        Set of pip-installable package names.

    Raises:
        DepdetectError: If the source cannot be parsed.

    Example::

        analyze_source("import yaml\\nfrom PIL import Image\\n")
        # → {"pyyaml", "pillow"}
    """
    imports = parse_imports(source, file_path=file_path)
    return {resolve_pip_name(name) for name in imports}
