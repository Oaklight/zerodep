"""Correctness tests for zerodep config module.

Covers: env vars, .env files, config files (JSON/YAML/TOML/INI),
type coercion (bool/int/float/list/tuple), Csv, Choices, prefix,
nested keys, priority override, UndefinedValueError, and comparison
with python-decouple where applicable.
"""

from __future__ import annotations

import json
import os
import sys
import textwrap

import pytest

sys.path.insert(0, os.path.dirname(__file__))
from config import (
    MISSING,
    Choices,
    Config,
    Csv,
    UndefinedValueError,
    _apply_cast,
    _cast_bool,
    _cast_list,
    _deep_get,
    _flatten_dict,
    config,
    setup,
)

# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    """Remove test env vars and reset module-level config between tests."""
    import config as config_mod

    config_mod._default_config = None
    for key in list(os.environ):
        if key.startswith("ZCFG_") or key.startswith("TEST_"):
            monkeypatch.delenv(key, raising=False)


@pytest.fixture()
def tmp_env(tmp_path):
    """Write a .env file in a temp dir and return its path."""

    def _write(content: str, filename: str = ".env") -> str:
        p = tmp_path / filename
        p.write_text(textwrap.dedent(content))
        return str(p)

    return _write


@pytest.fixture()
def tmp_config(tmp_path):
    """Write a config file in a temp dir and return its path."""

    def _write(content: str, filename: str) -> str:
        p = tmp_path / filename
        if filename.endswith(".toml"):
            p.write_bytes(content.encode("utf-8"))
        else:
            p.write_text(textwrap.dedent(content))
        return str(p)

    return _write


# ── Bool coercion ───────────────────────────────────────────────────────────


class TestCastBool:
    @pytest.mark.parametrize(
        "val", ["1", "true", "True", "TRUE", "yes", "on", "t", "y"]
    )
    def test_truthy(self, val):
        assert _cast_bool(val) is True

    @pytest.mark.parametrize(
        "val",
        ["0", "false", "False", "FALSE", "no", "off", "f", "n", ""],
    )
    def test_falsy(self, val):
        assert _cast_bool(val) is False

    def test_bool_passthrough(self):
        assert _cast_bool(True) is True
        assert _cast_bool(False) is False

    def test_invalid(self):
        with pytest.raises(ValueError, match="Cannot convert"):
            _cast_bool("maybe")


# ── List coercion ───────────────────────────────────────────────────────────


class TestCastList:
    def test_csv(self):
        assert _cast_list("a, b, c") == ["a", "b", "c"]

    def test_json_array(self):
        assert _cast_list('["x", "y"]') == ["x", "y"]

    def test_already_list(self):
        assert _cast_list([1, 2]) == [1, 2]

    def test_already_tuple(self):
        assert _cast_list((1, 2)) == [1, 2]

    def test_empty(self):
        assert _cast_list("") == []


# ── Apply cast ──────────────────────────────────────────────────────────────


class TestApplyCast:
    def test_none_cast(self):
        assert _apply_cast("hello", None) == "hello"

    def test_int(self):
        assert _apply_cast("42", int) == 42

    def test_float(self):
        assert _apply_cast("3.14", float) == pytest.approx(3.14)

    def test_bool(self):
        assert _apply_cast("yes", bool) is True

    def test_list(self):
        assert _apply_cast("a,b", list) == ["a", "b"]

    def test_tuple(self):
        assert _apply_cast("a,b", tuple) == ("a", "b")

    def test_custom_callable(self):
        assert _apply_cast("hello", str.upper) == "HELLO"


# ── Deep get ────────────────────────────────────────────────────────────────


class TestDeepGet:
    def test_simple(self):
        assert _deep_get({"a": 1}, ["a"]) == 1

    def test_nested(self):
        assert _deep_get({"a": {"b": {"c": 3}}}, ["a", "b", "c"]) == 3

    def test_missing(self):
        assert _deep_get({"a": 1}, ["b"]) is MISSING

    def test_missing_nested(self):
        assert _deep_get({"a": 1}, ["a", "b"]) is MISSING

    def test_case_insensitive(self):
        data = {"Database": {"Host": "localhost"}}
        assert _deep_get(data, ["database", "host"]) == "localhost"


# ── Flatten dict ────────────────────────────────────────────────────────────


