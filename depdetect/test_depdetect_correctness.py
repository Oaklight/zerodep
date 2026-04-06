"""Correctness tests: zerodep depdetect."""

from __future__ import annotations

import os
import subprocess
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.dirname(__file__))

# Also test internal helpers
from depdetect import (
    DepdetectError,
    DependencyReport,
    DependencyStatus,
    Requirement,
    _compare_versions,
    _parse_version,
    analyze_source,
    check_binary,
    check_env_var,
    check_python_package,
    check_requirements,
    get_binary_version,
    parse_compatibility,
    parse_imports,
    parse_requirements,
    parse_tool_hints,
    resolve_pip_name,
)

# ── TestParseImports ──


class TestParseImports:
    def test_simple_import(self):
        assert parse_imports("import requests") == {"requests"}

    def test_from_import(self):
        assert parse_imports("from requests import get") == {"requests"}

    def test_stdlib_filtered(self):
        result = parse_imports("import os\nimport sys\nimport json\n")
        assert result == set()

    def test_mixed_stdlib_and_third_party(self):
        source = "import os\nimport requests\nimport json\nimport flask\n"
        result = parse_imports(source)
        assert result == {"requests", "flask"}

    def test_relative_import_skipped(self):
        source = "from . import utils\nfrom .models import User\n"
        assert parse_imports(source) == set()

    def test_dotted_import(self):
        source = "from requests.auth import HTTPBasicAuth\n"
        assert parse_imports(source) == {"requests"}

    def test_dotted_import_statement(self):
        source = "import requests.auth\n"
        assert parse_imports(source) == {"requests"}

    def test_conditional_import_in_try_except(self):
        source = "try:\n    import ujson\nexcept ImportError:\n    import json\n"
        result = parse_imports(source)
        # ujson is third-party, json is stdlib
        assert "ujson" in result
        assert "json" not in result

    def test_import_inside_function(self):
        source = "def foo():\n    import pandas\n    return pandas.DataFrame()\n"
        assert parse_imports(source) == {"pandas"}

    def test_invalid_source_raises(self):
        with pytest.raises(DepdetectError, match="cannot parse"):
            parse_imports("def (broken syntax")

    def test_empty_source(self):
        assert parse_imports("") == set()

    def test_comment_only_source(self):
        assert parse_imports("# import requests\n") == set()

    def test_multiple_imports_one_line(self):
        source = "import numpy, pandas, scipy\n"
        result = parse_imports(source)
        assert result == {"numpy", "pandas", "scipy"}

    def test_file_path_in_error(self):
        with pytest.raises(DepdetectError, match="test.py"):
            parse_imports("def (broken", file_path="test.py")


# ── TestParseRequirements ──


class TestParseRequirements:
    def test_simple_package(self):
        result = parse_requirements("requests\n")
        assert len(result) == 1
        assert result[0].name == "requests"
        assert result[0].category == "python"
        assert result[0].op is None
        assert result[0].version is None

    def test_version_constraint(self):
        result = parse_requirements("requests>=2.28.0\n")
        assert result[0].name == "requests"
        assert result[0].op == ">="
        assert result[0].version == "2.28.0"

    def test_exact_version(self):
        result = parse_requirements("requests==2.28.0\n")
        assert result[0].op == "=="
        assert result[0].version == "2.28.0"

    def test_compatible_release(self):
        result = parse_requirements("requests~=2.28\n")
        assert result[0].op == "~="
        assert result[0].version == "2.28"

    def test_extras(self):
        result = parse_requirements("requests[security]\n")
        assert result[0].name == "requests"
        assert result[0].extras == "security"

    def test_extras_with_version(self):
        result = parse_requirements("uvicorn[standard]>=0.24.0\n")
        assert result[0].name == "uvicorn"
        assert result[0].extras == "standard"
        assert result[0].op == ">="
        assert result[0].version == "0.24.0"

    def test_comments_and_blanks(self):
        text = "# This is a comment\n\nrequests\n\n# Another comment\nflask\n"
        result = parse_requirements(text)
        assert len(result) == 2
        assert result[0].name == "requests"
        assert result[1].name == "flask"

    def test_dash_r_skipped(self):
        text = "-r base.txt\nrequests\n"
        result = parse_requirements(text)
        assert len(result) == 1
        assert result[0].name == "requests"

    def test_dash_e_skipped(self):
        text = "-e git+https://github.com/foo/bar.git\nrequests\n"
        result = parse_requirements(text)
        assert len(result) == 1

    def test_multiple_packages(self):
        text = "requests>=2.28\nflask>=2.0\npillow>=10.0\n"
        result = parse_requirements(text)
        assert len(result) == 3
        names = [r.name for r in result]
        assert names == ["requests", "flask", "pillow"]

    def test_empty_input(self):
        assert parse_requirements("") == []

    def test_not_equal(self):
        result = parse_requirements("requests!=2.28.0\n")
        assert result[0].op == "!="

    def test_less_than(self):
        result = parse_requirements("requests<3.0.0\n")
        assert result[0].op == "<"


