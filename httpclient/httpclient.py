# /// zerodep
# version = "0.1.0"
# deps = []
# ///

"""Zero-dependency sync + async HTTP REST client.

Part of zerodep: https://github.com/Oaklight/zerodep
Copyright (c) 2026 Peng Ding. MIT License.

Sync (http.client) and async (asyncio streams) HTTP/1.1 client
for REST API consumption. Thread-safe by design.

Sync usage::

    response = get("https://httpbin.org/get")
    response.json()

Async usage::

    response = await async_get("https://httpbin.org/get")
    response.json()

Session usage::

    with Client() as client:
        r = client.get("https://httpbin.org/get")

    async with AsyncClient() as client:
        r = await client.get("https://httpbin.org/get")
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import http.client
import json as _json
import os
import ssl
import threading
import time
import warnings
import zlib
from collections.abc import AsyncIterator, Iterator
from typing import IO, Any
from urllib.parse import quote, urlencode, urlparse

# ── Defaults ──

DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_REDIRECTS = 10
DEFAULT_USER_AGENT = "zerodep-http/0.1"
DEFAULT_POOL_SIZE = 10
DEFAULT_POOL_IDLE_TIMEOUT = 60.0


# ── Response ──


class Response:
    """HTTP response object.

    Attributes:
        status_code: HTTP status code.
        headers: Response headers as dict (last value wins for duplicates).
        content: Raw response body as bytes.
        url: Final URL after redirects.
    """

    __slots__ = ("status_code", "headers", "content", "url", "_text", "_json")

    def __init__(
        self,
        status_code: int,
        headers: dict[str, str],
        content: bytes,
        url: str,
    ) -> None:
        self.status_code = status_code
        self.headers = headers
        self.content = content
        self.url = url
        self._text: str | None = None
        self._json: Any = None

    @property
    def text(self) -> str:
        """Decode response body as text."""
        if self._text is None:
            encoding = self._guess_encoding()
            self._text = self.content.decode(encoding, errors="replace")
        return self._text

    def json(self) -> Any:
        """Parse response body as JSON."""
        if self._json is None:
            self._json = _json.loads(self.content)
        return self._json

    @property
    def ok(self) -> bool:
        """True if status_code is 2xx."""
        return 200 <= self.status_code < 300

    def raise_for_status(self) -> None:
        """Raise HTTPError if status is not 2xx."""
        if not self.ok:
            raise HTTPError(self.status_code, self.text, self.url)

    def _guess_encoding(self) -> str:
        return _guess_encoding_from_headers(self.headers)

    # ── Context managers (no-op, body is already fully read) ──

    def __enter__(self) -> Response:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    async def __aenter__(self) -> Response:
        return self

    async def __aexit__(self, *args: Any) -> None:
        self.close()

    def close(self) -> None:
        """No-op close for a fully-read response."""

    async def aclose(self) -> None:
        """No-op async close for a fully-read response."""

    def __repr__(self) -> str:
        return f"<Response [{self.status_code}]>"


def _guess_encoding_from_headers(headers: dict[str, str]) -> str:
    """Extract charset from Content-Type header, default utf-8."""
    ct = headers.get("content-type", "")
    for part in ct.split(";"):
        part = part.strip()
        if part.startswith("charset="):
            return part[8:].strip().strip('"')
    return "utf-8"


# ── Auth ──


class Auth:
    """Base class for HTTP authentication."""

    def auth_headers(self, method: str, url: str) -> dict[str, str]:
        """Return authorization headers.

        Args:
            method: HTTP method.
            url: Request URL.

        Returns:
            Dict of headers to add to the request.
        """
        raise NotImplementedError


class BasicAuth(Auth):
    """HTTP Basic authentication."""

    def __init__(self, username: str, password: str) -> None:
        self._username = username
        self._password = password

    def auth_headers(self, method: str, url: str) -> dict[str, str]:
        """Return Basic Authorization header."""
        credentials = f"{self._username}:{self._password}".encode()
        return {"Authorization": "Basic " + base64.b64encode(credentials).decode()}


class DigestAuth(Auth):
    """HTTP Digest authentication."""

    def __init__(self, username: str, password: str) -> None:
        self._username = username
        self._password = password
        self._nc = 0

    def auth_headers(self, method: str, url: str) -> dict[str, str]:
        """Not usable without a server challenge."""
        raise NotImplementedError("DigestAuth requires a server challenge")

    def auth_headers_from_challenge(
        self, method: str, path: str, challenge: str
    ) -> dict[str, str]:
        """Compute Digest auth headers from a WWW-Authenticate challenge.

        Args:
            method: HTTP method.
            path: Request path (URI).
            challenge: The WWW-Authenticate header value.

        Returns:
            Dict with the Authorization header.
        """
        params = _parse_digest_challenge(challenge)
        realm = params.get("realm", "")
        nonce = params.get("nonce", "")
        qop = params.get("qop", "")
        opaque = params.get("opaque", "")
        algorithm = params.get("algorithm", "MD5").upper()

        self._nc += 1
        nc_hex = f"{self._nc:08x}"
        cnonce = os.urandom(16).hex()

        if algorithm == "SHA-256":
            hash_fn = hashlib.sha256
        else:
            hash_fn = hashlib.md5

        ha1 = hash_fn(f"{self._username}:{realm}:{self._password}".encode()).hexdigest()
        ha2 = hash_fn(f"{method}:{path}".encode()).hexdigest()

        if qop == "auth":
            response = hash_fn(
                f"{ha1}:{nonce}:{nc_hex}:{cnonce}:{qop}:{ha2}".encode()
            ).hexdigest()
        else:
            response = hash_fn(f"{ha1}:{nonce}:{ha2}".encode()).hexdigest()

        header = (
            f'Digest username="{self._username}", realm="{realm}", '
            f'nonce="{nonce}", uri="{path}", response="{response}"'
        )
        if qop:
            header += f', qop={qop}, nc={nc_hex}, cnonce="{cnonce}"'
        if opaque:
            header += f', opaque="{opaque}"'
        header += f", algorithm={algorithm}"

        return {"Authorization": header}


def _normalize_auth(
    auth: tuple[str, str] | Auth | None,
) -> Auth | None:
    """Convert auth parameter to an Auth instance.

    Args:
        auth: A (username, password) tuple, an Auth subclass, or None.

    Returns:
        An Auth instance or None.
    """
    if auth is None:
        return None
    if isinstance(auth, tuple):
        return BasicAuth(auth[0], auth[1])
    return auth


def _parse_digest_challenge(header_value: str) -> dict[str, str]:
    """Parse a Digest WWW-Authenticate challenge into a dict.

    Args:
        header_value: The full WWW-Authenticate header value.

    Returns:
        Dict of challenge parameters.
    """
    if header_value.lower().startswith("digest "):
        header_value = header_value[7:]
    result: dict[str, str] = {}
    import re

    for match in re.finditer(r'(\w+)=(?:"([^"]*)"|([\w\-]+))', header_value):
        key = match.group(1)
        value = match.group(2) if match.group(2) is not None else match.group(3)
        result[key] = value
    return result


# ── Decompression helpers ──


def _decompress_body(body: bytes, encoding: str) -> bytes:
    """Decompress a response body based on Content-Encoding.

    Args:
        body: The raw response body bytes.
        encoding: The Content-Encoding value.

    Returns:
        Decompressed bytes, or original body if encoding is unsupported.
    """
    if encoding in ("gzip", "x-gzip"):
        return zlib.decompress(body, 16 + zlib.MAX_WBITS)
    if encoding == "deflate":
        try:
            return zlib.decompress(body, -zlib.MAX_WBITS)
        except zlib.error:
            return zlib.decompress(body)
    return body


def _make_decompressor(encoding: str) -> zlib.decompressobj | None:
    """Create a streaming decompressor for the given encoding.

    Args:
        encoding: The Content-Encoding value.

    Returns:
        A zlib.decompressobj or None if encoding is unsupported.
    """
    if encoding in ("gzip", "x-gzip"):
        return zlib.decompressobj(16 + zlib.MAX_WBITS)
    if encoding == "deflate":
        return zlib.decompressobj(-zlib.MAX_WBITS)
    return None


# ── Proxy helpers ──


def _parse_proxy(proxy: str) -> tuple[str, int, str | None, str | None]:
    """Parse a proxy URL into components.

    Args:
        proxy: Proxy URL (e.g. "http://user:pass@host:port").

    Returns:
        Tuple of (hostname, port, username_or_None, password_or_None).
    """
    parsed = urlparse(proxy)
    hostname = parsed.hostname or ""
    port = parsed.port or 8080
    username = parsed.username or None
    password = parsed.password or None
    return hostname, port, username, password


def _proxy_auth_header(username: str, password: str) -> str:
    """Build a Proxy-Authorization Basic header value.

    Args:
        username: Proxy username.
        password: Proxy password.

    Returns:
        The header value string.
    """
    credentials = f"{username}:{password}".encode()
    return "Basic " + base64.b64encode(credentials).decode()


# ── Streaming Response ──


class StreamingResponse:
    """HTTP streaming response — holds the connection open.

    Use as a context manager to ensure cleanup::

        with get(url, stream=True) as r:
            for chunk in r.iter_bytes():
                process(chunk)

        async with await async_get(url, stream=True) as r:
            async for line in r.aiter_lines():
                handle(line)
    """

    __slots__ = (
        "status_code",
        "headers",
        "url",
        "_encoding",
        "_decompressor",
        "_sync_resp",
        "_sync_conn",
        "_async_reader",
        "_async_writer",
        "_async_timeout",
        "_is_chunked",
        "_content_length",
        "_bytes_remaining",
        "_closed",
    )

    status_code: int
    headers: dict[str, str]
    url: str
    _encoding: str
    _sync_resp: http.client.HTTPResponse | None
    _sync_conn: http.client.HTTPConnection | None
    _async_reader: asyncio.StreamReader | None
    _async_writer: asyncio.StreamWriter | None
    _async_timeout: float | None
    _is_chunked: bool
    _content_length: int | None
    _bytes_remaining: int | None
    _closed: bool

    def __init__(self) -> None:
        raise TypeError("Use _from_sync() or _from_async()")

    @classmethod
    def _from_sync(
        cls,
        status_code: int,
        headers: dict[str, str],
        url: str,
        resp: http.client.HTTPResponse,
        conn: http.client.HTTPConnection,
        content_encoding: str = "",
    ) -> "StreamingResponse":
        obj = object.__new__(cls)
        obj.status_code = status_code
        obj.headers = headers
        obj.url = url
        obj._encoding = _guess_encoding_from_headers(headers)
        obj._decompressor = (
            _make_decompressor(content_encoding) if content_encoding else None
        )
        obj._sync_resp = resp
        obj._sync_conn = conn
        obj._async_reader = None
        obj._async_writer = None
        obj._async_timeout = None
        obj._is_chunked = False
        obj._content_length = None
        obj._bytes_remaining = None
        obj._closed = False
        return obj

    @classmethod
    def _from_async(
        cls,
        status_code: int,
        headers: dict[str, str],
        url: str,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        is_chunked: bool,
        content_length: int | None,
        timeout: float,
        content_encoding: str = "",
    ) -> "StreamingResponse":
        obj = object.__new__(cls)
        obj.status_code = status_code
        obj.headers = headers
        obj.url = url
        obj._encoding = _guess_encoding_from_headers(headers)
        obj._decompressor = (
            _make_decompressor(content_encoding) if content_encoding else None
        )
        obj._sync_resp = None
        obj._sync_conn = None
        obj._async_reader = reader
        obj._async_writer = writer
        obj._async_timeout = timeout
        obj._is_chunked = is_chunked
        obj._content_length = content_length
        obj._bytes_remaining = content_length
        obj._closed = False
        return obj

    @property
    def ok(self) -> bool:
        """True if status_code is 2xx."""
        return 200 <= self.status_code < 300

    def raise_for_status(self) -> None:
        """Raise HTTPError if status is not 2xx."""
        if not self.ok:
            raise HTTPError(self.status_code, "", self.url)

    # ── Sync iteration ──

    def iter_bytes(self, chunk_size: int = 4096) -> Iterator[bytes]:
        """Yield response body in chunks."""
        if self._sync_resp is None:
            raise RuntimeError("iter_bytes() on async response")
        try:
            while True:
                chunk = self._sync_resp.read(chunk_size)
                if not chunk:
                    break
                if self._decompressor:
                    chunk = self._decompressor.decompress(chunk)
                yield chunk
            if self._decompressor:
                remaining = self._decompressor.flush()
                if remaining:
                    yield remaining
        except (OSError, http.client.HTTPException) as exc:
            raise ConnectionError(str(exc)) from exc

    def iter_lines(self) -> Iterator[str]:
        """Yield response body line by line (decoded)."""
        if self._sync_resp is None:
            raise RuntimeError("iter_lines() on async response")
        try:
            while True:
                line = self._sync_resp.readline()
                if not line:
                    break
                yield line.decode(self._encoding, errors="replace").rstrip("\r\n")
        except (OSError, http.client.HTTPException) as exc:
            raise ConnectionError(str(exc)) from exc

    def read(self) -> bytes:
        """Consume entire stream into bytes."""
        return b"".join(self.iter_bytes())

    # ── Async iteration ──

    async def aiter_bytes(self, chunk_size: int = 4096) -> AsyncIterator[bytes]:
        """Async yield response body in chunks."""
        if self._async_reader is None:
            raise RuntimeError("aiter_bytes() on sync response")
        try:
            if self._is_chunked:
                async for chunk in self._aiter_chunked():
                    if self._decompressor:
                        chunk = self._decompressor.decompress(chunk)
                    yield chunk
            elif self._bytes_remaining is not None:
                while self._bytes_remaining > 0:
                    to_read = min(chunk_size, self._bytes_remaining)
                    data = await asyncio.wait_for(
                        self._async_reader.read(to_read),
                        timeout=self._async_timeout,
                    )
                    if not data:
                        break
                    self._bytes_remaining -= len(data)
                    if self._decompressor:
                        data = self._decompressor.decompress(data)
                    yield data
            else:
                while True:
                    data = await asyncio.wait_for(
                        self._async_reader.read(chunk_size),
                        timeout=self._async_timeout,
                    )
                    if not data:
                        break
                    if self._decompressor:
                        data = self._decompressor.decompress(data)
                    yield data
            if self._decompressor:
                remaining = self._decompressor.flush()
                if remaining:
                    yield remaining
        except asyncio.TimeoutError:
            raise TimeoutError(f"Streaming read timed out for {self.url}")
        except OSError as exc:
            raise ConnectionError(str(exc)) from exc

    async def _aiter_chunked(self) -> AsyncIterator[bytes]:
        """Decode chunked transfer encoding from async reader."""
        assert self._async_reader is not None  # guaranteed by aiter_bytes guard
        reader = self._async_reader
        timeout = self._async_timeout
        while True:
            size_line = await asyncio.wait_for(reader.readline(), timeout=timeout)
            size_str = size_line.decode("latin-1").split(";")[0].strip()
            if not size_str:
                break
            chunk_size = int(size_str, 16)
            if chunk_size == 0:
                await asyncio.wait_for(
                    reader.readline(), timeout=timeout
                )  # trailing \r\n
                break
            data = await asyncio.wait_for(
                reader.readexactly(chunk_size), timeout=timeout
            )
            await asyncio.wait_for(reader.readline(), timeout=timeout)  # trailing \r\n
            yield data

    async def aiter_lines(self) -> AsyncIterator[str]:
        """Async yield response body line by line (decoded)."""
        buf = ""
        async for chunk in self.aiter_bytes():
            buf += chunk.decode(self._encoding, errors="replace")
            while "\n" in buf:
                line, buf = buf.split("\n", 1)
                yield line.rstrip("\r")
        if buf:
            yield buf.rstrip("\r")

    async def aread(self) -> bytes:
        """Async consume entire stream into bytes."""
        parts = []
        async for chunk in self.aiter_bytes():
            parts.append(chunk)
        return b"".join(parts)

    # ── Context managers ──

    def __enter__(self) -> "StreamingResponse":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    async def __aenter__(self) -> "StreamingResponse":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.aclose()

    def close(self) -> None:
        """Close the underlying sync connection."""
        if self._closed:
            return
        self._closed = True
        if self._sync_resp is not None:
            try:
                self._sync_resp.close()
            except Exception:
                pass
        if self._sync_conn is not None:
            try:
                self._sync_conn.close()
            except Exception:
                pass

    async def aclose(self) -> None:
        """Close the underlying async connection."""
        if self._closed:
            return
        self._closed = True
        if self._async_writer is not None:
            try:
                self._async_writer.close()
                await self._async_writer.wait_closed()
            except Exception:
                pass

    def __del__(self) -> None:
        if not self._closed:
            warnings.warn(
                f"Unclosed StreamingResponse for {self.url}",
                ResourceWarning,
                stacklevel=2,
            )
            self.close()

    def __repr__(self) -> str:
        return f"<StreamingResponse [{self.status_code}]>"


# ── Exceptions ──


class HTTPError(Exception):
    """Raised on non-2xx status when raise_for_status() is called."""

    def __init__(self, status_code: int, body: str, url: str) -> None:
        self.status_code = status_code
        self.body = body
        self.url = url
        super().__init__(f"HTTP {status_code} for {url}")


class TooManyRedirects(HTTPError):
    """Raised when redirect limit is exceeded."""

    def __init__(self, url: str, max_redirects: int) -> None:
        super().__init__(0, "", url)
        self.max_redirects = max_redirects
        Exception.__init__(self, f"Too many redirects (>{max_redirects}) for {url}")


class ConnectionError(Exception):
    """Raised on connection failures."""


class TimeoutError(Exception):
    """Raised on request timeout."""


# ── URL helpers ──


def _build_url(url: str, params: dict[str, Any] | None = None) -> str:
    """Append query parameters to URL."""
    if not params:
        return url
    sep = "&" if "?" in url else "?"
    encoded = urlencode(
        {k: v for k, v in params.items() if v is not None}, quote_via=quote
    )
    return f"{url}{sep}{encoded}"


def _parse_url(url: str) -> tuple[str, str, int, str, bool]:
    """Parse URL into (scheme, host, port, path, is_https)."""
    parsed = urlparse(url)
    is_https = parsed.scheme == "https"
    host = parsed.hostname or ""
    port = parsed.port or (443 if is_https else 80)
    path = parsed.path or "/"
    if parsed.query:
        path = f"{path}?{parsed.query}"
    return parsed.scheme, host, port, path, is_https


def _prepare_body(
    data: bytes | str | dict[str, str] | None = None,
    json: Any = None,
    files: dict[str, Any] | list[tuple[str, Any]] | None = None,
) -> tuple[bytes | None, str | None]:
    """Prepare request body and content-type header.

    Priority: json > files > data.
    When files is provided and data is a dict, data fields are included
    as text parts in the multipart body.

    Returns:
        (body_bytes, content_type) tuple.
    """
    if json is not None:
        return _json.dumps(json, ensure_ascii=False).encode("utf-8"), "application/json"
    if files is not None:
        form_data = data if isinstance(data, dict) else None
        return _encode_multipart(form_data, files)
    if isinstance(data, str):
        return data.encode("utf-8"), "application/x-www-form-urlencoded"
    if isinstance(data, bytes):
        return data, "application/octet-stream"
    return None, None


def _read_file_content(value: bytes | IO[bytes]) -> bytes:
    """Read bytes from a file object or return bytes as-is."""
    if isinstance(value, bytes):
        return value
    return value.read()


def _get_filename(value: bytes | IO[bytes]) -> str:
    """Extract filename from a file object, or return a default."""
    if isinstance(value, bytes):
        return "upload"
    name = getattr(value, "name", None)
    if name:
        return os.path.basename(name)
    return "upload"


def _normalize_file_value(
    value: Any,
) -> tuple[str, bytes, str]:
    """Normalize a files parameter value to (filename, content, content_type).

    Accepted formats:
        bytes / file object      -> ("upload"/basename, content, octet-stream)
        (filename, content)      -> (filename, content, octet-stream)
        (filename, content, ct)  -> (filename, content, ct)
    """
    if isinstance(value, (bytes, IO)) or hasattr(value, "read"):
        fn = _get_filename(value)
        ct = "application/octet-stream"
        return fn, _read_file_content(value), ct
    if isinstance(value, (tuple, list)):
        if len(value) == 2:
            fname, content = value
            return fname, _read_file_content(content), "application/octet-stream"
        if len(value) == 3:
            fname, content, ct = value
            return fname, _read_file_content(content), ct
    raise ValueError(f"Invalid file value format: {type(value)}")


def _encode_multipart(
    data: dict[str, str] | None,
    files: dict[str, Any] | list[tuple[str, Any]],
) -> tuple[bytes, str]:
    """Encode multipart/form-data body.

    Args:
        data: Optional form fields to include as text parts.
        files: File fields as dict or list of (name, value) tuples.

    Returns:
        (body_bytes, content_type_with_boundary).
    """
    boundary = os.urandom(16).hex()
    parts: list[bytes] = []

    # Encode form data fields
    if data:
        for name, value in data.items():
            part = (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="{name}"\r\n'
                f"\r\n"
                f"{value}\r\n"
            )
            parts.append(part.encode("utf-8"))

    # Encode file fields
    items: list[tuple[str, Any]]
    if isinstance(files, dict):
        items = list(files.items())
    else:
        items = list(files)

    for name, value in items:
        filename, content, content_type = _normalize_file_value(value)
        header = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'
            f"Content-Type: {content_type}\r\n"
            f"\r\n"
        )
        parts.append(header.encode("utf-8") + content + b"\r\n")

    # Final boundary
    parts.append(f"--{boundary}--\r\n".encode("utf-8"))

    body = b"".join(parts)
    content_type = f"multipart/form-data; boundary={boundary}"
    return body, content_type


def _merge_headers(
    base: dict[str, str] | None,
    extra: dict[str, str] | None,
) -> dict[str, str]:
    """Merge header dicts (case-insensitive merge, last wins)."""
    merged: dict[str, str] = {}
    for h in (base, extra):
        if h:
            for k, v in h.items():
                merged[k] = v
    return merged


# ── Connection pools ──


class _SyncConnectionPool:
    """Thread-safe connection pool for sync HTTP connections."""

    def __init__(self, pool_size: int = DEFAULT_POOL_SIZE) -> None:
        self._pool: dict[
            tuple[str, int, bool],
            list[tuple[http.client.HTTPConnection, float]],
        ] = {}
        self._pool_size = pool_size
        self._lock = threading.Lock()

    def acquire(
        self,
        host: str,
        port: int,
        is_https: bool,
        timeout: float,
        verify: bool,
    ) -> http.client.HTTPConnection | None:
        """Acquire a connection from the pool if available.

        Args:
            host: Target hostname.
            port: Target port.
            is_https: Whether the connection uses TLS.
            timeout: Connection timeout.
            verify: Whether to verify TLS certificates.

        Returns:
            A reusable connection or None.
        """
        key = (host, port, is_https)
        now = time.monotonic()
        with self._lock:
            conns = self._pool.get(key, [])
            while conns:
                conn, timestamp = conns.pop()
                if now - timestamp > DEFAULT_POOL_IDLE_TIMEOUT:
                    try:
                        conn.close()
                    except Exception:
                        pass
                    continue
                if conn.sock is not None and conn.sock.fileno() != -1:
                    return conn
                try:
                    conn.close()
                except Exception:
                    pass
        return None

    def release(
        self,
        host: str,
        port: int,
        is_https: bool,
        conn: http.client.HTTPConnection,
    ) -> None:
        """Return a connection to the pool.

        Args:
            host: Target hostname.
            port: Target port.
            is_https: Whether the connection uses TLS.
            conn: The connection to return.
        """
        key = (host, port, is_https)
        with self._lock:
            conns = self._pool.setdefault(key, [])
            if len(conns) < self._pool_size:
                conns.append((conn, time.monotonic()))
            else:
                try:
                    conn.close()
                except Exception:
                    pass

    def close_all(self) -> None:
        """Close all pooled connections."""
        with self._lock:
            for conns in self._pool.values():
                for conn, _ in conns:
                    try:
                        conn.close()
                    except Exception:
                        pass
            self._pool.clear()


class _AsyncConnectionPool:
    """Async connection pool for async HTTP connections."""

    def __init__(self, pool_size: int = DEFAULT_POOL_SIZE) -> None:
        self._pool: dict[
            tuple[str, int, bool],
            list[
                tuple[
                    asyncio.StreamReader,
                    asyncio.StreamWriter,
                    float,
                ]
            ],
        ] = {}
        self._pool_size = pool_size
        self._lock = asyncio.Lock()

    async def acquire(
        self,
        host: str,
        port: int,
        is_https: bool,
        timeout: float,
        verify: bool,
    ) -> tuple[asyncio.StreamReader, asyncio.StreamWriter] | None:
        """Acquire a connection from the pool if available.

        Args:
            host: Target hostname.
            port: Target port.
            is_https: Whether the connection uses TLS.
            timeout: Connection timeout.
            verify: Whether to verify TLS certificates.

        Returns:
            A (reader, writer) tuple or None.
        """
        key = (host, port, is_https)
        now = time.monotonic()
        async with self._lock:
            conns = self._pool.get(key, [])
            while conns:
                reader, writer, timestamp = conns.pop()
                if now - timestamp > DEFAULT_POOL_IDLE_TIMEOUT:
                    try:
                        writer.close()
                        await writer.wait_closed()
                    except Exception:
                        pass
                    continue
                if not reader.at_eof():
                    return reader, writer
                try:
                    writer.close()
                    await writer.wait_closed()
                except Exception:
                    pass
        return None

    async def release(
        self,
        host: str,
        port: int,
        is_https: bool,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        """Return a connection to the pool.

        Args:
            host: Target hostname.
            port: Target port.
            is_https: Whether the connection uses TLS.
            reader: The stream reader.
            writer: The stream writer.
        """
        key = (host, port, is_https)
        async with self._lock:
            conns = self._pool.setdefault(key, [])
            if len(conns) < self._pool_size:
                conns.append((reader, writer, time.monotonic()))
            else:
                try:
                    writer.close()
                    await writer.wait_closed()
                except Exception:
                    pass

    async def close_all(self) -> None:
        """Close all pooled connections."""
        async with self._lock:
            for conns in self._pool.values():
                for _, writer, _ in conns:
                    try:
                        writer.close()
                        await writer.wait_closed()
                    except Exception:
                        pass
            self._pool.clear()


# ── Sync implementation (http.client) ──


def _sync_request(
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    data: bytes | str | dict[str, str] | None = None,
    json: Any = None,
    files: dict[str, Any] | list[tuple[str, Any]] | None = None,
    params: dict[str, Any] | None = None,
    timeout: float = DEFAULT_TIMEOUT,
    max_redirects: int = DEFAULT_MAX_REDIRECTS,
    verify: bool = True,
    stream: bool = False,
    auth: tuple[str, str] | Auth | None = None,
    proxy: str | None = None,
    _pool: _SyncConnectionPool | None = None,
) -> Response | StreamingResponse:
    """Perform a synchronous HTTP request."""
    url = _build_url(url, params)
    body, content_type = _prepare_body(data, json, files)

    req_headers: dict[str, str] = {"User-Agent": DEFAULT_USER_AGENT}
    req_headers["Accept-Encoding"] = "gzip, deflate"
    if content_type:
        req_headers["Content-Type"] = content_type
    if body is not None:
        req_headers["Content-Length"] = str(len(body))
    req_headers.update(headers or {})

    auth_obj = _normalize_auth(auth)
    if isinstance(auth_obj, BasicAuth):
        req_headers.update(auth_obj.auth_headers(method, url))

    redirects = 0
    _digest_attempted = False
    while True:
        scheme, host, port, path, is_https = _parse_url(url)

        close_conn = True
        conn: http.client.HTTPConnection | None = None
        try:
            if proxy:
                proxy_host, proxy_port, proxy_user, proxy_pass = _parse_proxy(proxy)
                if not is_https:
                    conn = http.client.HTTPConnection(
                        proxy_host, proxy_port, timeout=timeout
                    )
                    request_path = url
                    if proxy_user and proxy_pass:
                        req_headers["Proxy-Authorization"] = _proxy_auth_header(
                            proxy_user, proxy_pass
                        )
                else:
                    # CONNECT tunnel for HTTPS through proxy
                    tunnel_conn = http.client.HTTPConnection(
                        proxy_host, proxy_port, timeout=timeout
                    )
                    connect_headers: dict[str, str] = {"Host": f"{host}:{port}"}
                    if proxy_user and proxy_pass:
                        connect_headers["Proxy-Authorization"] = _proxy_auth_header(
                            proxy_user, proxy_pass
                        )
                    tunnel_conn.request(
                        "CONNECT", f"{host}:{port}", headers=connect_headers
                    )
                    tunnel_resp = tunnel_conn.getresponse()
                    if tunnel_resp.status != 200:
                        tunnel_conn.close()
                        raise ConnectionError(
                            f"CONNECT tunnel failed: {tunnel_resp.status}"
                        )
                    tunnel_resp.read()
                    sock = tunnel_conn.sock
                    if verify:
                        ctx = ssl.create_default_context()
                    else:
                        ctx = ssl._create_unverified_context()
                    wrapped = ctx.wrap_socket(sock, server_hostname=host)
                    conn = http.client.HTTPSConnection(
                        host, port, timeout=timeout, context=ctx
                    )
                    conn.sock = wrapped
                    request_path = path
            elif _pool:
                pooled_conn = _pool.acquire(host, port, is_https, timeout, verify)
                if pooled_conn is not None:
                    conn = pooled_conn
                    req_headers["Connection"] = "keep-alive"
                    request_path = path
                else:
                    conn = None
                    request_path = path
            else:
                request_path = path

            if conn is None:
                if is_https:
                    if verify:
                        ctx = ssl.create_default_context()
                    else:
                        ctx = ssl._create_unverified_context()
                    conn = http.client.HTTPSConnection(
                        host, port, timeout=timeout, context=ctx
                    )
                else:
                    conn = http.client.HTTPConnection(host, port, timeout=timeout)

            if _pool and not proxy:
                req_headers.setdefault("Connection", "keep-alive")

            try:
                conn.request(method, request_path, body=body, headers=req_headers)
                resp = conn.getresponse()
                resp_headers = {k.lower(): v for k, v in resp.getheaders()}
                status = resp.status

                # Handle redirects
                if status in (301, 302, 303, 307, 308) and "location" in resp_headers:
                    resp.read()  # consume redirect body
                    redirects += 1
                    if redirects > max_redirects:
                        raise TooManyRedirects(url, max_redirects)
                    location = resp_headers["location"]
                    if location.startswith("/"):
                        url = f"{scheme}://{host}:{port}{location}"
                    else:
                        url = location
                    if status == 303 or (status in (301, 302) and method == "POST"):
                        method = "GET"
                        body = None
                        req_headers.pop("Content-Type", None)
                        req_headers.pop("Content-Length", None)
                    continue

                # Digest auth retry
                if (
                    isinstance(auth_obj, DigestAuth)
                    and status == 401
                    and not _digest_attempted
                ):
                    www_auth = resp_headers.get("www-authenticate", "")
                    if www_auth.lower().startswith("digest"):
                        resp.read()
                        digest_headers = auth_obj.auth_headers_from_challenge(
                            method, path, www_auth
                        )
                        req_headers.update(digest_headers)
                        _digest_attempted = True
                        conn.close()
                        continue

                content_encoding = resp_headers.get("content-encoding", "")

                if stream:
                    close_conn = False
                    return StreamingResponse._from_sync(
                        status,
                        resp_headers,
                        url,
                        resp,
                        conn,
                        content_encoding=content_encoding,
                    )

                resp_body = resp.read()
                if content_encoding:
                    resp_body = _decompress_body(resp_body, content_encoding)
                return Response(status, resp_headers, resp_body, url)
            finally:
                if close_conn:
                    if (
                        _pool
                        and not proxy
                        and not stream
                        and resp_headers.get("connection", "").lower() != "close"
                    ):
                        _pool.release(host, port, is_https, conn)
                    else:
                        conn.close()

        except (OSError, http.client.HTTPException) as exc:
            raise ConnectionError(f"Connection to {host}:{port} failed: {exc}") from exc
        except TimeoutError:
            raise
        except Exception as exc:
            if "timed out" in str(exc).lower():
                msg = f"Request to {url} timed out after {timeout}s"
                raise TimeoutError(msg) from exc
            raise


# ── Async helpers ──


async def _async_read_response_headers(
    reader: asyncio.StreamReader,
    timeout: float,
) -> tuple[int, dict[str, str]]:
    """Read HTTP status line and headers from an asyncio StreamReader.

    Does NOT consume the body — the reader is left positioned at the
    start of the response body.

    Returns:
        (status_code, headers_dict).
    """
    # Status line: "HTTP/1.1 200 OK\r\n"
    status_line = await asyncio.wait_for(reader.readline(), timeout=timeout)
    status_str = status_line.decode("latin-1").rstrip("\r\n")
    parts = status_str.split(" ", 2)
    if len(parts) < 2:
        raise ConnectionError(f"Malformed status line: {status_str}")
    status_code = int(parts[1])

    # Headers until empty line
    headers: dict[str, str] = {}
    while True:
        line = await asyncio.wait_for(reader.readline(), timeout=timeout)
        decoded = line.decode("latin-1").rstrip("\r\n")
        if not decoded:
            break
        if ":" in decoded:
            k, v = decoded.split(":", 1)
            headers[k.strip().lower()] = v.strip()

    return status_code, headers


async def _async_read_chunked_body(
    reader: asyncio.StreamReader,
    timeout: float,
) -> bytes:
    """Read a chunked transfer-encoded body from an asyncio StreamReader."""
    parts: list[bytes] = []
    while True:
        size_line = await asyncio.wait_for(reader.readline(), timeout=timeout)
        size_str = size_line.decode("latin-1").split(";")[0].strip()
        if not size_str:
            break
        chunk_size = int(size_str, 16)
        if chunk_size == 0:
            await asyncio.wait_for(reader.readline(), timeout=timeout)  # trailing \r\n
            break
        data = await asyncio.wait_for(reader.readexactly(chunk_size), timeout=timeout)
        await asyncio.wait_for(reader.readline(), timeout=timeout)  # trailing \r\n
        parts.append(data)
    return b"".join(parts)


async def _async_read_body(
    reader: asyncio.StreamReader,
    headers: dict[str, str],
    timeout: float,
) -> bytes:
    """Read the response body based on Content-Length or Transfer-Encoding.

    Falls back to reading until EOF when neither header is present.
    """
    te = headers.get("transfer-encoding", "")
    if te.lower() == "chunked":
        return await _async_read_chunked_body(reader, timeout)

    cl = headers.get("content-length")
    if cl is not None:
        length = int(cl)
        if length == 0:
            return b""
        return await asyncio.wait_for(reader.readexactly(length), timeout=timeout)

    # No Content-Length, no chunked — read until EOF
    return await asyncio.wait_for(reader.read(), timeout=timeout)


# ── Async implementation (asyncio streams) ──


async def _async_request(
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    data: bytes | str | dict[str, str] | None = None,
    json: Any = None,
    files: dict[str, Any] | list[tuple[str, Any]] | None = None,
    params: dict[str, Any] | None = None,
    timeout: float = DEFAULT_TIMEOUT,
    max_redirects: int = DEFAULT_MAX_REDIRECTS,
    verify: bool = True,
    stream: bool = False,
    auth: tuple[str, str] | Auth | None = None,
    proxy: str | None = None,
    _pool: _AsyncConnectionPool | None = None,
) -> Response | StreamingResponse:
    """Perform an asynchronous HTTP request using asyncio streams."""
    url = _build_url(url, params)
    body, content_type = _prepare_body(data, json, files)

    req_headers: dict[str, str] = {"User-Agent": DEFAULT_USER_AGENT}
    req_headers["Accept-Encoding"] = "gzip, deflate"
    if content_type:
        req_headers["Content-Type"] = content_type
    if body is not None:
        req_headers["Content-Length"] = str(len(body))
    req_headers.update(headers or {})

    auth_obj = _normalize_auth(auth)
    if isinstance(auth_obj, BasicAuth):
        req_headers.update(auth_obj.auth_headers(method, url))

    redirects = 0
    _digest_attempted = False
    while True:
        scheme, host, port, path, is_https = _parse_url(url)

        reader: asyncio.StreamReader | None = None
        writer: asyncio.StreamWriter | None = None

        try:
            if proxy:
                proxy_host, proxy_port, proxy_user, proxy_pass = _parse_proxy(proxy)
                if not is_https:
                    reader, writer = await asyncio.wait_for(
                        asyncio.open_connection(proxy_host, proxy_port),
                        timeout=timeout,
                    )
                    request_path = url
                    if proxy_user and proxy_pass:
                        req_headers["Proxy-Authorization"] = _proxy_auth_header(
                            proxy_user, proxy_pass
                        )
                else:
                    # CONNECT tunnel for HTTPS through proxy
                    proxy_reader, proxy_writer = await asyncio.wait_for(
                        asyncio.open_connection(proxy_host, proxy_port),
                        timeout=timeout,
                    )
                    connect_line = f"CONNECT {host}:{port} HTTP/1.1\r\n"
                    connect_headers = f"Host: {host}:{port}\r\n"
                    if proxy_user and proxy_pass:
                        connect_headers += (
                            f"Proxy-Authorization: "
                            f"{_proxy_auth_header(proxy_user, proxy_pass)}\r\n"
                        )
                    connect_headers += "\r\n"
                    proxy_writer.write(
                        (connect_line + connect_headers).encode("latin-1")
                    )
                    await asyncio.wait_for(proxy_writer.drain(), timeout=timeout)
                    tunnel_status, _ = await _async_read_response_headers(
                        proxy_reader, timeout
                    )
                    if tunnel_status != 200:
                        proxy_writer.close()
                        try:
                            await proxy_writer.wait_closed()
                        except Exception:
                            pass
                        raise ConnectionError(f"CONNECT tunnel failed: {tunnel_status}")
                    # Upgrade to TLS over the tunnel
                    if verify:
                        ctx = ssl.create_default_context()
                    else:
                        ctx = ssl._create_unverified_context()
                    loop = asyncio.get_event_loop()
                    transport = proxy_writer.transport
                    new_transport = await loop.start_tls(
                        transport, transport.get_protocol(), ctx, server_hostname=host
                    )
                    reader = proxy_reader
                    writer = proxy_writer
                    writer._transport = new_transport  # type: ignore[attr-defined]
                    request_path = path
            elif _pool:
                result = await _pool.acquire(host, port, is_https, timeout, verify)
                if result is not None:
                    reader, writer = result
                    req_headers["Connection"] = "keep-alive"
                    request_path = path
                else:
                    request_path = path
            else:
                request_path = path

            if reader is None or writer is None:
                if is_https:
                    if verify:
                        ctx = ssl.create_default_context()
                    else:
                        ctx = ssl._create_unverified_context()
                else:
                    ctx = None
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(host, port, ssl=ctx),
                    timeout=timeout,
                )
        except asyncio.TimeoutError:
            msg = f"Connection to {host}:{port} timed out after {timeout}s"
            raise TimeoutError(msg)
        except OSError as exc:
            raise ConnectionError(f"Connection to {host}:{port} failed: {exc}") from exc

        if _pool and not proxy:
            req_headers.setdefault("Connection", "keep-alive")

        close_writer = True
        resp_headers: dict[str, str] = {}
        try:
            # Build raw HTTP/1.1 request
            request_line = f"{method} {request_path} HTTP/1.1\r\n"
            header_lines = f"Host: {host}\r\n"
            for k, v in req_headers.items():
                header_lines += f"{k}: {v}\r\n"
            if not _pool or proxy:
                header_lines += "Connection: close\r\n"
            header_lines += "\r\n"

            raw_request = (request_line + header_lines).encode("latin-1")
            writer.write(raw_request)
            if body:
                writer.write(body)
            await asyncio.wait_for(writer.drain(), timeout=timeout)

            # Read response headers
            status, resp_headers = await _async_read_response_headers(reader, timeout)

            # Handle redirects
            if status in (301, 302, 303, 307, 308) and "location" in resp_headers:
                await _async_read_body(reader, resp_headers, timeout)
                redirects += 1
                if redirects > max_redirects:
                    raise TooManyRedirects(url, max_redirects)
                location = resp_headers["location"]
                if location.startswith("/"):
                    url = f"{scheme}://{host}:{port}{location}"
                else:
                    url = location
                if status == 303 or (status in (301, 302) and method == "POST"):
                    method = "GET"
                    body = None
                    req_headers.pop("Content-Type", None)
                    req_headers.pop("Content-Length", None)
                continue

            # Digest auth retry
            if (
                isinstance(auth_obj, DigestAuth)
                and status == 401
                and not _digest_attempted
            ):
                www_auth = resp_headers.get("www-authenticate", "")
                if www_auth.lower().startswith("digest"):
                    await _async_read_body(reader, resp_headers, timeout)
                    digest_headers = auth_obj.auth_headers_from_challenge(
                        method, path, www_auth
                    )
                    req_headers.update(digest_headers)
                    _digest_attempted = True
                    continue

            content_encoding = resp_headers.get("content-encoding", "")

            if stream:
                # Return streaming response — don't close writer
                close_writer = False
                te = resp_headers.get("transfer-encoding", "")
                is_chunked = te.lower() == "chunked"
                cl = resp_headers.get("content-length")
                content_length = int(cl) if cl else None
                return StreamingResponse._from_async(
                    status,
                    resp_headers,
                    url,
                    reader,
                    writer,
                    is_chunked,
                    content_length,
                    timeout,
                    content_encoding=content_encoding,
                )

            # Non-streaming: read body based on Content-Length / chunked
            resp_body = await _async_read_body(reader, resp_headers, timeout)
            if content_encoding:
                resp_body = _decompress_body(resp_body, content_encoding)
            return Response(status, resp_headers, resp_body, url)
        except asyncio.TimeoutError:
            raise TimeoutError(f"Request to {url} timed out after {timeout}s")
        finally:
            if close_writer:
                if (
                    _pool
                    and not proxy
                    and not stream
                    and resp_headers.get("connection", "").lower() != "close"
                ):
                    await _pool.release(host, port, is_https, reader, writer)
                else:
                    writer.close()
                    try:
                        await writer.wait_closed()
                    except Exception:
                        pass


# ── Sync convenience functions ──


def get(url: str, **kwargs: Any) -> Response | StreamingResponse:
    """Send a GET request."""
    return _sync_request("GET", url, **kwargs)


def post(url: str, **kwargs: Any) -> Response | StreamingResponse:
    """Send a POST request."""
    return _sync_request("POST", url, **kwargs)


def put(url: str, **kwargs: Any) -> Response | StreamingResponse:
    """Send a PUT request."""
    return _sync_request("PUT", url, **kwargs)


def patch(url: str, **kwargs: Any) -> Response | StreamingResponse:
    """Send a PATCH request."""
    return _sync_request("PATCH", url, **kwargs)


def delete(url: str, **kwargs: Any) -> Response | StreamingResponse:
    """Send a DELETE request."""
    return _sync_request("DELETE", url, **kwargs)


def head(url: str, **kwargs: Any) -> Response | StreamingResponse:
    """Send a HEAD request."""
    return _sync_request("HEAD", url, **kwargs)


def options(url: str, **kwargs: Any) -> Response | StreamingResponse:
    """Send an OPTIONS request."""
    return _sync_request("OPTIONS", url, **kwargs)


# ── Async convenience functions ──


async def async_get(url: str, **kwargs: Any) -> Response | StreamingResponse:
    """Send an async GET request."""
    return await _async_request("GET", url, **kwargs)


async def async_post(url: str, **kwargs: Any) -> Response | StreamingResponse:
    """Send an async POST request."""
    return await _async_request("POST", url, **kwargs)


async def async_put(url: str, **kwargs: Any) -> Response | StreamingResponse:
    """Send an async PUT request."""
    return await _async_request("PUT", url, **kwargs)


async def async_patch(url: str, **kwargs: Any) -> Response | StreamingResponse:
    """Send an async PATCH request."""
    return await _async_request("PATCH", url, **kwargs)


async def async_delete(url: str, **kwargs: Any) -> Response | StreamingResponse:
    """Send an async DELETE request."""
    return await _async_request("DELETE", url, **kwargs)


async def async_head(url: str, **kwargs: Any) -> Response | StreamingResponse:
    """Send an async HEAD request."""
    return await _async_request("HEAD", url, **kwargs)


async def async_options(url: str, **kwargs: Any) -> Response | StreamingResponse:
    """Send an async OPTIONS request."""
    return await _async_request("OPTIONS", url, **kwargs)


# ── Session classes ──


class Client:
    """Synchronous HTTP client session with connection pooling.

    Thread-safe: uses a threading.Lock internally.

    Usage::

        with Client(headers={"Authorization": "Bearer token"}) as c:
            r = c.get("https://api.example.com/data")
    """

    def __init__(
        self,
        *,
        headers: dict[str, str] | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_redirects: int = DEFAULT_MAX_REDIRECTS,
        verify: bool = True,
        auth: tuple[str, str] | Auth | None = None,
        proxy: str | None = None,
        pool_size: int = DEFAULT_POOL_SIZE,
    ) -> None:
        self._base_headers = headers or {}
        self._timeout = timeout
        self._max_redirects = max_redirects
        self._verify = verify
        self._auth = auth
        self._proxy = proxy
        self._pool = _SyncConnectionPool(pool_size)
        self._lock = threading.Lock()

    def request(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> Response | StreamingResponse:
        """Send an HTTP request."""
        kwargs.setdefault("timeout", self._timeout)
        kwargs.setdefault("max_redirects", self._max_redirects)
        kwargs.setdefault("verify", self._verify)
        kwargs.setdefault("auth", self._auth)
        kwargs.setdefault("proxy", self._proxy)
        kwargs["_pool"] = self._pool
        kwargs["headers"] = _merge_headers(self._base_headers, kwargs.get("headers"))
        if kwargs.get("stream"):
            return _sync_request(method, url, **kwargs)
        with self._lock:
            return _sync_request(method, url, **kwargs)

    def get(self, url: str, **kwargs: Any) -> Response | StreamingResponse:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> Response | StreamingResponse:
        return self.request("POST", url, **kwargs)

    def put(self, url: str, **kwargs: Any) -> Response | StreamingResponse:
        return self.request("PUT", url, **kwargs)

    def patch(self, url: str, **kwargs: Any) -> Response | StreamingResponse:
        return self.request("PATCH", url, **kwargs)

    def delete(self, url: str, **kwargs: Any) -> Response | StreamingResponse:
        return self.request("DELETE", url, **kwargs)

    def head(self, url: str, **kwargs: Any) -> Response | StreamingResponse:
        return self.request("HEAD", url, **kwargs)

    def options(self, url: str, **kwargs: Any) -> Response | StreamingResponse:
        return self.request("OPTIONS", url, **kwargs)

    def close(self) -> None:
        """Close all pooled connections."""
        self._pool.close_all()

    def __enter__(self) -> Client:
        return self

    def __exit__(self, *args: Any) -> None:
        self._pool.close_all()


class AsyncClient:
    """Asynchronous HTTP client session with connection pooling.

    Safe to use from a single asyncio task; for concurrent requests
    from the same client, use asyncio.Lock internally.

    Usage::

        async with AsyncClient(headers={"Authorization": "Bearer token"}) as c:
            r = await c.get("https://api.example.com/data")
    """

    def __init__(
        self,
        *,
        headers: dict[str, str] | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_redirects: int = DEFAULT_MAX_REDIRECTS,
        verify: bool = True,
        auth: tuple[str, str] | Auth | None = None,
        proxy: str | None = None,
        pool_size: int = DEFAULT_POOL_SIZE,
    ) -> None:
        self._base_headers = headers or {}
        self._timeout = timeout
        self._max_redirects = max_redirects
        self._verify = verify
        self._auth = auth
        self._proxy = proxy
        self._pool = _AsyncConnectionPool(pool_size)
        self._lock = asyncio.Lock()

    async def request(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> Response | StreamingResponse:
        """Send an async HTTP request."""
        kwargs.setdefault("timeout", self._timeout)
        kwargs.setdefault("max_redirects", self._max_redirects)
        kwargs.setdefault("verify", self._verify)
        kwargs.setdefault("auth", self._auth)
        kwargs.setdefault("proxy", self._proxy)
        kwargs["_pool"] = self._pool
        kwargs["headers"] = _merge_headers(self._base_headers, kwargs.get("headers"))
        if kwargs.get("stream"):
            return await _async_request(method, url, **kwargs)
        async with self._lock:
            return await _async_request(method, url, **kwargs)

    async def get(self, url: str, **kwargs: Any) -> Response | StreamingResponse:
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs: Any) -> Response | StreamingResponse:
        return await self.request("POST", url, **kwargs)

    async def put(self, url: str, **kwargs: Any) -> Response | StreamingResponse:
        return await self.request("PUT", url, **kwargs)

    async def patch(self, url: str, **kwargs: Any) -> Response | StreamingResponse:
        return await self.request("PATCH", url, **kwargs)

    async def delete(self, url: str, **kwargs: Any) -> Response | StreamingResponse:
        return await self.request("DELETE", url, **kwargs)

    async def head(self, url: str, **kwargs: Any) -> Response | StreamingResponse:
        return await self.request("HEAD", url, **kwargs)

    async def options(self, url: str, **kwargs: Any) -> Response | StreamingResponse:
        return await self.request("OPTIONS", url, **kwargs)

    async def aclose(self) -> None:
        """Close all pooled connections."""
        await self._pool.close_all()

    async def __aenter__(self) -> AsyncClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self._pool.close_all()
