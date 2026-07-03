# /// zerodep
# version = "0.1.0"
# deps = []
# tier = "subsystem"
# category = "storage"
# note = "Install/update via: https://zerodep.readthedocs.io/en/latest/guide/cli/"
# ///
"""Zero-dependency S3-compatible storage client (stdlib only).

Implements AWS Signature Version 4 and a minimal S3 REST client covering the
four operations needed to drive a read/write object cache:

- ``bucket_exists`` — check whether a bucket is accessible
- ``make_bucket``   — create a bucket
- ``get_object``    — download an object (returns a readable response)
- ``put_object``    — upload an object

Compatible with AWS S3, Cloudflare R2, Oracle Object Storage, MinIO, and any
other S3-compatible backend.  Uses only Python stdlib (``hashlib``, ``hmac``,
``http.client``, ``urllib.parse``, ``xml.etree.ElementTree``).

Part of zerodep: https://github.com/Oaklight/zerodep
Copyright (c) 2026 Peng Ding. MIT License.

Basic usage::

    from s3 import S3Client

    client = S3Client(
        endpoint="s3.amazonaws.com",
        access_key="AKIAIOSFODNN7EXAMPLE",
        secret_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        region="us-east-1",
    )

    if not client.bucket_exists("my-bucket"):
        client.make_bucket("my-bucket")

    import io, gzip, json
    payload = gzip.compress(json.dumps({"hello": "world"}).encode())
    client.put_object("my-bucket", "data/hello.json.gz", io.BytesIO(payload),
                      length=len(payload), content_type="application/json")

    response = client.get_object("my-bucket", "data/hello.json.gz")
    try:
        data = json.loads(gzip.decompress(response.read()))
    finally:
        response.close()

Cloudflare R2 example::

    client = S3Client(
        endpoint="<account>.r2.cloudflarestorage.com",
        access_key="...",
        secret_key="...",
        region="auto",
        url_style="path",   # R2 requires path-style
    )

URL styles:

- ``"path"``         — ``https://endpoint/bucket/key``  (R2, OCI, MinIO)
- ``"virtual-host"`` — ``https://bucket.endpoint/key``  (AWS S3 default)
"""

from __future__ import annotations

import hashlib
import hmac
import http.client
import logging
import ssl
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import IO

__all__ = [
    # Exceptions
    "S3Error",
    "S3NoSuchBucket",
    "S3NoSuchKey",
    # Response
    "S3Response",
    # Client
    "S3Client",
]

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

_S3_NS = "http://s3.amazonaws.com/doc/2006-03-01/"


class S3Error(Exception):
    """Base class for S3 errors returned by the server."""

    def __init__(self, code: str, message: str, status: int = 0) -> None:
        self.code = code
        self.message = message
        self.status = status
        super().__init__(f"S3Error {code}: {message} (HTTP {status})")


class S3NoSuchBucket(S3Error):
    """Raised when the requested bucket does not exist."""


class S3NoSuchKey(S3Error):
    """Raised when the requested object key does not exist."""


# ---------------------------------------------------------------------------
# Response wrapper
# ---------------------------------------------------------------------------


class S3Response:
    """Thin wrapper around an ``http.client.HTTPResponse``.

    Provides the same ``read()`` / ``close()`` / ``release_conn()``
    interface used by ``minio`` responses, so callers can migrate
    without changing their error-handling code.

    Can be used as a context manager::

        with client.get_object(bucket, key) as resp:
            data = resp.read()
    """

    def __init__(self, resp: http.client.HTTPResponse) -> None:
        self._resp = resp

    # ---------- minio-compatible surface ----------

    def read(self, amt: int | None = None) -> bytes:
        """Read response body (or up to *amt* bytes)."""
        if amt is None:
            return self._resp.read()
        return self._resp.read(amt)

    def close(self) -> None:
        """Close the underlying socket."""
        self._resp.close()

    def release_conn(self) -> None:
        """Alias for :meth:`close` (minio compatibility)."""
        self.close()

    # ---------- extras ----------

    @property
    def status(self) -> int:
        return self._resp.status

    @property
    def headers(self) -> http.client.HTTPMessage:
        return self._resp.headers

    def iter_chunks(self, chunk_size: int = 65536):
        """Iterate over the response body in chunks."""
        while True:
            chunk = self._resp.read(chunk_size)
            if not chunk:
                break
            yield chunk

    # ---------- context manager ----------

    def __enter__(self) -> "S3Response":
        return self

    def __exit__(self, *_) -> None:
        self.close()


# ---------------------------------------------------------------------------
# AWS Signature Version 4
# ---------------------------------------------------------------------------


