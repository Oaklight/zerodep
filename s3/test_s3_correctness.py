"""Correctness tests for the zerodep s3 module (Phase 1).

Tests are split into two tiers:

1. **Unit tests** (no network) — test SigV4 signing, URL construction,
   XML error parsing, and the ``S3Response`` wrapper using mock HTTP
   responses.  These run in CI unconditionally.

2. **Integration tests** (live S3 backend) — skipped unless the
   environment variables ``S3_TEST_ENDPOINT``, ``S3_TEST_ACCESS_KEY``,
   and ``S3_TEST_SECRET_KEY`` are set.  Point at any S3-compatible
   backend (MinIO, Cloudflare R2, AWS S3, Oracle OCI, …).

Environment variables for integration tests::

    S3_TEST_ENDPOINT    e.g. "localhost:9000" or "<acct>.r2.cloudflarestorage.com"
    S3_TEST_ACCESS_KEY  access key
    S3_TEST_SECRET_KEY  secret key
    S3_TEST_REGION      (optional, default "us-east-1")
    S3_TEST_SECURE      (optional, "0" to disable TLS; default "1")
    S3_TEST_URL_STYLE   (optional, "path" or "virtual-host"; default "path")
    S3_TEST_BUCKET      (optional, bucket name; default "zerodep-s3-test")
"""

from __future__ import annotations

import gzip
import hashlib
import io
import json
import os
import threading
import time
import unittest
import unittest.mock
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest.mock import MagicMock, patch