# ── TestParseCompatibility ──


class TestParseCompatibility:
    def test_python_version_plus(self):
        result = parse_compatibility("Python 3.10+")
        assert len(result) >= 1
        python_req = [r for r in result if r.name.lower() == "python"][0]
        assert python_req.category == "runtime"
        assert python_req.version == "3.10"

    def test_node_version(self):
        result = parse_compatibility("Node.js >= 18")
        found = [r for r in result if "node" in r.name.lower()]
        assert len(found) >= 1

    def test_binary_version(self):
        result = parse_compatibility("pandoc >= 3.0")
        pandoc = [r for r in result if r.name.lower() == "pandoc"]
        assert len(pandoc) == 1
        assert pandoc[0].category == "binary"
        assert pandoc[0].op == ">="
        assert pandoc[0].version == "3.0"

    def test_multiple_requirements(self):
        result = parse_compatibility("Python 3.10+, pandoc >= 3.0")
        assert len(result) >= 2

    def test_no_version(self):
        result = parse_compatibility("Docker")
        assert len(result) >= 1

    def test_empty_input(self):
        assert parse_compatibility("") == []

    def test_noise_words_filtered(self):
        result = parse_compatibility("Requires pandoc and git")
        names_lower = {r.name.lower() for r in result}
        assert "requires" not in names_lower
        assert "and" not in names_lower


# ── TestParseToolHints ──


class TestParseToolHints:
    def test_single_hint(self):
        result = parse_tool_hints("Bash(git:*) Read")
        assert result == ["git"]

    def test_multiple_hints(self):
        result = parse_tool_hints("Bash(git:* docker:* npm:*) Read")
        assert result == ["git", "docker", "npm"]

    def test_no_parentheses(self):
        result = parse_tool_hints("Bash Read Write")
        assert result == []

    def test_empty_input(self):
        result = parse_tool_hints("")
        assert result == []

    def test_multiple_tool_groups(self):
        result = parse_tool_hints("Bash(git:*) Docker(compose:*)")
        assert "git" in result
        assert "compose" in result


# ── TestResolvePipName ──


class TestResolvePipName:
    def test_static_mapping_pil(self):
        assert resolve_pip_name("PIL") == "pillow"

    def test_static_mapping_yaml(self):
        # Metadata may return canonical casing "PyYAML"; both are valid
        assert resolve_pip_name("yaml").lower() == "pyyaml"

    def test_static_mapping_dotenv(self):
        assert resolve_pip_name("dotenv") == "python-dotenv"

    def test_static_mapping_cv2(self):
        assert resolve_pip_name("cv2") == "opencv-python"

    def test_static_mapping_sklearn(self):
        assert resolve_pip_name("sklearn") == "scikit-learn"

    def test_static_mapping_bs4(self):
        assert resolve_pip_name("bs4") == "beautifulsoup4"

    def test_heuristic_underscore_to_hyphen(self):
        # Unknown package — fallback to heuristic
        assert resolve_pip_name("my_package") == "my-package"

    def test_already_correct_name(self):
        assert resolve_pip_name("requests") == "requests"

    def test_metadata_lookup(self):
        """Test that installed packages can be resolved via metadata."""
        # pytest itself should be resolvable
        result = resolve_pip_name("pytest")
        assert result.lower() == "pytest"


