"""Fixtures for s3 module tests.

Provides a session-scoped SeaweedFS Docker container and pre-configured
S3 clients (zerodep, boto3, minio) for benchmark and integration tests.

The container is skipped automatically when Docker is unavailable.  Set
``S3_TEST_ENDPOINT`` (plus ``S3_TEST_ACCESS_KEY`` / ``S3_TEST_SECRET_KEY``)
to use an externally managed S3 server instead — this is how CI provides
the endpoint.
"""

from __future__ import annotations

import atexit
import os
import random
import shutil
import subprocess
import sys
import time

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from s3 import S3Client

# ── Constants ──

_SEAWEEDFS_IMAGE = "chrislusf/seaweedfs:latest"
_S3_PORT = 8333
_ACCESS_KEY = "admin"
_SECRET_KEY = "secret"
_REGION = "us-east-1"
_BENCH_BUCKET = "bench"
_STARTUP_TIMEOUT = 60  # seconds — `weed mini` boots master+volume+filer+s3

# Deterministic test payloads
_RNG = random.Random(42)  # noqa: S311
SMALL_PAYLOAD = _RNG.randbytes(1_024)  # 1 KB
MEDIUM_PAYLOAD = _RNG.randbytes(100_000)  # 100 KB
LARGE_PAYLOAD = _RNG.randbytes(1_000_000)  # 1 MB

PAYLOADS = {
    "small": SMALL_PAYLOAD,
    "medium": MEDIUM_PAYLOAD,
    "large": LARGE_PAYLOAD,
}


# ── Server helpers ──


def _docker_available() -> bool:
    """Check if Docker CLI is available and the daemon is running."""
    if not shutil.which("docker"):
        return False
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            timeout=10,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, OSError):
        return False


def _wait_for_s3(
    endpoint: str,
    access_key: str,
    secret_key: str,
    timeout: float,
    secure: bool = False,
) -> bool:
    """Poll ListBuckets until the S3 gateway answers with valid creds.

    SeaweedFS has no dedicated health route, so a successful authenticated
    call is the readiness signal: a 200 proves the gateway is listening, the
    credentials are loaded, and SigV4 verification works.
    """
    client = S3Client(
        endpoint=endpoint,
        access_key=access_key,
        secret_key=secret_key,
        region=_REGION,
        secure=secure,
        url_style="path",
    )
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            client.list_buckets()
            return True
        except Exception:  # noqa: BLE001 — refused/403/500 all mean "not ready"
            time.sleep(0.5)
    return False


def _external_target() -> tuple[str, str, str] | None:
    """Read an externally provided S3 endpoint from the environment.

    Returns ``(endpoint, access_key, secret_key)`` or ``None`` when
    ``S3_TEST_ENDPOINT`` is unset.
    """
    endpoint = os.environ.get("S3_TEST_ENDPOINT")
    if not endpoint:
        return None
    access_key = os.environ.get("S3_TEST_ACCESS_KEY")
    secret_key = os.environ.get("S3_TEST_SECRET_KEY")
    if not (access_key and secret_key):
        pytest.skip(
            "S3_TEST_ENDPOINT is set but S3_TEST_ACCESS_KEY / "
            "S3_TEST_SECRET_KEY are missing"
        )
    return endpoint, access_key, secret_key


def _secure() -> bool:
    """Whether to use HTTPS — benchmark default is plain HTTP."""
    return os.environ.get("S3_TEST_SECURE", "0") != "0"


# ── Fixtures ──


