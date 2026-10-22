"""Benchmark: zerodep s3 vs boto3 vs minio.

Requires a SeaweedFS Docker container (started automatically via conftest.py),
or an externally provided server via the ``S3_TEST_ENDPOINT`` /
``S3_TEST_ACCESS_KEY`` / ``S3_TEST_SECRET_KEY`` environment variables.
Skipped when neither is available, or when reference libraries are missing.
"""

from __future__ import annotations

import importlib
import io
import itertools
import os
import sys
import uuid

import pytest

# Every case here takes the ``benchmark`` fixture. Without the plugin
# they would be reported as errors rather than skipped, which reads as a
# broken tree for anyone who installed the module without the extras.
pytest.importorskip("pytest_benchmark")

sys.path.insert(0, os.path.dirname(__file__))

from conftest import LARGE_PAYLOAD, MEDIUM_PAYLOAD, SMALL_PAYLOAD


def _import_reference(name: str):
    """Import a reference library despite the repo's ``xml/`` directory.

    pytest's default (prepend) import mode puts each test directory on
    ``sys.path`` as it collects, and this repo ships an ``xml/`` directory
    for the zerodep ``xml`` module.  With that directory on the path,
    ``import xml`` finds ``xml/xml.py`` — a module, not a package — so
    ``import xml.etree`` fails; botocore imports ``xml.etree``, so a plain
    ``import boto3`` raises ModuleNotFoundError here and the whole
    comparison was skipped as "boto3 not installed".

    Hide those path entries and clear the stale ``xml`` cache for the
    duration of the import, then restore both — the cache-restoring form
    matches ``xml/test_xml_benchmark.py``, so the repo's own ``xml`` module
    stays importable for the rest of the session.
    """
    shadowed = [
        (index, path)
        for index, path in enumerate(sys.path)
        if os.path.isfile(os.path.join(path, "xml.py"))
    ]
    for _, path in shadowed:
        sys.path.remove(path)
    cached = {
        key: sys.modules.pop(key)
        for key in [k for k in sys.modules if k == "xml" or k.startswith("xml.")]
    }
    try:
        return importlib.import_module(name)
    finally:
        # Put the hidden entries back at their original positions rather than
        # at the end, and drop whatever the import cached under the stdlib
        # name so the previously cached modules win again.
        for index, path in shadowed:
            sys.path.insert(index, path)
        for key in [k for k in sys.modules if k == "xml" or k.startswith("xml.")]:
            del sys.modules[key]
        sys.modules.update(cached)


def _require_reference(name: str, attribute: str):
    """Import a reference library, skipping only if it is genuinely absent.

    A ``ModuleNotFoundError`` for the library itself means it is not
    installed, so the module skips.  Anything else — a broken transitive
    import inside the library — must propagate: reporting that as "not
    installed" is exactly the swallow that hid the ``xml`` shadowing bug.
    """
    try:
        module = _import_reference(name)
    except ModuleNotFoundError as exc:
        if exc.name != name:
            raise
        pytest.skip(f"{name} not installed", allow_module_level=True)
    if not hasattr(module, attribute):
        raise ImportError(f"imported {name} has no {attribute!r} — not the real {name}")
    return module


boto3 = _require_reference("boto3", "client")
minio_mod = _require_reference("minio", "Minio")


# ── Cross-validation (non-benchmarked) ──


