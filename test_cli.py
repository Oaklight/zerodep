"""Tests for CLI enhancements: --json, --exit-code, update --all, config."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

CLI = str(Path(__file__).parent / "zerodep.py")


def run_cli(*args: str, cwd: str | Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, CLI, "--local", *args],
        capture_output=True,
        text=True,
        cwd=cwd,
    )


# ── _read_config ──


def test_read_config_from_pyproject(tmp_path: Path):
    vendor = tmp_path / "_vendor"
    vendor.mkdir()
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[tool.zerodep]\nvendor-dir = "_vendor"\n', encoding="utf-8")
    r = run_cli("outdated", "--json", cwd=tmp_path)
    assert r.returncode == 0
    data = json.loads(r.stdout)
    assert "modules" in data
    assert "outdated_count" in data


def test_read_config_no_pyproject(tmp_path: Path):
    r = run_cli("outdated", "--json", cwd=tmp_path)
    assert r.returncode == 0
    data = json.loads(r.stdout)
    assert data["modules"] == []


def test_read_config_malformed_toml(tmp_path: Path):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("this is not valid toml {{{\n", encoding="utf-8")
    r = run_cli("outdated", "--json", cwd=tmp_path)
    assert r.returncode == 0
    data = json.loads(r.stdout)
    assert data["modules"] == []


def test_read_config_no_zerodep_section(tmp_path: Path):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[tool.ruff]\ntarget-version = "py310"\n', encoding="utf-8")
    r = run_cli("outdated", "--json", cwd=tmp_path)
    assert r.returncode == 0
    data = json.loads(r.stdout)
    assert data["modules"] == []


# ── outdated --json ──


def test_outdated_json_structure(tmp_path: Path):
    vendor = tmp_path / "_vendor"
    vendor.mkdir()
    r = run_cli("outdated", "--json", "-d", str(vendor))
    assert r.returncode == 0
    data = json.loads(r.stdout)
    assert isinstance(data["modules"], list)
    assert isinstance(data["outdated_count"], int)


def test_outdated_json_module_fields(tmp_path: Path):
    vendor = tmp_path / "_vendor"
    vendor.mkdir()
    # Copy a real vendored file to test with
    src = Path(__file__).parent / "yaml" / "yaml.py"
    if src.exists():
        (vendor / "yaml.py").write_text(
            src.read_text(encoding="utf-8"), encoding="utf-8"
        )
        r = run_cli("outdated", "--json", "-d", str(vendor))
        data = json.loads(r.stdout)
        if data["modules"]:
            mod = data["modules"][0]
            assert "name" in mod
            assert "local_version" in mod
            assert "latest_version" in mod
            assert "status" in mod


# ── outdated --exit-code ──


def test_exit_code_zero_when_up_to_date(tmp_path: Path):
    vendor = tmp_path / "_vendor"
    vendor.mkdir()
    src = Path(__file__).parent / "yaml" / "yaml.py"
    if src.exists():
        (vendor / "yaml.py").write_text(
            src.read_text(encoding="utf-8"), encoding="utf-8"
        )
        r = run_cli("outdated", "--exit-code", "-d", str(vendor))
        assert r.returncode == 0


def test_exit_code_one_when_outdated(tmp_path: Path):
    vendor = tmp_path / "_vendor"
    vendor.mkdir()
    # Write a fake yaml.py with old version and different content
    (vendor / "yaml.py").write_text(
        '# /// zerodep\n# version = "0.0.1"\n# deps = []\n# ///\npass\n',
        encoding="utf-8",
    )
    r = run_cli("outdated", "--exit-code", "-d", str(vendor))
    assert r.returncode == 1


# ── update --all ──


def test_update_all_nothing_outdated(tmp_path: Path):
    vendor = tmp_path / "_vendor"
    vendor.mkdir()
    src = Path(__file__).parent / "yaml" / "yaml.py"
    if src.exists():
        (vendor / "yaml.py").write_text(
            src.read_text(encoding="utf-8"), encoding="utf-8"
        )
        r = run_cli("update", "--all", "-d", str(vendor))
        assert r.returncode == 0
        assert "up-to-date" in r.stdout.lower()


def test_update_no_args_errors():
    r = run_cli("update")
    assert r.returncode == 1
    assert "--all" in r.stderr


def test_update_all_with_modules_errors():
    r = run_cli("update", "--all", "yaml")
    assert r.returncode == 1
    assert "cannot use --all" in r.stderr