# ── TestCheckBinary ──


class TestCheckBinary:
    def test_found(self):
        with patch("depdetect.shutil.which", return_value="/usr/bin/git"):
            assert check_binary("git") == "/usr/bin/git"

    def test_not_found(self):
        with patch("depdetect.shutil.which", return_value=None):
            assert check_binary("nonexistent-binary-xyz") is None

    def test_alias_resolution(self):
        def mock_which(name):
            if name == "node":
                return "/usr/bin/node"
            return None

        with patch("depdetect.shutil.which", side_effect=mock_which):
            assert check_binary("node.js") == "/usr/bin/node"

    def test_alias_resolution_first_candidate(self):
        """First matching candidate wins."""
        call_count = 0

        def mock_which(name):
            nonlocal call_count
            call_count += 1
            if name == "python3":
                return "/usr/bin/python3"
            if name == "python":
                return "/usr/bin/python"
            return None

        with patch("depdetect.shutil.which", side_effect=mock_which):
            result = check_binary("python")
            assert result == "/usr/bin/python3"


# ── TestCheckPythonPackage ──


class TestCheckPythonPackage:
    def test_found(self):
        mock_spec = MagicMock()
        with patch("depdetect.importlib.util.find_spec", return_value=mock_spec):
            assert check_python_package("requests") is True

    def test_not_found(self):
        with patch("depdetect.importlib.util.find_spec", return_value=None):
            assert check_python_package("nonexistent_package_xyz") is False

    def test_pip_name_mapping(self):
        """pillow → find_spec("PIL")"""
        mock_spec = MagicMock()

        def mock_find_spec(name):
            if name == "PIL":
                return mock_spec
            return None

        with patch("depdetect.importlib.util.find_spec", side_effect=mock_find_spec):
            assert check_python_package("pillow") is True

    def test_module_not_found_error(self):
        with patch(
            "depdetect.importlib.util.find_spec",
            side_effect=ModuleNotFoundError,
        ):
            assert check_python_package("broken") is False


# ── TestCheckEnvVar ──


class TestCheckEnvVar:
    def test_set(self):
        with patch.dict(os.environ, {"MY_VAR": "value"}):
            assert check_env_var("MY_VAR") is True

    def test_not_set(self):
        env = os.environ.copy()
        env.pop("NONEXISTENT_VAR_XYZ", None)
        with patch.dict(os.environ, env, clear=True):
            assert check_env_var("NONEXISTENT_VAR_XYZ") is False

    def test_empty_value(self):
        with patch.dict(os.environ, {"EMPTY_VAR": ""}):
            assert check_env_var("EMPTY_VAR") is False


# ── TestGetBinaryVersion ──


class TestGetBinaryVersion:
    def test_extracts_version(self):
        mock_result = MagicMock()
        mock_result.stdout = "git version 2.43.0\n"
        mock_result.stderr = ""

        with (
            patch("depdetect.shutil.which", return_value="/usr/bin/git"),
            patch("depdetect.subprocess.run", return_value=mock_result),
        ):
            assert get_binary_version("git") == "2.43.0"

    def test_binary_not_found(self):
        with patch("depdetect.shutil.which", return_value=None):
            assert get_binary_version("nonexistent") is None

    def test_timeout_handled(self):
        with (
            patch("depdetect.shutil.which", return_value="/usr/bin/slow"),
            patch(
                "depdetect.subprocess.run",
                side_effect=subprocess.TimeoutExpired("slow", 5.0),
            ),
        ):
            assert get_binary_version("slow") is None

    def test_oserror_handled(self):
        with (
            patch("depdetect.shutil.which", return_value="/usr/bin/broken"),
            patch("depdetect.subprocess.run", side_effect=OSError("permission denied")),
        ):
            assert get_binary_version("broken") is None

    def test_no_version_in_output(self):
        mock_result = MagicMock()
        mock_result.stdout = "some tool with no version info\n"
        mock_result.stderr = ""

        with (
            patch("depdetect.shutil.which", return_value="/usr/bin/tool"),
            patch("depdetect.subprocess.run", return_value=mock_result),
        ):
            assert get_binary_version("tool") is None


