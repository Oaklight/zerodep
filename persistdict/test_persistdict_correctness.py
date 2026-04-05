"""Correctness tests: zerodep persistdict."""

import os
import sys
import tempfile
import threading

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from persistdict import (
    Backend,
    JsonFileBackend,
    JsonSerializer,
    Serializer,
    SqliteBackend,
    open,
)

# ── Fixtures ──────────────────────────────────────────────────────────────


@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d


@pytest.fixture(params=["json", "sqlite"], ids=["json-backend", "sqlite-backend"])
def persist_dict(request, tmp_dir):
    """Parametrized fixture yielding PersistDict with each backend."""
    if request.param == "json":
        path = os.path.join(tmp_dir, "test.json")
    else:
        path = os.path.join(tmp_dir, "test.db")
    d = open(path)
    yield d
    d.close()


@pytest.fixture(params=["json", "sqlite"], ids=["json-backend", "sqlite-backend"])
def backend_path(request, tmp_dir):
    """Return (backend_type, path) tuple."""
    if request.param == "json":
        return ("json", os.path.join(tmp_dir, "test.json"))
    return ("sqlite", os.path.join(tmp_dir, "test.db"))


# ── TestJsonSerializer ────────────────────────────────────────────────────


class TestJsonSerializer:
    def test_round_trip_primitives(self):
        s = JsonSerializer()
        for val in ("hello", 42, 3.14, True, False, None):
            assert s.loads(s.dumps(val)) == val

    def test_round_trip_collections(self):
        s = JsonSerializer()
        data = {"a": [1, 2, {"nested": True}], "b": None}
        assert s.loads(s.dumps(data)) == data

    def test_non_serializable_raises(self):
        s = JsonSerializer()
        with pytest.raises(TypeError):
            s.dumps(object())

    def test_custom_kwargs(self):
        s = JsonSerializer(sort_keys=True, indent=2)
        result = s.dumps({"b": 1, "a": 2})
        assert result.index('"a"') < result.index('"b"')
        assert "\n" in result

    def test_ensure_ascii_default(self):
        s = JsonSerializer()
        result = s.dumps("你好")
        assert "你好" in result

    def test_ensure_ascii_true(self):
        s = JsonSerializer(ensure_ascii=True)
        result = s.dumps("你好")
        assert "\\u" in result

    def test_protocol_compliance(self):
        assert isinstance(JsonSerializer(), Serializer)


# ── TestJsonFileBackend ───────────────────────────────────────────────────


class TestJsonFileBackend:
    def test_create_new(self, tmp_dir):
        path = os.path.join(tmp_dir, "new.json")
        be = JsonFileBackend(path)
        assert len(be) == 0
        be.close()

    def test_set_get(self, tmp_dir):
        path = os.path.join(tmp_dir, "test.json")
        be = JsonFileBackend(path)
        be.set("k", '"v"')
        assert be.get("k") == '"v"'
        be.close()

    def test_get_missing_raises(self, tmp_dir):
        be = JsonFileBackend(os.path.join(tmp_dir, "test.json"))
        with pytest.raises(KeyError):
            be.get("missing")
        be.close()

    def test_delete(self, tmp_dir):
        be = JsonFileBackend(os.path.join(tmp_dir, "test.json"))
        be.set("k", "1")
        be.delete("k")
        assert not be.contains("k")
        be.close()

    def test_delete_missing_raises(self, tmp_dir):
        be = JsonFileBackend(os.path.join(tmp_dir, "test.json"))
        with pytest.raises(KeyError):
            be.delete("nope")
        be.close()

    def test_contains(self, tmp_dir):
        be = JsonFileBackend(os.path.join(tmp_dir, "test.json"))
        be.set("k", "1")
        assert be.contains("k")
        assert not be.contains("other")
        be.close()

    def test_keys_and_len(self, tmp_dir):
        be = JsonFileBackend(os.path.join(tmp_dir, "test.json"))
        be.set("a", "1")
        be.set("b", "2")
        assert sorted(be.keys()) == ["a", "b"]
        assert len(be) == 2
        be.close()

    def test_clear(self, tmp_dir):
        be = JsonFileBackend(os.path.join(tmp_dir, "test.json"))
        be.set("a", "1")
        be.set("b", "2")
        be.clear()
        assert len(be) == 0
        be.close()

    def test_persistence(self, tmp_dir):
        path = os.path.join(tmp_dir, "test.json")
        be = JsonFileBackend(path)
        be.set("key", '"value"')
        be.close()
        be2 = JsonFileBackend(path)
        assert be2.get("key") == '"value"'
        be2.close()

    def test_atomic_flush(self, tmp_dir):
        path = os.path.join(tmp_dir, "test.json")
        be = JsonFileBackend(path)
        be.set("k", "1")
        be.flush()
        assert os.path.exists(path)
        be.close()

    def test_corrupt_file_raises(self, tmp_dir):
        path = os.path.join(tmp_dir, "bad.json")
        with builtins_open(path, "w") as f:
            f.write("{invalid json")
        with pytest.raises(ValueError, match="corrupt JSON"):
            JsonFileBackend(path)

    def test_empty_file(self, tmp_dir):
        path = os.path.join(tmp_dir, "empty.json")
        with builtins_open(path, "w") as f:
            f.write("")
        be = JsonFileBackend(path)
        assert len(be) == 0
        be.close()

    def test_empty_object_file(self, tmp_dir):
        path = os.path.join(tmp_dir, "empty_obj.json")
        with builtins_open(path, "w") as f:
            f.write("{}")
        be = JsonFileBackend(path)
        assert len(be) == 0
        be.close()

    def test_non_object_file_raises(self, tmp_dir):
        path = os.path.join(tmp_dir, "list.json")
        with builtins_open(path, "w") as f:
            f.write("[1, 2, 3]")
        with pytest.raises(ValueError, match="expected JSON object"):
            JsonFileBackend(path)

    def test_parent_dir_creation(self, tmp_dir):
        path = os.path.join(tmp_dir, "sub", "dir", "test.json")
        be = JsonFileBackend(path)
        be.set("k", "1")
        be.flush()
        assert os.path.exists(path)
        be.close()

    def test_protocol_compliance(self, tmp_dir):
        be = JsonFileBackend(os.path.join(tmp_dir, "test.json"))
        assert isinstance(be, Backend)
        be.close()