def _hmac_sha256(key: bytes, msg: str) -> bytes:
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _derive_signing_key(secret_key: str, date: str, region: str, service: str) -> bytes:
    """Derive the SigV4 signing key from its four HMAC-SHA256 steps."""
    k_date = _hmac_sha256(("AWS4" + secret_key).encode("utf-8"), date)
    k_region = _hmac_sha256(k_date, region)
    k_service = _hmac_sha256(k_region, service)
    k_signing = _hmac_sha256(k_service, "aws4_request")
    return k_signing


def _sign_request(
    method: str,
    url: str,
    headers: dict[str, str],
    payload: bytes,
    access_key: str,
    secret_key: str,
    region: str,
    service: str = "s3",
) -> dict[str, str]:
    """Return a *new* headers dict with ``Authorization`` and date headers added.

    Args:
        method:     HTTP method (GET, PUT, HEAD, DELETE, …).
        url:        Full request URL including query string.
        headers:    Request headers (will not be mutated).
        payload:    Request body bytes (b"" for requests without a body).
        access_key: AWS / S3-compatible access key.
        secret_key: AWS / S3-compatible secret key.
        region:     Region string (``"us-east-1"``, ``"auto"``, …).
        service:    Service name (always ``"s3"``).

    Returns:
        A copy of *headers* extended with ``x-amz-date``,
        ``x-amz-content-sha256``, and ``Authorization``.
    """
    now = datetime.now(timezone.utc)
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")  # e.g. 20240101T120000Z
    date_stamp = now.strftime("%Y%m%d")  # e.g. 20240101

    parsed = urllib.parse.urlparse(url)
    host = parsed.netloc
    path = parsed.path or "/"
    query = parsed.query

    payload_hash = _sha256_hex(payload)

    # Build signed headers (must be sorted, lowercase)
    hdrs = dict(headers)
    hdrs["host"] = host
    hdrs["x-amz-date"] = amz_date
    hdrs["x-amz-content-sha256"] = payload_hash

    signed_names = sorted(k.lower() for k in hdrs)
    canonical_headers = "".join(
        f"{k}:{hdrs[k].strip()}\n" for k in sorted(hdrs, key=str.lower)
    )
    signed_headers_str = ";".join(signed_names)

    # Canonical query string: sort by name then value
    if query:
        params = urllib.parse.parse_qsl(query, keep_blank_values=True)
        canonical_qs = urllib.parse.urlencode(sorted(params))
    else:
        canonical_qs = ""

    # Canonical request
    canonical_request = "\n".join(
        [
            method.upper(),
            urllib.parse.quote(path, safe="/-_.~"),
            canonical_qs,
            canonical_headers,
            signed_headers_str,
            payload_hash,
        ]
    )

    # String to sign
    credential_scope = f"{date_stamp}/{region}/{service}/aws4_request"
    string_to_sign = "\n".join(
        [
            "AWS4-HMAC-SHA256",
            amz_date,
            credential_scope,
            _sha256_hex(canonical_request.encode("utf-8")),
        ]
    )

    # Signature
    signing_key = _derive_signing_key(secret_key, date_stamp, region, service)
    signature = hmac.new(
        signing_key, string_to_sign.encode("utf-8"), hashlib.sha256
    ).hexdigest()

    authorization = (
        f"AWS4-HMAC-SHA256 Credential={access_key}/{credential_scope}, "
        f"SignedHeaders={signed_headers_str}, "
        f"Signature={signature}"
    )

    result = dict(hdrs)
    result["Authorization"] = authorization
    return result


# ---------------------------------------------------------------------------
# XML helpers
# ---------------------------------------------------------------------------


def _find_xml_el(root: ET.Element, tag: str) -> ET.Element | None:
    """Find *tag* with or without the S3 XML namespace."""
    el = root.find(tag)
    if el is None:
        el = root.find(f"{{{_S3_NS}}}{tag}")
    return el


def _parse_s3_error(body: bytes, status: int) -> S3Error:
    """Parse an S3 XML error response into the appropriate exception."""
    code = "Unknown"
    message = body.decode("utf-8", errors="replace")
    try:
        root = ET.fromstring(body)
        code_el = _find_xml_el(root, "Code")
        msg_el = _find_xml_el(root, "Message")
        if code_el is not None and code_el.text:
            code = code_el.text
        if msg_el is not None and msg_el.text:
            message = msg_el.text
    except ET.ParseError:
        pass

    if code == "NoSuchBucket":
        return S3NoSuchBucket(code, message, status)
    if code == "NoSuchKey":
        return S3NoSuchKey(code, message, status)
    return S3Error(code, message, status)


# ---------------------------------------------------------------------------
# S3Client
# ---------------------------------------------------------------------------