class TestFlattenDict:
    def test_flat(self):
        assert _flatten_dict({"a": 1, "b": 2}) == {"a": 1, "b": 2}

    def test_nested(self):
        assert _flatten_dict({"db": {"host": "localhost", "port": 5432}}) == {
            "db__host": "localhost",
            "db__port": 5432,
        }

    def test_custom_separator(self):
        result = _flatten_dict({"db": {"host": "h"}}, separator=".")
        assert result == {"db.host": "h"}


# ── Csv helper ──────────────────────────────────────────────────────────────


class TestCsv:
    def test_basic(self):
        assert Csv()("a, b, c") == ["a", "b", "c"]

    def test_cast_int(self):
        assert Csv(cast=int)("1,2,3") == [1, 2, 3]

    def test_custom_delimiter(self):
        assert Csv(delimiter=";")("a;b;c") == ["a", "b", "c"]

    def test_post_process_tuple(self):
        assert Csv(post_process=tuple)("a,b") == ("a", "b")

    def test_list_passthrough(self):
        assert Csv(cast=int)([1, 2, 3]) == [1, 2, 3]


# ── Choices helper ──────────────────────────────────────────────────────────


class TestChoices:
    def test_valid(self):
        c = Choices(["dev", "staging", "prod"])
        assert c("dev") == "dev"

    def test_invalid(self):
        c = Choices(["dev", "prod"])
        with pytest.raises(ValueError, match="not a valid choice"):
            c("staging")

    def test_with_cast(self):
        c = Choices([1, 2, 3], cast=int)
        assert c("2") == 2


# ── Config from env vars ───────────────────────────────────────────────────


class TestConfigEnvVars:
    def test_read_env(self, monkeypatch):
        monkeypatch.setenv("TEST_KEY", "value123")
        cfg = Config(dotenv_path=None)
        assert cfg("TEST_KEY") == "value123"

    def test_prefix(self, monkeypatch):
        monkeypatch.setenv("MYAPP_PORT", "8080")
        cfg = Config(dotenv_path=None, prefix="MYAPP_")
        assert cfg("PORT", cast=int) == 8080

    def test_missing_raises(self):
        cfg = Config(dotenv_path=None)
        with pytest.raises(UndefinedValueError, match="not set"):
            cfg("SURELY_MISSING_KEY_XYZ")

    def test_default(self):
        cfg = Config(dotenv_path=None)
        assert cfg("MISSING_KEY", default="fallback") == "fallback"

    def test_default_with_cast(self):
        cfg = Config(dotenv_path=None)
        assert cfg("MISSING", default="42", cast=int) == 42

    def test_has(self, monkeypatch):
        monkeypatch.setenv("TEST_EXISTS", "1")
        cfg = Config(dotenv_path=None)
        assert cfg.has("TEST_EXISTS") is True
        assert cfg.has("TEST_NOT_EXISTS") is False


# ── Config from .env file ──────────────────────────────────────────────────


class TestConfigDotenv:
    def test_load_dotenv(self, tmp_env):
        path = tmp_env("DB_HOST=localhost\nDB_PORT=5432\n")
        cfg = Config(dotenv_path=path)
        assert cfg("DB_HOST") == "localhost"
        assert cfg("DB_PORT", cast=int) == 5432

    def test_env_overrides_dotenv(self, monkeypatch, tmp_env):
        path = tmp_env("APP_MODE=file\n")
        monkeypatch.setenv("APP_MODE", "env")
        cfg = Config(dotenv_path=path)
        assert cfg("APP_MODE") == "env"

    def test_dotenv_with_prefix(self, tmp_env):
        path = tmp_env("MYAPP_SECRET=abc123\n")
        cfg = Config(dotenv_path=path, prefix="MYAPP_")
        assert cfg("SECRET") == "abc123"


# ── Config from JSON file ──────────────────────────────────────────────────


class TestConfigJson:
    def test_flat_json(self, tmp_config):
        path = tmp_config('{"host": "localhost", "port": 5432}', "config.json")
        cfg = Config(dotenv_path=None, config_path=path)
        assert cfg("host") == "localhost"
        assert cfg("port", cast=int) == 5432

    def test_nested_json(self, tmp_config):
        data = {"database": {"host": "db.example.com", "port": 3306}}
        path = tmp_config(json.dumps(data), "config.json")
        cfg = Config(dotenv_path=None, config_path=path)
        assert cfg("database__host") == "db.example.com"
        assert cfg("database__port", cast=int) == 3306

    def test_invalid_json_root(self, tmp_config):
        path = tmp_config("[1, 2, 3]", "config.json")
        with pytest.raises(ValueError, match="must be an object"):
            Config(dotenv_path=None, config_path=path)


