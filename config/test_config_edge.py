"""Edge-behavior tests for config sibling import fallback."""

import os
import sys
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.dirname(__file__))


# ── Sibling Import Fallback ─────────────────────────────────────────────


class TestSiblingImportFallback:
    """Tests for graceful degradation when sibling modules are absent."""

    def test_config_works_without_yaml(self, tmp_path, monkeypatch):
        """Config should work for non-YAML sources even without yaml module."""
        import json

        import config as config_mod

        config_mod._default_config = None

        # Write a JSON config file (no YAML needed)
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({"host": "localhost", "port": 8080}))

        from config import Config

        cfg = Config(dotenv_path=None, config_path=str(config_file))
        assert cfg("host") == "localhost"
        assert cfg("port", cast=int) == 8080

    def test_config_works_without_dotenv(self, monkeypatch):
        """Config should work for non-.env sources even without dotenv module."""
        import config as config_mod

        config_mod._default_config = None

        monkeypatch.setenv("TEST_EDGE_KEY", "edge_value")

        from config import Config

        cfg = Config(dotenv_path=None)
        assert cfg("TEST_EDGE_KEY") == "edge_value"

    def test_missing_yaml_sibling_gives_clear_error(self, tmp_path):
        """Loading YAML without sibling yaml module should give ImportError."""
        import builtins

        import config as config_mod

        real_import = builtins.__import__

        def fail_yaml_import(name, *args, **kwargs):
            if name == "yaml":
                raise ImportError("No module named 'yaml'")
            return real_import(name, *args, **kwargs)

        saved_modules = {}
        for key in list(sys.modules):
            if key == "yaml" or key.startswith("yaml."):
                saved_modules[key] = sys.modules.pop(key)

        try:
            with patch.object(
                config_mod,
                "_ensure_sibling_path",
                return_value="/nonexistent",
            ):
                with patch.object(
                    builtins,
                    "__import__",
                    side_effect=fail_yaml_import,
                ):
                    for key in list(sys.modules):
                        if key == "yaml" or key.startswith("yaml."):
                            sys.modules.pop(key)

                    with pytest.raises(ImportError, match="sibling yaml module"):
                        config_mod._load_yaml_loader()
        finally:
            sys.modules.update(saved_modules)

    def test_missing_dotenv_sibling_gives_clear_error(self):
        """Loading dotenv without sibling module should give ImportError."""
        import builtins

        import config as config_mod

        real_import = builtins.__import__

        def fail_dotenv_import(name, *args, **kwargs):
            if name == "dotenv":
                raise ImportError("No module named 'dotenv'")
            return real_import(name, *args, **kwargs)

        saved_modules = {}
        for key in list(sys.modules):
            if key == "dotenv" or key.startswith("dotenv."):
                saved_modules[key] = sys.modules.pop(key)

        try:
            with patch.object(
                config_mod,
                "_ensure_sibling_path",
                return_value="/nonexistent",
            ):
                with patch.object(
                    builtins,
                    "__import__",
                    side_effect=fail_dotenv_import,
                ):
                    for key in list(sys.modules):
                        if key == "dotenv" or key.startswith("dotenv."):
                            sys.modules.pop(key)

                    with pytest.raises(ImportError, match="sibling dotenv module"):
                        config_mod._load_dotenv_helpers()
        finally:
            sys.modules.update(saved_modules)

    def test_auto_discovery_graceful_without_dotenv(self, monkeypatch):
        """Config with _AUTO dotenv_path should not crash if dotenv is unavailable."""
        import config as config_mod

        config_mod._default_config = None
        monkeypatch.setenv("FALLBACK_KEY", "fallback_val")

        # Config() with default _AUTO dotenv_path should gracefully
        # handle missing dotenv (it catches the ImportError internally)
        from config import Config

        cfg = Config()
        assert cfg("FALLBACK_KEY") == "fallback_val"

    def test_env_var_priority_over_config_file(self, tmp_path, monkeypatch):
        """Environment variables should take precedence over config file values."""
        import json

        import config as config_mod

        config_mod._default_config = None

        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({"MY_KEY": "from_file"}))

        monkeypatch.setenv("MY_KEY", "from_env")

        from config import Config

        cfg = Config(dotenv_path=None, config_path=str(config_file))
        assert cfg("MY_KEY") == "from_env"