# ── TestSqliteBackend ─────────────────────────────────────────────────────


class TestSqliteBackend:
    def test_create_new(self, tmp_dir):
        path = os.path.join(tmp_dir, "new.db")
        be = SqliteBackend(path)
        assert len(be) == 0
        be.close()

    def test_set_get(self, tmp_dir):
        be = SqliteBackend(os.path.join(tmp_dir, "test.db"))
        be.set("k", '"v"')
        assert be.get("k") == '"v"'
        be.close()

    def test_get_missing_raises(self, tmp_dir):
        be = SqliteBackend(os.path.join(tmp_dir, "test.db"))
        with pytest.raises(KeyError):
            be.get("missing")
        be.close()

    def test_delete(self, tmp_dir):
        be = SqliteBackend(os.path.join(tmp_dir, "test.db"))
        be.set("k", "1")
        be.delete("k")
        assert not be.contains("k")
        be.close()

    def test_delete_missing_raises(self, tmp_dir):
        be = SqliteBackend(os.path.join(tmp_dir, "test.db"))
        with pytest.raises(KeyError):
            be.delete("nope")
        be.close()

    def test_contains(self, tmp_dir):
        be = SqliteBackend(os.path.join(tmp_dir, "test.db"))
        be.set("k", "1")
        assert be.contains("k")
        assert not be.contains("other")
        be.close()

    def test_keys_and_len(self, tmp_dir):
        be = SqliteBackend(os.path.join(tmp_dir, "test.db"))
        be.set("a", "1")
        be.set("b", "2")
        assert sorted(be.keys()) == ["a", "b"]
        assert len(be) == 2
        be.close()

    def test_clear(self, tmp_dir):
        be = SqliteBackend(os.path.join(tmp_dir, "test.db"))
        be.set("a", "1")
        be.set("b", "2")
        be.clear()
        assert len(be) == 0
        be.close()

    def test_persistence(self, tmp_dir):
        path = os.path.join(tmp_dir, "test.db")
        be = SqliteBackend(path)
        be.set("key", '"value"')
        be.close()
        be2 = SqliteBackend(path)
        assert be2.get("key") == '"value"'
        be2.close()

    def test_wal_mode(self, tmp_dir):
        be = SqliteBackend(os.path.join(tmp_dir, "test.db"))
        mode = be._conn.execute("PRAGMA journal_mode").fetchone()[0]
        assert mode == "wal"
        be.close()

    def test_invalid_table_name(self, tmp_dir):
        with pytest.raises(ValueError, match="invalid table name"):
            SqliteBackend(os.path.join(tmp_dir, "test.db"), table="drop table;")

    def test_invalid_table_name_digit_start(self, tmp_dir):
        with pytest.raises(ValueError, match="invalid table name"):
            SqliteBackend(os.path.join(tmp_dir, "test.db"), table="123bad")

    def test_multi_table(self, tmp_dir):
        path = os.path.join(tmp_dir, "multi.db")
        be1 = SqliteBackend(path, table="users")
        be2 = SqliteBackend(path, table="config")
        be1.set("alice", "1")
        be2.set("debug", "true")
        assert be1.contains("alice")
        assert not be1.contains("debug")
        assert be2.contains("debug")
        assert not be2.contains("alice")
        be1.close()
        be2.close()

    def test_parent_dir_creation(self, tmp_dir):
        path = os.path.join(tmp_dir, "sub", "dir", "test.db")
        be = SqliteBackend(path)
        be.set("k", "1")
        assert os.path.exists(path)
        be.close()

    def test_protocol_compliance(self, tmp_dir):
        be = SqliteBackend(os.path.join(tmp_dir, "test.db"))
        assert isinstance(be, Backend)
        be.close()

    def test_upsert(self, tmp_dir):
        be = SqliteBackend(os.path.join(tmp_dir, "test.db"))
        be.set("k", "old")
        be.set("k", "new")
        assert be.get("k") == "new"
        assert len(be) == 1
        be.close()


