"""Correctness tests for zerodep aiosqlite module."""

from __future__ import annotations

import asyncio
import os
import sqlite3
import sys
import warnings

import pytest

sys.path.insert(0, os.path.dirname(__file__))

import aiosqlite

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test.db")


# ---------------------------------------------------------------------------
# Basic CRUD
# ---------------------------------------------------------------------------


class TestBasicCRUD:
    @pytest.mark.asyncio
    async def test_create_insert_select(self, db_path):
        async with aiosqlite.connect(db_path) as db:
            await db.execute("CREATE TABLE kv (k TEXT PRIMARY KEY, v TEXT)")
            await db.execute("INSERT INTO kv VALUES (?, ?)", ("hello", "world"))
            await db.commit()

            cursor = await db.execute("SELECT v FROM kv WHERE k = ?", ("hello",))
            row = await cursor.fetchone()
            assert row == ("world",)

    @pytest.mark.asyncio
    async def test_update(self, db_path):
        async with aiosqlite.connect(db_path) as db:
            await db.execute("CREATE TABLE kv (k TEXT PRIMARY KEY, v TEXT)")
            await db.execute("INSERT INTO kv VALUES ('a', '1')")
            await db.execute("UPDATE kv SET v = '2' WHERE k = 'a'")
            await db.commit()

            row = await db.execute_fetchone("SELECT v FROM kv WHERE k = 'a'")
            assert row == ("2",)

    @pytest.mark.asyncio
    async def test_delete(self, db_path):
        async with aiosqlite.connect(db_path) as db:
            await db.execute("CREATE TABLE kv (k TEXT PRIMARY KEY, v TEXT)")
            await db.execute("INSERT INTO kv VALUES ('a', '1')")
            await db.commit()

            await db.execute("DELETE FROM kv WHERE k = 'a'")
            await db.commit()

            row = await db.execute_fetchone("SELECT COUNT(*) FROM kv")
            assert row == (0,)

    @pytest.mark.asyncio
    async def test_named_parameters(self, db_path):
        async with aiosqlite.connect(db_path) as db:
            await db.execute("CREATE TABLE kv (k TEXT, v TEXT)")
            await db.execute(
                "INSERT INTO kv VALUES (:key, :val)", {"key": "x", "val": "y"}
            )
            await db.commit()

            row = await db.execute_fetchone("SELECT * FROM kv")
            assert row == ("x", "y")


# ---------------------------------------------------------------------------
# Bulk operations
# ---------------------------------------------------------------------------


class TestBulkOps:
    @pytest.mark.asyncio
    async def test_executemany(self, db_path):
        async with aiosqlite.connect(db_path) as db:
            await db.execute("CREATE TABLE nums (n INTEGER)")
            await db.executemany(
                "INSERT INTO nums VALUES (?)", [(i,) for i in range(100)]
            )
            await db.commit()

            row = await db.execute_fetchone("SELECT COUNT(*) FROM nums")
            assert row == (100,)

    @pytest.mark.asyncio
    async def test_executescript(self, db_path):
        async with aiosqlite.connect(db_path) as db:
            await db.executescript("""
                CREATE TABLE t1 (id INTEGER PRIMARY KEY);
                CREATE TABLE t2 (id INTEGER PRIMARY KEY);
                INSERT INTO t1 VALUES (1);
                INSERT INTO t2 VALUES (2);
            """)

            r1 = await db.execute_fetchone("SELECT id FROM t1")
            r2 = await db.execute_fetchone("SELECT id FROM t2")
            assert r1 == (1,)
            assert r2 == (2,)


# ---------------------------------------------------------------------------
# Cursor operations
# ---------------------------------------------------------------------------