# ── Config from YAML file ──────────────────────────────────────────────────


class TestConfigYaml:
    def test_flat_yaml(self, tmp_config):
        pytest.importorskip("yaml", reason="sibling yaml module required")
        path = tmp_config("host: localhost\nport: 5432\n", "config.yaml")
        cfg = Config(dotenv_path=None, config_path=path)
        assert cfg("host") == "localhost"
        assert cfg("port", cast=int) == 5432

    def test_nested_yaml(self, tmp_config):
        pytest.importorskip("yaml", reason="sibling yaml module required")
        content = "database:\n  host: db.example.com\n  port: 3306\n"
        path = tmp_config(content, "config.yml")
        cfg = Config(dotenv_path=None, config_path=path)
        assert cfg("database__host") == "db.example.com"

    def test_empty_yaml(self, tmp_config):
        pytest.importorskip("yaml", reason="sibling yaml module required")
        path = tmp_config("", "config.yaml")
        cfg = Config(dotenv_path=None, config_path=path)
        assert cfg("key", default="fallback") == "fallback"


# ── Config from TOML file ──────────────────────────────────────────────────


class TestConfigToml:
    def test_flat_toml(self, tmp_config):
        pytest.importorskip("tomllib", reason="Python 3.11+ required")
        path = tmp_config('host = "localhost"\nport = 5432\n', "config.toml")
        cfg = Config(dotenv_path=None, config_path=path)
        assert cfg("host") == "localhost"
        assert cfg("port", cast=int) == 5432

    def test_nested_toml(self, tmp_config):
        pytest.importorskip("tomllib", reason="Python 3.11+ required")
        content = '[database]\nhost = "db.example.com"\nport = 3306\n'
        path = tmp_config(content, "config.toml")
        cfg = Config(dotenv_path=None, config_path=path)
        assert cfg("database__host") == "db.example.com"


# ── Config from INI file ───────────────────────────────────────────────────


class TestConfigIni:
    def test_ini_sections(self, tmp_config):
        content = "[database]\nhost = localhost\nport = 5432\n"
        path = tmp_config(content, "settings.ini")
        cfg = Config(dotenv_path=None, config_path=path)
        assert cfg("database__host") == "localhost"
        assert cfg("database__port", cast=int) == 5432

    def test_ini_defaults(self, tmp_config):
        content = "[DEFAULT]\ndebug = false\n\n[app]\nname = myapp\n"
        path = tmp_config(content, "settings.cfg")
        cfg = Config(dotenv_path=None, config_path=path)
        assert cfg("app__name") == "myapp"
        # DEFAULT values appear in every section
        assert cfg("app__debug", cast=bool) is False


# ── Priority override ──────────────────────────────────────────────────────


class TestPriority:
    def test_env_over_dotenv_over_config(self, monkeypatch, tmp_env, tmp_config):
        # Config file has lowest priority
        config_path = tmp_config('{"APP_MODE": "config"}', "config.json")
        # .env has medium priority
        dotenv_path = tmp_env("APP_MODE=dotenv\n")
        cfg = Config(dotenv_path=dotenv_path, config_path=config_path)

        # .env wins over config file
        assert cfg("APP_MODE") == "dotenv"

        # env var wins over .env
        monkeypatch.setenv("APP_MODE", "environ")
        assert cfg("APP_MODE") == "environ"

    def test_default_is_lowest(self, tmp_config):
        config_path = tmp_config('{"key": "from_file"}', "config.json")
        cfg = Config(dotenv_path=None, config_path=config_path)
        assert cfg("key", default="ignored") == "from_file"


# ── Nested key access ──────────────────────────────────────────────────────


class TestNestedKeys:
    def test_separator(self, tmp_config):
        data = {"level1": {"level2": {"level3": "deep"}}}
        path = tmp_config(json.dumps(data), "config.json")
        cfg = Config(dotenv_path=None, config_path=path)
        assert cfg("level1__level2__level3") == "deep"

    def test_custom_separator(self, tmp_config):
        data = {"a": {"b": "found"}}
        path = tmp_config(json.dumps(data), "config.json")
        cfg = Config(dotenv_path=None, config_path=path, separator=".")
        assert cfg("a.b") == "found"

    def test_env_overrides_nested(self, monkeypatch, tmp_config):
        data = {"database": {"host": "from_file"}}
        path = tmp_config(json.dumps(data), "config.json")
        monkeypatch.setenv("database__host", "from_env")
        cfg = Config(dotenv_path=None, config_path=path)
        assert cfg("database__host") == "from_env"


