"""Fixtures for s3 module tests.

Provides a session-scoped MinIO Docker container and pre-configured
S3 clients (zerodep, boto3, minio) for benchmark and integration tests.
The container is skipped automatically when Docker is unavailable.
"""

from __future__ import annotations

import atexit
import os
import random
import shutil
import subprocess
import sys
import time
from http.client import HTTPConnection

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from s3 import S3Client

# ── Constants ──

_MINIO_IMAGE = "minio/minio:latest"
_ACCESS_KEY = "minioadmin"
_SECRET_KEY = "minioadmin"
_REGION = "us-east-1"
_BENCH_BUCKET = "bench"
_STARTUP_TIMEOUT = 30  # seconds

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

# ── Docker helpers ──


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


def _wait_for_minio(host: str, port: int, timeout: float) -> bool:
    """Poll MinIO health endpoint until ready or timeout."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            conn = HTTPConnection(host, port, timeout=2)
            conn.request("GET", "/minio/health/live")
            resp = conn.getresponse()
            resp.read()
            conn.close()
            if resp.status == 200:
                return True
        except (OSError, ConnectionError):
            pass
        time.sleep(0.3)
    return False


# ── Fixtures ──


@pytest.fixture(scope="session")
def minio_endpoint():
    """Start a MinIO Docker container and yield its endpoint.

    Skips all dependent tests when Docker is unavailable.
    The container is removed on teardown (and via atexit as safety net).
    """
    if not _docker_available():
        pytest.skip("Docker not available — skipping S3 Docker tests")

    container_id = None
    try:
        # Start container with random port mapping
        result = subprocess.run(
            [
                "docker",
                "run",
                "-d",
                "--rm",
                "-p",
                "0:9000",
                "-e",
                f"MINIO_ROOT_USER={_ACCESS_KEY}",
                "-e",
                f"MINIO_ROOT_PASSWORD={_SECRET_KEY}",
                _MINIO_IMAGE,
                "server",
                "/data",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            pytest.skip(f"Failed to start MinIO container: {result.stderr.strip()}")

        container_id = result.stdout.strip()

        # Register cleanup as safety net
        def _cleanup():
            subprocess.run(
                ["docker", "rm", "-f", container_id],
                capture_output=True,
                timeout=15,
            )

        atexit.register(_cleanup)

        # Get assigned port
        port_result = subprocess.run(
            ["docker", "port", container_id, "9000"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if port_result.returncode != 0:
            pytest.skip("Failed to get MinIO container port")

        # Parse "0.0.0.0:XXXXX" or ":::XXXXX"
        port_line = port_result.stdout.strip().split("\n")[0]
        port = int(port_line.rsplit(":", 1)[1])

        # Wait for MinIO to be ready
        if not _wait_for_minio("127.0.0.1", port, _STARTUP_TIMEOUT):
            pytest.skip("MinIO container did not become ready in time")

        endpoint = f"127.0.0.1:{port}"
        yield endpoint

    finally:
        if container_id:
            subprocess.run(
                ["docker", "rm", "-f", container_id],
                capture_output=True,
                timeout=15,
            )


@pytest.fixture(scope="session")
def s3_zerodep_client(minio_endpoint):
    """Zerodep S3Client connected to the MinIO container."""
    return S3Client(
        endpoint=minio_endpoint,
        access_key=_ACCESS_KEY,
        secret_key=_SECRET_KEY,
        region=_REGION,
        secure=False,
        url_style="path",
    )


@pytest.fixture(scope="session")
def s3_boto3_client(minio_endpoint):
    """boto3 S3 client connected to the MinIO container."""
    try:
        import boto3
        from botocore.config import Config
    except ImportError:
        pytest.skip("boto3 not installed")

    return boto3.client(
        "s3",
        endpoint_url=f"http://{minio_endpoint}",
        aws_access_key_id=_ACCESS_KEY,
        aws_secret_access_key=_SECRET_KEY,
        region_name=_REGION,
        config=Config(signature_version="s3v4"),
    )


@pytest.fixture(scope="session")
def s3_minio_client(minio_endpoint):
    """minio-py client connected to the MinIO container."""
    try:
        from minio import Minio
    except ImportError:
        pytest.skip("minio not installed")

    return Minio(
        minio_endpoint,
        access_key=_ACCESS_KEY,
        secret_key=_SECRET_KEY,
        secure=False,
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
