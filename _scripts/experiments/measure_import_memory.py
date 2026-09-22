#!/usr/bin/env python3
"""Experiment 1: Import-Time Memory Footprint.

Measures peak heap allocation (via tracemalloc) for importing each zerodep
module vs importing the reference library.

Methodology:
- For each module, spawn a fresh subprocess that:
  1. Starts tracemalloc
  2. Imports the module
  3. Prints peak memory (tracemalloc.get_traced_memory()[1])
- 10 repetitions per module, report median, p25, p75
- Fresh process per measurement to avoid import caching

Usage:
    python measure_import_memory.py --zerodep-root /path/to/zerodep
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import statistics
import subprocess
import sys
import textwrap
import venv
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Module <-> reference library mapping
# ---------------------------------------------------------------------------

# bench-* extras from pyproject.toml, with the primary reference package
# and its import name.  Each entry:
#   module_name -> {
#       "bench_extra": "bench-xxx",   # pyproject.toml optional-dependency key
#       "references": {
#           "PackageName==version": "import_name",
#           ...
#       }
#   }
#
# Only the *first* package in each bench extra is the primary reference.
# Some bench extras contain ancillary deps (e.g. Pillow for qrcode) that
# are needed but not measured.

MODULE_REFS: dict[str, dict] = {
    "yaml": {
        "bench_extra": "bench-yaml",
        "references": {"PyYAML==6.0.3": "yaml"},
    },
    "dotenv": {
        "bench_extra": "bench-dotenv",
        "references": {"python-dotenv==1.2.2": "dotenv"},
    },
    "jsonx": {
        "bench_extra": "bench-jsonx",
        "references": {
            "commentjson==0.9.0": "commentjson",
            "jsonlines==4.0.0": "jsonlines",
        },
    },
    "structlog": {
        "bench_extra": "bench-structlog",
        "references": {"structlog==25.5.0": "structlog"},
    },
    "retry": {
        "bench_extra": "bench-retry",
        "references": {"tenacity==9.1.4": "tenacity"},
    },
    "tabulate": {
        "bench_extra": "bench-tabulate",
        "references": {"tabulate==0.10.0": "tabulate"},
    },
    "soup": {
        "bench_extra": "bench-soup",
        "references": {"beautifulsoup4==4.14.3": "bs4"},
    },
    "validate": {
        "bench_extra": "bench-validate",
        "references": {"pydantic==2.13.0": "pydantic"},
    },
    "markdown": {
        "bench_extra": "bench-markdown",
        "references": {"mistune==3.3.3": "mistune"},
    },
    "diff": {
        "bench_extra": "bench-diff",
        "references": {"unidiff==0.7.5": "unidiff"},
    },
    "frontmatter": {
        "bench_extra": "bench-frontmatter",
        "references": {"python-frontmatter==1.1.0": "frontmatter"},
    },
    "config": {
        "bench_extra": "bench-config",
        "references": {"python-decouple==3.8": "decouple"},
    },
    "cache": {
        "bench_extra": "bench-cache",
        "references": {"cachetools==7.0.5": "cachetools"},
    },
    "xml": {
        "bench_extra": "bench-xml",
        "references": {"xmltodict==1.0.4": "xmltodict"},
    },
    "jsonrpc": {
        "bench_extra": "bench-jsonrpc",
        "references": {"jsonrpcserver==5.0.9": "jsonrpcserver"},
    },
    "semver": {
        "bench_extra": "bench-semver",
        "references": {"packaging==26.1": "packaging"},
    },
    "persistdict": {
        "bench_extra": "bench-persistdict",
        "references": {"sqlitedict==2.1.0": "sqlitedict"},
    },
    "sparse_search": {
        "bench_extra": "bench-search",
        "references": {"rank-bm25==0.2.2": "rank_bm25"},
    },
    "readability": {
        "bench_extra": "bench-readability",
        "references": {"readability-lxml==0.8.4.1": "readability"},
    },
    "useragent": {
        "bench_extra": "bench-useragent",
        "references": {"ua-generator>=2.0.0": "ua_generator"},
    },
    "multipart": {
        "bench_extra": "bench-multipart",
        "references": {"python-multipart>=0.0.20": "multipart"},
    },
    "aes": {
        "bench_extra": "bench-aes",
        "references": {"pycryptodome==3.23.0": "Crypto"},
    },
    "qr": {
        "bench_extra": "bench-qr",
        "references": {"qrcode==8.2": "qrcode"},
    },
    "protobuf": {
        "bench_extra": "bench-protobuf",
        "references": {"protobuf==7.34.1": "google.protobuf"},
    },
    "jsonschema": {
        "bench_extra": "bench-jsonschema",
        "references": {"jsonschema==4.23.0": "jsonschema"},
    },
    "runner": {
        "bench_extra": "bench-runner",
        "references": {"sh==2.2.4": "sh"},
    },
    "ratelimit": {
        "bench_extra": "bench-ratelimit",
        "references": {"limits==5.8.0": "limits"},
    },
    "profiler": {
        "bench_extra": "bench-profiler",
        "references": {"pyinstrument>=5.0.0": "pyinstrument"},
    },
    "scheduler": {
        "bench_extra": "bench-scheduler",
        "references": {"APScheduler==3.11.2": "apscheduler"},
    },
    "sse": {
        "bench_extra": "bench-sse",
        "references": {"httpx-sse==0.4.3": "httpx_sse"},
    },
    "httpclient": {
        "bench_extra": "bench-http",
        "references": {"httpx==0.28.1": "httpx"},
    },
    "png": {
        "bench_extra": "bench-png",
        "references": {"Pillow==12.3.0": "PIL"},
    },
}

# Modules that have no bench-* reference — import-only zerodep measurement
ZERODEP_ONLY_MODULES = [
    "ansi",
    "filelock",
    "llmstxt",
    "prompt",
    "synctex",
    "toon",
    "vcs",
    "depdetect",
    "skills",
    "a2a",
    "acp",
    "httpserver",
    "websocket",
    "cdp",
    "s3",
]

REPETITIONS = 10

# Stripped environment for fair measurement
_STRIP_VARS = {"PYTHONPATH", "PYTHONSTARTUP", "PYTHONCASEOK"}


def _make_clean_env() -> dict[str, str]:
    """Build a clean environment for subprocess measurements."""
    env = {k: v for k, v in os.environ.items() if k not in _STRIP_VARS}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def _zerodep_import_snippet(module_dir: str, module_name: str) -> str:
    """Python snippet that measures peak tracemalloc for a zerodep import."""
    return textwrap.dedent(f"""\
        import sys, tracemalloc
        sys.path.insert(0, {module_dir!r})
        tracemalloc.start()
        import {module_name}
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(peak)
    """)


def _reference_import_snippet(import_name: str) -> str:
    """Python snippet that measures peak tracemalloc for a reference import."""
    return textwrap.dedent(f"""\
        import tracemalloc
        tracemalloc.start()
        import {import_name}
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(peak)
    """)


def _run_memory_measurement(
    python: str, snippet: str, env: dict[str, str]
) -> int | None:
    """Run a snippet in a subprocess and return peak memory in bytes."""
    try:
        result = subprocess.run(
            [python, "-c", snippet],
            capture_output=True,
            text=True,
            timeout=60,
            env=env,
        )
        if result.returncode != 0:
            return None
        return int(result.stdout.strip())
    except (subprocess.TimeoutExpired, ValueError, OSError):
        return None


def _percentile(data: list[int], p: float) -> int:
    """Compute the p-th percentile (0-100) of a sorted list."""
    if not data:
        return 0
    k = (len(data) - 1) * p / 100.0
    f = int(k)
    c = f + 1
    if c >= len(data):
        return data[f]
    return int(data[f] + (k - f) * (data[c] - data[f]))


def _compute_stats(raw: list[int]) -> dict:
    """Compute median, p25, p75 from raw measurements."""
    s = sorted(raw)
    return {
        "median_bytes": int(statistics.median(s)),
        "p25_bytes": _percentile(s, 25),
        "p75_bytes": _percentile(s, 75),
        "raw": raw,
    }


def _ensure_venv(venv_dir: Path, packages: list[str], python: str) -> str:
    """Create a venv and install packages if needed. Return venv python path."""
    venv_python = venv_dir / "bin" / "python"
    if venv_python.exists():
        # Check if all packages are installed
        result = subprocess.run(
            [str(venv_python), "-m", "pip", "list", "--format=json"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            installed = {p["name"].lower() for p in json.loads(result.stdout)}
            # Rough check: see if the first package name is installed
            pkg_name = packages[0].split("==")[0].split(">=")[0].lower()
            if pkg_name in installed:
                return str(venv_python)

    print(f"  Creating venv at {venv_dir} ...")
    venv.create(str(venv_dir), with_pip=True, clear=True)
    # Install packages
    cmd = [str(venv_python), "-m", "pip", "install", "-q"] + packages
    subprocess.run(cmd, check=True, timeout=300, capture_output=True)
    return str(venv_python)


def _get_venv_dir(results_dir: Path, bench_extra: str) -> Path:
    """Return the venv directory for a given bench extra."""
    return results_dir / "venvs" / bench_extra


def measure_module(
    module_name: str,
    zerodep_root: Path,
    results_dir: Path,
    system_python: str,
    env: dict[str, str],
    repetitions: int,
) -> dict | None:
    """Measure import memory for one module (zerodep + references)."""
    module_dir = zerodep_root / module_name
    module_py = module_dir / f"{module_name}.py"

    if not module_py.exists():
        print(f"  [SKIP] {module_name}: {module_py} not found")
        return None

    result: dict = {}

    # --- Zerodep measurement ---
    snippet = _zerodep_import_snippet(str(module_dir), module_name)
    raw_zd: list[int] = []
    for i in range(repetitions):
        val = _run_memory_measurement(system_python, snippet, env)
        if val is not None:
            raw_zd.append(val)
        if (i + 1) % 5 == 0:
            sys.stdout.write(".")
            sys.stdout.flush()

    if not raw_zd:
        print(f"  [FAIL] {module_name}: zerodep import failed all {repetitions} reps")
        return None

    result["zerodep"] = _compute_stats(raw_zd)

    # --- Reference measurements ---
    if module_name in MODULE_REFS:
        ref_info = MODULE_REFS[module_name]
        bench_extra = ref_info["bench_extra"]
        references = ref_info["references"]

        # Create venv with all packages from this bench extra
        all_packages = list(references.keys())
        venv_dir = _get_venv_dir(results_dir, bench_extra)
        try:
            venv_python = _ensure_venv(venv_dir, all_packages, system_python)
        except (subprocess.CalledProcessError, OSError) as exc:
            print(f"  [WARN] {module_name}: venv setup failed: {exc}")
            result["references"] = {}
            return result

        ref_results: dict = {}
        for pkg_spec, import_name in references.items():
            snippet = _reference_import_snippet(import_name)
            raw_ref: list[int] = []
            for i in range(repetitions):
                val = _run_memory_measurement(venv_python, snippet, env)
                if val is not None:
                    raw_ref.append(val)

            if raw_ref:
                ref_results[pkg_spec] = _compute_stats(raw_ref)
            else:
                print(f"  [WARN] {module_name}: ref {pkg_spec} import failed")

        result["references"] = ref_results

        # Compute ratio (zerodep median / first reference median)
        if ref_results:
            first_ref_stats = next(iter(ref_results.values()))
            zd_median = result["zerodep"]["median_bytes"]
            ref_median = first_ref_stats["median_bytes"]
            if ref_median > 0:
                result["ratio"] = round(ref_median / zd_median, 1)
    else:
        result["references"] = {}

    return result


def print_summary_table(modules: dict) -> None:
    """Print a human-readable summary table to stdout."""
    hdr = (
        f"{'Module':<16} {'Zerodep (B)':>14} "
        f"{'Reference':>30} {'Ref (B)':>14} {'Ratio':>8}"
    )
    print("\n" + "=" * len(hdr))
    print(hdr)
    print("-" * len(hdr))

    for mod_name in sorted(modules.keys()):
        data = modules[mod_name]
        zd = data["zerodep"]["median_bytes"]
        refs = data.get("references", {})
        if refs:
            for pkg_spec, ref_stats in refs.items():
                ref_median = ref_stats["median_bytes"]
                ratio = data.get("ratio", "")
                ratio_str = f"{ratio}x" if ratio else "N/A"
                row = (
                    f"{mod_name:<16} {zd:>14,} "
                    f"{pkg_spec:>30} {ref_median:>14,} "
                    f"{ratio_str:>8}"
                )
                print(row)
                mod_name = ""  # blank for subsequent refs
                zd = ""  # type: ignore[assignment]
        else:
            print(f"{mod_name:<16} {zd:>14,} {'(no reference)':>30} {'':>14} {'':>8}")

    print("=" * len(hdr))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Experiment 1: Import-Time Memory Footprint"
    )
    parser.add_argument(
        "--zerodep-root",
        type=Path,
        required=True,
        help="Path to zerodep project root",
    )
    parser.add_argument(
        "--repetitions",
        type=int,
        default=REPETITIONS,
        help=f"Number of repetitions per measurement (default: {REPETITIONS})",
    )
    parser.add_argument(
        "--modules",
        nargs="*",
        default=None,
        help="Specific modules to measure (default: all)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output JSON path (default: results/import_memory.json)",
    )
    args = parser.parse_args()

    zerodep_root = args.zerodep_root.resolve()
    if not (zerodep_root / "pyproject.toml").exists():
        print(f"Error: {zerodep_root} does not look like a zerodep project root")
        sys.exit(1)

    script_dir = Path(__file__).resolve().parent
    results_dir = script_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    output_path = args.output or (results_dir / "import_memory.json")
    system_python = sys.executable
    env = _make_clean_env()

    # Determine which modules to measure
    all_module_names = sorted(set(MODULE_REFS.keys()) | set(ZERODEP_ONLY_MODULES))
    if args.modules:
        target_modules = [m for m in args.modules if m in all_module_names]
        if not target_modules:
            print(f"Error: none of {args.modules} are known modules")
            sys.exit(1)
    else:
        target_modules = all_module_names

    print(f"Measuring import memory for {len(target_modules)} modules")
    print(f"  zerodep root: {zerodep_root}")
    print(f"  python: {system_python}")
    print(f"  repetitions: {args.repetitions}")
    print(f"  output: {output_path}")
    print()

    modules_data: dict = {}
    for mod_name in target_modules:
        print(f"[{mod_name}] ", end="", flush=True)
        data = measure_module(
            mod_name,
            zerodep_root,
            results_dir,
            system_python,
            env,
            args.repetitions,
        )
        if data is not None:
            modules_data[mod_name] = data
            zd = data["zerodep"]["median_bytes"]
            refs = data.get("references", {})
            if refs:
                first_ref = next(iter(refs.values()))
                ratio = data.get("ratio", "?")
                print(
                    f" zerodep={zd:,}B, ref={first_ref['median_bytes']:,}B, "
                    f"ratio={ratio}x"
                )
            else:
                print(f" zerodep={zd:,}B (no reference)")
        else:
            print(" SKIPPED")

    # Build output
    output = {
        "metadata": {
            "python_version": platform.python_version(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "hostname": platform.node(),
            "platform": platform.platform(),
            "repetitions": args.repetitions,
        },
        "modules": modules_data,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nResults written to {output_path}")

    print_summary_table(modules_data)


if __name__ == "__main__":
    main()