class TestCrossValidation:
    """Verify all three clients produce identical results."""

    def test_zerodep_write_boto3_read(
        self, s3_zerodep_client, s3_boto3_client, s3_bench_bucket
    ):
        key = "xval/zd-write.bin"
        payload = b"cross-validation-zerodep-to-boto3"
        s3_zerodep_client.put_object(s3_bench_bucket, key, payload, length=len(payload))
        resp = s3_boto3_client.get_object(Bucket=s3_bench_bucket, Key=key)
        assert resp["Body"].read() == payload

    def test_zerodep_write_minio_read(
        self, s3_zerodep_client, s3_minio_client, s3_bench_bucket
    ):
        key = "xval/zd-write-minio.bin"
        payload = b"cross-validation-zerodep-to-minio"
        s3_zerodep_client.put_object(s3_bench_bucket, key, payload, length=len(payload))
        resp = s3_minio_client.get_object(s3_bench_bucket, key)
        try:
            assert resp.read() == payload
        finally:
            resp.close()
            resp.release_conn()

    def test_boto3_write_zerodep_read(
        self, s3_zerodep_client, s3_boto3_client, s3_bench_bucket
    ):
        key = "xval/boto3-write.bin"
        payload = b"cross-validation-boto3-to-zerodep"
        s3_boto3_client.put_object(Bucket=s3_bench_bucket, Key=key, Body=payload)
        with s3_zerodep_client.get_object(s3_bench_bucket, key) as resp:
            assert resp.read() == payload

    def test_minio_write_zerodep_read(
        self, s3_zerodep_client, s3_minio_client, s3_bench_bucket
    ):
        key = "xval/minio-write.bin"
        payload = b"cross-validation-minio-to-zerodep"
        s3_minio_client.put_object(
            s3_bench_bucket, key, io.BytesIO(payload), len(payload)
        )
        with s3_zerodep_client.get_object(s3_bench_bucket, key) as resp:
            assert resp.read() == payload


# ── PUT benchmarks ──


class TestPutObjectSmall:
    _counter = itertools.count()

    def test_zerodep(self, benchmark, s3_zerodep_client, s3_bench_bucket):
        def _put():
            s3_zerodep_client.put_object(
                s3_bench_bucket,
                f"put/zd-small-{next(self._counter)}.bin",
                SMALL_PAYLOAD,
                length=len(SMALL_PAYLOAD),
            )

        benchmark(_put)

    def test_boto3(self, benchmark, s3_boto3_client, s3_bench_bucket):
        def _put():
            s3_boto3_client.put_object(
                Bucket=s3_bench_bucket,
                Key=f"put/boto3-small-{next(self._counter)}.bin",
                Body=SMALL_PAYLOAD,
            )

        benchmark(_put)

    def test_minio(self, benchmark, s3_minio_client, s3_bench_bucket):
        def _put():
            s3_minio_client.put_object(
                s3_bench_bucket,
                f"put/minio-small-{next(self._counter)}.bin",
                io.BytesIO(SMALL_PAYLOAD),
                len(SMALL_PAYLOAD),
            )

        benchmark(_put)


class TestPutObjectMedium:
    _counter = itertools.count()

    def test_zerodep(self, benchmark, s3_zerodep_client, s3_bench_bucket):
        def _put():
            s3_zerodep_client.put_object(
                s3_bench_bucket,
                f"put/zd-medium-{next(self._counter)}.bin",
                MEDIUM_PAYLOAD,
                length=len(MEDIUM_PAYLOAD),
            )

        benchmark(_put)

    def test_boto3(self, benchmark, s3_boto3_client, s3_bench_bucket):
        def _put():
            s3_boto3_client.put_object(
                Bucket=s3_bench_bucket,
                Key=f"put/boto3-medium-{next(self._counter)}.bin",
                Body=MEDIUM_PAYLOAD,
            )

        benchmark(_put)

    def test_minio(self, benchmark, s3_minio_client, s3_bench_bucket):
        def _put():
            s3_minio_client.put_object(
                s3_bench_bucket,
                f"put/minio-medium-{next(self._counter)}.bin",
                io.BytesIO(MEDIUM_PAYLOAD),
                len(MEDIUM_PAYLOAD),
            )

        benchmark(_put)


class TestPutObjectLarge:
    _counter = itertools.count()

    def test_zerodep(self, benchmark, s3_zerodep_client, s3_bench_bucket):
        def _put():
            s3_zerodep_client.put_object(
                s3_bench_bucket,
                f"put/zd-large-{next(self._counter)}.bin",
                LARGE_PAYLOAD,
                length=len(LARGE_PAYLOAD),
            )

        benchmark(_put)

    def test_boto3(self, benchmark, s3_boto3_client, s3_bench_bucket):
        def _put():
            s3_boto3_client.put_object(
                Bucket=s3_bench_bucket,
                Key=f"put/boto3-large-{next(self._counter)}.bin",
                Body=LARGE_PAYLOAD,
            )

        benchmark(_put)

    def test_minio(self, benchmark, s3_minio_client, s3_bench_bucket):
        def _put():
            s3_minio_client.put_object(
                s3_bench_bucket,
                f"put/minio-large-{next(self._counter)}.bin",
                io.BytesIO(LARGE_PAYLOAD),
                len(LARGE_PAYLOAD),
            )

        benchmark(_put)