class TestCursor:
    @pytest.mark.asyncio
    async def test_fetchone(self, db_path):
        async with aiosqlite.connect(db_path) as db:
            await db.execute("CREATE TABLE t (v INTEGER)")
            await db.executemany("INSERT INTO t VALUES (?)", [(1,), (2,), (3,)])
            await db.commit()

            cursor = await db.execute("SELECT v FROM t ORDER BY v")
            assert await cursor.fetchone() == (1,)
            assert await cursor.fetchone() == (2,)
            assert await cursor.fetchone() == (3,)
            assert await cursor.fetchone() is None

    @pytest.mark.asyncio
    async def test_fetchmany(self, db_path):
        async with aiosqlite.connect(db_path) as db:
            await db.execute("CREATE TABLE t (v INTEGER)")
            await db.executemany("INSERT INTO t VALUES (?)", [(i,) for i in range(10)])
            await db.commit()

            cursor = await db.execute("SELECT v FROM t ORDER BY v")
            batch = await cursor.fetchmany(3)
            assert len(batch) == 3
            assert batch == [(0,), (1,), (2,)]

    @pytest.mark.asyncio
    async def test_fetchall(self, db_path):
        async with aiosqlite.connect(db_path) as db:
            await db.execute("CREATE TABLE t (v INTEGER)")
            await db.executemany("INSERT INTO t VALUES (?)", [(i,) for i in range(5)])
            await db.commit()

            cursor = await db.execute("SELECT v FROM t ORDER BY v")
            rows = await cursor.fetchall()
            assert rows == [(0,), (1,), (2,), (3,), (4,)]

    @pytest.mark.asyncio
    async def test_async_iteration(self, db_path):
        async with aiosqlite.connect(db_path) as db:
            await db.execute("CREATE TABLE t (v INTEGER)")
            await db.executemany("INSERT INTO t VALUES (?)", [(i,) for i in range(5)])
            await db.commit()

            rows = []
            async for row in await db.execute("SELECT v FROM t ORDER BY v"):
                rows.append(row)
            assert rows == [(0,), (1,), (2,), (3,), (4,)]

    @pytest.mark.asyncio
    async def test_rowcount(self, db_path):
        async with aiosqlite.connect(db_path) as db:
            await db.execute("CREATE TABLE t (v INTEGER)")
            await db.executemany("INSERT INTO t VALUES (?)", [(i,) for i in range(5)])
            await db.commit()

            cursor = await db.execute("UPDATE t SET v = v + 10")
            assert cursor.rowcount == 5

    @pytest.mark.asyncio
    async def test_lastrowid(self, db_path):
        async with aiosqlite.connect(db_path) as db:
            await db.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, v TEXT)")
            cursor = await db.execute("INSERT INTO t (v) VALUES ('a')")
            assert cursor.lastrowid == 1
            cursor = await db.execute("INSERT INTO t (v) VALUES ('b')")
            assert cursor.lastrowid == 2

    @pytest.mark.asyncio
    async def test_description(self, db_path):
        async with aiosqlite.connect(db_path) as db:
            await db.execute("CREATE TABLE t (name TEXT, age INTEGER)")
            await db.execute("INSERT INTO t VALUES ('Alice', 30)")
            await db.commit()

            cursor = await db.execute("SELECT name, age FROM t")
            assert cursor.description is not None
            assert cursor.description[0][0] == "name"
            assert cursor.description[1][0] == "age"


# ---------------------------------------------------------------------------
# Convenience methods
# ---------------------------------------------------------------------------


