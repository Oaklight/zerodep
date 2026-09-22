#!/usr/bin/env python3
"""Measure supply-chain attack surface of reference libraries vs zerodep modules.

For each bench-* extra defined in pyproject.toml, this script:
  1. Creates a fresh venv and installs the reference libraries.
  2. Counts transitive dependencies (pip list).
  3. Counts total third-party lines of Python code (pip show --files).
  4. Runs pip-audit to find known CVEs.
  5. Queries the PyPI JSON API for maintainer usernames of each transitive dep.

zerodep modules have zero third-party deps, so all metrics are 0 by design.

Usage:
    python measure_supply_chain.py --zerodep-root /path/to/zerodep
"""

from __future__ import annotations

import argparse
import json
import logging
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

try:
    import tomllib
except ImportError:
    tomllib = None  # type: ignore[assignment]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# Packages that pip always installs but are not "real" dependencies
_BASELINE_PKGS = {"pip", "setuptools", "wheel", "pkg_resources"}


# ---------------------------------------------------------------------------
# pyproject.toml parsing
# ---------------------------------------------------------------------------


def parse_bench_extras(pyproject_path: Path) -> dict[str, list[str]]:
    """Return {module_name: [pinned_req, ...]} from bench-* optional-deps."""
    if tomllib is None:
        raise RuntimeError("Python 3.11+ required (tomllib)")
    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)
    extras = data.get("project", {}).get("optional-dependencies", {})
    result: dict[str, list[str]] = {}
    for key, reqs in extras.items():
        if key.startswith("bench-"):
            module_name = key.removeprefix("bench-")
            result[module_name] = list(reqs)
    return result


# ---------------------------------------------------------------------------
# Venv helpers
# ---------------------------------------------------------------------------


def create_venv(venv_dir: Path) -> Path:
    """Create a fresh venv and return the python executable path."""
    subprocess.run(
        [sys.executable, "-m", "venv", str(venv_dir)],
        check=True,
        capture_output=True,
    )
    python = venv_dir / "bin" / "python"
    if not python.exists():
        python = venv_dir / "Scripts" / "python.exe"  # Windows fallback
    return python


def install_packages(python: Path, requirements: list[str]) -> None:
    """pip install a list of requirements into the venv."""
    subprocess.run(
        [str(python), "-m", "pip", "install", "--quiet", *requirements],
        check=True,
        capture_output=True,
    )


