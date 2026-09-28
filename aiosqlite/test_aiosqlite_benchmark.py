"""Benchmark: zerodep aiosqlite vs aiosqlite."""

import asyncio
import os
import sys

import pytest

_this_dir = os.path.dirname(__file__)

_saved_path = sys.path[:]
sys.path = [
    p
    for p in sys.path
    if os.path.abspath(p)
    not in (
        os.path.abspath(_this_dir),
        os.path.abspath(os.path.join(_this_dir, "..")),
    )
]
_cached = sys.modules.pop("aiosqlite", None)

try:
    import aiosqlite as ref_aiosqlite

    if not hasattr(ref_aiosqlite, "connect"):
        raise ImportError("Not the real aiosqlite")
except ImportError:
    pytest.skip("aiosqlite not installed", allow_module_level=True)
finally:
    sys.path = _saved_path
    for _k in list(sys.modules):
        if _k == "aiosqlite" or _k.startswith("aiosqlite."):
            sys.modules.pop(_k, None)
    if _cached is not None:
        sys.modules["aiosqlite"] = _cached

sys.path.insert(0, _this_dir)
import aiosqlite


def _run_async(coro_fn, *args, **kwargs):
    return asyncio.run(coro_fn(*args, **kwargs))


BULK_N = 1000
_ROWS = [(f"val_{i}",) for i in range(BULK_N)]

CREATE_TABLE = "CREATE TABLE IF NOT EXISTS t (id INTEGER PRIMARY KEY, v TEXT)"
INSERT_ONE = "INSERT INTO t (v) VALUES (?)"
SELECT_ALL = "SELECT * FROM t"


def _setup_db(db_path, lib, populate=False):
    async def _init():
        async with lib.connect(db_path) as db:
            await db.execute(CREATE_TABLE)
            if populate:
                await db.executemany(INSERT_ONE, _ROWS)
            await db.commit()

    asyncio.run(_init())


# ── Single INSERT + SELECT (basic latency) ──


class TestSingleInsertSelect:
    def test_zerodep(self, benchmark, tmp_path):
        db_path = str(tmp_path / "zd.db")
        _setup_db(db_path, aiosqlite)

        async def _bench():
            async with aiosqlite.connect(db_path) as db:
                await db.execute("DELETE FROM t")
                await db.execute(INSERT_ONE, ("hello",))
                await db.commit()
                cur = await db.execute("SELECT v FROM t WHERE id = last_insert_rowid()")
                await cur.fetchone()

        benchmark(_run_async, _bench)

    def test_aiosqlite(self, benchmark, tmp_path):
        db_path = str(tmp_path / "ref.db")
        _setup_db(db_path, ref_aiosqlite)

        async def _bench():
            async with ref_aiosqlite.connect(db_path) as db:
                await db.execute("DELETE FROM t")
                await db.execute(INSERT_ONE, ("hello",))
                await db.commit()
                cur = await db.execute("SELECT v FROM t WHERE id = last_insert_rowid()")
                await cur.fetchone()

        benchmark(_run_async, _bench)


# ── Bulk INSERT (executemany) ──


class TestBulkInsert:
    def test_zerodep(self, benchmark, tmp_path):
        db_path = str(tmp_path / "zd.db")
        _setup_db(db_path, aiosqlite)

        async def _bench():
            async with aiosqlite.connect(db_path) as db:
                await db.execute("DELETE FROM t")
                await db.executemany(INSERT_ONE, _ROWS)
                await db.commit()

        benchmark(_run_async, _bench)

    def test_aiosqlite(self, benchmark, tmp_path):
        db_path = str(tmp_path / "ref.db")
        _setup_db(db_path, ref_aiosqlite)

        async def _bench():
            async with ref_aiosqlite.connect(db_path) as db:
                await db.execute("DELETE FROM t")
                await db.executemany(INSERT_ONE, _ROWS)
                await db.commit()

        benchmark(_run_async, _bench)


# ── Bulk SELECT (execute_fetchall) ──


class TestBulkSelect:
    def test_zerodep(self, benchmark, tmp_path):
        db_path = str(tmp_path / "zd.db")
        _setup_db(db_path, aiosqlite, populate=True)

        async def _bench():
            async with aiosqlite.connect(db_path) as db:
                await db.execute_fetchall(SELECT_ALL)

        benchmark(_run_async, _bench)

    def test_aiosqlite(self, benchmark, tmp_path):
        db_path = str(tmp_path / "ref.db")
        _setup_db(db_path, ref_aiosqlite, populate=True)

        async def _bench():
            async with ref_aiosqlite.connect(db_path) as db:
                await db.execute_fetchall(SELECT_ALL)

        benchmark(_run_async, _bench)


# ── Cursor async iteration ──


class TestCursorIteration:
    def test_zerodep(self, benchmark, tmp_path):
        db_path = str(tmp_path / "zd.db")
        _setup_db(db_path, aiosqlite, populate=True)

        async def _bench():
            async with aiosqlite.connect(db_path) as db:
                rows = []
                async for row in await db.execute(SELECT_ALL):
                    rows.append(row)

        benchmark(_run_async, _bench)

    def test_aiosqlite(self, benchmark, tmp_path):
        db_path = str(tmp_path / "ref.db")
        _setup_db(db_path, ref_aiosqlite, populate=True)

        async def _bench():
            async with ref_aiosqlite.connect(db_path) as db:
                rows = []
                async for row in await db.execute(SELECT_ALL):
                    rows.append(row)

        benchmark(_run_async, _bench)


# ── execute_insert ──


class TestExecuteInsert:
    N = 100

    def test_zerodep(self, benchmark, tmp_path):
        db_path = str(tmp_path / "zd.db")
        _setup_db(db_path, aiosqlite)

        async def _bench():
            async with aiosqlite.connect(db_path) as db:
                await db.execute("DELETE FROM t")
                for i in range(self.N):
                    await db.execute_insert(INSERT_ONE, (f"v{i}",))
                await db.commit()

        benchmark(_run_async, _bench)

    def test_aiosqlite(self, benchmark, tmp_path):
        db_path = str(tmp_path / "ref.db")
        _setup_db(db_path, ref_aiosqlite)

        async def _bench():
            async with ref_aiosqlite.connect(db_path) as db:
                await db.execute("DELETE FROM t")
                for i in range(self.N):
                    await db.execute_insert(INSERT_ONE, (f"v{i}",))
                await db.commit()

        benchmark(_run_async, _bench)