# ── GET benchmarks ──


class TestGetObjectSmall:
    def test_zerodep(
        self, benchmark, s3_zerodep_client, s3_bench_bucket, s3_preloaded_objects
    ):
        key = s3_preloaded_objects["small"]

        def _get():
            with s3_zerodep_client.get_object(s3_bench_bucket, key) as resp:
                resp.read()

        benchmark(_get)

    def test_boto3(
        self, benchmark, s3_boto3_client, s3_bench_bucket, s3_preloaded_objects
    ):
        key = s3_preloaded_objects["small"]

        def _get():
            resp = s3_boto3_client.get_object(Bucket=s3_bench_bucket, Key=key)
            resp["Body"].read()

        benchmark(_get)

    def test_minio(
        self, benchmark, s3_minio_client, s3_bench_bucket, s3_preloaded_objects
    ):
        key = s3_preloaded_objects["small"]

        def _get():
            resp = s3_minio_client.get_object(s3_bench_bucket, key)
            resp.read()
            resp.close()
            resp.release_conn()

        benchmark(_get)


class TestGetObjectMedium:
    def test_zerodep(
        self, benchmark, s3_zerodep_client, s3_bench_bucket, s3_preloaded_objects
    ):
        key = s3_preloaded_objects["medium"]

        def _get():
            with s3_zerodep_client.get_object(s3_bench_bucket, key) as resp:
                resp.read()

        benchmark(_get)

    def test_boto3(
        self, benchmark, s3_boto3_client, s3_bench_bucket, s3_preloaded_objects
    ):
        key = s3_preloaded_objects["medium"]

        def _get():
            resp = s3_boto3_client.get_object(Bucket=s3_bench_bucket, Key=key)
            resp["Body"].read()

        benchmark(_get)

    def test_minio(
        self, benchmark, s3_minio_client, s3_bench_bucket, s3_preloaded_objects
    ):
        key = s3_preloaded_objects["medium"]

        def _get():
            resp = s3_minio_client.get_object(s3_bench_bucket, key)
            resp.read()
            resp.close()
            resp.release_conn()

        benchmark(_get)


class TestGetObjectLarge:
    def test_zerodep(
        self, benchmark, s3_zerodep_client, s3_bench_bucket, s3_preloaded_objects
    ):
        key = s3_preloaded_objects["large"]

        def _get():
            with s3_zerodep_client.get_object(s3_bench_bucket, key) as resp:
                resp.read()

        benchmark(_get)

    def test_boto3(
        self, benchmark, s3_boto3_client, s3_bench_bucket, s3_preloaded_objects
    ):
        key = s3_preloaded_objects["large"]

        def _get():
            resp = s3_boto3_client.get_object(Bucket=s3_bench_bucket, Key=key)
            resp["Body"].read()

        benchmark(_get)

    def test_minio(
        self, benchmark, s3_minio_client, s3_bench_bucket, s3_preloaded_objects
    ):
        key = s3_preloaded_objects["large"]

        def _get():
            resp = s3_minio_client.get_object(s3_bench_bucket, key)
            resp.read()
            resp.close()
            resp.release_conn()

        benchmark(_get)


# ── bucket_exists benchmark ──


class TestBucketExists:
    def test_zerodep(self, benchmark, s3_zerodep_client, s3_bench_bucket):
        benchmark(s3_zerodep_client.bucket_exists, s3_bench_bucket)

    def test_boto3(self, benchmark, s3_boto3_client, s3_bench_bucket):
        benchmark(s3_boto3_client.head_bucket, Bucket=s3_bench_bucket)

    def test_minio(self, benchmark, s3_minio_client, s3_bench_bucket):
        benchmark(s3_minio_client.bucket_exists, s3_bench_bucket)


# ── make_bucket benchmark ──

