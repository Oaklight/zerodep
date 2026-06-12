# /// zerodep
# version = "0.3.1"
# deps = ["dotenv", "yaml", "jsonx"]
# tier = "subsystem"
# category = "config"
# note = "Install/update via: https://zerodep.readthedocs.io/en/latest/guide/cli/"
# ///

"""Unified configuration loader — zero dependencies, stdlib only, Python 3.10+.

Part of zerodep: https://github.com/Oaklight/zerodep
Copyright (c) 2026 Peng Ding. MIT License.

Drop-in replacement for python-decouple / dynaconf core functionality.
Loads settings from environment variables, .env files, and config files
(JSON, JSONC, YAML, TOML, INI) with type coercion and prefix support.

Example::

    from config import config, setup

    # Auto-discovers .env, reads env vars
    setup(prefix="MYAPP_")
    debug = config("DEBUG", default=False, cast=bool)
    port  = config("PORT", default=8000, cast=int)
    hosts = config("ALLOWED_HOSTS", cast=Csv())

    # Or use Config directly
    cfg = Config(config_path="settings.yaml", prefix="MYAPP_")
    db_host = cfg("DATABASE__HOST", default="localhost")
"""

from __future__ import annotations

import configparser
import json
import os
import sys
from pathlib import Path
from typing import Any, Callable, Sequence

__all__ = [
    # Sentinels
    "MISSING",
    # Exceptions
    "ConfigError",
    "UndefinedValueError",
    # Type coercion helpers
    "Csv",
    "Choices",
    # Main class
    "Config",
    # Module-level convenience
    "setup",
    "config",
]


def _ensure_sibling_path(name: str) -> str:
    """Return the sibling module directory and prepend it to ``sys.path``."""
    sibling_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", name)
    if sibling_dir not in sys.path:
        sys.path.insert(0, sibling_dir)
    return sibling_dir


# ── Sibling module loaders (lazy) ───────────────────────────────────────────


def _load_dotenv_helpers() -> tuple[Callable[..., Any], Callable[..., Any]]:
    """Load sibling ``dotenv`` helpers on demand."""
    _ensure_sibling_path("dotenv")
    sys.modules.pop("dotenv", None)
    try:
        from dotenv import dotenv_values, find_dotenv
    except ImportError as exc:
        raise ImportError(
            ".env loading requires the sibling dotenv module. "
            "Copy dotenv/dotenv.py into your project, "
            "or set dotenv_path=None to disable."
        ) from exc
    return dotenv_values, find_dotenv


def _load_yaml_loader() -> Callable[[str], Any]:
    """Load the sibling ``yaml`` module's ``load`` function on demand."""
    _ensure_sibling_path("yaml")
    sys.modules.pop("yaml", None)
    try:
        from yaml import load as yaml_load
    except ImportError as exc:
        raise ImportError(
            "YAML config files require the sibling yaml module. "
            "Copy yaml/yaml.py into your project."
        ) from exc
    return yaml_load


def _load_jsonx_loader() -> Callable[[str], Any] | None:
    """Load the sibling ``jsonx`` (or legacy ``jsonc``) module's loader.

    Returns the ``loads`` function if available, else ``None``.
    """
    # Try jsonx first (renamed from jsonc)
    _ensure_sibling_path("jsonx")
    sys.modules.pop("jsonx", None)
    try:
        from jsonx import loads as jsonx_loads
    except ImportError:
        # Fall back to legacy jsonc for backward compatibility
        _ensure_sibling_path("jsonc")
        sys.modules.pop("jsonc", None)
        try:
            from jsonc import loads as jsonx_loads
        except ImportError:
            return None
    return jsonx_loads


# ── Stdlib tomllib (Python 3.11+) ───────────────────────────────────────────

try:
    import tomllib  # type: ignore[import-not-found]

    _HAS_TOML = True
except ModuleNotFoundError:
    _HAS_TOML = False

# ── Sentinels ───────────────────────────────────────────────────────────────


class _Missing:
    """Sentinel for missing configuration values."""

    _instance: _Missing | None = None

    def __new__(cls) -> _Missing:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "MISSING"

    def __bool__(self) -> bool:
        return False


