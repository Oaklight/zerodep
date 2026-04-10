"""zerodep CLI — copy zero-dependency Python modules into your project.

Usage::

    python zerodep.py list                  # list available modules
    python zerodep.py info <module>         # module details + deps
    python zerodep.py add <module> [...]    # copy modules to cwd
    python zerodep.py outdated              # check local files for updates
    python zerodep.py manifest              # regenerate manifest.json

Requires Python 3.10+, zero external dependencies.
"""

from __future__ import annotations

__version__ = "2026.4.11"

import argparse
import ast
import hashlib
import json
import re
import shutil
import subprocess
import sys
import textwrap
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# ── Constants ──

REPO_OWNER = "Oaklight"
REPO_NAME = "zerodep"
BRANCH = "master"

_SOURCES = [
    f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{BRANCH}/{{path}}",
    f"https://cdn.jsdelivr.net/gh/{REPO_OWNER}/{REPO_NAME}@{BRANCH}/{{path}}",
    f"https://fastly.jsdelivr.net/gh/{REPO_OWNER}/{REPO_NAME}@{BRANCH}/{{path}}",
]

CACHE_DIR = Path.home() / ".zerodep" / "cache"
MANIFEST_PATH = "manifest.json"

# Modules where the directory name != file name (multi-file or renamed)
# Discovered automatically during manifest generation.


# ── Network ──