# Bucket names must be unique per process: the counters restart at 0 in
# every run, so against a server a previous run already touched the
# "*-mk-0" names still exist and make_bucket fails with
# BucketAlreadyOwnedByYou (dropping three benchmarks from the artifact).
_run_id = uuid.uuid4().hex[:8]
_zd_bucket_counter = itertools.count()
_boto3_bucket_counter = itertools.count()
_minio_bucket_counter = itertools.count()


class TestMakeBucket:
    def test_zerodep(self, benchmark, s3_zerodep_client):
        def _make():
            s3_zerodep_client.make_bucket(f"zd-mk-{_run_id}-{next(_zd_bucket_counter)}")

        benchmark(_make)

    def test_boto3(self, benchmark, s3_boto3_client):
        def _make():
            s3_boto3_client.create_bucket(
                Bucket=f"boto3-mk-{_run_id}-{next(_boto3_bucket_counter)}"
            )

        benchmark(_make)

    def test_minio(self, benchmark, s3_minio_client):
        def _make():
            s3_minio_client.make_bucket(
                f"minio-mk-{_run_id}-{next(_minio_bucket_counter)}"
            )

        benchmark(_make)


# ── Phase 2: stat_object benchmark ──


class TestStatObject:
    def test_zerodep(
        self, benchmark, s3_zerodep_client, s3_bench_bucket, s3_preloaded_objects
    ):
        key = s3_preloaded_objects["small"]
        benchmark(s3_zerodep_client.stat_object, s3_bench_bucket, key)

    def test_boto3(
        self, benchmark, s3_boto3_client, s3_bench_bucket, s3_preloaded_objects
    ):
        key = s3_preloaded_objects["small"]
        benchmark(s3_boto3_client.head_object, Bucket=s3_bench_bucket, Key=key)

    def test_minio(
        self, benchmark, s3_minio_client, s3_bench_bucket, s3_preloaded_objects
    ):
        key = s3_preloaded_objects["small"]
        benchmark(s3_minio_client.stat_object, s3_bench_bucket, key)


# ── Phase 2: list_objects benchmark ──


class TestListObjectsSmall:
    """List 10 objects — no pagination."""

    def test_zerodep(
        self, benchmark, s3_zerodep_client, s3_bench_bucket, s3_populated_bucket
    ):
        prefix = s3_populated_bucket["small"]["prefix"]
        benchmark(
            s3_zerodep_client.list_objects,
            s3_bench_bucket,
            prefix=prefix,
            recursive=True,
        )

    def test_boto3(
        self, benchmark, s3_boto3_client, s3_bench_bucket, s3_populated_bucket
    ):
        prefix = s3_populated_bucket["small"]["prefix"]

        def _list():
            s3_boto3_client.list_objects_v2(Bucket=s3_bench_bucket, Prefix=prefix)

        benchmark(_list)

    def test_minio(
        self, benchmark, s3_minio_client, s3_bench_bucket, s3_populated_bucket
    ):
        prefix = s3_populated_bucket["small"]["prefix"]

        def _list():
            list(
                s3_minio_client.list_objects(
                    s3_bench_bucket, prefix=prefix, recursive=True
                )
            )

        benchmark(_list)


class TestListObjectsMedium:
    """List 100 objects — single page but heavier XML parsing."""

    def test_zerodep(
        self, benchmark, s3_zerodep_client, s3_bench_bucket, s3_populated_bucket
    ):
        prefix = s3_populated_bucket["medium"]["prefix"]
        benchmark(
            s3_zerodep_client.list_objects,
            s3_bench_bucket,
            prefix=prefix,
            recursive=True,
        )

    def test_boto3(
        self, benchmark, s3_boto3_client, s3_bench_bucket, s3_populated_bucket
    ):
        prefix = s3_populated_bucket["medium"]["prefix"]

        def _list():
            s3_boto3_client.list_objects_v2(Bucket=s3_bench_bucket, Prefix=prefix)

        benchmark(_list)

    def test_minio(
        self, benchmark, s3_minio_client, s3_bench_bucket, s3_populated_bucket
    ):
        prefix = s3_populated_bucket["medium"]["prefix"]

        def _list():
            list(
                s3_minio_client.list_objects(
                    s3_bench_bucket, prefix=prefix, recursive=True
                )
            )

        benchmark(_list)


