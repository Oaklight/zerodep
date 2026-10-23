"""Tests for CLI enhancements: --json, --exit-code, update --all, config."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

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


# ── lock file + status ──


def _install(vendor: Path, *modules: str) -> None:
    vendor.mkdir(exist_ok=True)
    r = run_cli("add", *modules, "-d", str(vendor), "-y")
    assert r.returncode == 0, r.stderr


def _read_lock(vendor: Path) -> dict:
    return json.loads((vendor / "zerodep.lock.json").read_text(encoding="utf-8"))


def _write_lock(vendor: Path, data: dict) -> None:
    (vendor / "zerodep.lock.json").write_text(
        json.dumps(data, indent=2, sort_keys=True), encoding="utf-8"
    )


FAKE_OLD_YAML = '# /// zerodep\n# version = "0.0.1"\n# deps = []\n# ///\npass\n'


def test_add_writes_lock_and_marks_dependencies(tmp_path: Path):
    vendor = tmp_path / "_vendor"
    _install(vendor, "sse")
    lock = _read_lock(vendor)
    assert lock["lock_version"] == 1
    assert lock["source"]["ref"] == "master"
    assert lock["modules"]["sse"]["requested"] is True
    assert lock["modules"]["httpclient"]["requested"] is False
    recorded = lock["modules"]["sse"]["files"]["sse.py"]
    assert len(recorded) == 64


def test_add_no_lock_skips_lock_file(tmp_path: Path):
    vendor = tmp_path / "_vendor"
    vendor.mkdir()
    r = run_cli("add", "yaml", "-d", str(vendor), "-y", "--no-lock")
    assert r.returncode == 0, r.stderr
    assert not (vendor / "zerodep.lock.json").exists()


def test_status_json_reports_tracked_state(tmp_path: Path):
    vendor = tmp_path / "_vendor"
    _install(vendor, "yaml")
    r = run_cli("status", "--json", "-d", str(vendor))
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    assert data["lock"] is True
    row = data["modules"][0]
    assert row["name"] == "yaml"
    assert row["state"] == "up-to-date"
    assert row["tracked"] is True


def test_status_without_lock_reports_unverified(tmp_path: Path):
    vendor = tmp_path / "_vendor"
    vendor.mkdir()
    (vendor / "yaml.py").write_text(
        (Path(__file__).parent / "yaml" / "yaml.py").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    r = run_cli("status", "--json", "-d", str(vendor))
    data = json.loads(r.stdout)
    assert data["lock"] is False
    assert data["modules"][0]["state"] == "up-to-date"
    with (vendor / "yaml.py").open("a", encoding="utf-8") as fh:
        fh.write("# local patch\n")
    r = run_cli("status", "--json", "--exit-code", "-d", str(vendor))
    assert r.returncode == 1
    data = json.loads(r.stdout)
    # No baseline: an edited file is indistinguishable from an old one.
    assert data["modules"][0]["state"] == "unverified"


def test_add_refuses_to_clobber_tracked_edit(tmp_path: Path):
    vendor = tmp_path / "_vendor"
    _install(vendor, "yaml")
    with (vendor / "yaml.py").open("a", encoding="utf-8") as fh:
        fh.write("# local patch\n")
    r = run_cli("add", "yaml", "-d", str(vendor), "-y")
    assert r.returncode == 1
    assert "differ from upstream" in r.stderr
    assert "# local patch" in (vendor / "yaml.py").read_text(encoding="utf-8")
    r = run_cli("add", "yaml", "-d", str(vendor), "-y", "--force")
    assert r.returncode == 0, r.stderr
    assert "# local patch" not in (vendor / "yaml.py").read_text(encoding="utf-8")


def test_add_refuses_to_clobber_untracked_edit(tmp_path: Path):
    vendor = tmp_path / "_vendor"
    vendor.mkdir()
    (vendor / "yaml.py").write_text(
        (Path(__file__).parent / "yaml" / "yaml.py").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    with (vendor / "yaml.py").open("a", encoding="utf-8") as fh:
        fh.write("# local patch\n")
    r = run_cli("add", "yaml", "-d", str(vendor), "-y")
    assert r.returncode == 1
    assert "differ from upstream" in r.stderr


def test_add_refuses_older_untracked_edit(tmp_path: Path):
    # Without a baseline an old file and an old+edited file look the same, so
    # the older version must not be used as permission to overwrite.
    vendor = tmp_path / "_vendor"
    vendor.mkdir()
    (vendor / "yaml.py").write_text(FAKE_OLD_YAML + "# local patch\n", encoding="utf-8")
    r = run_cli("add", "yaml", "-d", str(vendor), "-y")
    assert r.returncode == 1
    assert "differ from upstream" in r.stderr
    assert "# local patch" in (vendor / "yaml.py").read_text(encoding="utf-8")


def test_update_skips_locally_modified_and_exits_one(tmp_path: Path):
    vendor = tmp_path / "_vendor"
    _install(vendor, "yaml")
    with (vendor / "yaml.py").open("a", encoding="utf-8") as fh:
        fh.write("# local patch\n")

    r = run_cli("update", "--all", "-d", str(vendor))
    assert r.returncode == 1
    assert "skipped (locally-modified)" in r.stderr
    assert "# local patch" in (vendor / "yaml.py").read_text(encoding="utf-8")


def test_update_force_overwrites_local_edit(tmp_path: Path):
    vendor = tmp_path / "_vendor"
    _install(vendor, "yaml")
    with (vendor / "yaml.py").open("a", encoding="utf-8") as fh:
        fh.write("# local patch\n")
    lock = _read_lock(vendor)
    lock["modules"]["yaml"]["upstream_hash"] = "0" * 64
    lock["modules"]["yaml"]["version"] = "0.0.1"
    _write_lock(vendor, lock)

    r = run_cli("update", "--all", "--force", "-d", str(vendor))
    assert r.returncode == 0, r.stderr
    assert "# local patch" not in (vendor / "yaml.py").read_text(encoding="utf-8")
    r = run_cli("status", "--json", "-d", str(vendor))
    assert json.loads(r.stdout)["modules"][0]["state"] == "up-to-date"


def test_update_diff_writes_nothing(tmp_path: Path):
    vendor = tmp_path / "_vendor"
    vendor.mkdir()
    (vendor / "yaml.py").write_text(FAKE_OLD_YAML, encoding="utf-8")
    r = run_cli("update", "yaml", "--diff", "-d", str(vendor))
    assert r.returncode == 0, r.stderr
    assert "---" in r.stdout and "+++" in r.stdout
    assert (vendor / "yaml.py").read_text(encoding="utf-8") == FAKE_OLD_YAML
    assert not (vendor / "zerodep.lock.json").exists()


def test_update_check_flags_unverified_legacy_module(tmp_path: Path):
    vendor = tmp_path / "_vendor"
    vendor.mkdir()
    (vendor / "yaml.py").write_text(FAKE_OLD_YAML, encoding="utf-8")
    r = run_cli("update", "yaml", "--check", "-d", str(vendor))
    assert r.returncode == 1
    assert "skipped (unverified)" in r.stderr
    assert (vendor / "yaml.py").read_text(encoding="utf-8") == FAKE_OLD_YAML


def test_update_records_lock_for_untracked_module(tmp_path: Path):
    vendor = tmp_path / "_vendor"
    vendor.mkdir()
    (vendor / "yaml.py").write_text(FAKE_OLD_YAML, encoding="utf-8")
    r = run_cli("update", "yaml", "--force", "-d", str(vendor))
    assert r.returncode == 0, r.stderr
    lock = _read_lock(vendor)
    assert "yaml" in lock["modules"]
    assert lock["modules"]["yaml"]["requested"] is True
    r = run_cli("status", "--json", "-d", str(vendor))
    assert json.loads(r.stdout)["modules"][0]["state"] == "up-to-date"


# ── integrity + ref resolution (unit) ──


def _import_cli():
    import zerodep

    return zerodep


def test_integrity_check_rejects_tampered_payload():
    zerodep = _import_cli()
    mod = zerodep._load_manifest(local=True)["modules"]["yaml"]
    try:
        zerodep._verify_payload("yaml/yaml.py", "tampered", mod, "master")
    except SystemExit as exc:  # _die exits with status 1
        assert exc.code == 1
    else:  # pragma: no cover - explicit failure path
        raise AssertionError("tampered payload was accepted")


def test_integrity_check_accepts_matching_payload():
    zerodep = _import_cli()
    manifest = zerodep._load_manifest(local=True)
    mod = manifest["modules"]["yaml"]
    text = (Path(__file__).parent / "yaml" / "yaml.py").read_text(encoding="utf-8")
    zerodep._verify_payload("yaml/yaml.py", text, mod, "master")


def test_resolve_ref_prefers_explicit_and_local():
    zerodep = _import_cli()
    assert zerodep._resolve_ref("v1.2.3") == "v1.2.3"
    assert zerodep._resolve_ref(None, local=True) == zerodep.BRANCH


def test_resolve_ref_uses_and_caches_latest_release(tmp_path: Path, monkeypatch):
    zerodep = _import_cli()
    monkeypatch.setattr(zerodep, "CACHE_DIR", tmp_path)
    calls = []

    def fake_fetch(url: str, timeout: int = 15) -> bytes:
        calls.append(url)
        return b'{"tag_name": "v2099.1.2"}'

    monkeypatch.setattr(zerodep, "_fetch_url", fake_fetch)
    assert zerodep._resolve_ref(None) == "v2099.1.2"
    assert len(calls) == 1

    def boom(url: str, timeout: int = 15) -> bytes:  # pragma: no cover
        raise AssertionError("release lookup should be cached")

    monkeypatch.setattr(zerodep, "_fetch_url", boom)
    assert zerodep._resolve_ref(None) == "v2099.1.2"


def test_integrity_check_skips_secondary_files():
    # content_hash covers the primary file only; secondary files must not be
    # compared against it or every multi-file module would fail to install.
    zerodep = _import_cli()
    mod = {"primary_file": "foo/foo.py", "content_hash": "0" * 64}
    zerodep._verify_payload("foo/helper.py", "not the hash", mod, "master")


def test_ref_cache_dir_is_filesystem_safe():
    zerodep = _import_cli()
    for ref in ("..", ".", "../../etc", "v2026.10.23"):
        path = zerodep._ref_cache_dir(ref)
        assert path.parent == zerodep.CACHE_DIR / "refs"
        assert path.name not in {"", ".", ".."}


# ── lock bootstrap of legacy installs ──


def _copy_clean(vendor: Path, module: str) -> None:
    vendor.mkdir(exist_ok=True)
    (vendor / f"{module}.py").write_text(
        (Path(__file__).parent / module / f"{module}.py").read_text(encoding="utf-8"),
        encoding="utf-8",
    )


def _status_rows(vendor: Path) -> dict[str, dict]:
    r = run_cli("status", "--json", "-d", str(vendor))
    assert r.returncode == 0, r.stderr
    return {row["name"]: row for row in json.loads(r.stdout)["modules"]}


def test_bootstrap_adopts_clean_legacy_module(tmp_path: Path):
    vendor = tmp_path / "_vendor"
    _copy_clean(vendor, "yaml")
    r = run_cli("add", "sse", "-d", str(vendor), "-y")
    assert r.returncode == 0, r.stderr
    lock = _read_lock(vendor)
    assert "yaml" in lock["modules"]
    assert lock["modules"]["yaml"]["requested"] is True
    assert _status_rows(vendor)["yaml"]["state"] == "up-to-date"


def test_bootstrap_never_adopts_an_edited_file(tmp_path: Path):
    vendor = tmp_path / "_vendor"
    _copy_clean(vendor, "yaml")
    with (vendor / "yaml.py").open("a", encoding="utf-8") as fh:
        fh.write("# local patch\n")
    r = run_cli("add", "sse", "-d", str(vendor), "-y")
    assert r.returncode == 0, r.stderr
    lock = _read_lock(vendor)
    assert "yaml" not in lock["modules"]
    row = _status_rows(vendor)["yaml"]
    assert row["state"] == "unverified"
    assert row["tracked"] is False

    # --all must not silently overwrite a file it never adopted.
    r = run_cli("update", "--all", "-d", str(vendor))
    assert r.returncode == 1
    assert "skipped (unverified)" in r.stderr
    assert "# local patch" in (vendor / "yaml.py").read_text(encoding="utf-8")


def test_bootstrap_leaves_old_version_untracked(tmp_path: Path):
    vendor = tmp_path / "_vendor"
    vendor.mkdir()
    (vendor / "yaml.py").write_text(FAKE_OLD_YAML, encoding="utf-8")
    r = run_cli("add", "sse", "-d", str(vendor), "-y")
    assert r.returncode == 0, r.stderr
    assert "yaml" not in _read_lock(vendor)["modules"]
    assert _status_rows(vendor)["yaml"]["state"] == "unverified"

    # An older copy may also be an edited copy; require --force to replace it.
    r = run_cli("update", "--all", "-d", str(vendor))
    assert r.returncode == 1
    assert (vendor / "yaml.py").read_text(encoding="utf-8") == FAKE_OLD_YAML

    r = run_cli("update", "yaml", "--force", "-d", str(vendor))
    assert r.returncode == 0, r.stderr
    assert _status_rows(vendor)["yaml"]["state"] == "up-to-date"


# ── review follow-ups: dependency growth, local integrity, removals ──


def test_select_update_candidates_pulls_in_missing_dependencies():
    import argparse

    zerodep = _import_cli()
    manifest = {
        "modules": {
            "yaml": {
                "version": "1.0.0",
                "content_hash": "a" * 64,
                "deps": ["httpclient"],
                "files": ["yaml/yaml.py"],
            },
            "httpclient": {
                "version": "1.0.0",
                "content_hash": "b" * 64,
                "deps": [],
                "files": ["httpclient/httpclient.py"],
            },
        }
    }
    rows = {
        "yaml": {
            "name": "yaml",
            "state": "up-to-date",
            "installed_version": "1.0.0",
            "latest_version": "1.0.0",
            "missing_deps": ["httpclient"],
        }
    }
    lock = {"modules": {"yaml": {}}}
    args = argparse.Namespace(update_all=True, modules=[], no_deps=False, force=False)
    candidates, skipped, removed = zerodep._select_update_candidates(
        args, rows, lock, manifest
    )
    assert "httpclient" in candidates
    assert "yaml" not in candidates  # already up to date
    assert skipped == []
    assert removed == []


def test_status_exit_code_flags_missing_dependencies(tmp_path: Path):
    vendor = tmp_path / "_vendor"
    vendor.mkdir()
    r = run_cli("add", "sse", "--no-deps", "-d", str(vendor), "-y")
    assert r.returncode == 0, r.stderr
    r = run_cli("status", "--exit-code", "-d", str(vendor))
    assert r.returncode == 1
    assert "depends on httpclient" in r.stderr


def test_local_checkout_payload_is_verified(tmp_path: Path, monkeypatch):
    zerodep = _import_cli()
    mod = {"primary_file": "yaml/yaml.py", "content_hash": "0" * 64}
    try:
        zerodep._verify_payload("yaml/yaml.py", "tampered", mod, "master", local=True)
    except SystemExit as exc:
        assert exc.code == 1
    else:  # pragma: no cover - explicit failure path
        raise AssertionError("a tampered local checkout was accepted")


def test_update_reports_upstream_removed_module(tmp_path: Path):
    vendor = tmp_path / "_vendor"
    _install(vendor, "yaml")
    lock = _read_lock(vendor)
    lock["modules"]["ghost"] = {
        "version": "0.1.0",
        "upstream_hash": None,
        "requested": True,
        "files": {"ghost.py": "0" * 64},
    }
    _write_lock(vendor, lock)
    (vendor / "ghost.py").write_text("# /// zerodep\n# ///\npass\n", encoding="utf-8")

    r = run_cli("status", "--json", "-d", str(vendor))
    rows = {row["name"]: row for row in json.loads(r.stdout)["modules"]}
    assert rows["ghost"]["state"] == "upstream-removed"

    r = run_cli("update", "--all", "-d", str(vendor))
    assert r.returncode == 1
    assert "no longer published upstream" in r.stderr

    r = run_cli("update", "--all", "--check", "-d", str(vendor))
    assert r.returncode == 1
    assert "ghost: upstream-removed" in r.stdout


def test_update_no_lock_leaves_lock_alone(tmp_path: Path):
    vendor = tmp_path / "_vendor"
    vendor.mkdir()
    (vendor / "yaml.py").write_text(FAKE_OLD_YAML, encoding="utf-8")
    r = run_cli("update", "yaml", "--force", "--no-lock", "-d", str(vendor))
    assert r.returncode == 0, r.stderr
    assert not (vendor / "zerodep.lock.json").exists()


def test_prepare_file_only_reads_checkout_with_local(monkeypatch):
    zerodep = _import_cli()
    mod = zerodep._load_manifest(local=True)["modules"]["yaml"]
    seen: list[str] = []

    def fake_fetch(path: str, *, offline: bool = False, ref: str | None = None):
        seen.append(ref or "")
        return (Path(__file__).parent / "yaml" / "yaml.py").read_bytes()

    monkeypatch.setattr(zerodep, "_fetch_with_fallback", fake_fetch)
    text = zerodep._prepare_file(
        "yaml/yaml.py", mod, offline=False, ref="vTEST", local=False
    )
    assert seen == ["vTEST"]  # --ref provenance is not faked from the checkout
    assert "zerodep add yaml" in text


def test_write_files_verifies_everything_before_writing(tmp_path: Path, monkeypatch):
    zerodep = _import_cli()
    manifest = zerodep._load_manifest(local=True)
    yaml_text = (Path(__file__).parent / "yaml" / "yaml.py").read_text(encoding="utf-8")

    def fake_fetch(path: str, *, offline: bool = False, ref: str | None = None):
        return (yaml_text if path == "yaml/yaml.py" else "tampered").encode()

    monkeypatch.setattr(zerodep, "_fetch_with_fallback", fake_fetch)
    plan = [
        ("yaml", "yaml/yaml.py", tmp_path / "yaml.py"),
        ("sse", "sse/sse.py", tmp_path / "sse.py"),
    ]
    with pytest.raises(SystemExit):
        zerodep._write_files(
            plan,
            manifest["modules"],
            tmp_path,
            offline=False,
            ref="vTEST",
            local=False,
        )
    # The valid first file must not be written when a later one is rejected.
    assert not (tmp_path / "yaml.py").exists()


# ── release-check ──


def _make_release_repo(tmp_path: Path) -> Path:
    """Build a minimal repo that ``release-check`` can inspect."""
    real_cli = Path(__file__).parent / "zerodep.py"
    shutil.copy2(real_cli, tmp_path / "zerodep.py")
    version = re.search(
        r'^__version__ = "([^"]+)"',
        real_cli.read_text(encoding="utf-8"),
        re.MULTILINE,
    ).group(1)
    (tmp_path / "pyproject.toml").write_text(
        f'[project]\nname = "zerodep"\nversion = "{version}"\n', encoding="utf-8"
    )
    module_dir = tmp_path / "demo"
    module_dir.mkdir()
    (module_dir / "demo.py").write_text(
        '# /// zerodep\n# version = "0.1.0"\n# deps = []\n# tier = "medium"\n'
        '# category = "text"\n# ///\n\nVALUE = 1\n',
        encoding="utf-8",
    )
    r = subprocess.run(
        [sys.executable, str(tmp_path / "zerodep.py"), "--local", "manifest"],
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )
    assert r.returncode == 0, r.stderr
    return tmp_path


def _run_release_check(repo: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(repo / "zerodep.py"), "release-check", *extra],
        capture_output=True,
        text=True,
        cwd=repo,
    )


def test_release_check_passes_on_a_consistent_tree(tmp_path: Path):
    repo = _make_release_repo(tmp_path)
    r = _run_release_check(repo, "--allow-dirty")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "release-check passed" in r.stdout
    assert "docs worktrees are not mounted" in r.stdout


def test_release_check_fails_on_a_stale_manifest(tmp_path: Path):
    repo = _make_release_repo(tmp_path)
    (repo / "demo" / "demo.py").write_text(
        (repo / "demo" / "demo.py").read_text(encoding="utf-8") + "\nVALUE = 2\n",
        encoding="utf-8",
    )
    r = _run_release_check(repo, "--allow-dirty")
    assert r.returncode == 1
    assert "manifest.json is stale" in r.stdout


def test_release_check_fails_on_a_version_mismatch(tmp_path: Path):
    repo = _make_release_repo(tmp_path)
    (repo / "pyproject.toml").write_text(
        '[project]\nname = "zerodep"\nversion = "2020.1.1"\n', encoding="utf-8"
    )
    r = _run_release_check(repo, "--allow-dirty")
    assert r.returncode == 1
    assert "pyproject.toml has 2020.1.1" in r.stdout


def test_release_check_fails_on_a_non_calver_version(tmp_path: Path):
    repo = _make_release_repo(tmp_path)
    cli = (repo / "zerodep.py").read_text(encoding="utf-8")
    (repo / "zerodep.py").write_text(
        re.sub(
            r'^__version__ = "[^"]+"',
            '__version__ = "0.1.0"',
            cli,
            count=1,
            flags=re.MULTILINE,
        ),
        encoding="utf-8",
    )
    (repo / "pyproject.toml").write_text(
        '[project]\nname = "zerodep"\nversion = "0.1.0"\n', encoding="utf-8"
    )
    r = _run_release_check(repo, "--allow-dirty")
    assert r.returncode == 1
    assert "is not CalVer" in r.stdout


def test_release_check_ignores_timestamp_drift(tmp_path: Path):
    repo = _make_release_repo(tmp_path)
    manifest = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))
    for entry in manifest["modules"].values():
        entry["last_updated"] = "2000-01-01T00:00:00+00:00"
    manifest["generated"] = "2000-01-01T00:00:00+00:00"
    (repo / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    r = _run_release_check(repo, "--allow-dirty")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "manifest.json matches the source tree" in r.stdout


def test_release_check_accepts_a_calver_release_version(tmp_path: Path):
    repo = _make_release_repo(tmp_path)
    r = _run_release_check(repo, "--allow-dirty", "--version", "2030.1.2")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "v2030.1.2 is free to tag" in r.stdout


def test_release_check_rejects_a_non_calver_release_version(tmp_path: Path):
    repo = _make_release_repo(tmp_path)
    r = _run_release_check(repo, "--allow-dirty", "--version", "1.0")
    assert r.returncode == 1
    assert "1.0 is not CalVer" in r.stdout


def test_release_check_rejects_an_existing_tag(tmp_path: Path):
    repo = _make_release_repo(tmp_path)
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "init"],
        cwd=repo,
        check=True,
    )
    subprocess.run(["git", "tag", "v2030.1.2"], cwd=repo, check=True)
    r = _run_release_check(repo, "--version", "2030.1.2")
    assert r.returncode == 1
    assert "tag v2030.1.2 already exists" in r.stdout


def test_release_check_reports_uncommitted_tracked_changes(tmp_path: Path):
    repo = _make_release_repo(tmp_path)
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "init"],
        cwd=repo,
        check=True,
    )
    (repo / "demo" / "demo.py").write_text(
        (repo / "demo" / "demo.py").read_text(encoding="utf-8") + "\nVALUE = 3\n",
        encoding="utf-8",
    )
    r = _run_release_check(repo)
    assert r.returncode == 1
    assert "tracked file(s) uncommitted" in r.stdout


# ── lifecycle: list filters, search, dry-run, remove ──


def test_list_category_filters_and_json(tmp_path: Path):
    r = run_cli("list", "--category", "serialization", "--json")
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    assert data["category"] == "serialization"
    assert data["count"] == len(data["modules"]) > 0
    assert {m["category"] for m in data["modules"]} == {"serialization"}


def test_list_unknown_category_errors():
    r = run_cli("list", "--category", "nope")
    assert r.returncode == 1
    assert "unknown category" in r.stderr


def test_search_matches_name_description_and_deps():
    r = run_cli("search", "http", "--json")
    assert r.returncode == 0, r.stderr
    names = {m["name"] for m in json.loads(r.stdout)["modules"]}
    assert {"httpclient", "httpserver"} <= names

    r = run_cli("search", "sse", "--json")
    assert {m["name"] for m in json.loads(r.stdout)["modules"]} == {"sse"}

    r = run_cli("search", "no-such-term-anywhere")
    assert r.returncode == 0
    assert "No modules match" in r.stdout


def test_add_dry_run_writes_nothing(tmp_path: Path):
    vendor = tmp_path / "_vendor"
    vendor.mkdir()
    r = run_cli("add", "yaml", "--dry-run", "-d", str(vendor))
    assert r.returncode == 0, r.stderr
    assert "Would copy 1 file(s)" in r.stdout
    assert list(vendor.iterdir()) == []


def test_update_dry_run_writes_nothing(tmp_path: Path):
    vendor = tmp_path / "_vendor"
    _install(vendor, "yaml")
    lock = _read_lock(vendor)
    lock["modules"]["yaml"]["upstream_hash"] = "0" * 64
    _write_lock(vendor, lock)
    before = (vendor / "yaml.py").read_text(encoding="utf-8")

    r = run_cli("update", "--all", "--dry-run", "-d", str(vendor))
    assert r.returncode == 0, r.stderr
    assert "would update" in r.stdout
    assert (vendor / "yaml.py").read_text(encoding="utf-8") == before
    r = run_cli("status", "--json", "-d", str(vendor))
    assert json.loads(r.stdout)["modules"][0]["state"] == "outdated"


def test_remove_deletes_files_and_lock_entry(tmp_path: Path):
    vendor = tmp_path / "_vendor"
    _install(vendor, "sse")
    r = run_cli("remove", "sse", "-y", "-d", str(vendor))
    assert r.returncode == 0, r.stderr
    assert not (vendor / "sse.py").exists()
    assert (vendor / "httpclient.py").exists()
    lock = _read_lock(vendor)
    assert "sse" not in lock["modules"]
    assert "httpclient" in lock["modules"]
    assert "unused dependency: httpclient" in r.stderr


def test_remove_dry_run_writes_nothing(tmp_path: Path):
    vendor = tmp_path / "_vendor"
    _install(vendor, "yaml")
    r = run_cli("remove", "yaml", "--dry-run", "-d", str(vendor))
    assert r.returncode == 0, r.stderr
    assert (vendor / "yaml.py").exists()
    assert "yaml" in _read_lock(vendor)["modules"]


def test_remove_refuses_modified_without_force(tmp_path: Path):
    vendor = tmp_path / "_vendor"
    _install(vendor, "yaml")
    with (vendor / "yaml.py").open("a", encoding="utf-8") as fh:
        fh.write("# local patch\n")
    r = run_cli("remove", "yaml", "-y", "-d", str(vendor))
    assert r.returncode == 1
    assert "locally modified" in r.stderr
    assert (vendor / "yaml.py").exists()

    r = run_cli("remove", "yaml", "--force", "--json", "-d", str(vendor))
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout)["removed"] == ["yaml"]
    assert not (vendor / "yaml.py").exists()


def test_remove_warns_about_remaining_dependents(tmp_path: Path):
    vendor = tmp_path / "_vendor"
    _install(vendor, "sse")
    r = run_cli("remove", "httpclient", "-y", "-d", str(vendor))
    assert r.returncode == 0, r.stderr
    assert "still required by sse" in r.stderr


def test_remove_json_needs_yes(tmp_path: Path):
    vendor = tmp_path / "_vendor"
    _install(vendor, "yaml")
    r = run_cli("remove", "yaml", "--json", "-d", str(vendor))
    assert r.returncode == 1
    assert "needs --yes" in r.stderr
    assert (vendor / "yaml.py").exists()


def test_remove_unknown_module_errors(tmp_path: Path):
    vendor = tmp_path / "_vendor"
    vendor.mkdir()
    r = run_cli("remove", "notinstalled", "-y", "-d", str(vendor))
    assert r.returncode == 1
    assert "not installed here" in r.stderr


# ── release-check helpers ──


def test_parse_imports_separates_optional_from_hard():
    zerodep = _import_cli()
    source = """