def _fetch_url(url: str, timeout: int = 15) -> bytes:
    """Fetch raw bytes from a URL using urllib."""
    req = urllib.request.Request(url, headers={"User-Agent": "zerodep-cli"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def _fetch_with_fallback(path: str, *, offline: bool = False) -> bytes:
    """Try sources in order, cache result, fall back to cache."""
    cache_file = CACHE_DIR / path
    if offline:
        if cache_file.exists():
            return cache_file.read_bytes()
        _die(f"offline mode: {path!r} not found in cache ({cache_file})")

    for src in _SOURCES:
        url = src.format(path=path)
        try:
            data = _fetch_url(url)
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            cache_file.write_bytes(data)
            return data
        except (urllib.error.URLError, OSError, TimeoutError):
            continue

    # All sources failed — try cache
    if cache_file.exists():
        _warn(f"network unavailable, using cached {path}")
        return cache_file.read_bytes()

    _die(
        f"could not fetch {path!r} from any source and no cache exists.\n"
        "  Check your network or use --offline with a populated cache."
    )
    return b""  # unreachable, for type checker


def _load_manifest(*, offline: bool = False, local: bool = False) -> dict:
    """Load manifest.json from network/cache or local file."""
    if local:
        # Use local manifest.json in repo root
        local_path = Path(__file__).resolve().parent / MANIFEST_PATH
        if not local_path.exists():
            _die(
                f"local {MANIFEST_PATH} not found. "
                "Run 'zerodep manifest' to generate it."
            )
        return json.loads(local_path.read_text())

    data = _fetch_with_fallback(MANIFEST_PATH, offline=offline)
    return json.loads(data)


# ── Dependency Resolution ──


def _resolve_deps(
    names: list[str],
    manifest: dict,
    *,
    no_deps: bool = False,
) -> list[str]:
    """Topological resolve: return ordered list of modules to copy."""
    modules = manifest["modules"]
    resolved: list[str] = []
    seen: set[str] = set()

    def _visit(name: str) -> None:
        if name in seen:
            return
        if name not in modules:
            _die(
                f"unknown module: {name!r}. "
                "Run 'zerodep list' to see available modules."
            )
        seen.add(name)
        if not no_deps:
            for dep in modules[name].get("deps", []):
                _visit(dep)
        resolved.append(name)

    for n in names:
        _visit(n)
    return resolved


def _build_reverse_deps(modules: dict) -> dict[str, list[str]]:
    """Build a mapping from each module to the list of modules that depend on it."""
    reverse: dict[str, list[str]] = {}
    for mod_name, mod in modules.items():
        for dep in mod.get("deps", []):
            reverse.setdefault(dep, []).append(mod_name)
    return reverse


def _transitive_dependents(
    seeds: set[str], reverse_deps: dict[str, list[str]]
) -> set[str]:
    """BFS from *seeds* through *reverse_deps* to find all affected modules."""
    visited = set(seeds)
    queue = list(seeds)
    i = 0
    while i < len(queue):
        mod = queue[i]
        i += 1
        for dep in reverse_deps.get(mod, []):
            if dep not in visited:
                visited.add(dep)
                queue.append(dep)
    return visited


def _find_changed_modules(repo_root: Path, modules: dict) -> dict[str, str]:
    """Detect which modules have been modified since their declared version tag.

    Returns:
        Dict mapping module name to status: "up-to-date", "modified", "new", or "error".
    """
    status_map: dict[str, str] = {}
    for mod_name, mod in sorted(modules.items()):
        version = mod["version"]
        tag = f"v{version}"
        primary_file = mod["files"][0]

        try:
            result = subprocess.run(
                ["git", "show", f"{tag}:{primary_file}"],
                cwd=repo_root,
                capture_output=True,
                text=True,
                timeout=5,
            )
        except subprocess.SubprocessError:
            status_map[mod_name] = "error"
            continue

        if result.returncode != 0:
            status_map[mod_name] = "new"
            continue

        tag_hash = _normalized_hash(result.stdout)
        cur_hash = _normalized_hash(
            (repo_root / primary_file).read_text(encoding="utf-8")
        )
        status_map[mod_name] = "up-to-date" if tag_hash == cur_hash else "modified"
    return status_map


def _find_test_file(mod_name: str, modules: dict, repo_root: Path) -> Path | None:
    """Locate the correctness test file for a module."""
    primary = modules[mod_name]["files"][0]
    mod_dir = repo_root / Path(primary).parent
    matches = sorted(mod_dir.glob("test_*_correctness.py"))
    return matches[0] if matches else None


# ── Manifest Generation ──

# Directories/files to skip when scanning for modules
_SKIP_DIRS = {
    "build",
    "dist",
    "docs_en",
    "docs_zh",
    "plans",
    ".git",
    ".github",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    "site",
}


def _content_hash_from_string(source: str) -> str:
    """Return SHA-256 hex digest of *source* with the frontmatter block stripped.

    The ``# /// zerodep`` … ``# ///`` block is excluded so that metadata-only
    changes (version bumps, tier reclassification) do not alter the hash.
    """
    lines = source.splitlines(keepends=True)
    filtered: list[str] = []
    in_block = False
    for line in lines:
        stripped = line.strip()
        if stripped == "# /// zerodep":
            in_block = True
            continue
        if in_block and stripped == "# ///":
            in_block = False
            continue
        if not in_block:
            filtered.append(line)
    return hashlib.sha256("".join(filtered).encode("utf-8")).hexdigest()


def _content_hash(filepath: Path) -> str:
    """Return SHA-256 hex digest of *filepath* with the frontmatter block stripped."""
    return _content_hash_from_string(filepath.read_text(encoding="utf-8"))


def _git_last_updated(filepath: Path, repo_root: Path) -> str | None:
    """Return the ISO 8601 author-date of the last commit touching *filepath*."""
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%aI", "--", str(filepath)],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=5,
        )
        ts = result.stdout.strip()
        return ts if ts else None
    except (subprocess.SubprocessError, FileNotFoundError):
        return None


def _scan_modules(repo_root: Path) -> dict:
    """Scan repo recursively for module directories and extract metadata.

    A directory is considered a module if it contains non-test ``.py`` files.
    The module name is the leaf directory name (e.g. ``network/httpclient/``
    registers as ``httpclient``).  Intermediate grouping directories that
    contain no ``.py`` files are traversed but not registered.
    """
    modules: dict[str, dict] = {}

    def _walk(directory: Path) -> None:
        for entry in sorted(directory.iterdir()):
            if (
                not entry.is_dir()
                or entry.name.startswith(".")
                or entry.name in _SKIP_DIRS
            ):
                continue

            # Find non-test .py files in this directory
            py_files = sorted(
                f
                for f in entry.glob("*.py")
                if not f.name.startswith("test_") and f.name != "conftest.py"
            )

            if py_files:
                mod_name = entry.name
                if mod_name in modules:
                    prev_dir = str(Path(modules[mod_name]["files"][0]).parent)
                    cur_dir = str(entry.relative_to(repo_root))
                    _warn(
                        f"duplicate module name {mod_name!r}: "
                        f"found in {prev_dir} and {cur_dir}, keeping first"
                    )
                else:
                    # Primary module file: prefer dir_name.py, else first file
                    primary = None
                    for f in py_files:
                        if f.stem == entry.name:
                            primary = f
                            break
                    if primary is None:
                        primary = py_files[0]

                    source = primary.read_text(encoding="utf-8")
                    meta = _extract_frontmatter(source)
                    version = meta.get("version", "0.0.0")
                    deps = meta.get("deps", [])
                    description = _extract_docstring_first_line(source) or ""
                    files = [str(f.relative_to(repo_root)) for f in py_files]

                    tier = meta.get("tier", "")
                    category = meta.get("category", "")

                    # Get last commit timestamp for the primary file
                    last_updated = _git_last_updated(primary, repo_root)
                    chash = _content_hash(primary)

                    modules[mod_name] = {
                        "description": description,
                        "files": files,
                        "version": version,
                        "deps": deps,
                        "tier": tier,
                        "category": category,
                        "last_updated": last_updated,
                        "content_hash": chash,
                    }

            # Recurse into subdirectories
            _walk(entry)

    _walk(repo_root)
    return modules


def _extract_frontmatter(source: str) -> dict[str, str | list]:
    """Extract metadata from ``# /// zerodep`` frontmatter block.

    Parses a PEP 723-style comment block::

        # /// zerodep
        # version = "0.2.0"
        # deps = ["httpclient"]
        # ///

    Returns:
        Dict with parsed key-value pairs (values via ``ast.literal_eval``).
    """
    result: dict[str, str | list] = {}
    in_block = False
    for line in source.splitlines():
        stripped = line.strip()
        if stripped == "# /// zerodep":
            in_block = True
            continue
        if stripped == "# ///" and in_block:
            break
        if in_block and stripped.startswith("# "):
            content = stripped[2:]
            if "=" in content:
                key, _, val = content.partition("=")
                key = key.strip()
                val = val.strip()
                try:
                    result[key] = ast.literal_eval(val)
                except (ValueError, SyntaxError):
                    result[key] = val
    return result


def _extract_docstring_first_line(source: str) -> str | None:
    """Extract the first line of the module docstring."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None
    if (
        tree.body
        and isinstance(tree.body[0], ast.Expr)
        and isinstance(tree.body[0].value, ast.Constant)
        and isinstance(tree.body[0].value.value, str)
    ):
        first_line = tree.body[0].value.value.strip().split("\n")[0]
        # Remove trailing period/dash fragments
        return first_line.rstrip(".")
    return None


def _generate_manifest(repo_root: Path) -> dict:
    """Generate the full manifest dict."""
    modules = _scan_modules(repo_root)
    return {
        "version": "1",
        "generated": datetime.now(timezone.utc).isoformat(),
        "modules": modules,
    }


# ── Output Helpers ──


def _die(msg: str) -> None:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def _warn(msg: str) -> None:
    print(f"warning: {msg}", file=sys.stderr)


def _ok(msg: str) -> None:
    print(msg)


# ── Commands ──


def cmd_list(args: argparse.Namespace) -> None:
    """List available modules."""
    manifest = _load_manifest(offline=args.offline, local=args.local)
    modules = manifest["modules"]

    if not modules:
        _ok("No modules found.")
        return

    # Canonical category display order
    _CATEGORY_ORDER = [
        "network",
        "terminal",
        "data",
        "crypto",
        "process",
        "devtools",
        "utility",
    ]
    _CATEGORY_LABELS = {
        "network": "Network",
        "terminal": "Terminal",
        "data": "Data",
        "crypto": "Crypto",
        "process": "Process",
        "devtools": "Dev Tools",
        "utility": "Utility",
    }

    # Group modules by category
    by_category: dict[str, list[str]] = {}
    for name, mod in modules.items():
        cat = mod.get("category", "")
        by_category.setdefault(cat, []).append(name)

    # Column widths
    name_w = max(len(n) for n in modules)
    ver_w = max(len(m.get("version", "")) for m in modules.values())
    tier_w = max(len(m.get("tier", "")) for m in modules.values())
    tier_w = max(tier_w, len("Tier"))

    # Ordered categories (known first, then unknown)
    ordered_cats = [c for c in _CATEGORY_ORDER if c in by_category]
    for c in sorted(by_category):
        if c not in ordered_cats:
            ordered_cats.append(c)

    cat_count = 0
    for cat in ordered_cats:
        names = sorted(by_category[cat])
        label = _CATEGORY_LABELS.get(cat, cat or "Uncategorized")
        if cat_count > 0:
            _ok("")
        _ok(f"  {label}")
        for name in names:
            mod = modules[name]
            ver = mod.get("version", "?")
            tier = mod.get("tier", "")
            desc = mod.get("description", "")
            max_desc = (
                shutil.get_terminal_size((80, 24)).columns
                - name_w
                - ver_w
                - tier_w
                - 16
            )
            if max_desc > 10 and len(desc) > max_desc:
                desc = desc[: max_desc - 3] + "..."
            _ok(f"    {name:<{name_w}}  {ver:<{ver_w}}  {tier:<{tier_w}}  {desc}")
        cat_count += 1

    cats_shown = len([c for c in ordered_cats if by_category.get(c)])
    _ok(f"\n  {len(modules)} modules available ({cats_shown} categories)")


def cmd_info(args: argparse.Namespace) -> None:
    """Show module details."""
    manifest = _load_manifest(offline=args.offline, local=args.local)
    modules = manifest["modules"]
    name = args.module

    if name not in modules:
        _die(f"unknown module: {name!r}. Run 'zerodep list' to see available modules.")

    mod = modules[name]
    _ok(f"Module:      {name}")
    _ok(f"Version:     {mod.get('version', '?')}")
    _ok(f"Category:    {mod.get('category', '(unknown)')}")
    _ok(f"Tier:        {mod.get('tier', '(unknown)')}")
    _ok(f"Description: {mod.get('description', '(none)')}")
    _ok(f"Files:       {', '.join(mod.get('files', []))}")

    deps = mod.get("deps", [])
    if deps:
        _ok(f"Dependencies: {', '.join(deps)}")
        # Show transitive deps
        all_deps = _resolve_deps([name], manifest)
        all_deps.remove(name)
        if all_deps:
            _ok(f"  (transitive: {', '.join(all_deps)})")
    else:
        _ok("Dependencies: none")


def cmd_add(args: argparse.Namespace) -> None:
    """Copy module files to target directory."""
    manifest = _load_manifest(offline=args.offline, local=args.local)

    # Resolve dependencies
    to_copy = _resolve_deps(args.modules, manifest, no_deps=args.no_deps)

    # Determine target directory
    target = Path(args.dir).resolve()

    # Build file list
    file_plan: list[tuple[str, Path]] = []  # (remote_path, local_dest)
    modules_data = manifest["modules"]

    for mod_name in to_copy:
        mod = modules_data[mod_name]
        for remote_path in mod.get("files", []):
            filename = Path(remote_path).name
            if args.nested:
                dest = target / mod_name / filename
            else:
                dest = target / filename
            file_plan.append((remote_path, dest))

    if not file_plan:
        _ok("Nothing to copy.")
        return

    # Show plan
    if not args.yes:
        _ok("Will copy:")
        for remote, dest in file_plan:
            mod_name = remote.split("/")[0]
            label = mod_name
            if mod_name not in args.modules:
                label += " (dependency)"
            if dest.is_relative_to(Path.cwd()):
                rel_dest = dest.relative_to(Path.cwd())
            else:
                rel_dest = dest
            _ok(f"  {Path(remote).name:<25s} -> {rel_dest}  [{label}]")
        _ok(f"Target: {target}")

        # Check for existing files
        existing = [dest for _, dest in file_plan if dest.exists()]
        if existing:
            _warn(f"{len(existing)} file(s) will be overwritten")

        if not args.force:
            answer = input("Continue? [Y/n] ").strip().lower()
            if answer and answer != "y":
                _ok("Aborted.")
                return

    # Fetch and copy
    repo_root = Path(__file__).resolve().parent
    copied = 0
    for remote_path, dest in file_plan:
        dest.parent.mkdir(parents=True, exist_ok=True)
        # Try local first (if running from repo)
        local_file = repo_root / remote_path
        if local_file.exists():
            data = local_file.read_bytes()
        else:
            data = _fetch_with_fallback(remote_path, offline=args.offline)
        # Replace generic note with module-specific note
        mod_name = remote_path.split("/")[0]
        text = data.decode("utf-8")
        generic = (
            "Install/update via: https://zerodep.readthedocs.io/en/latest/guide/cli/"
        )
        specific = f"Install/update via `zerodep add {mod_name}`"
        text = text.replace(generic, specific)
        dest.write_text(text, encoding="utf-8")
        copied += 1

    _ok(f"Copied {copied} file(s) to {target}")


def cmd_update(args: argparse.Namespace) -> None:
    """Update existing module files (alias for add --force --yes)."""
    args.force = True
    args.yes = True
    cmd_add(args)


def cmd_manifest(args: argparse.Namespace) -> None:
    """Regenerate manifest.json from local module source files."""
    repo_root = Path(__file__).resolve().parent
    manifest = _generate_manifest(repo_root)

    out_path = repo_root / MANIFEST_PATH
    out_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    n = len(manifest["modules"])
    _ok(f"Generated {MANIFEST_PATH} with {n} modules")

    # Show deps summary
    deps_mods = {
        name: mod["deps"]
        for name, mod in manifest["modules"].items()
        if mod.get("deps")
    }
    if deps_mods:
        _ok("Modules with dependencies:")
        for name, deps in sorted(deps_mods.items()):
            _ok(f"  {name} -> {', '.join(deps)}")


def cmd_outdated(args: argparse.Namespace) -> None:
    """Check local zerodep files against the upstream manifest for changes."""
    manifest = _load_manifest(local=args.local, offline=args.offline)
    modules_data = manifest.get("modules", {})

    scan_dir = Path.cwd()
    rows: list[tuple[str, str, str, str]] = []

    for mod_name, mod in sorted(modules_data.items()):
        upstream_hash = mod.get("content_hash")
        if not upstream_hash:
            continue
        for rel_path in mod.get("files", []):
            filename = Path(rel_path).name
            local_file = scan_dir / filename
            if not local_file.exists():
                continue
            local_hash = _content_hash(local_file)
            local_meta = _extract_frontmatter(local_file.read_text(encoding="utf-8"))
            local_ver = local_meta.get("version", "?")
            upstream_ver = mod.get("version", "?")
            if local_hash == upstream_hash:
                status = "up-to-date"
            else:
                status = "outdated"
            rows.append((mod_name, local_ver, upstream_ver, status))

    if not rows:
        _ok("No zerodep modules found in current directory.")
        return

    # Print table
    headers = ("Module", "Local Ver", "Latest Ver", "Status")
    widths = [max(len(headers[i]), *(len(r[i]) for r in rows)) for i in range(4)]
    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    print(fmt.format(*headers))
    print(fmt.format(*("-" * w for w in widths)))
    for row in rows:
        print(fmt.format(*row))


def _normalized_hash(source: str) -> str:
    """Content hash with extra normalization for cross-era comparison.

    Strips the frontmatter block (like ``_content_hash_from_string``), then
    additionally removes artifacts of the v0.1.0 → v0.2.0 frontmatter
    migration so that pre- and post-migration files of functionally identical
    code produce the same hash:

    * Leading blank lines (visual separator after ``# ///`` end marker).
    * In-code ``__version__ = "..."`` lines (moved into frontmatter).
    """
    lines = source.splitlines(keepends=True)
    filtered: list[str] = []
    in_block = False
    for line in lines:
        stripped = line.strip()
        if stripped == "# /// zerodep":
            in_block = True
            continue
        if in_block and stripped == "# ///":
            in_block = False
            continue
        if not in_block:
            # Skip __version__ = "..." lines (migrated to frontmatter)
            if re.match(r'^__version__\s*=\s*["\']', stripped):
                continue
            filtered.append(line)
    text = "".join(filtered).lstrip("\n")
    # Collapse runs of blank lines left by removed __version__ / frontmatter
    text = re.sub(r"\n{3,}", "\n\n", text)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def cmd_version_check(args: argparse.Namespace) -> None:
    """Check which modules have been modified since their declared version."""
    repo_root = Path(__file__).resolve().parent
    modules = _scan_modules(repo_root)
    if not modules:
        _die("no modules found")

    status_map = _find_changed_modules(repo_root, modules)
    display = {
        "up-to-date": "up-to-date",
        "modified": "modified (needs version bump)",
        "new": "new (needs version bump)",
        "error": "error",
    }

    rows: list[tuple[str, str, str]] = []
    for mod_name in sorted(status_map):
        version = modules[mod_name]["version"]
        rows.append((mod_name, version, display[status_map[mod_name]]))

    # Print table
    headers = ("Module", "Version", "Status")
    widths = [max(len(headers[i]), *(len(r[i]) for r in rows)) for i in range(3)]
    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    print(fmt.format(*headers))
    print(fmt.format(*("-" * w for w in widths)))

    modified = 0
    for row in rows:
        print(fmt.format(*row))
        if "needs version bump" in row[2]:
            modified += 1

    if modified:
        _warn(f"{modified} module(s) need a version bump")
    else:
        _ok("all modules up-to-date")


def cmd_dep_graph(args: argparse.Namespace) -> None:
    """Show module dependency relationships."""
    repo_root = Path(__file__).resolve().parent
    modules = _scan_modules(repo_root)
    if not modules:
        _die("no modules found")

    reverse_deps = _build_reverse_deps(modules)

    if args.module:
        # Single module detail view
        name = args.module
        if name not in modules:
            _die(
                f"unknown module: {name!r}. "
                "Run 'zerodep list' to see available modules."
            )
        mod = modules[name]
        deps = mod.get("deps", [])
        rev = reverse_deps.get(name, [])
        trans = _transitive_dependents({name}, reverse_deps) - {name}

        print(f"Module: {name} (v{mod['version']})")
        print(f"  Depends on: {', '.join(sorted(deps)) or '(none)'}")
        print(f"  Depended on by: {', '.join(sorted(rev)) or '(none)'}")
        if trans:
            print(f"  Transitively affects: {', '.join(sorted(trans))}")
        return

    # Table view: show all modules that participate in any dependency
    rows: list[tuple[str, str, str]] = []
    for mod_name in sorted(modules):
        deps = modules[mod_name].get("deps", [])
        rev = reverse_deps.get(mod_name, [])
        if not deps and not rev:
            continue
        rows.append(
            (
                mod_name,
                ", ".join(sorted(deps)) or "(none)",
                ", ".join(sorted(rev)) or "(none)",
            )
        )

    if not rows:
        _ok("no inter-module dependencies found")
        return

    headers = ("Module", "Depends on", "Depended on by")
    widths = [max(len(headers[i]), *(len(r[i]) for r in rows)) for i in range(3)]
    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    print(fmt.format(*headers))
    print(fmt.format(*("-" * w for w in widths)))
    for row in rows:
        print(fmt.format(*row))


def cmd_dep_check(args: argparse.Namespace) -> None:
    """Test changed modules and their downstream dependents."""
    repo_root = Path(__file__).resolve().parent
    modules = _scan_modules(repo_root)
    if not modules:
        _die("no modules found")

    # Determine which modules to treat as changed
    if args.modules:
        for name in args.modules:
            if name not in modules:
                _die(
                    f"unknown module: {name!r}. "
                    "Run 'zerodep list' to see available modules."
                )
        changed = set(args.modules)
    else:
        status_map = _find_changed_modules(repo_root, modules)
        changed = {m for m, s in status_map.items() if s in ("modified", "new")}

    if not changed:
        _ok("all modules up-to-date, nothing to check")
        return

    reverse_deps = _build_reverse_deps(modules)
    affected = _transitive_dependents(changed, reverse_deps)
    downstream = affected - changed

    print(f"Changed modules: {', '.join(sorted(changed))}")
    if downstream:
        print(f"Affected downstream: {', '.join(sorted(downstream))}")
    print(f"Total modules to test: {len(affected)}")
    print()

    # Run tests
    results: list[tuple[str, str, str, str]] = []
    for mod_name in sorted(affected):
        test_file = _find_test_file(mod_name, modules, repo_root)
        is_changed = "yes" if mod_name in changed else "no"

        if test_file is None:
            results.append((mod_name, is_changed, "skip", "no test file"))
            continue

        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    str(test_file),
                    "-x",
                    "--tb=short",
                    "-q",
                ],
                cwd=repo_root,
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode == 0:
                results.append((mod_name, is_changed, "pass", ""))
            else:
                summary = result.stdout.strip().split("\n")[-1] if result.stdout else ""
                results.append((mod_name, is_changed, "FAIL", summary))
        except subprocess.TimeoutExpired:
            results.append((mod_name, is_changed, "FAIL", "timeout (120s)"))
        except subprocess.SubprocessError as e:
            results.append((mod_name, is_changed, "error", str(e)))

    # Print results table
    headers = ("Module", "Changed", "Test", "Detail")
    widths = [max(len(headers[i]), *(len(r[i]) for r in results)) for i in range(4)]
    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    print(fmt.format(*headers))
    print(fmt.format(*("-" * w for w in widths)))
    for row in results:
        print(fmt.format(*row))

    passed = sum(1 for r in results if r[2] == "pass")
    failed = sum(1 for r in results if r[2] == "FAIL")
    skipped = sum(1 for r in results if r[2] == "skip")
    print()
    parts = [f"{passed} passed"]
    if failed:
        parts.append(f"{failed} failed")
    if skipped:
        parts.append(f"{skipped} skipped")
    print(", ".join(parts))

    if failed:
        sys.exit(1)


def cmd_version(args: argparse.Namespace) -> None:
    """Print version."""
    _ok(f"zerodep {__version__}")


# ── CLI Entry Point ──


def main(argv: list[str] | None = None) -> None:
    """CLI dispatcher."""
    parser = argparse.ArgumentParser(
        prog="zerodep",
        description="Copy zero-dependency Python modules into your project.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            examples:
              zerodep list                   List all available modules
              zerodep info sse               Show module details and deps
              zerodep add scheduler          Copy scheduler.py to current dir
              zerodep add sse retry -d lib/  Copy sse + httpclient + retry to lib/
              zerodep add sse --nested       Copy into sse/ and httpclient/ subdirs
              zerodep add sse --no-deps      Copy only sse.py, skip httpclient
              zerodep manifest               Regenerate manifest.json
              zerodep version-check          Check for modules needing a bump
              zerodep dep-graph              Show all module dependencies
              zerodep dep-graph yaml         Show dependencies for yaml module
              zerodep dep-check              Test changed modules + dependents
              zerodep dep-check yaml config  Test specific modules + dependents
        """),
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="use only cached files, no network",
    )
    parser.add_argument(
        "--local",
        action="store_true",
        help="use local manifest.json instead of fetching from remote",
    )

    sub = parser.add_subparsers(dest="command")

    # list
    sub.add_parser("list", help="list available modules")

    # info
    p_info = sub.add_parser("info", help="show module details")
    p_info.add_argument("module", help="module name")

    # add
    p_add = sub.add_parser("add", help="copy modules to your project")
    p_add.add_argument("modules", nargs="+", help="module names to copy")
    p_add.add_argument("-d", "--dir", default=".", help="target directory (default: .)")
    p_add.add_argument(
        "--nested", action="store_true", help="use subdirectories per module"
    )
    p_add.add_argument("--no-deps", action="store_true", help="skip dependencies")
    p_add.add_argument("-y", "--yes", action="store_true", help="skip confirmation")
    p_add.add_argument(
        "-f", "--force", action="store_true", help="overwrite without prompt"
    )

    # update
    p_update = sub.add_parser("update", help="update existing modules")
    p_update.add_argument("modules", nargs="+", help="module names to update")
    p_update.add_argument(
        "-d", "--dir", default=".", help="target directory (default: .)"
    )
    p_update.add_argument(
        "--nested", action="store_true", help="use subdirectories per module"
    )
    p_update.add_argument("--no-deps", action="store_true", help="skip dependencies")

    # outdated
    sub.add_parser("outdated", help="check local files for upstream changes")

    # manifest
    sub.add_parser("manifest", help="regenerate manifest.json from source")

    # version-check
    sub.add_parser("version-check", help="check modules for uncommitted version bumps")

    # dep-graph
    p_depgraph = sub.add_parser("dep-graph", help="show module dependency graph")
    p_depgraph.add_argument(
        "module", nargs="?", default=None, help="specific module (default: all)"
    )

    # dep-check
    p_depcheck = sub.add_parser(
        "dep-check", help="test changed modules and their dependents"
    )
    p_depcheck.add_argument(
        "modules", nargs="*", default=[], help="modules to check (default: auto-detect)"
    )

    # version
    sub.add_parser("version", help="show version")

    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    commands = {
        "list": cmd_list,
        "info": cmd_info,
        "add": cmd_add,
        "update": cmd_update,
        "outdated": cmd_outdated,
        "manifest": cmd_manifest,
        "version-check": cmd_version_check,
        "dep-graph": cmd_dep_graph,
        "dep-check": cmd_dep_check,
        "version": cmd_version,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