# ── TestPersistDict ───────────────────────────────────────────────────────


class TestPersistDict:
    def test_getitem_setitem(self, persist_dict):
        persist_dict["name"] = "Alice"
        assert persist_dict["name"] == "Alice"

    def test_getitem_missing_raises(self, persist_dict):
        with pytest.raises(KeyError):
            persist_dict["missing"]

    def test_delitem(self, persist_dict):
        persist_dict["k"] = 1
        del persist_dict["k"]
        assert "k" not in persist_dict

    def test_delitem_missing_raises(self, persist_dict):
        with pytest.raises(KeyError):
            del persist_dict["nope"]

    def test_iter(self, persist_dict):
        persist_dict["a"] = 1
        persist_dict["b"] = 2
        assert sorted(persist_dict) == ["a", "b"]

    def test_len(self, persist_dict):
        assert len(persist_dict) == 0
        persist_dict["x"] = 1
        assert len(persist_dict) == 1

    def test_contains(self, persist_dict):
        persist_dict["k"] = 1
        assert "k" in persist_dict
        assert "other" not in persist_dict

    def test_contains_non_str(self, persist_dict):
        assert 42 not in persist_dict

    def test_get_default(self, persist_dict):
        assert persist_dict.get("missing") is None
        assert persist_dict.get("missing", 99) == 99

    def test_pop(self, persist_dict):
        persist_dict["k"] = "v"
        assert persist_dict.pop("k") == "v"
        assert "k" not in persist_dict

    def test_pop_default(self, persist_dict):
        assert persist_dict.pop("nope", "default") == "default"

    def test_popitem(self, persist_dict):
        persist_dict["only"] = 1
        k, v = persist_dict.popitem()
        assert k == "only"
        assert v == 1
        assert len(persist_dict) == 0

    def test_clear(self, persist_dict):
        persist_dict["a"] = 1
        persist_dict["b"] = 2
        persist_dict.clear()
        assert len(persist_dict) == 0

    def test_update(self, persist_dict):
        persist_dict.update({"a": 1, "b": 2})
        assert persist_dict["a"] == 1
        assert persist_dict["b"] == 2

    def test_setdefault(self, persist_dict):
        persist_dict.setdefault("k", 42)
        assert persist_dict["k"] == 42
        persist_dict.setdefault("k", 99)
        assert persist_dict["k"] == 42

    def test_keys_values_items(self, persist_dict):
        persist_dict["a"] = 1
        persist_dict["b"] = 2
        assert sorted(persist_dict.keys()) == ["a", "b"]
        assert sorted(persist_dict.values()) == [1, 2]
        assert sorted(persist_dict.items()) == [("a", 1), ("b", 2)]

    def test_key_type_validation(self, persist_dict):
        with pytest.raises(TypeError, match="keys must be str"):
            persist_dict[123] = "value"
        with pytest.raises(TypeError, match="keys must be str"):
            _ = persist_dict[123]
        with pytest.raises(TypeError, match="keys must be str"):
            del persist_dict[123]

    def test_complex_values(self, persist_dict):
        data = {"nested": {"list": [1, 2, 3], "flag": True, "null": None}}
        persist_dict["complex"] = data
        assert persist_dict["complex"] == data

    def test_repr(self, persist_dict):
        r = repr(persist_dict)
        assert r.startswith("PersistDict(")


class TestPersistDictPersistence:
    def test_json_round_trip(self, tmp_dir):
        path = os.path.join(tmp_dir, "rt.json")
        with open(path) as d:
            d["name"] = "Alice"
            d["scores"] = [95, 87]
        with open(path) as d:
            assert d["name"] == "Alice"
            assert d["scores"] == [95, 87]
            assert len(d) == 2

    def test_sqlite_round_trip(self, tmp_dir):
        path = os.path.join(tmp_dir, "rt.db")
        with open(path) as d:
            d["name"] = "Alice"
            d["scores"] = [95, 87]
        with open(path) as d:
            assert d["name"] == "Alice"
            assert d["scores"] == [95, 87]
            assert len(d) == 2