from s3 import (
    S3Client,
    S3Error,
    S3NoSuchBucket,
    S3NoSuchKey,
    S3Response,
    _derive_signing_key,
    _parse_s3_error,
    _sha256_hex,
    _sign_request,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_FAKE_ENDPOINT = "s3.example.com"
_FAKE_ACCESS = "AKIAIOSFODNN7EXAMPLE"
_FAKE_SECRET = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
_FAKE_REGION = "us-east-1"


def _client(**kwargs) -> S3Client:
    defaults = dict(
        endpoint=_FAKE_ENDPOINT,
        access_key=_FAKE_ACCESS,
        secret_key=_FAKE_SECRET,
        region=_FAKE_REGION,
        secure=False,
    )
    defaults.update(kwargs)
    return S3Client(**defaults)


def _mock_response(status: int, body: bytes = b"") -> MagicMock:
    """Build a mock http.client.HTTPResponse."""
    resp = MagicMock()
    resp.status = status
    resp.read.return_value = body
    resp.headers = {}
    return resp


def _s3_error_xml(code: str, message: str) -> bytes:
    return (
        f"<?xml version='1.0'?>"
        f"<Error><Code>{code}</Code><Message>{message}</Message></Error>"
    ).encode()


# ---------------------------------------------------------------------------
# Unit tests: SigV4 helpers
# ---------------------------------------------------------------------------


class TestSigV4Helpers(unittest.TestCase):
    def test_sha256_hex_known_value(self):
        # SHA-256("") = e3b0...
        result = _sha256_hex(b"")
        self.assertEqual(
            result, "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        )

    def test_sha256_hex_hello(self):
        result = _sha256_hex(b"hello")
        self.assertEqual(result, hashlib.sha256(b"hello").hexdigest())

    def test_derive_signing_key_deterministic(self):
        k1 = _derive_signing_key(_FAKE_SECRET, "20240101", "us-east-1", "s3")
        k2 = _derive_signing_key(_FAKE_SECRET, "20240101", "us-east-1", "s3")
        self.assertEqual(k1, k2)

    def test_derive_signing_key_differs_by_date(self):
        k1 = _derive_signing_key(_FAKE_SECRET, "20240101", "us-east-1", "s3")
        k2 = _derive_signing_key(_FAKE_SECRET, "20240102", "us-east-1", "s3")
        self.assertNotEqual(k1, k2)

    def test_derive_signing_key_differs_by_region(self):
        k1 = _derive_signing_key(_FAKE_SECRET, "20240101", "us-east-1", "s3")
        k2 = _derive_signing_key(_FAKE_SECRET, "20240101", "eu-west-1", "s3")
        self.assertNotEqual(k1, k2)


class TestSignRequest(unittest.TestCase):
    def test_returns_required_headers(self):
        headers = _sign_request(
            method="GET",
            url=f"https://{_FAKE_ENDPOINT}/my-bucket/my-key",
            headers={},
            payload=b"",
            access_key=_FAKE_ACCESS,
            secret_key=_FAKE_SECRET,
            region=_FAKE_REGION,
        )
        self.assertIn("Authorization", headers)
        self.assertIn("x-amz-date", headers)
        self.assertIn("x-amz-content-sha256", headers)

    def test_authorization_starts_with_aws4_hmac(self):
        headers = _sign_request(
            method="PUT",
            url=f"https://{_FAKE_ENDPOINT}/bucket/key",
            headers={"Content-Type": "application/json", "Content-Length": "4"},
            payload=b"body",
            access_key=_FAKE_ACCESS,
            secret_key=_FAKE_SECRET,
            region=_FAKE_REGION,
        )
        self.assertTrue(headers["Authorization"].startswith("AWS4-HMAC-SHA256 "))

    def test_authorization_contains_credential(self):
        headers = _sign_request(
            method="GET",
            url=f"https://{_FAKE_ENDPOINT}/b/k",
            headers={},
            payload=b"",
            access_key=_FAKE_ACCESS,
            secret_key=_FAKE_SECRET,
            region=_FAKE_REGION,
        )
        self.assertIn(f"Credential={_FAKE_ACCESS}/", headers["Authorization"])

    def test_content_sha256_matches_payload(self):
        payload = b"test body data"
        headers = _sign_request(
            method="PUT",
            url=f"https://{_FAKE_ENDPOINT}/b/k",
            headers={},
            payload=payload,
            access_key=_FAKE_ACCESS,
            secret_key=_FAKE_SECRET,
            region=_FAKE_REGION,
        )
        self.assertEqual(
            headers["x-amz-content-sha256"], hashlib.sha256(payload).hexdigest()
        )

    def test_host_included_in_signed_headers(self):
        headers = _sign_request(
            method="GET",
            url=f"https://{_FAKE_ENDPOINT}/b/k",
            headers={},
            payload=b"",
            access_key=_FAKE_ACCESS,
            secret_key=_FAKE_SECRET,
            region=_FAKE_REGION,
        )
        self.assertIn("host", headers["Authorization"])


# ---------------------------------------------------------------------------
# Unit tests: XML error parsing
# ---------------------------------------------------------------------------


class TestParseS3Error(unittest.TestCase):
    def test_no_such_bucket(self):
        xml = _s3_error_xml("NoSuchBucket", "The bucket does not exist")
        err = _parse_s3_error(xml, 404)
        self.assertIsInstance(err, S3NoSuchBucket)
        self.assertEqual(err.code, "NoSuchBucket")
        self.assertEqual(err.status, 404)

    def test_no_such_key(self):
        xml = _s3_error_xml("NoSuchKey", "The key does not exist")
        err = _parse_s3_error(xml, 404)
        self.assertIsInstance(err, S3NoSuchKey)

    def test_generic_error(self):
        xml = _s3_error_xml("AccessDenied", "Access Denied")
        err = _parse_s3_error(xml, 403)
        self.assertIsInstance(err, S3Error)
        self.assertNotIsInstance(err, (S3NoSuchBucket, S3NoSuchKey))
        self.assertEqual(err.code, "AccessDenied")

    def test_malformed_xml_falls_back_gracefully(self):
        err = _parse_s3_error(b"not xml", 500)
        self.assertIsInstance(err, S3Error)
        self.assertEqual(err.status, 500)


# ---------------------------------------------------------------------------
# Unit tests: S3Response wrapper
# ---------------------------------------------------------------------------


class TestS3Response(unittest.TestCase):
    def test_read_delegates_to_underlying(self):
        mock_resp = _mock_response(200, b"hello world")
        s3r = S3Response(mock_resp)
        self.assertEqual(s3r.read(), b"hello world")

    def test_close_delegates(self):
        mock_resp = _mock_response(200)
        s3r = S3Response(mock_resp)
        s3r.close()
        mock_resp.close.assert_called_once()

    def test_release_conn_delegates_to_close(self):
        mock_resp = _mock_response(200)
        s3r = S3Response(mock_resp)
        s3r.release_conn()
        mock_resp.close.assert_called_once()

    def test_status_property(self):
        mock_resp = _mock_response(200)
        s3r = S3Response(mock_resp)
        self.assertEqual(s3r.status, 200)

    def test_context_manager_closes_on_exit(self):
        mock_resp = _mock_response(200, b"data")
        with S3Response(mock_resp) as s3r:
            data = s3r.read()
        self.assertEqual(data, b"data")
        mock_resp.close.assert_called_once()

    def test_iter_chunks(self):
        chunks = [b"abc", b"def", b""]
        mock_resp = _mock_response(200)
        mock_resp.read.side_effect = chunks
        s3r = S3Response(mock_resp)
        result = b"".join(s3r.iter_chunks(3))
        self.assertEqual(result, b"abcdef")


# ---------------------------------------------------------------------------
# Unit tests: S3Client URL construction
# ---------------------------------------------------------------------------


class TestS3ClientURLs(unittest.TestCase):
    def test_path_style_bucket_url(self):
        c = _client(url_style="path", secure=False)
        url = c._bucket_url("mybucket")
        self.assertEqual(url, "http://s3.example.com/mybucket/")

    def test_virtual_host_bucket_url(self):
        c = _client(url_style="virtual-host", secure=False)
        url = c._bucket_url("mybucket")
        self.assertEqual(url, "http://mybucket.s3.example.com/")

    def test_path_style_object_url(self):
        c = _client(url_style="path", secure=False)
        url = c._object_url("mybucket", "path/to/key")
        self.assertEqual(url, "http://s3.example.com/mybucket/path/to/key")

    def test_virtual_host_object_url(self):
        c = _client(url_style="virtual-host", secure=False)
        url = c._object_url("mybucket", "path/to/key")
        self.assertEqual(url, "http://mybucket.s3.example.com/path/to/key")

    def test_key_with_special_chars_encoded(self):
        c = _client(url_style="path", secure=False)
        url = c._object_url("b", "render/a b+c.json.gz")
        # space should be encoded, + should be encoded, / should be preserved
        self.assertIn("render/", url)
        self.assertNotIn(" ", url)

    def test_endpoint_scheme_stripped(self):
        c = S3Client(
            endpoint="https://s3.amazonaws.com",
            access_key=_FAKE_ACCESS,
            secret_key=_FAKE_SECRET,
        )
        self.assertEqual(c._endpoint, "s3.amazonaws.com")

    def test_invalid_url_style_raises(self):
        with self.assertRaises(ValueError):
            S3Client(
                endpoint=_FAKE_ENDPOINT,
                access_key=_FAKE_ACCESS,
                secret_key=_FAKE_SECRET,
                url_style="ftp",
            )


# ---------------------------------------------------------------------------
# Unit tests: S3Client operations (mocked HTTP)
# ---------------------------------------------------------------------------


class TestS3ClientMocked(unittest.TestCase):
    """Test S3Client operations with a mocked _request method."""

    def setUp(self):
        self.client = _client()

    def _mock_op(self, method_name: str, mock_resp: MagicMock):
        return patch.object(self.client, "_request", return_value=mock_resp)

    # --- bucket_exists ---

    def test_bucket_exists_200(self):
        with self._mock_op("_request", _mock_response(200)):
            self.assertTrue(self.client.bucket_exists("b"))

    def test_bucket_exists_403(self):
        with self._mock_op("_request", _mock_response(403)):
            self.assertTrue(self.client.bucket_exists("b"))

    def test_bucket_exists_404(self):
        with self._mock_op(
            "_request", _mock_response(404, _s3_error_xml("NoSuchBucket", "nope"))
        ):
            self.assertFalse(self.client.bucket_exists("b"))

    def test_bucket_exists_500_raises(self):
        with self._mock_op(
            "_request", _mock_response(500, _s3_error_xml("InternalError", "oops"))
        ):
            with self.assertRaises(S3Error):
                self.client.bucket_exists("b")

    # --- make_bucket ---

    def test_make_bucket_success(self):
        with self._mock_op("_request", _mock_response(200)):
            self.client.make_bucket("newbucket")  # should not raise

    def test_make_bucket_error_raises(self):
        with self._mock_op(
            "_request",
            _mock_response(409, _s3_error_xml("BucketAlreadyOwnedByYou", "owned")),
        ):
            with self.assertRaises(S3Error):
                self.client.make_bucket("dup")

    # --- get_object ---

    def test_get_object_200(self):
        with self._mock_op("_request", _mock_response(200, b"content")):
            resp = self.client.get_object("b", "k")
            self.assertEqual(resp.read(), b"content")

    def test_get_object_404_no_such_key(self):
        with self._mock_op(
            "_request", _mock_response(404, _s3_error_xml("NoSuchKey", "missing"))
        ):
            with self.assertRaises(S3NoSuchKey):
                self.client.get_object("b", "k")

    def test_get_object_404_no_such_bucket(self):
        with self._mock_op(
            "_request", _mock_response(404, _s3_error_xml("NoSuchBucket", "gone"))
        ):
            with self.assertRaises(S3NoSuchBucket):
                self.client.get_object("b", "k")

    # --- put_object ---

    def test_put_object_bytes(self):
        with self._mock_op("_request", _mock_response(200)):
            self.client.put_object("b", "k", b"data", length=4)

    def test_put_object_file_like(self):
        buf = io.BytesIO(b"file data")
        with self._mock_op("_request", _mock_response(200)):
            self.client.put_object("b", "k", buf, length=9)

    def test_put_object_with_metadata(self):
        captured_headers: dict = {}

        def fake_request(method, url, headers=None, body=None):
            captured_headers.update(headers or {})
            return _mock_response(200)

        with patch.object(self.client, "_request", side_effect=fake_request):
            self.client.put_object(
                "b", "k", b"x", length=1, metadata={"stored-at": "1720000000"}
            )

        # Should appear with x-amz-meta- prefix (case-normalised)
        self.assertIn(
            "x-amz-meta-stored-at", {k.lower(): v for k, v in captured_headers.items()}
        )

    def test_put_object_metadata_prefix_not_doubled(self):
        """If caller already uses x-amz-meta- prefix, don't double it."""
        captured_headers: dict = {}

        def fake_request(method, url, headers=None, body=None):
            captured_headers.update(headers or {})
            return _mock_response(200)

        with patch.object(self.client, "_request", side_effect=fake_request):
            self.client.put_object(
                "b", "k", b"x", length=1, metadata={"x-amz-meta-mykey": "val"}
            )

        norm = {k.lower(): v for k, v in captured_headers.items()}
        self.assertIn("x-amz-meta-mykey", norm)
        self.assertNotIn("x-amz-meta-x-amz-meta-mykey", norm)

    def test_put_object_error_raises(self):
        with self._mock_op(
            "_request", _mock_response(403, _s3_error_xml("AccessDenied", "no"))
        ):
            with self.assertRaises(S3Error):
                self.client.put_object("b", "k", b"x", length=1)


# ---------------------------------------------------------------------------
# Unit tests: round-trip with local HTTP mock server
# ---------------------------------------------------------------------------


class _SimpleMockS3Handler(BaseHTTPRequestHandler):
    """Minimal in-process HTTP server that pretends to be S3."""

    _objects: dict[str, bytes] = {}
    _buckets: set[str] = set()

    def log_message(self, *args):  # silence request logs
        pass

    def do_HEAD(self):
        parsed = urllib.parse.urlparse(self.path)
        parts = parsed.path.strip("/").split("/", 1)
        bucket = parts[0] if parts else ""
        if bucket in self._buckets:
            self.send_response(200)
            self.end_headers()
        else:
            body = _s3_error_xml("NoSuchBucket", bucket)
            self.send_response(404)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    def do_PUT(self):
        parsed = urllib.parse.urlparse(self.path)
        parts = parsed.path.strip("/").split("/", 1)
        if len(parts) == 1:
            # create bucket
            bucket = parts[0]
            self._buckets.add(bucket)
            self.send_response(200)
            self.end_headers()
        else:
            bucket, key = parts[0], parts[1]
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            self._objects[f"{bucket}/{key}"] = body
            self.send_response(200)
            self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        parts = parsed.path.strip("/").split("/", 1)
        if len(parts) < 2:
            self.send_response(400)
            self.end_headers()
            return
        bucket, key = parts[0], parts[1]
        obj_key = f"{bucket}/{key}"
        if obj_key in self._objects:
            data = self._objects[obj_key]
            self.send_response(200)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        else:
            body = _s3_error_xml("NoSuchKey", key)
            self.send_response(404)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)


class TestLocalMockServer(unittest.TestCase):
    """Round-trip tests using a real (local) HTTP server."""

    @classmethod
    def setUpClass(cls):
        _SimpleMockS3Handler._objects = {}
        _SimpleMockS3Handler._buckets = set()
        cls.server = HTTPServer(("127.0.0.1", 0), _SimpleMockS3Handler)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.client = S3Client(
            endpoint=f"127.0.0.1:{cls.port}",
            access_key=_FAKE_ACCESS,
            secret_key=_FAKE_SECRET,
            region=_FAKE_REGION,
            secure=False,
            url_style="path",
        )

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def test_bucket_not_exists(self):
        self.assertFalse(self.client.bucket_exists("no-such-bucket"))

    def test_make_bucket_then_exists(self):
        self.client.make_bucket("testbucket")
        self.assertTrue(self.client.bucket_exists("testbucket"))

    def test_put_and_get_object(self):
        self.client.make_bucket("rw-bucket")
        payload = gzip.compress(json.dumps({"k": "v"}).encode())
        self.client.put_object(
            "rw-bucket",
            "render/abc.json.gz",
            payload,
            length=len(payload),
            content_type="application/json",
        )
        with self.client.get_object("rw-bucket", "render/abc.json.gz") as resp:
            data = resp.read()
        self.assertEqual(json.loads(gzip.decompress(data)), {"k": "v"})

    def test_get_missing_key_raises(self):
        self.client.make_bucket("exist-bucket")
        with self.assertRaises(S3NoSuchKey):
            self.client.get_object("exist-bucket", "ghost/key")

    def test_put_file_like_object(self):
        self.client.make_bucket("filelike-bucket")
        payload = b"binary file content"
        buf = io.BytesIO(payload)
        self.client.put_object("filelike-bucket", "file.bin", buf, length=len(payload))
        with self.client.get_object("filelike-bucket", "file.bin") as resp:
            self.assertEqual(resp.read(), payload)


# ---------------------------------------------------------------------------
# Integration tests (skipped without env vars)
# ---------------------------------------------------------------------------

_INTEGRATION_SKIP = not (
    os.environ.get("S3_TEST_ENDPOINT")
    and os.environ.get("S3_TEST_ACCESS_KEY")
    and os.environ.get("S3_TEST_SECRET_KEY")
)


@unittest.skipIf(
    _INTEGRATION_SKIP, "S3_TEST_* env vars not set — skipping integration tests"
)
class TestS3Integration(unittest.TestCase):
    """Live integration tests against a real S3-compatible backend."""

    @classmethod
    def setUpClass(cls):
        cls.client = S3Client(
            endpoint=os.environ["S3_TEST_ENDPOINT"],
            access_key=os.environ["S3_TEST_ACCESS_KEY"],
            secret_key=os.environ["S3_TEST_SECRET_KEY"],
            region=os.environ.get("S3_TEST_REGION", "us-east-1"),
            secure=os.environ.get("S3_TEST_SECURE", "1") != "0",
            url_style=os.environ.get("S3_TEST_URL_STYLE", "path"),
        )
        cls.bucket = os.environ.get("S3_TEST_BUCKET", "zerodep-s3-test")

    def test_bucket_lifecycle(self):
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)
        self.assertTrue(self.client.bucket_exists(self.bucket))

    def test_put_get_roundtrip(self):
        payload = gzip.compress(json.dumps({"ts": time.time()}).encode())
        key = f"test/roundtrip-{int(time.time())}.json.gz"
        self.client.put_object(
            self.bucket,
            key,
            payload,
            length=len(payload),
            content_type="application/json",
            metadata={"stored-at": str(int(time.time()))},
        )
        with self.client.get_object(self.bucket, key) as resp:
            raw = resp.read()
        result = json.loads(gzip.decompress(raw))
        self.assertIn("ts", result)

    def test_get_missing_key(self):
        with self.assertRaises(S3NoSuchKey):
            self.client.get_object(
                self.bucket, f"test/definitely-missing-{time.time()}"
            )


if __name__ == "__main__":
    unittest.main()