MISSING = _Missing()


class _Auto:
    """Sentinel indicating auto-discovery of .env files."""

    _instance: _Auto | None = None

    def __new__(cls) -> _Auto:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "AUTO"


_AUTO = _Auto()

# ── Sentinel for injection parameters ──────────────────────────────────────


class _Unset:
    """Sentinel indicating 'use default sibling auto-discovery'."""

    _instance: _Unset | None = None

    def __new__(cls) -> _Unset:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "UNSET"


_UNSET = _Unset()

# ── Exceptions ──────────────────────────────────────────────────────────────


class ConfigError(Exception):
    """Base exception for all config operations."""


class UndefinedValueError(ConfigError):
    """Raised when a required configuration value is missing."""


# ── Bool constants ──────────────────────────────────────────────────────────

_TRUTHY = frozenset({"1", "true", "yes", "on", "t", "y"})
_FALSY = frozenset({"0", "false", "no", "off", "f", "n", ""})

# ── Type coercion helpers ───────────────────────────────────────────────────


class Csv:
    """Parse comma-separated values with optional per-item casting.

    Example::

        Csv()("a, b, c")           # ["a", "b", "c"]
        Csv(cast=int)("1,2,3")     # [1, 2, 3]
        Csv(delimiter=";")("a;b")  # ["a", "b"]

    Args:
        cast: Callable applied to each item after splitting.
        delimiter: String to split on.
        strip: Characters to strip from each item. Use ``" %s"`` to strip
            whitespace around the format-string placeholder (default).
        post_process: Callable applied to the final list (e.g. ``tuple``).
    """

    def __init__(
        self,
        cast: Callable[[str], Any] = str,
        delimiter: str = ",",
        strip: str = " %s",
        post_process: Callable[[list[Any]], Any] = list,
    ) -> None:
        self.cast = cast
        self.delimiter = delimiter
        self.strip = strip
        self.post_process = post_process

    def __call__(self, value: str) -> Any:
        if isinstance(value, (list, tuple)):
            return self.post_process([self.cast(item) for item in value])
        parts = str(value).split(self.delimiter)
        result = []
        for part in parts:
            item = part.strip(self.strip.replace("%s", "")) if self.strip else part
            if item or not self.strip:
                result.append(self.cast(item))
        return self.post_process(result)


class Choices:
    """Validate that a value belongs to a fixed set.

    Example::

        Choices(["dev", "staging", "prod"])("dev")  # "dev"
        Choices([1, 2, 3], cast=int)("2")           # 2

    Args:
        choices: Allowed values (after casting).
        cast: Callable applied before validation.
    """

    def __init__(
        self,
        choices: Sequence[Any],
        cast: Callable[[str], Any] = str,
    ) -> None:
        self.choices = choices
        self.cast = cast

    def __call__(self, value: str) -> Any:
        casted = self.cast(value)
        if casted not in self.choices:
            raise ValueError(
                f"{casted!r} is not a valid choice. Allowed: {list(self.choices)}"
            )
        return casted


# ── File loaders ────────────────────────────────────────────────────────────