class TestPersistDictCustomSerializer:
    def test_custom_serializer(self, tmp_dir):
        class UpperSerializer:
            def dumps(self, obj):
                return str(obj).upper()

            def loads(self, s):
                return s.lower()

        path = os.path.join(tmp_dir, "custom.db")
        d = open(path, serializer=UpperSerializer())
        d["k"] = "hello"
        assert d["k"] == "hello"
        d.close()


# ── TestPersistDictContextManager ─────────────────────────────────────────


class TestPersistDictContextManager:
    def test_context_manager(self, tmp_dir):
        path = os.path.join(tmp_dir, "ctx.json")
        with open(path) as d:
            d["k"] = "v"
        with open(path) as d:
            assert d["k"] == "v"

    def test_close_idempotent(self, tmp_dir):
        path = os.path.join(tmp_dir, "ctx.json")
        d = open(path)
        d["k"] = 1
        d.close()
        d.close()  # should not raise


# ── TestPersistDictThreadSafety ───────────────────────────────────────────


class TestPersistDictThreadSafety:
    def test_concurrent_writes(self, backend_path):
        kind, path = backend_path
        d = open(path, backend=kind)
        errors: list[Exception] = []

        def writer(start: int) -> None:
            try:
                for i in range(100):
                    d[f"key_{start + i}"] = start + i
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=writer, args=(i * 100,)) for i in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Thread errors: {errors}"
        assert len(d) == 400
        d.close()

    def test_concurrent_read_write(self, backend_path):
        kind, path = backend_path
        d = open(path, backend=kind)
        d["shared"] = 0
        errors: list[Exception] = []

        def writer() -> None:
            try:
                for i in range(200):
                    d["shared"] = i
            except Exception as exc:
                errors.append(exc)

        def reader() -> None:
            try:
                for _ in range(200):
                    _ = d["shared"]
            except Exception as exc:
                errors.append(exc)

        threads = [
            threading.Thread(target=writer),
            threading.Thread(target=reader),
            threading.Thread(target=reader),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Thread errors: {errors}"
        d.close()

    def test_no_lock(self, tmp_dir):
        path = os.path.join(tmp_dir, "nolock.db")
        d = open(path, lock=False)
        d["k"] = 1
        assert d["k"] == 1
        d.close()


# ── TestOpenFactory ───────────────────────────────────────────────────────


class TestOpenFactory:
    def test_auto_json(self, tmp_dir):
        path = os.path.join(tmp_dir, "data.json")
        d = open(path)
        assert isinstance(d._backend, JsonFileBackend)
        d.close()

    def test_auto_db(self, tmp_dir):
        path = os.path.join(tmp_dir, "data.db")
        d = open(path)
        assert isinstance(d._backend, SqliteBackend)
        d.close()

    def test_auto_sqlite(self, tmp_dir):
        path = os.path.join(tmp_dir, "data.sqlite")
        d = open(path)
        assert isinstance(d._backend, SqliteBackend)
        d.close()

    def test_auto_sqlite3(self, tmp_dir):
        path = os.path.join(tmp_dir, "data.sqlite3")
        d = open(path)
        assert isinstance(d._backend, SqliteBackend)
        d.close()

    def test_explicit_json(self, tmp_dir):
        path = os.path.join(tmp_dir, "data.dat")
        d = open(path, backend="json")
        assert isinstance(d._backend, JsonFileBackend)
        d.close()

    def test_explicit_sqlite(self, tmp_dir):
        path = os.path.join(tmp_dir, "data.dat")
        d = open(path, backend="sqlite")
        assert isinstance(d._backend, SqliteBackend)
        d.close()

    def test_unknown_extension_raises(self, tmp_dir):
        path = os.path.join(tmp_dir, "data.xyz")
        with pytest.raises(ValueError, match="cannot auto-detect"):
            open(path)

    def test_unknown_backend_raises(self, tmp_dir):
        path = os.path.join(tmp_dir, "data.json")
        with pytest.raises(ValueError, match="unknown backend"):
            open(path, backend="redis")

    def test_table_forwarded(self, tmp_dir):
        path = os.path.join(tmp_dir, "data.db")
        d = open(path, table="custom")
        assert d._backend._table == "custom"
        d.close()

    def test_context_manager_via_factory(self, tmp_dir):
        path = os.path.join(tmp_dir, "ctx.json")
        with open(path) as d:
            d["k"] = "v"
        with open(path) as d:
            assert d["k"] == "v"


# ── Helpers ───────────────────────────────────────────────────────────────

# Alias to avoid shadowing by persistdict.open
builtins_open = (  # type: ignore[index]
    __builtins__["open"] if isinstance(__builtins__, dict) else __builtins__.open
)