class TestListObjectsLarge:
    """List 1500 objects — forces pagination (2 pages at 1000/page)."""

    def test_zerodep(
        self, benchmark, s3_zerodep_client, s3_bench_bucket, s3_populated_bucket
    ):
        prefix = s3_populated_bucket["large"]["prefix"]
        benchmark(
            s3_zerodep_client.list_objects,
            s3_bench_bucket,
            prefix=prefix,
            recursive=True,
        )

    def test_boto3(
        self, benchmark, s3_boto3_client, s3_bench_bucket, s3_populated_bucket
    ):
        prefix = s3_populated_bucket["large"]["prefix"]

        def _list():
            # boto3 paginator handles continuation automatically
            paginator = s3_boto3_client.get_paginator("list_objects_v2")
            objs = []
            for page in paginator.paginate(Bucket=s3_bench_bucket, Prefix=prefix):
                objs.extend(page.get("Contents", []))

        benchmark(_list)

    def test_minio(
        self, benchmark, s3_minio_client, s3_bench_bucket, s3_populated_bucket
    ):
        prefix = s3_populated_bucket["large"]["prefix"]

        def _list():
            list(
                s3_minio_client.list_objects(
                    s3_bench_bucket, prefix=prefix, recursive=True
                )
            )

        benchmark(_list)


# ── Phase 2: copy_object benchmark ──

_copy_counter = itertools.count()


class TestCopyObject:
    def test_zerodep(
        self, benchmark, s3_zerodep_client, s3_bench_bucket, s3_preloaded_objects
    ):
        src = s3_preloaded_objects["small"]

        def _copy():
            dst = f"copy/zd-{next(_copy_counter)}.bin"
            s3_zerodep_client.copy_object(s3_bench_bucket, src, s3_bench_bucket, dst)

        benchmark(_copy)

    def test_boto3(
        self, benchmark, s3_boto3_client, s3_bench_bucket, s3_preloaded_objects
    ):
        src = s3_preloaded_objects["small"]

        def _copy():
            dst = f"copy/boto3-{next(_copy_counter)}.bin"
            s3_boto3_client.copy_object(
                Bucket=s3_bench_bucket,
                Key=dst,
                CopySource={"Bucket": s3_bench_bucket, "Key": src},
            )

        benchmark(_copy)

    def test_minio(
        self, benchmark, s3_minio_client, s3_bench_bucket, s3_preloaded_objects
    ):
        from minio.commonconfig import CopySource

        src_key = s3_preloaded_objects["small"]

        def _copy():
            dst = f"copy/minio-{next(_copy_counter)}.bin"
            s3_minio_client.copy_object(
                s3_bench_bucket,
                dst,
                CopySource(s3_bench_bucket, src_key),
            )

        benchmark(_copy)


# ── Phase 2: remove_object benchmark ──

_rm_counter = itertools.count()


class TestRemoveObject:
    def test_zerodep(self, benchmark, s3_zerodep_client, s3_bench_bucket):
        def _remove():
            key = f"rm/zd-{next(_rm_counter)}.bin"
            s3_zerodep_client.put_object(
                s3_bench_bucket, key, SMALL_PAYLOAD, length=len(SMALL_PAYLOAD)
            )
            s3_zerodep_client.remove_object(s3_bench_bucket, key)

        benchmark(_remove)

    def test_boto3(self, benchmark, s3_boto3_client, s3_bench_bucket):
        def _remove():
            key = f"rm/boto3-{next(_rm_counter)}.bin"
            s3_boto3_client.put_object(
                Bucket=s3_bench_bucket, Key=key, Body=SMALL_PAYLOAD
            )
            s3_boto3_client.delete_object(Bucket=s3_bench_bucket, Key=key)

        benchmark(_remove)

    def test_minio(self, benchmark, s3_minio_client, s3_bench_bucket):
        def _remove():
            key = f"rm/minio-{next(_rm_counter)}.bin"
            s3_minio_client.put_object(
                s3_bench_bucket,
                key,
                io.BytesIO(SMALL_PAYLOAD),
                len(SMALL_PAYLOAD),
            )
            s3_minio_client.remove_object(s3_bench_bucket, key)

        benchmark(_remove)