# ── as_dict ─────────────────────────────────────────────────────────────────


class TestAsDict:
    def test_includes_config(self, tmp_config):
        data = {"db": {"host": "h", "port": 5432}}
        path = tmp_config(json.dumps(data), "config.json")
        cfg = Config(dotenv_path=None, config_path=path)
        d = cfg.as_dict()
        assert d["db__host"] == "h"
        assert d["db__port"] == 5432

    def test_prefix_strips_in_as_dict(self, monkeypatch):
        monkeypatch.setenv("APP_KEY1", "v1")
        cfg = Config(dotenv_path=None, prefix="APP_")
        d = cfg.as_dict()
        assert d["KEY1"] == "v1"


# ── Module-level convenience ────────────────────────────────────────────────


class TestModuleLevel:
    def test_setup_and_config(self, monkeypatch):
        monkeypatch.setenv("ZCFG_PORT", "9090")
        setup(dotenv_path=None, prefix="ZCFG_")
        assert config("PORT", cast=int) == 9090

    def test_auto_init(self, monkeypatch):
        import config as config_mod

        config_mod._default_config = None
        monkeypatch.setenv("AUTO_KEY", "auto_val")
        assert config("AUTO_KEY") == "auto_val"


# ── Unsupported format ──────────────────────────────────────────────────────


class TestUnsupportedFormat:
    def test_bad_extension(self, tmp_config):
        path = tmp_config("data", "config.xyz")
        with pytest.raises(ValueError, match="Unsupported config file format"):
            Config(dotenv_path=None, config_path=path)


# ── Comparison with python-decouple ─────────────────────────────────────────

_has_decouple = True
try:
    import decouple as ref_decouple
except ImportError:
    _has_decouple = False


@pytest.mark.skipif(not _has_decouple, reason="python-decouple not installed")
class TestVsDecouple:
    """Verify our behavior matches python-decouple for common scenarios."""

    def test_env_lookup(self, monkeypatch):
        monkeypatch.setenv("DECOUPLE_TEST", "hello")
        assert config("DECOUPLE_TEST") == ref_decouple.config("DECOUPLE_TEST")

    def test_default(self):
        mine = config("MISSING_DEC", default="fb")
        theirs = ref_decouple.config("MISSING_DEC", default="fb")
        assert mine == theirs

    def test_cast_int(self, monkeypatch):
        monkeypatch.setenv("DEC_INT", "42")
        assert config("DEC_INT", cast=int) == ref_decouple.config("DEC_INT", cast=int)

    def test_cast_bool_true(self, monkeypatch):
        monkeypatch.setenv("DEC_BOOL", "true")
        assert config("DEC_BOOL", cast=bool) is True
        assert ref_decouple.config("DEC_BOOL", cast=bool) is True

    def test_cast_bool_false(self, monkeypatch):
        monkeypatch.setenv("DEC_BOOL_F", "false")
        assert config("DEC_BOOL_F", cast=bool) is False
        assert ref_decouple.config("DEC_BOOL_F", cast=bool) is False

    def test_csv(self, monkeypatch):
        monkeypatch.setenv("DEC_CSV", "a, b, c")
        mine = config("DEC_CSV", cast=Csv())
        theirs = ref_decouple.config("DEC_CSV", cast=ref_decouple.Csv())
        assert mine == theirs

    def test_choices_valid(self, monkeypatch):
        monkeypatch.setenv("DEC_ENV", "prod")
        mine = config("DEC_ENV", cast=Choices(["dev", "prod"]))
        theirs = ref_decouple.config(
            "DEC_ENV",
            cast=ref_decouple.Choices(["dev", "prod"]),
        )
        assert mine == theirs

    def test_choices_invalid(self, monkeypatch):
        monkeypatch.setenv("DEC_ENV2", "staging")
        with pytest.raises(ValueError):
            config("DEC_ENV2", cast=Choices(["dev", "prod"]))
        with pytest.raises(ValueError):
            ref_decouple.config(
                "DEC_ENV2",
                cast=ref_decouple.Choices(["dev", "prod"]),
            )

    def test_undefined_raises(self):
        with pytest.raises(UndefinedValueError):
            config("TOTALLY_UNDEFINED_KEY_XYZ")
        with pytest.raises(ref_decouple.UndefinedValueError):
            ref_decouple.config("TOTALLY_UNDEFINED_KEY_XYZ")
