#!/usr/bin/env python3
"""Measure install footprint of zerodep modules vs their reference libraries.

For each zerodep module that has a bench-* reference in pyproject.toml:
  - Measures the zerodep single-file size (bytes)
  - For each reference package: creates a fresh venv, installs it, and measures
    wheel size, installed size, and transitive dependency count
  - For multi-package bench groups: also measures the combined install

Outputs JSON to results/install_footprint.json and prints a summary table.

Usage::

    python measure_install_footprint.py --zerodep-root /path/to/zerodep
    python measure_install_footprint.py  # auto-detects from script location
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

# ── Bench-name → module directory mapping ──
# Most bench-* keys match the directory name, but a few differ.
BENCH_TO_MODULE_DIR = {
    "http": "httpclient",
    "search": "sparse_search",
}


def _module_dir_for_bench(bench_name: str) -> str:
    """Return the module directory name for a bench-* key."""
    return BENCH_TO_MODULE_DIR.get(bench_name, bench_name)


def _module_file(zerodep_root: Path, module_dir: str) -> Path | None:
    """Return the path to the main module .py file, or None if not found."""
    candidate = zerodep_root / module_dir / f"{module_dir}.py"
    if candidate.exists():
        return candidate
    return None


# ── pyproject.toml parsing ──


def parse_bench_extras(pyproject_path: Path) -> dict[str, list[str]]:
    """Parse bench-* optional-dependencies from pyproject.toml.

    Returns a dict mapping bench group name (without 'bench-' prefix) to
    a list of package specifiers (e.g. ["PyYAML==6.0.3"]).
    """
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib  # type: ignore[no-redef]

    text = pyproject_path.read_text(encoding="utf-8")
    data = tomllib.loads(text)

    extras = data.get("project", {}).get("optional-dependencies", {})
    bench_groups: dict[str, list[str]] = {}
    for key, deps in extras.items():
        if key.startswith("bench-"):
            bench_name = key[len("bench-") :]
            bench_groups[bench_name] = deps
    return bench_groups


# ── Venv + measurement helpers ──


def _run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    """Run a command, raising on failure."""
    return subprocess.run(cmd, capture_output=True, text=True, check=True, **kwargs)


def _venv_python(venv_dir: Path) -> Path:
    """Return the python executable inside a venv."""
    if sys.platform == "win32":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def create_venv(venv_dir: Path) -> Path:
    """Create a fresh venv and return its python path."""
    _run([sys.executable, "-m", "venv", str(venv_dir)])
    return _venv_python(venv_dir)


def measure_baseline_venv(python: str) -> int:
    """Measure the site-packages size of a fresh venv (bytes)."""
    result = _run(
        [
            python,
            "-c",
            "import sysconfig; print(sysconfig.get_path('purelib'))",
        ]
    )
    site_packages = Path(result.stdout.strip())
    return _dir_size(site_packages)


def _dir_size(path: Path) -> int:
    """Recursively sum file sizes under path (bytes)."""
    total = 0
    for dirpath, _dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            try:
                total += os.path.getsize(fp)
            except OSError:
                pass
    return total


def install_and_measure(
    packages: list[str],
    label: str,
    baseline_bytes: int,
) -> dict | None:
    """Install packages into a fresh venv and measure footprint.

    Returns a dict with wheel_bytes, installed_bytes, transitive_deps, etc.
    Returns None if installation fails.
    """
    tmpdir = tempfile.mkdtemp(prefix="zerodep_footprint_")
    try:
        venv_dir = Path(tmpdir) / "venv"
        venv_python = str(create_venv(venv_dir))

        # Install the packages
        install_cmd = [venv_python, "-m", "pip", "install", "-q"] + packages
        try:
            _run(install_cmd)
        except subprocess.CalledProcessError as exc:
            print(f"  WARNING: install failed for {label}: {exc.stderr[:200]}")
            return None

        # Count transitive deps (pip list minus pip and setuptools)
        result = _run([venv_python, "-m", "pip", "list", "--format=json"])
        all_pkgs = json.loads(result.stdout)
        skip = {"pip", "setuptools"}
        transitive = [p["name"] for p in all_pkgs if p["name"].lower() not in skip]

        # Measure installed size
        result = _run(
            [
                venv_python,
                "-c",
                "import sysconfig; print(sysconfig.get_path('purelib'))",
            ]
        )
        site_packages = Path(result.stdout.strip())
        installed_bytes = _dir_size(site_packages) - baseline_bytes

        return {
            "installed_bytes": max(0, installed_bytes),
            "transitive_deps": sorted(transitive),
            "transitive_dep_count": len(transitive),
        }
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def download_wheel(package_spec: str) -> int | None:
    """Download a single wheel (no deps) and return its size in bytes.

    Returns None on failure.
    """
    tmpdir = tempfile.mkdtemp(prefix="zerodep_wheel_")
    try:
        cmd = [
            sys.executable,
            "-m",
            "pip",
            "download",
            "--no-deps",
            "-d",
            tmpdir,
            package_spec,
        ]
        try:
            _run(cmd)
        except subprocess.CalledProcessError as exc:
            msg = f"wheel download failed for {package_spec}"
            print(f"  WARNING: {msg}: {exc.stderr[:200]}")
            return None

        # Find the downloaded file
        files = list(Path(tmpdir).iterdir())
        if not files:
            return None
        return sum(f.stat().st_size for f in files)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


# ── Main measurement loop ──


def measure_all(
    zerodep_root: Path,
    only_modules: list[str] | None = None,
) -> dict:
    """Run all measurements and return the results dict.

    Args:
        zerodep_root: Path to the zerodep repo root.
        only_modules: If given, only measure these bench group names
            (e.g. ["yaml", "dotenv"]).  Default: measure all.
    """
    pyproject = zerodep_root / "pyproject.toml"
    bench_groups = parse_bench_extras(pyproject)

    if only_modules:
        total = len(bench_groups)
        bench_groups = {k: v for k, v in bench_groups.items() if k in only_modules}
        print(f"Measuring {len(bench_groups)} of {total} bench-* groups")
    else:
        print(f"Found {len(bench_groups)} bench-* groups in pyproject.toml")
    print()

    # Measure baseline venv size once
    print("Measuring baseline venv size...")
    baseline_tmpdir = tempfile.mkdtemp(prefix="zerodep_baseline_")
    try:
        baseline_venv = Path(baseline_tmpdir) / "venv"
        baseline_python = str(create_venv(baseline_venv))
        baseline_bytes = measure_baseline_venv(baseline_python)
        print(f"  Baseline site-packages: {baseline_bytes:,} bytes")
    finally:
        shutil.rmtree(baseline_tmpdir, ignore_errors=True)

    results: dict = {
        "metadata": {
            "python_version": platform.python_version(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "hostname": platform.node(),
            "platform": platform.platform(),
        },
        "baseline_venv_bytes": baseline_bytes,
        "modules": {},
    }

    for bench_name in sorted(bench_groups):
        packages = bench_groups[bench_name]
        module_dir = _module_dir_for_bench(bench_name)
        module_file = _module_file(zerodep_root, module_dir)

        if module_file is None:
            path = f"{module_dir}/{module_dir}.py"
            print(f"[{bench_name}] not found: {path}, skipping")
            continue

        zerodep_bytes = module_file.stat().st_size
        rel = f"{module_dir}/{module_dir}.py"
        print(f"[{bench_name}] zerodep: {rel} = {zerodep_bytes:,} B")

        module_result: dict = {
            "zerodep_file": str(module_file.relative_to(zerodep_root)),
            "zerodep_bytes": zerodep_bytes,
            "references": {},
        }

        # Measure each reference package individually
        for pkg_spec in packages:
            print(f"  Measuring {pkg_spec} ...")

            # Download wheel to get wheel-only size
            wheel_bytes = download_wheel(pkg_spec)

            # Install in fresh venv to get installed size + deps
            info = install_and_measure([pkg_spec], pkg_spec, baseline_bytes)

            ref_result: dict = {}
            if wheel_bytes is not None:
                ref_result["wheel_bytes"] = wheel_bytes
            if info is not None:
                ref_result.update(info)

            if ref_result:
                module_result["references"][pkg_spec] = ref_result

        # For multi-package groups, also measure combined install
        if len(packages) > 1:
            combined_label = " + ".join(packages)
            print(f"  Measuring combined: {combined_label} ...")
            combined_info = install_and_measure(
                packages, combined_label, baseline_bytes
            )
            if combined_info is not None:
                module_result["references"][combined_label] = combined_info

        results["modules"][module_dir] = module_result
        print()

    return results


def format_bytes(b: int) -> str:
    """Format bytes as human-readable string."""
    if b < 1024:
        return f"{b} B"
    if b < 1024 * 1024:
        return f"{b / 1024:.1f} KB"
    return f"{b / (1024 * 1024):.1f} MB"


def print_summary(results: dict) -> None:
    """Print a summary table to stdout."""
    modules = results["modules"]
    if not modules:
        print("No modules measured.")
        return

    # Header
    print()
    print("=" * 100)
    print("INSTALL FOOTPRINT SUMMARY")
    print("=" * 100)
    print(
        f"{'Module':<20} {'Zerodep':<12} {'Reference':<30} "
        f"{'Wheel':<12} {'Installed':<12} {'Deps':>5}"
    )
    print("-" * 100)

    for mod_name in sorted(modules):
        mod = modules[mod_name]
        zd = format_bytes(mod["zerodep_bytes"])
        refs = mod["references"]

        first = True
        for ref_name, ref_data in refs.items():
            wheel = (
                format_bytes(ref_data.get("wheel_bytes", 0))
                if "wheel_bytes" in ref_data
                else "--"
            )
            installed = (
                format_bytes(ref_data.get("installed_bytes", 0))
                if "installed_bytes" in ref_data
                else "--"
            )
            deps = str(ref_data.get("transitive_dep_count", "--"))

            row = f"{ref_name:<30} {wheel:<12} {installed:<12} {deps:>5}"
            if first:
                print(f"{mod_name:<20} {zd:<12} {row}")
                first = False
            else:
                print(f"{'':<20} {'':<12} {row}")

        if not refs:
            print(f"{mod_name:<20} {zd:<12} {'(all failed)':<30}")

    print("=" * 100)
    print(f"Python: {results['metadata']['python_version']}")
    baseline = format_bytes(results["baseline_venv_bytes"])
    print(f"Baseline venv site-packages: {baseline}")
    print()


# ── CLI ──


def main() -> None:
    """Entry point."""
    parser = argparse.ArgumentParser(
        description=(
            "Measure install footprint of zerodep modules vs reference libraries."
        ),
    )
    parser.add_argument(
        "--zerodep-root",
        type=Path,
        default=None,
        help="Path to zerodep repo root (default: auto-detect from script location)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help=("Output JSON path (default: results/install_footprint.json)"),
    )
    parser.add_argument(
        "--modules",
        nargs="*",
        default=None,
        help="Only measure these bench groups (e.g. yaml dotenv). Default: all.",
    )
    args = parser.parse_args()

    # Resolve zerodep root
    if args.zerodep_root:
        zerodep_root = args.zerodep_root.resolve()
    else:
        # Auto-detect: script is at _scripts/experiments/measure_install_footprint.py
        zerodep_root = Path(__file__).resolve().parent.parent.parent

    if not (zerodep_root / "pyproject.toml").exists():
        print(f"ERROR: pyproject.toml not found at {zerodep_root}", file=sys.stderr)
        sys.exit(1)

    print(f"Zerodep root: {zerodep_root}")

    # Run measurements (filtered if --modules given)
    results = measure_all(zerodep_root, only_modules=args.modules)

    # Write JSON output
    if args.output:
        output_path = args.output
    else:
        output_path = zerodep_root / "results" / "install_footprint.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(results, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Results written to {output_path}")

    # Print summary
    print_summary(results)


if __name__ == "__main__":
    main()