def _load_json_file(path: str | os.PathLike[str]) -> dict[str, Any]:
    """Load a JSON file and return a dict."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"JSON config must be an object, got {type(data).__name__}")
    return data


def _load_jsonc_file(path: str | os.PathLike[str]) -> dict[str, Any]:
    """Load a JSONC file, falling back to plain JSON if jsonc module is unavailable."""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    jsonc_loads = _load_jsonx_loader()
    if jsonc_loads is not None:
        data = jsonc_loads(text)
    else:
        data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError(f"JSONC config must be an object, got {type(data).__name__}")
    return data


def _load_yaml_file(path: str | os.PathLike[str]) -> dict[str, Any]:
    """Load a YAML file using the sibling yaml module."""
    yaml_load = _load_yaml_loader()
    with open(path, encoding="utf-8") as f:
        text = f.read()
    data = yaml_load(text)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML config must be a mapping, got {type(data).__name__}")
    return data


def _load_toml_file(path: str | os.PathLike[str]) -> dict[str, Any]:
    """Load a TOML file using stdlib tomllib (Python 3.11+)."""
    if not _HAS_TOML:
        raise ImportError("TOML config files require Python 3.11+ (tomllib).")
    with open(path, "rb") as f:
        return tomllib.load(f)


def _load_ini_file(
    path: str | os.PathLike[str], separator: str = "__"
) -> dict[str, Any]:
    """Load an INI/CFG file and flatten sections into separator-joined keys.

    Example: ``[database]`` section with ``host = localhost`` becomes
    ``database__host = localhost`` (using the default separator).
    """
    parser = configparser.ConfigParser()
    parser.read(path, encoding="utf-8")
    data: dict[str, Any] = {}
    for section in parser.sections():
        for key, value in parser.items(section):
            flat_key = f"{section}{separator}{key}"
            data[flat_key] = value
    if parser.defaults():
        for key, value in parser.defaults().items():
            data[key] = value
    return data


_LOADERS: dict[str, Callable[..., dict[str, Any]]] = {
    ".json": _load_json_file,
    ".jsonc": _load_jsonc_file,
    ".yaml": _load_yaml_file,
    ".yml": _load_yaml_file,
    ".toml": _load_toml_file,
    ".ini": _load_ini_file,
    ".cfg": _load_ini_file,
}

# ── Internal helpers ────────────────────────────────────────────────────────


def _cast_bool(value: Any) -> bool:
    """Convert a value to bool using common truthy/falsy strings."""
    if isinstance(value, bool):
        return value
    s = str(value).lower().strip()
    if s in _TRUTHY:
        return True
    if s in _FALSY:
        return False
    raise ValueError(
        f"Cannot convert {value!r} to bool. Use one of: {sorted(_TRUTHY | _FALSY)}"
    )


def _cast_list(value: Any) -> list[Any]:
    """Convert a value to list: try JSON array first, then comma-split."""
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    s = str(value).strip()
    if s.startswith("["):
        try:
            result = json.loads(s)
            if isinstance(result, list):
                return result
        except (json.JSONDecodeError, ValueError):
            pass
    return [item.strip() for item in s.split(",") if item.strip()]


def _cast_tuple(value: Any) -> tuple[Any, ...]:
    """Convert a value to tuple via _cast_list."""
    return tuple(_cast_list(value))


def _apply_cast(value: Any, cast: type | Callable[..., Any] | None) -> Any:
    """Apply a type cast to a value."""
    if cast is None:
        return value
    if cast is bool:
        return _cast_bool(value)
    if cast is list:
        return _cast_list(value)
    if cast is tuple:
        return _cast_tuple(value)
    return cast(value)


def _deep_get(data: dict[str, Any], parts: list[str]) -> Any:
    """Retrieve a nested value from a dict using a list of key parts.

    Returns *MISSING* if any intermediate key is missing or not a dict.
    """
    current: Any = data
    for part in parts:
        if not isinstance(current, dict):
            return MISSING
        # Try exact key first, then case-insensitive
        if part in current:
            current = current[part]
        else:
            lower = part.lower()
            found = False
            for k in current:
                if k.lower() == lower:
                    current = current[k]
                    found = True
                    break
            if not found:
                return MISSING
    return current


def _flatten_dict(
    data: dict[str, Any], separator: str = "__", prefix: str = ""
) -> dict[str, Any]:
    """Flatten a nested dict into separator-joined keys."""
    result: dict[str, Any] = {}
    for key, value in data.items():
        full_key = f"{prefix}{separator}{key}" if prefix else key
        if isinstance(value, dict):
            result.update(_flatten_dict(value, separator, full_key))
        else:
            result[full_key] = value
    return result


# ── Main Config class ───────────────────────────────────────────────────────


class Config:
    """Unified configuration loader with multi-source support.

    Sources are checked in priority order (highest first):

    1. Environment variables (``os.environ``), optionally prefixed
    2. ``.env`` file values (via sibling dotenv module)
    3. Config file values (JSON, JSONC, YAML, TOML, INI)
    4. Default value passed to ``get()``/``__call__()``

    Args:
        dotenv_path: Path to ``.env`` file. Use ``None`` to disable,
            or omit (default ``_AUTO``) to auto-discover by searching
            upward from the current directory.
        config_path: Path to a config file. Format is detected from the
            file extension.
        prefix: Prefix for environment variable lookups. For example,
            ``prefix="MYAPP_"`` means looking up ``"PORT"`` checks
            ``os.environ["MYAPP_PORT"]``.
        separator: Separator for nested key access. Default ``"__"``
            means ``"DATABASE__HOST"`` resolves to ``data["DATABASE"]["HOST"]``
            or ``data["database"]["host"]`` in config files.
        loaders: Override the file-format loader registry. Defaults to
            ``_UNSET`` (use built-in loaders with sibling auto-discovery
            for yaml/jsonc). Pass a ``dict`` mapping extensions (e.g.
            ``".yaml"``) to loader callables to replace the defaults.
            Stdlib loaders (json, toml, ini) are always available unless
            explicitly overridden.
        dotenv_loader: Override the dotenv loading mechanism. Defaults to
            ``_UNSET`` (auto-discover sibling ``dotenv`` module). Pass
            ``None`` to disable .env loading entirely, or a callable that
            returns ``(dotenv_values_fn, find_dotenv_fn)`` to inject a
            custom implementation.

    Example::

        cfg = Config(config_path="settings.yaml", prefix="MYAPP_")
        debug = cfg("DEBUG", default=False, cast=bool)
        db_host = cfg("DATABASE__HOST", default="localhost")
    """

    def __init__(
        self,
        *,
        dotenv_path: str | os.PathLike[str] | None | _Auto = _AUTO,
        config_path: str | os.PathLike[str] | None = None,
        prefix: str = "",
        separator: str = "__",
        loaders: dict[str, Callable[..., dict[str, Any]]] | None | _Unset = _UNSET,
        dotenv_loader: Callable[[], tuple[Callable[..., Any], Callable[..., Any]]]
        | None
        | _Unset = _UNSET,
    ) -> None:
        self._prefix = prefix
        self._separator = separator
        self._dotenv_data: dict[str, str | None] = {}
        self._config_data: dict[str, Any] = {}
        self._loaders: dict[str, Callable[..., dict[str, Any]]]

        # Resolve loader registry
        if isinstance(loaders, _Unset):
            self._loaders = _LOADERS
        elif loaders is None:
            self._loaders = {}
        else:
            self._loaders = loaders

        # Load .env file
        if dotenv_loader is None:
            pass  # .env explicitly disabled
        elif isinstance(dotenv_path, _Auto):
            try:
                if isinstance(dotenv_loader, _Unset):
                    dotenv_values, find_dotenv = _load_dotenv_helpers()
                else:
                    dotenv_values, find_dotenv = dotenv_loader()
            except ImportError:
                pass
            else:
                found = find_dotenv(usecwd=True)
                if found:
                    self._dotenv_data = dotenv_values(found)
        elif dotenv_path is not None:
            if isinstance(dotenv_loader, _Unset):
                dotenv_values, _find_dotenv = _load_dotenv_helpers()
            else:
                dotenv_values, _find_dotenv = dotenv_loader()
            self._dotenv_data = dotenv_values(str(dotenv_path))

        # Load config file
        if config_path is not None:
            self._load_config_file(config_path)

    def _load_config_file(self, path: str | os.PathLike[str]) -> None:
        """Load a config file based on its extension."""
        p = Path(path)
        ext = p.suffix.lower()
        loader = self._loaders.get(ext)
        if loader is None:
            raise ValueError(
                f"Unsupported config file format: {ext!r}. "
                f"Supported: {', '.join(sorted(self._loaders))}"
            )
        if loader in (_load_ini_file,):
            self._config_data = loader(p, separator=self._separator)
        else:
            self._config_data = loader(p)

    def _lookup(self, key: str) -> Any:
        """Look up a key across all sources in priority order.

        Returns the value if found, or *MISSING* if not found anywhere.
        """
        # 1. Environment variables (with prefix)
        env_key = f"{self._prefix}{key}" if self._prefix else key
        env_val = os.environ.get(env_key)
        if env_val is not None:
            return env_val

        # 2. .env file values (with prefix)
        dotenv_val = self._dotenv_data.get(env_key)
        if dotenv_val is not None:
            return dotenv_val

        # 3. Config file values (exact key first, then nested lookup)
        if self._config_data:
            # Exact key match (e.g. INI-flattened keys)
            if key in self._config_data:
                return self._config_data[key]
            # Nested lookup via separator splitting
            if self._separator in key:
                parts = key.split(self._separator)
                result = _deep_get(self._config_data, parts)
                if result is not MISSING:
                    return result

        return MISSING

    def get(
        self,
        key: str,
        *,
        default: Any = MISSING,
        cast: type | Callable[..., Any] | None = None,
    ) -> Any:
        """Retrieve a configuration value.

        Args:
            key: Configuration key to look up.
            default: Default value if key is not found. If not provided and
                the key is missing, ``UndefinedValueError`` is raised.
            cast: Type or callable to apply to the value. Built-in support
                for ``bool``, ``int``, ``float``, ``list``, ``tuple``.
                Also accepts ``Csv(...)`` and ``Choices(...)`` instances.

        Returns:
            The resolved and optionally cast configuration value.

        Raises:
            UndefinedValueError: If key is missing and no default is given.
        """
        value = self._lookup(key)

        if value is MISSING:
            if default is MISSING:
                raise UndefinedValueError(
                    f"{key!r} is not set and has no default value."
                )
            value = default

        return _apply_cast(value, cast)

    def __call__(
        self,
        key: str,
        *,
        default: Any = MISSING,
        cast: type | Callable[..., Any] | None = None,
    ) -> Any:
        """Shorthand for ``get()``. See :meth:`get` for details."""
        return self.get(key, default=default, cast=cast)

    def has(self, key: str) -> bool:
        """Check whether a key exists in any source."""
        return self._lookup(key) is not MISSING

    def as_dict(self) -> dict[str, Any]:
        """Return a merged view of all config sources (flattened).

        Lower-priority sources are merged first, so higher-priority
        sources overwrite them.
        """
        merged: dict[str, Any] = {}
        # 3. Config file (lowest priority)
        if self._config_data:
            merged.update(_flatten_dict(self._config_data, self._separator))
        # 2. .env file
        for k, v in self._dotenv_data.items():
            if v is not None:
                merged[k] = v
        # 1. Environment variables (only those matching prefix)
        if self._prefix:
            plen = len(self._prefix)
            for k, v in os.environ.items():
                if k.startswith(self._prefix):
                    merged[k[plen:]] = v
        else:
            merged.update(os.environ)
        return merged


# ── Module-level convenience ────────────────────────────────────────────────

_default_config: Config | None = None


def setup(
    *,
    dotenv_path: str | os.PathLike[str] | None | _Auto = _AUTO,
    config_path: str | os.PathLike[str] | None = None,
    prefix: str = "",
    separator: str = "__",
) -> Config:
    """Initialize the module-level :class:`Config` instance.

    Call this once at application startup to configure sources and prefix.
    Subsequent calls to :func:`config` will use this instance.

    Args:
        dotenv_path: Path to ``.env`` file, ``None`` to disable, or
            ``_AUTO`` (default) to auto-discover.
        config_path: Path to a config file (JSON/YAML/TOML/INI).
        prefix: Prefix for environment variable lookups.
        separator: Separator for nested key access.

    Returns:
        The newly created :class:`Config` instance.
    """
    global _default_config
    _default_config = Config(
        dotenv_path=dotenv_path,
        config_path=config_path,
        prefix=prefix,
        separator=separator,
    )
    return _default_config


def config(
    key: str,
    *,
    default: Any = MISSING,
    cast: type | Callable[..., Any] | None = None,
) -> Any:
    """Look up a configuration value using the module-level instance.

    If :func:`setup` has not been called, a default :class:`Config` is
    created automatically (auto-discovers ``.env``, no config file,
    no prefix).

    Args:
        key: Configuration key.
        default: Fallback value if missing.
        cast: Type or callable to coerce the value.

    Returns:
        The resolved configuration value.

    Raises:
        UndefinedValueError: If key is missing and no default.
    """
    global _default_config
    if _default_config is None:
        _default_config = Config()
    return _default_config(key, default=default, cast=cast)