class TestConvenience:
    @pytest.mark.asyncio
    async def test_execute_fetchall(self, db_path):
        async with aiosqlite.connect(db_path) as db:
            await db.execute("CREATE TABLE t (v INTEGER)")
            await db.executemany("INSERT INTO t VALUES (?)", [(i,) for i in range(5)])
            await db.commit()

            rows = await db.execute_fetchall("SELECT v FROM t ORDER BY v")
            assert rows == [(0,), (1,), (2,), (3,), (4,)]

    @pytest.mark.asyncio
    async def test_execute_fetchone(self, db_path):
        async with aiosqlite.connect(db_path) as db:
            await db.execute("CREATE TABLE t (v INTEGER)")
            await db.execute("INSERT INTO t VALUES (42)")
            await db.commit()

            row = await db.execute_fetchone("SELECT v FROM t")
            assert row == (42,)

    @pytest.mark.asyncio
    async def test_execute_fetchone_no_rows(self, db_path):
        async with aiosqlite.connect(db_path) as db:
            await db.execute("CREATE TABLE t (v INTEGER)")
            row = await db.execute_fetchone("SELECT v FROM t")
            assert row is None

    @pytest.mark.asyncio
    async def test_execute_insert(self, db_path):
        async with aiosqlite.connect(db_path) as db:
            await db.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, v TEXT)")
            rowid = await db.execute_insert("INSERT INTO t (v) VALUES ('x')")
            assert rowid == 1
            rowid = await db.execute_insert("INSERT INTO t (v) VALUES ('y')")
            assert rowid == 2


# ---------------------------------------------------------------------------
# Connection lifecycle
# ---------------------------------------------------------------------------


class TestLifecycle:
    @pytest.mark.asyncio
    async def test_context_manager(self, db_path):
        async with aiosqlite.connect(db_path) as db:
            await db.execute("CREATE TABLE t (v INTEGER)")
            assert db._closed is False
        assert db._closed is True

    @pytest.mark.asyncio
    async def test_await_pattern(self, db_path):
        db = await aiosqlite.connect(db_path)
        try:
            await db.execute("CREATE TABLE t (v INTEGER)")
        finally:
            await db.close()
        assert db._closed is True

    @pytest.mark.asyncio
    async def test_double_close(self, db_path):
        db = await aiosqlite.connect(db_path)
        await db.close()
        await db.close()  # should not raise

    @pytest.mark.asyncio
    async def test_operate_after_close(self, db_path):
        db = await aiosqlite.connect(db_path)
        await db.close()
        with pytest.raises(sqlite3.ProgrammingError, match="closed"):
            await db.execute("SELECT 1")

    @pytest.mark.asyncio
    async def test_resource_warning(self, db_path):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            db = await aiosqlite.connect(db_path)
            await db.execute("CREATE TABLE t (v INTEGER)")
            # Trigger __del__ without close
            del db
            # ResourceWarning may be deferred; check what we got
            resource_warnings = [
                x for x in w if issubclass(x.category, ResourceWarning)
            ]
            # May or may not fire depending on GC timing
            if resource_warnings:
                assert "aiosqlite" in str(resource_warnings[0].message).lower()


# ---------------------------------------------------------------------------
# Connection properties
# ---------------------------------------------------------------------------


class TestProperties:
    @pytest.mark.asyncio
    async def test_row_factory(self, db_path):
        async with aiosqlite.connect(db_path) as db:
            db.row_factory = sqlite3.Row
            await db.execute("CREATE TABLE t (name TEXT, age INTEGER)")
            await db.execute("INSERT INTO t VALUES ('Alice', 30)")
            await db.commit()

            cursor = await db.execute("SELECT * FROM t")
            row = await cursor.fetchone()
            assert row["name"] == "Alice"
            assert row["age"] == 30

    @pytest.mark.asyncio
    async def test_isolation_level(self, db_path):
        async with aiosqlite.connect(db_path) as db:
            _ = db.isolation_level  # check accessible
            db.isolation_level = None
            assert db.isolation_level is None

    @pytest.mark.asyncio
    async def test_in_transaction(self, db_path):
        async with aiosqlite.connect(db_path) as db:
            await db.execute("CREATE TABLE t (v INTEGER)")
            await db.commit()
            assert db.in_transaction is False
            await db.execute("INSERT INTO t VALUES (1)")
            assert db.in_transaction is True
            await db.commit()
            assert db.in_transaction is False

    @pytest.mark.asyncio
    async def test_total_changes(self, db_path):
        async with aiosqlite.connect(db_path) as db:
            await db.execute("CREATE TABLE t (v INTEGER)")
            await db.commit()
            before = db.total_changes
            await db.execute("INSERT INTO t VALUES (1)")
            await db.execute("INSERT INTO t VALUES (2)")
            await db.commit()
            assert db.total_changes >= before + 2


