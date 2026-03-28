"""zerodep CLI — copy zero-dependency Python modules into your project.

Usage::

    python zerodep.py list                  # list available modules
    python zerodep.py info <module>         # module details + deps
    python zerodep.py add <module> [...]    # copy modules to cwd
    python zerodep.py manifest              # regenerate manifest.json

Requires Python 3.10+, zero external dependencies.
"""

from __future__ import annotations

__version__ = "0.1.0"

import argparse
import ast
import json
import shutil
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


# ── Manifest Generation ──

# Directories/files to skip when scanning for modules
_SKIP_DIRS = {
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

                    modules[mod_name] = {
                        "description": description,
                        "files": files,
                        "version": version,
                        "deps": deps,
                    }

            # Recurse into subdirectories
            _walk(entry)

    _walk(repo_root)
    return modules


def _extract_frontmatter(source: str) -> dict[str, str | list]:
    """Extract metadata from ``# /// zerodep`` frontmatter block.

    Parses a PEP 723-style comment block::

        # /// zerodep
        # version = "0.1.0"
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

    # Column widths
    name_w = max(len(n) for n in modules)
    ver_w = max(len(m.get("version", "")) for m in modules.values())

    header = f"  {'Module':<{name_w}}  {'Version':<{ver_w}}  Description"
    _ok(header)
    _ok(f"  {'-' * name_w}  {'-' * ver_w}  {'-' * 40}")

    for name in sorted(modules):
        mod = modules[name]
        ver = mod.get("version", "?")
        desc = mod.get("description", "")
        # Truncate description
        max_desc = shutil.get_terminal_size((80, 24)).columns - name_w - ver_w - 8
        if max_desc > 10 and len(desc) > max_desc:
            desc = desc[: max_desc - 3] + "..."
        _ok(f"  {name:<{name_w}}  {ver:<{ver_w}}  {desc}")

    _ok(f"\n  {len(modules)} modules available")


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
        dest.write_bytes(data)
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

    # manifest
    sub.add_parser("manifest", help="regenerate manifest.json from source")

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
        "manifest": cmd_manifest,
        "version": cmd_version,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