# ── TestVersionComparison ──


class TestVersionComparison:
    def test_parse_version(self):
        assert _parse_version("2.43.0") == (2, 43, 0)

    def test_parse_version_two_parts(self):
        assert _parse_version("3.10") == (3, 10)

    def test_parse_version_single(self):
        assert _parse_version("18") == (18,)

    def test_gte_satisfied(self):
        assert _compare_versions("3.10.5", ">=", "3.10") is True

    def test_gte_equal(self):
        assert _compare_versions("3.10", ">=", "3.10") is True

    def test_gte_not_satisfied(self):
        assert _compare_versions("3.9", ">=", "3.10") is False

    def test_gt_satisfied(self):
        assert _compare_versions("3.11", ">", "3.10") is True

    def test_gt_not_satisfied(self):
        assert _compare_versions("3.10", ">", "3.10") is False

    def test_lte_satisfied(self):
        assert _compare_versions("3.10", "<=", "3.10") is True

    def test_lt_satisfied(self):
        assert _compare_versions("3.9", "<", "3.10") is True

    def test_eq_satisfied(self):
        assert _compare_versions("3.10.0", "==", "3.10.0") is True

    def test_eq_not_satisfied(self):
        assert _compare_versions("3.10.1", "==", "3.10.0") is False

    def test_neq_satisfied(self):
        assert _compare_versions("3.10.1", "!=", "3.10.0") is True

    def test_compatible_release(self):
        # ~=2.28 means >=2.28, ==2.*
        assert _compare_versions("2.30", "~=", "2.28") is True
        assert _compare_versions("3.0", "~=", "2.28") is False

    def test_unknown_operator(self):
        # Unknown op — assume satisfied
        assert _compare_versions("1.0", "??", "2.0") is True


# ── TestDependencyReport ──


class TestDependencyReport:
    def test_satisfied_all_found(self):
        report = DependencyReport(
            dependencies=[
                DependencyStatus("git", "binary", None, True, message="ok"),
                DependencyStatus("requests", "python", None, True, message="ok"),
            ]
        )
        assert report.satisfied is True
        assert report.missing == []

    def test_not_satisfied_some_missing(self):
        report = DependencyReport(
            dependencies=[
                DependencyStatus("git", "binary", None, True, message="ok"),
                DependencyStatus("pandoc", "binary", None, False, message="missing"),
            ]
        )
        assert report.satisfied is False
        assert len(report.missing) == 1
        assert report.missing[0].name == "pandoc"

    def test_empty_report(self):
        report = DependencyReport()
        assert report.satisfied is True
        assert report.missing == []

    def test_summary_format(self):
        report = DependencyReport(
            dependencies=[
                DependencyStatus(
                    "git",
                    "binary",
                    None,
                    True,
                    found_version="2.43.0",
                    message="found",
                ),
                DependencyStatus(
                    "pandoc",
                    "binary",
                    ">=3.0",
                    False,
                    message="not found",
                ),
            ]
        )
        summary = report.summary()
        assert "[OK] git (2.43.0)" in summary
        assert "[MISSING] pandoc" in summary
        assert "1/2 dependencies satisfied" in summary


# ── TestCheckRequirements ──


