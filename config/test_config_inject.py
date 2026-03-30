"""Tests for Config loaders + dotenv_loader injection API."""

from __future__ import annotations

import json
import os
import tempfile
import unittest


class TestConfigLoadersInjection(unittest.TestCase):
    """Test the loaders parameter on Config."""

    def test_custom_loader_for_custom_extension(self):
        """User can register a loader for a custom file extension."""
        from config import Config

        def _load_custom(path):
            return {"greeting": "hello"}

        with tempfile.NamedTemporaryFile(suffix=".custom", mode="w", delete=False) as f:
            f.write("ignored")
            f.flush()
            try:
                cfg = Config(
                    dotenv_path=None,
                    config_path=f.name,
                    loaders={".custom": _load_custom},
                )
                self.assertEqual(cfg("greeting"), "hello")
            finally:
                os.unlink(f.name)

    def test_override_yaml_loader(self):
        """User can replace the yaml loader with their own."""
        from config import Config

        def _mock_yaml_loader(path):
            return {"from_custom_yaml": True}

        with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w", delete=False) as f:
            f.write("key: value")
            f.flush()
            try:
                cfg = Config(
                    dotenv_path=None,
                    config_path=f.name,
                    loaders={".yaml": _mock_yaml_loader},
                )
                self.assertTrue(cfg("from_custom_yaml", cast=bool))
            finally:
                os.unlink(f.name)

    def test_empty_loaders_rejects_config_file(self):
        """When loaders={}, config_path should fail."""
        from config import Config

        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            json.dump({"k": "v"}, f)
            f.flush()
            try:
                with self.assertRaises(ValueError) as ctx:
                    Config(dotenv_path=None, config_path=f.name, loaders={})
                self.assertIn("Unsupported", str(ctx.exception))
            finally:
                os.unlink(f.name)

    def test_default_loaders_load_json(self):
        """Default behavior (loaders=_UNSET) still works for JSON."""
        from config import Config

        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            json.dump({"port": "8080"}, f)
            f.flush()
            try:
                cfg = Config(dotenv_path=None, config_path=f.name)
                self.assertEqual(cfg("port"), "8080")
            finally:
                os.unlink(f.name)


class TestConfigDotenvInjection(unittest.TestCase):
    """Test the dotenv_loader parameter on Config."""

    def test_dotenv_loader_none_disables_env(self):
        """dotenv_loader=None should skip .env loading entirely."""
        from config import Config

        # Even with AUTO dotenv_path, dotenv_loader=None should skip
        cfg = Config(dotenv_loader=None)
        # Should not raise; just have no dotenv data
        self.assertEqual(cfg._dotenv_data, {})

    def test_custom_dotenv_loader(self):
        """User can inject a custom dotenv loader."""
        from config import Config

        def _custom_dotenv_factory():
            def _values(path):
                return {"INJECTED_KEY": "injected_value"}

            def _find(**kwargs):
                return "/fake/.env"

            return _values, _find

        cfg = Config(dotenv_loader=_custom_dotenv_factory)
        self.assertEqual(cfg._dotenv_data.get("INJECTED_KEY"), "injected_value")

    def test_custom_dotenv_loader_with_explicit_path(self):
        """Custom dotenv loader works with explicit dotenv_path."""
        from config import Config

        def _custom_dotenv_factory():
            def _values(path):
                return {"FROM_PATH": path}

            def _find(**kwargs):
                return "unused"

            return _values, _find

        cfg = Config(dotenv_path="/my/.env", dotenv_loader=_custom_dotenv_factory)
        self.assertEqual(cfg._dotenv_data.get("FROM_PATH"), "/my/.env")


if __name__ == "__main__":
    unittest.main()