def pip_list(python: Path) -> list[dict]:
    """Return pip list --format=json output as parsed list."""
    result = subprocess.run(
        [str(python), "-m", "pip", "list", "--format=json"],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


# ---------------------------------------------------------------------------
# Metric 1: Transitive dependency count
# ---------------------------------------------------------------------------


def get_transitive_deps(python: Path) -> list[str]:
    """Return sorted list of non-baseline package names installed in the venv."""
    pkgs = pip_list(python)
    return sorted(p["name"] for p in pkgs if p["name"].lower() not in _BASELINE_PKGS)


# ---------------------------------------------------------------------------
# Metric 2: Total third-party LOC
# ---------------------------------------------------------------------------


def get_site_packages(python: Path) -> Path | None:
    """Return the site-packages directory for the venv."""
    result = subprocess.run(
        [
            str(python),
            "-c",
            "import site; print(site.getsitepackages()[0])",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    sp = Path(result.stdout.strip())
    return sp if sp.is_dir() else None


def count_loc_for_package(python: Path, pkg_name: str) -> int:
    """Count lines of .py files belonging to a package via pip show --files."""
    result = subprocess.run(
        [str(python), "-m", "pip", "show", "--files", pkg_name],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return 0

    # Parse the Location and Files from pip show output
    location = ""
    in_files = False
    files: list[str] = []
    for line in result.stdout.splitlines():
        if line.startswith("Location:"):
            location = line.split(":", 1)[1].strip()
        elif line.startswith("Files:"):
            in_files = True
        elif in_files:
            stripped = line.strip()
            if stripped:
                files.append(stripped)

    if not location:
        return 0

    loc_dir = Path(location)
    total = 0
    for rel_path in files:
        if not rel_path.endswith(".py"):
            continue
        full_path = loc_dir / rel_path
        if full_path.is_file():
            try:
                total += sum(1 for _ in full_path.open("r", errors="replace"))
            except OSError:
                pass
    return total


def count_total_loc(python: Path, dep_names: list[str]) -> int:
    """Sum LOC across all transitive dependencies."""
    total = 0
    for pkg in dep_names:
        loc = count_loc_for_package(python, pkg)
        log.debug("  LOC for %s: %d", pkg, loc)
        total += loc
    return total


# ---------------------------------------------------------------------------
# Metric 3: Known CVE count (pip-audit)
# ---------------------------------------------------------------------------


def run_pip_audit(python: Path) -> list[dict]:
    """Run pip-audit in the venv and return list of vulnerability dicts.

    Each dict has keys: id, package, severity (if available).
    pip-audit must be installed in the *measurement* environment (not the venv).
    We run it pointing at the venv's python.
    """
    # Try running pip-audit as a subprocess; it needs to audit the venv
    try:
        result = subprocess.run(
            [
                "pip-audit",
                "--python",
                str(python),
                "--format=json",
                "--output=-",
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
    except FileNotFoundError:
        log.warning("pip-audit not found in PATH; skipping CVE check")
        return []
    except subprocess.TimeoutExpired:
        log.warning("pip-audit timed out")
        return []

    # pip-audit exits non-zero when vulnerabilities are found; that's fine
    stdout = result.stdout.strip()
    if not stdout:
        return []

    try:
        data = json.loads(stdout)
    except json.JSONDecodeError:
        log.warning("Failed to parse pip-audit JSON output")
        return []

    # pip-audit JSON format: {"dependencies": [{"name": ..., "vulns": [...]}]}
    cves = []
    for dep in data.get("dependencies", []):
        pkg = dep.get("name", "unknown")
        for vuln in dep.get("vulns", []):
            cves.append(
                {
                    "id": vuln.get("id", "UNKNOWN"),
                    "package": pkg,
                    "severity": vuln.get("fix_versions", ["unknown"])[0]
                    if vuln.get("fix_versions")
                    else "unknown",
                }
            )
    return cves


# ---------------------------------------------------------------------------
# Metric 4: Maintainer count (PyPI JSON API)
# ---------------------------------------------------------------------------


def query_pypi_maintainers(pkg_name: str) -> list[str]:
    """Query PyPI JSON API for maintainer/author usernames of a package.

    Returns a list of unique usernames. Handles network failures gracefully.
    """
    url = f"https://pypi.org/pypi/{pkg_name}/json"
    req = Request(url, headers={"Accept": "application/json"})
    try:
        with urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
    except (URLError, OSError, json.JSONDecodeError) as exc:
        log.warning("PyPI API failed for %s: %s", pkg_name, exc)
        return []

    maintainers: set[str] = set()

    # info.author / info.maintainer (older projects)
    for field in ("author", "maintainer"):
        name = data.get("info", {}).get(field)
        if name and name.strip():
            maintainers.add(name.strip())

    # info.author_email / info.maintainer_email (extract name or email)
    for field in ("author_email", "maintainer_email"):
        email = data.get("info", {}).get(field)
        if email and email.strip():
            # Some emails are "Name <email>" format
            for part in email.split(","):
                part = part.strip()
                if "<" in part:
                    name = part.split("<")[0].strip()
                    if name:
                        maintainers.add(name)
                elif "@" in part:
                    maintainers.add(part)

    return sorted(maintainers)


def collect_maintainers(dep_names: list[str]) -> list[str]:
    """Collect unique maintainers across all transitive deps, with rate limiting."""
    all_maintainers: set[str] = set()
    for i, pkg in enumerate(dep_names):
        maintainers = query_pypi_maintainers(pkg)
        all_maintainers.update(maintainers)
        log.debug("  Maintainers for %s: %s", pkg, maintainers)
        # Rate limit: 1s delay between calls (skip after last)
        if i < len(dep_names) - 1:
            time.sleep(1)
    return sorted(all_maintainers)


# ---------------------------------------------------------------------------
# Per-module measurement
# ---------------------------------------------------------------------------


def measure_module(
    module_name: str,
    requirements: list[str],
    tmpdir: Path,
    skip_pypi: bool = False,
) -> dict:
    """Measure all supply-chain metrics for one bench-* group.

    Returns a dict keyed by the pinned requirement string (e.g., "PyYAML==6.0.3").
    """
    label = ", ".join(requirements)
    log.info("Measuring module '%s': %s", module_name, label)

    venv_dir = tmpdir / f"venv-{module_name}"
    python = create_venv(venv_dir)
    install_packages(python, requirements)

    deps = get_transitive_deps(python)
    log.info("  Transitive deps (%d): %s", len(deps), deps)

    total_loc = count_total_loc(python, deps)
    log.info("  Total third-party LOC: %d", total_loc)

    cves = run_pip_audit(python)
    log.info("  Known CVEs: %d", len(cves))

    if skip_pypi:
        maintainers: list[str] = []
        log.info("  Skipping PyPI maintainer query (--skip-pypi)")
    else:
        maintainers = collect_maintainers(deps)
        log.info("  Unique maintainers: %d", len(maintainers))

    # Clean up venv to save disk space
    shutil.rmtree(venv_dir, ignore_errors=True)

    # Key by the requirement string for output clarity
    req_key = ", ".join(requirements)
    return {
        req_key: {
            "transitive_deps": deps,
            "transitive_dep_count": len(deps),
            "total_third_party_loc": total_loc,
            "known_cves": cves,
            "known_cve_count": len(cves),
            "maintainers": maintainers,
            "maintainer_count": len(maintainers),
        }
    }


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------


def compute_aggregates(modules: dict) -> dict:
    """Compute deduplicated aggregate metrics across all modules."""
    all_deps: set[str] = set()
    all_cve_ids: set[str] = set()
    all_maintainers: set[str] = set()
    total_loc = 0

    for module_data in modules.values():
        refs = module_data.get("references", {})
        for ref_data in refs.values():
            for dep in ref_data.get("transitive_deps", []):
                all_deps.add(dep)
            for cve in ref_data.get("known_cves", []):
                all_cve_ids.add(cve.get("id", ""))
            all_maintainers.update(ref_data.get("maintainers", []))

    # For LOC deduplication: we need to re-measure shared deps once.
    # Since we've already torn down venvs, use the per-module totals
    # but note that shared deps (e.g., httpx in bench-http and bench-sse)
    # would be counted in each module's total. For a conservative aggregate,
    # we sum the per-module LOC (this slightly over-counts for shared deps).
    # A more precise approach would require keeping venvs alive or caching
    # per-dep LOC values. We flag this in the output.
    for module_data in modules.values():
        refs = module_data.get("references", {})
        for ref_data in refs.values():
            total_loc += ref_data.get("total_third_party_loc", 0)

    return {
        "total_unique_transitive_deps": len(all_deps),
        "total_third_party_loc": total_loc,
        "total_third_party_loc_note": (
            "sum of per-module LOC; shared deps may be counted in each module"
        ),
        "total_known_cves": len(all_cve_ids),
        "total_unique_maintainers": len(all_maintainers),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Measure supply-chain attack surface of reference libraries."
    )
    parser.add_argument(
        "--zerodep-root",
        type=Path,
        required=True,
        help="Path to the zerodep repository root",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output JSON path (default: <zerodep-root>/results/supply_chain.json)",
    )
    parser.add_argument(
        "--modules",
        nargs="*",
        default=None,
        help="Only measure these modules (e.g., yaml http). "
        "Default: all bench-* extras.",
    )
    parser.add_argument(
        "--skip-pypi",
        action="store_true",
        help="Skip PyPI API queries for maintainer info (faster, offline-safe)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    zerodep_root = args.zerodep_root.resolve()
    pyproject_path = zerodep_root / "pyproject.toml"
    if not pyproject_path.exists():
        log.error("pyproject.toml not found at %s", pyproject_path)
        sys.exit(1)

    output_path = args.output or (zerodep_root / "results" / "supply_chain.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Parse bench-* extras
    bench_extras = parse_bench_extras(pyproject_path)
    log.info("Found %d bench-* extras in pyproject.toml", len(bench_extras))

    # Filter modules if requested
    if args.modules:
        filtered = {}
        for m in args.modules:
            if m in bench_extras:
                filtered[m] = bench_extras[m]
            else:
                log.warning("Module '%s' not found in bench-* extras, skipping", m)
        bench_extras = filtered

    if not bench_extras:
        log.error("No bench-* extras to measure")
        sys.exit(1)

    # Collect results
    modules_result: dict[str, dict] = {}

    with tempfile.TemporaryDirectory(prefix="supply-chain-") as tmpdir:
        tmpdir_path = Path(tmpdir)
        for module_name, requirements in sorted(bench_extras.items()):
            log.info("=" * 60)
            try:
                refs = measure_module(
                    module_name,
                    requirements,
                    tmpdir_path,
                    skip_pypi=args.skip_pypi,
                )
                modules_result[module_name] = {"references": refs}
            except Exception:
                log.exception("Failed to measure module '%s'", module_name)
                modules_result[module_name] = {"references": {}, "error": True}

    # Build output
    result = {
        "metadata": {
            "python_version": platform.python_version(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "hostname": platform.node(),
        },
        "modules": modules_result,
        "aggregate": compute_aggregates(modules_result),
    }

    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)
    log.info("Results written to %s", output_path)


if __name__ == "__main__":
    main()