class TestCheckRequirements:
    def test_binary_found(self):
        with (
            patch("depdetect.shutil.which", return_value="/usr/bin/git"),
            patch("depdetect.subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(stdout="git version 2.43.0\n", stderr="")
            reqs = [Requirement("git", "binary")]
            report = check_requirements(reqs)
            assert report.satisfied is True

    def test_binary_not_found(self):
        with patch("depdetect.shutil.which", return_value=None):
            reqs = [Requirement("nonexistent", "binary")]
            report = check_requirements(reqs)
            assert report.satisfied is False

    def test_python_package_found(self):
        mock_spec = MagicMock()
        with (
            patch("depdetect.importlib.util.find_spec", return_value=mock_spec),
            patch("depdetect.importlib.metadata.version", return_value="2.31.0"),
        ):
            reqs = [Requirement("requests", "python", ">=", "2.28")]
            report = check_requirements(reqs)
            assert report.satisfied is True
            assert report.dependencies[0].found_version == "2.31.0"

    def test_python_version_fail(self):
        mock_spec = MagicMock()
        with (
            patch("depdetect.importlib.util.find_spec", return_value=mock_spec),
            patch("depdetect.importlib.metadata.version", return_value="1.0.0"),
        ):
            reqs = [Requirement("requests", "python", ">=", "2.28")]
            report = check_requirements(reqs)
            assert report.satisfied is False
            assert "!~" in report.dependencies[0].message

    def test_env_var_found(self):
        with patch.dict(os.environ, {"API_KEY": "secret"}):
            reqs = [Requirement("API_KEY", "env")]
            report = check_requirements(reqs)
            assert report.satisfied is True

    def test_env_var_missing(self):
        env = os.environ.copy()
        env.pop("MISSING_KEY", None)
        with patch.dict(os.environ, env, clear=True):
            reqs = [Requirement("MISSING_KEY", "env")]
            report = check_requirements(reqs)
            assert report.satisfied is False

    def test_runtime_python(self):
        reqs = [Requirement("Python", "runtime", ">=", "3.10")]
        report = check_requirements(reqs)
        # We're running on Python 3.10+, so this should pass
        assert report.satisfied is True
        assert report.dependencies[0].found_version is not None

    def test_mixed_requirements(self):
        with (
            patch("depdetect.shutil.which", return_value="/usr/bin/git"),
            patch("depdetect.subprocess.run") as mock_run,
            patch.dict(os.environ, {"MY_VAR": "yes"}),
        ):
            mock_run.return_value = MagicMock(stdout="git version 2.43.0\n", stderr="")
            reqs = [
                Requirement("git", "binary"),
                Requirement("MY_VAR", "env"),
                Requirement("Python", "runtime", ">=", "3.10"),
            ]
            report = check_requirements(reqs)
            assert report.satisfied is True
            assert len(report.dependencies) == 3

    def test_unknown_category(self):
        reqs = [Requirement("foo", "unknown_cat")]
        report = check_requirements(reqs)
        assert report.satisfied is False
        assert "unknown category" in report.dependencies[0].message


# ── TestAnalyzeSource ──


class TestAnalyzeSource:
    def test_resolves_pip_names(self):
        source = "import yaml\nfrom PIL import Image\n"
        result = analyze_source(source)
        result_lower = {r.lower() for r in result}
        assert "pyyaml" in result_lower
        assert "pillow" in result_lower

    def test_empty_source(self):
        assert analyze_source("") == set()

    def test_stdlib_excluded(self):
        source = "import os\nimport sys\nimport json\n"
        assert analyze_source(source) == set()

    def test_syntax_error_raises(self):
        with pytest.raises(DepdetectError):
            analyze_source("def (broken")

    def test_mixed(self):
        source = (
            "import os\nimport requests\n"
            "from sklearn.model_selection import train_test_split\n"
        )
        result = analyze_source(source)
        assert "requests" in result
        assert "scikit-learn" in result
        assert "os" not in result