class S3Client:
    """Minimal S3-compatible REST client (stdlib only, sync).

    Implements the four operations needed to drive a persistent render cache:
    :meth:`bucket_exists`, :meth:`make_bucket`, :meth:`get_object`,
    :meth:`put_object`.

    For async callers, wrap individual calls in ``asyncio.to_thread()``::

        data = await asyncio.to_thread(client.get_object, bucket, key)

    Args:
        endpoint:   S3 endpoint hostname (no scheme), e.g.
                    ``"s3.amazonaws.com"`` or ``"<acct>.r2.cloudflarestorage.com"``.
        access_key: Access key ID.
        secret_key: Secret access key.
        region:     Region string.  Pass ``"auto"`` for Cloudflare R2.
        secure:     Use HTTPS (default ``True``).
        url_style:  ``"path"`` (default) or ``"virtual-host"``.
                    Path-style: ``https://endpoint/bucket/key``.
                    Virtual-host-style: ``https://bucket.endpoint/key``.
        timeout:    Socket timeout in seconds (default 30).
    """

    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        region: str = "us-east-1",
        secure: bool = True,
        url_style: str = "path",
        timeout: int = 30,
    ) -> None:
        # Strip any scheme the caller may have included
        endpoint = endpoint.removeprefix("https://").removeprefix("http://").rstrip("/")
        self._endpoint = endpoint
        self._access_key = access_key
        self._secret_key = secret_key
        # Cloudflare R2 advertises "auto" — map to a valid SigV4 region token
        self._region = "auto" if region == "auto" else region
        self._secure = secure
        if url_style not in ("path", "virtual-host"):
            raise ValueError(
                f"url_style must be 'path' or 'virtual-host', got {url_style!r}"
            )
        self._url_style = url_style
        self._timeout = timeout
        self._ssl_ctx = ssl.create_default_context() if secure else None

    # ------------------------------------------------------------------ #
    # URL construction
    # ------------------------------------------------------------------ #

    def _bucket_url(self, bucket: str) -> str:
        scheme = "https" if self._secure else "http"
        if self._url_style == "virtual-host":
            return f"{scheme}://{bucket}.{self._endpoint}/"
        return f"{scheme}://{self._endpoint}/{bucket}/"

    def _object_url(self, bucket: str, key: str) -> str:
        scheme = "https" if self._secure else "http"
        key_enc = urllib.parse.quote(key, safe="/")
        if self._url_style == "virtual-host":
            return f"{scheme}://{bucket}.{self._endpoint}/{key_enc}"
        return f"{scheme}://{self._endpoint}/{bucket}/{key_enc}"

    # ------------------------------------------------------------------ #
    # Low-level HTTP
    # ------------------------------------------------------------------ #

    def _connect(self, host: str) -> http.client.HTTPConnection:
        if self._secure:
            return http.client.HTTPSConnection(
                host, timeout=self._timeout, context=self._ssl_ctx
            )
        return http.client.HTTPConnection(host, timeout=self._timeout)

    def _request(
        self,
        method: str,
        url: str,
        headers: dict[str, str] | None = None,
        body: bytes | IO[bytes] | None = None,
    ) -> http.client.HTTPResponse:
        """Sign and send one HTTP request; return the raw response."""
        parsed = urllib.parse.urlparse(url)
        host = parsed.netloc
        path_and_query = parsed.path
        if parsed.query:
            path_and_query += "?" + parsed.query

        hdrs: dict[str, str] = dict(headers or {})

        # Materialise body for signing
        # (small objects only; streaming is handled separately)
        if isinstance(body, (bytes, bytearray)):
            payload_bytes = bytes(body)
        elif body is None:
            payload_bytes = b""
        else:
            # File-like: read into memory for signing
            # (put_object handles chunking above)
            payload_bytes = body.read()
            body = payload_bytes  # re-send as bytes

        signed_hdrs = _sign_request(
            method=method,
            url=url,
            headers=hdrs,
            payload=payload_bytes,
            access_key=self._access_key,
            secret_key=self._secret_key,
            region=self._region,
        )

        conn = self._connect(host)
        try:
            conn.request(
                method,
                path_and_query,
                body=body if body else None,
                headers=signed_hdrs,
            )
            resp = conn.getresponse()
            # Detach response from connection so the caller can read it
            # after this method returns (http.client keeps the socket open
            # until the response body is consumed or closed).
            return resp
        except Exception:
            conn.close()
            raise

    def _request_expect_ok(
        self,
        method: str,
        url: str,
        headers: dict[str, str] | None = None,
        body: bytes | None = None,
        ok_statuses: tuple[int, ...] = (200, 204),
    ) -> http.client.HTTPResponse:
        """Send a request and raise :class:`S3Error` on unexpected status codes."""
        resp = self._request(method, url, headers=headers, body=body)
        if resp.status not in ok_statuses:
            err_body = resp.read()
            raise _parse_s3_error(err_body, resp.status)
        return resp

    # ------------------------------------------------------------------ #
    # Public API — Phase 1
    # ------------------------------------------------------------------ #

    def bucket_exists(self, bucket: str) -> bool:
        """Return ``True`` if *bucket* exists and is accessible.

        HTTP 200 and 403 both indicate the bucket exists (403 means it exists
        but this account lacks ``s3:ListBucket`` — the bucket is still there).
        HTTP 404 means the bucket does not exist.

        Args:
            bucket: Bucket name.

        Returns:
            ``True`` if the bucket exists, ``False`` otherwise.

        Raises:
            :class:`S3Error`: On unexpected server errors (5xx, etc.).
        """
        url = self._bucket_url(bucket)
        resp = self._request("HEAD", url)
        body = resp.read()

        if resp.status in (200, 301, 403):
            return True
        if resp.status == 404:
            return False
        raise _parse_s3_error(body, resp.status)

    def make_bucket(self, bucket: str) -> None:
        """Create *bucket*.

        For AWS S3 in regions other than ``us-east-1``, a
        ``<CreateBucketConfiguration>`` XML body is required.  For R2 / OCI /
        MinIO a plain PUT with no body works everywhere.

        Args:
            bucket: Bucket name.

        Raises:
            :class:`S3Error`: If creation fails (e.g. bucket already exists
                with ``BucketAlreadyOwnedByYou``).
        """
        url = self._bucket_url(bucket)
        headers: dict[str, str] = {"Content-Length": "0"}

        # For AWS S3, non-us-east-1 regions require a location constraint body
        if self._region not in ("us-east-1", "auto"):
            body_xml = (
                f'<?xml version="1.0" encoding="UTF-8"?>'
                f"<CreateBucketConfiguration "
                f'xmlns="http://s3.amazonaws.com/doc/2006-03-01/">'
                f"<LocationConstraint>{self._region}</LocationConstraint>"
                f"</CreateBucketConfiguration>"
            ).encode()
            headers["Content-Length"] = str(len(body_xml))
            headers["Content-Type"] = "application/xml"
            self._request_expect_ok(
                "PUT", url, headers=headers, body=body_xml, ok_statuses=(200,)
            )
        else:
            self._request_expect_ok(
                "PUT", url, headers=headers, body=b"", ok_statuses=(200,)
            )

        logger.info("Created bucket: %s", bucket)

    def get_object(self, bucket: str, key: str) -> S3Response:
        """Download the object at *bucket*/*key*.

        The caller is responsible for reading *and closing* the returned
        response::

            resp = client.get_object("my-bucket", "my-key")
            try:
                data = resp.read()
            finally:
                resp.close()

        Or equivalently::

            with client.get_object("my-bucket", "my-key") as resp:
                data = resp.read()

        Args:
            bucket: Bucket name.
            key:    Object key.

        Returns:
            :class:`S3Response` — a readable, closable response object.

        Raises:
            :class:`S3NoSuchBucket`: If the bucket does not exist.
            :class:`S3NoSuchKey`:    If the key does not exist.
            :class:`S3Error`:        On other server errors.
        """
        url = self._object_url(bucket, key)
        resp = self._request("GET", url)
        if resp.status != 200:
            err_body = resp.read()
            raise _parse_s3_error(err_body, resp.status)
        return S3Response(resp)

    def put_object(
        self,
        bucket: str,
        key: str,
        data: bytes | IO[bytes],
        length: int,
        content_type: str = "application/octet-stream",
        metadata: dict[str, str] | None = None,
    ) -> None:
        """Upload *data* to *bucket*/*key*.

        Args:
            bucket:       Bucket name.
            key:          Object key.
            data:         Bytes or a file-like object opened in binary mode.
            length:       Exact byte length of *data* (required for
                          ``Content-Length``).
            content_type: MIME type of the object (default
                          ``"application/octet-stream"``).
            metadata:     Optional user-defined metadata.  Keys are sent as
                          ``x-amz-meta-<key>`` headers; values must be
                          ASCII-safe strings.

        Raises:
            :class:`S3NoSuchBucket`: If the bucket does not exist.
            :class:`S3Error`:        On other server errors.
        """
        url = self._object_url(bucket, key)
        headers: dict[str, str] = {
            "Content-Type": content_type,
            "Content-Length": str(length),
        }
        if metadata:
            for k, v in metadata.items():
                # Normalise key: strip any existing x-amz-meta- prefix
                clean = k.lower().removeprefix("x-amz-meta-")
                headers[f"x-amz-meta-{clean}"] = v

        # Materialise bytes for signing
        if isinstance(data, (bytes, bytearray)):
            body_bytes = bytes(data)
        else:
            body_bytes = data.read()

        self._request_expect_ok(
            "PUT", url, headers=headers, body=body_bytes, ok_statuses=(200,)
        )
        logger.debug("Stored object: %s/%s (%d bytes)", bucket, key, length)