import os
import hard_dep
try:
    import optional_dep
except ImportError:
    optional_dep = None
import sys
if sys.version_info >= (3, 11):
    from tomllib import loads
else:
    from tomli import loads
"""
    hard, optional = zerodep._parse_imports(source)
    # A sys.version_info branch: the running-interpreter branch is real, the
    # older-Python fallback is a compatibility shim.
    assert hard == {"os", "hard_dep", "sys", "tomllib"}
    assert optional == {"optional_dep", "tomli"}


def test_parse_imports_rejects_bypasses():
    zerodep = _import_cli()
    source = """
try:
    import fatal_dep
except Exception:
    raise
if TYPE_CHECKING:
    import pandas
if sys.version_info >= (3, 11):
    import numpy
else:
    import legacy_dep
import importlib
importlib.import_module("scipy.stats")
"""
    hard, optional = zerodep._parse_imports(source)
    assert hard == {"fatal_dep", "numpy", "scipy", "importlib"}
    assert optional == {"pandas", "legacy_dep"}


def test_makefile_recipes_map_targets_to_tests(tmp_path: Path):
    zerodep = _import_cli()
    makefile = tmp_path / "Makefile"
    makefile.write_text(
        "test:\n"
        "\t$(PYTEST) a/test_a_correctness.py b/test_b_edge.py -v\n"
        "\n"
        "benchmark:\n"
        "\t$(PYTEST) a/test_a_benchmark.py -v\n"
        "help:\n"
        "\t@echo test_x.py\n",
        encoding="utf-8",
    )
    recipes, dynamic = zerodep._makefile_recipes(tmp_path)
    assert recipes["test"] == {
        "a/test_a_correctness.py",
        "b/test_b_edge.py",
    }
    assert recipes["benchmark"] == {"a/test_a_benchmark.py"}
    assert dynamic == set()


def test_makefile_recipes_handle_multi_targets_and_variables(tmp_path: Path):
    zerodep = _import_cli()
    makefile = tmp_path / "Makefile"
    makefile.write_text(
        "test lint:: a/test_a.py\n"
        "\t$(PYTEST) a/test_a.py -v\n"
        "checked:\n"
        "\t$(PYTEST) $(TESTS) -v\n",
        encoding="utf-8",
    )
    recipes, dynamic = zerodep._makefile_recipes(tmp_path)
    assert recipes["test"] == {"a/test_a.py"}
    assert recipes["lint"] == {"a/test_a.py"}
    assert dynamic == {"checked"}


def test_stdlib_check_flags_hard_third_party_import(tmp_path: Path):
    zerodep = _import_cli()
    (tmp_path / "mymod").mkdir()
    (tmp_path / "mymod" / "mymod.py").write_text(
        "import os\ntry:\n    import requests\nexcept ImportError:\n    pass\n"
        "import yaml_dep\n",
        encoding="utf-8",
    )
    modules = {"mymod": {"files": ["mymod/mymod.py"]}}
    status, detail = zerodep._run_stdlib_check(tmp_path, modules)
    assert status == "fail"
    assert "yaml_dep" in detail
    assert "requests" not in detail  # optional imports are allowed


def test_dependency_check_flags_undeclared_sibling(tmp_path: Path):
    zerodep = _import_cli()
    for name in ("alpha", "beta"):
        (tmp_path / name).mkdir()
    (tmp_path / "alpha" / "alpha.py").write_text(
        "from beta import helper\n", encoding="utf-8"
    )
    (tmp_path / "beta" / "beta.py").write_text("helper = 1\n", encoding="utf-8")
    modules = {
        "alpha": {"files": ["alpha/alpha.py"], "deps": []},
        "beta": {"files": ["beta/beta.py"], "deps": []},
    }
    status, detail = zerodep._run_dependency_check(tmp_path, modules)
    assert status == "fail"
    assert "alpha imports beta undeclared" in detail

    modules["alpha"]["deps"] = ["beta"]
    status, detail = zerodep._run_dependency_check(tmp_path, modules)
    assert status == "ok", detail


def test_tests_check_rejects_unknown_module():
    zerodep = _import_cli()
    status, detail = zerodep._run_tests_check(
        Path(__file__).parent, {"yaml": {}}, "nope"
    )
    assert status == "fail"
    assert "unknown module" in detail


def test_remove_refuses_untracked_edit(tmp_path: Path):
    vendor = tmp_path / "_vendor"
    vendor.mkdir()
    (vendor / "yaml.py").write_text(
        (Path(__file__).parent / "yaml" / "yaml.py").read_text(encoding="utf-8")
        + "# local patch\n",
        encoding="utf-8",
    )
    r = run_cli("remove", "yaml", "-y", "-d", str(vendor))
    assert r.returncode == 1
    assert "locally modified" in r.stderr
    assert (vendor / "yaml.py").exists()

    r = run_cli("remove", "yaml", "-y", "--force", "-d", str(vendor))
    assert r.returncode == 0, r.stderr
    assert not (vendor / "yaml.py").exists()


def test_remove_rejects_lock_path_escaping_target(tmp_path: Path):
    vendor = tmp_path / "_vendor"
    _install(vendor, "yaml")
    outside = tmp_path / "outside.py"
    outside.write_text("keep me\n", encoding="utf-8")
    lock = _read_lock(vendor)
    lock["modules"]["evil"] = {
        "version": "0.1.0",
        "upstream_hash": None,
        "requested": True,
        "files": {"../outside.py": "0" * 64},
    }
    _write_lock(vendor, lock)

    r = run_cli("remove", "evil", "-y", "-d", str(vendor))
    assert r.returncode == 1
    assert "points outside" in r.stderr
    assert outside.exists()


def test_release_check_reports_new_checks():
    r = run_cli("release-check", "--allow-dirty")
    assert r.returncode == 0, r.stderr
    for row in (
        "stdlib-imports",
        "dependencies",
        "benchmark-extras",
        "makefile-wiring",
    ):
        assert row in r.stdout
