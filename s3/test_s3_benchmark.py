"""Benchmark: zerodep s3 vs boto3 vs minio.

Requires a MinIO Docker container (started automatically via conftest.py).
Skipped when Docker is unavailable or reference libraries are not installed.
"""

from __future__ import annotations

import io
import itertools
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from conftest import LARGE_PAYLOAD, MEDIUM_PAYLOAD, SMALL_PAYLOAD

boto3 = pytest.importorskip("boto3", reason="boto3 not installed")
minio_mod = pytest.importorskip("minio", reason="minio not installed")


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

_zd_bucket_counter = itertools.count()
_boto3_bucket_counter = itertools.count()
_minio_bucket_counter = itertools.count()


class TestMakeBucket:
    def test_zerodep(self, benchmark, s3_zerodep_client):
        def _make():
            s3_zerodep_client.make_bucket(f"zd-mk-{next(_zd_bucket_counter)}")

        benchmark(_make)

    def test_boto3(self, benchmark, s3_boto3_client):
        def _make():
            s3_boto3_client.create_bucket(
                Bucket=f"boto3-mk-{next(_boto3_bucket_counter)}"
            )

        benchmark(_make)

    def test_minio(self, benchmark, s3_minio_client):
        def _make():
            s3_minio_client.make_bucket(f"minio-mk-{next(_minio_bucket_counter)}")

        benchmark(_make)