@pytest.fixture(scope="session")
def s3_endpoint():
    """Yield the S3 endpoint to test against.

    Uses ``S3_TEST_ENDPOINT`` when set (external server, e.g. CI).  Otherwise
    starts a SeaweedFS Docker container, skipping all dependent tests when
    Docker is unavailable.  The container is removed on teardown (and via
    atexit as a safety net).
    """
    external = _external_target()
    if external is not None:
        endpoint, access_key, secret_key = external
        if not _wait_for_s3(
            endpoint, access_key, secret_key, _STARTUP_TIMEOUT, _secure()
        ):
            pytest.skip(f"External S3 endpoint {endpoint} not ready in time")
        yield endpoint
        return

    if not _docker_available():
        pytest.skip("Docker not available — set S3_TEST_ENDPOINT to use an external S3")

    container_id = None
    try:
        result = subprocess.run(
            [
                "docker",
                "run",
                "-d",
                "--rm",
                "-p",
                f"0:{_S3_PORT}",
                "-e",
                f"AWS_ACCESS_KEY_ID={_ACCESS_KEY}",
                "-e",
                f"AWS_SECRET_ACCESS_KEY={_SECRET_KEY}",
                "-e",
                f"S3_BUCKET={_BENCH_BUCKET}",
                _SEAWEEDFS_IMAGE,
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            pytest.skip(f"Failed to start SeaweedFS container: {result.stderr.strip()}")

        container_id = result.stdout.strip()

        # Register atexit as a safety net: the finally block below handles
        # normal teardown, but atexit catches the case where pytest is
        # killed hard (SIGKILL) and the finally block never runs.
        def _cleanup():
            subprocess.run(
                ["docker", "rm", "-f", container_id],
                capture_output=True,
                timeout=15,
            )

        atexit.register(_cleanup)

        # Get assigned port
        port_result = subprocess.run(
            ["docker", "port", container_id, str(_S3_PORT)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if port_result.returncode != 0:
            pytest.skip("Failed to get SeaweedFS container port")

        # Parse "0.0.0.0:XXXXX" or ":::XXXXX"
        port_line = port_result.stdout.strip().split("\n")[0]
        port = int(port_line.rsplit(":", 1)[1])

        endpoint = f"127.0.0.1:{port}"
        if not _wait_for_s3(
            endpoint, _ACCESS_KEY, _SECRET_KEY, _STARTUP_TIMEOUT, secure=False
        ):
            pytest.skip("SeaweedFS container did not become ready in time")

        yield endpoint

    finally:
        if container_id:
            subprocess.run(
                ["docker", "rm", "-f", container_id],
                capture_output=True,
                timeout=15,
            )


@pytest.fixture(scope="session")
def s3_credentials():
    """Return ``(access_key, secret_key)`` for the active endpoint."""
    external = _external_target()
    if external is not None:
        return external[1], external[2]
    return _ACCESS_KEY, _SECRET_KEY


@pytest.fixture(scope="session")
def s3_zerodep_client(s3_endpoint, s3_credentials):
    """Zerodep S3Client connected to the test server."""
    access_key, secret_key = s3_credentials
    return S3Client(
        endpoint=s3_endpoint,
        access_key=access_key,
        secret_key=secret_key,
        region=_REGION,
        secure=_secure(),
        url_style="path",
    )


@pytest.fixture(scope="session")
def s3_boto3_client(s3_endpoint, s3_credentials):
    """boto3 S3 client connected to the test server."""
    try:
        import boto3
        from botocore.config import Config
    except ImportError:
        pytest.skip("boto3 not installed")

    access_key, secret_key = s3_credentials
    return boto3.client(
        "s3",
        endpoint_url=f"{'https' if _secure() else 'http'}://{s3_endpoint}",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=_REGION,
        config=Config(
            signature_version="s3v4",
            s3={"addressing_style": "path"},
        ),
    )


@pytest.fixture(scope="session")
def s3_minio_client(s3_endpoint, s3_credentials):
    """minio-py client connected to the test server."""
    try:
        from minio import Minio
    except ImportError:
        pytest.skip("minio not installed")

    access_key, secret_key = s3_credentials
    return Minio(
        s3_endpoint,
        access_key=access_key,
        secret_key=secret_key,
        secure=_secure(),
        region=_REGION,
    )


@pytest.fixture(scope="session")
def s3_bench_bucket(s3_zerodep_client):
    """Create the shared benchmark bucket once per session."""
    if not s3_zerodep_client.bucket_exists(_BENCH_BUCKET):
        s3_zerodep_client.make_bucket(_BENCH_BUCKET)
    return _BENCH_BUCKET


@pytest.fixture(scope="session")
def s3_preloaded_objects(s3_zerodep_client, s3_bench_bucket):
    """Upload SMALL/MEDIUM/LARGE payloads for GET benchmarks.

    Returns a dict mapping size label to object key.
    """
    keys = {}
    for label, data in PAYLOADS.items():
        key = f"preloaded/{label}.bin"
        s3_zerodep_client.put_object(
            s3_bench_bucket,
            key,
            data,
            length=len(data),
            content_type="application/octet-stream",
        )
        keys[label] = key
    return keys


@pytest.fixture(scope="session")
def s3_populated_bucket(s3_zerodep_client, s3_bench_bucket):
    """Upload objects under list-test/ for list_objects benchmarks.

    Creates three tiers to test listing at different scales:

    - ``list-test/small/``  — 10 objects  (no pagination)
    - ``list-test/medium/`` — 100 objects (no pagination, but heavier XML)
    - ``list-test/large/``  — 1500 objects (forces pagination at 1000)

    Each object has a deterministic, varying size (64 B – 4 KB) seeded
    by its index so results are reproducible without storing files.

    Returns a dict with tier info: ``{tier: {"prefix": ..., "count": ...}}``.
    """
    rng = random.Random(99)  # noqa: S311
    tiers = {
        "small": 10,
        "medium": 100,
        "large": 1500,
    }
    result = {}
    for tier, count in tiers.items():
        prefix = f"list-test/{tier}/"
        for i in range(count):
            # Varying size: 64 B – 4 KB, deterministic per index
            size = 64 + rng.randint(0, 4032)
            payload = rng.randbytes(size)
            key = f"{prefix}obj-{i:04d}.bin"
            s3_zerodep_client.put_object(
                s3_bench_bucket,
                key,
                payload,
                length=len(payload),
            )
        result[tier] = {"prefix": prefix, "count": count}
    return result