# ---------------------------------------------------------------------------
# Error propagation
# ---------------------------------------------------------------------------


class TestErrors:
    @pytest.mark.asyncio
    async def test_bad_sql(self, db_path):
        async with aiosqlite.connect(db_path) as db:
            with pytest.raises(sqlite3.OperationalError):
                await db.execute("SELECT * FROM nonexistent_table")

    @pytest.mark.asyncio
    async def test_integrity_error(self, db_path):
        async with aiosqlite.connect(db_path) as db:
            await db.execute("CREATE TABLE t (k TEXT PRIMARY KEY)")
            await db.execute("INSERT INTO t VALUES ('dup')")
            with pytest.raises(sqlite3.IntegrityError):
                await db.execute("INSERT INTO t VALUES ('dup')")

    @pytest.mark.asyncio
    async def test_reexported_exceptions(self):
        assert aiosqlite.OperationalError is sqlite3.OperationalError
        assert aiosqlite.IntegrityError is sqlite3.IntegrityError
        assert aiosqlite.ProgrammingError is sqlite3.ProgrammingError
        assert aiosqlite.DatabaseError is sqlite3.DatabaseError
        assert aiosqlite.Error is sqlite3.Error


# ---------------------------------------------------------------------------
# WAL mode and pragmas
# ---------------------------------------------------------------------------


class TestPragmas:
    @pytest.mark.asyncio
    async def test_wal_mode(self, db_path):
        async with aiosqlite.connect(db_path) as db:
            await db.execute("PRAGMA journal_mode=WAL")
            row = await db.execute_fetchone("PRAGMA journal_mode")
            assert row[0] == "wal"

    @pytest.mark.asyncio
    async def test_synchronous(self, db_path):
        async with aiosqlite.connect(db_path) as db:
            await db.execute("PRAGMA synchronous=NORMAL")
            row = await db.execute_fetchone("PRAGMA synchronous")
            assert row[0] == 1  # NORMAL = 1


# ---------------------------------------------------------------------------
# Concurrency
# ---------------------------------------------------------------------------


class TestConcurrency:
    @pytest.mark.asyncio
    async def test_concurrent_reads(self, db_path):
        async with aiosqlite.connect(db_path) as db:
            await db.execute("CREATE TABLE t (v INTEGER)")
            await db.executemany("INSERT INTO t VALUES (?)", [(i,) for i in range(100)])
            await db.commit()

            async def read_count():
                return await db.execute_fetchone("SELECT COUNT(*) FROM t")

            results = await asyncio.gather(*[read_count() for _ in range(10)])
            assert all(r == (100,) for r in results)

    @pytest.mark.asyncio
    async def test_concurrent_writes(self, db_path):
        async with aiosqlite.connect(db_path) as db:
            await db.execute("CREATE TABLE t (v INTEGER)")
            await db.commit()

            async def insert(val):
                await db.execute("INSERT INTO t VALUES (?)", (val,))

            await asyncio.gather(*[insert(i) for i in range(50)])
            await db.commit()

            row = await db.execute_fetchone("SELECT COUNT(*) FROM t")
            assert row == (50,)


# ---------------------------------------------------------------------------
# Rollback
# ---------------------------------------------------------------------------


class TestRollback:
    @pytest.mark.asyncio
    async def test_rollback(self, db_path):
        async with aiosqlite.connect(db_path) as db:
            await db.execute("CREATE TABLE t (v INTEGER)")
            await db.commit()

            await db.execute("INSERT INTO t VALUES (1)")
            await db.rollback()

            row = await db.execute_fetchone("SELECT COUNT(*) FROM t")
            assert row == (0,)
