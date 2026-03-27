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
import http.client
import json as _json
import os
import ssl
import threading
import warnings
from collections.abc import AsyncIterator, Iterator
from typing import IO, Any
from urllib.parse import quote, urlencode, urlparse

# ── Defaults ──

DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_REDIRECTS = 10
DEFAULT_USER_AGENT = "zerodep-http/0.1"


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
    ) -> "StreamingResponse":
        obj = object.__new__(cls)
        obj.status_code = status_code
        obj.headers = headers
        obj.url = url
        obj._encoding = _guess_encoding_from_headers(headers)
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
    ) -> "StreamingResponse":
        obj = object.__new__(cls)
        obj.status_code = status_code
        obj.headers = headers
        obj.url = url
        obj._encoding = _guess_encoding_from_headers(headers)
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
                yield chunk
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
                    yield data
            else:
                while True:
                    data = await asyncio.wait_for(
                        self._async_reader.read(chunk_size),
                        timeout=self._async_timeout,
                    )
                    if not data:
                        break
                    yield data
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
) -> Response | StreamingResponse:
    """Perform a synchronous HTTP request."""
    url = _build_url(url, params)
    body, content_type = _prepare_body(data, json, files)

    req_headers: dict[str, str] = {"User-Agent": DEFAULT_USER_AGENT}
    if content_type:
        req_headers["Content-Type"] = content_type
    if body is not None:
        req_headers["Content-Length"] = str(len(body))
    req_headers.update(headers or {})

    redirects = 0
    while True:
        scheme, host, port, path, is_https = _parse_url(url)

        close_conn = True
        try:
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

            try:
                conn.request(method, path, body=body, headers=req_headers)
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

                if stream:
                    close_conn = False
                    return StreamingResponse._from_sync(
                        status, resp_headers, url, resp, conn
                    )

                resp_body = resp.read()
                return Response(status, resp_headers, resp_body, url)
            finally:
                if close_conn:
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
) -> Response | StreamingResponse:
    """Perform an asynchronous HTTP request using asyncio streams."""
    url = _build_url(url, params)
    body, content_type = _prepare_body(data, json, files)

    req_headers: dict[str, str] = {"User-Agent": DEFAULT_USER_AGENT}
    if content_type:
        req_headers["Content-Type"] = content_type
    if body is not None:
        req_headers["Content-Length"] = str(len(body))
    req_headers.update(headers or {})

    redirects = 0
    while True:
        scheme, host, port, path, is_https = _parse_url(url)

        try:
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

        close_writer = True
        try:
            # Build raw HTTP/1.1 request
            request_line = f"{method} {path} HTTP/1.1\r\n"
            header_lines = f"Host: {host}\r\n"
            for k, v in req_headers.items():
                header_lines += f"{k}: {v}\r\n"
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
                )

            # Non-streaming: read body based on Content-Length / chunked
            resp_body = await _async_read_body(reader, resp_headers, timeout)
            return Response(status, resp_headers, resp_body, url)
        except asyncio.TimeoutError:
            raise TimeoutError(f"Request to {url} timed out after {timeout}s")
        finally:
            if close_writer:
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
    """Synchronous HTTP client session.

    Thread-safe: uses a threading.Lock internally. Each request creates
    a new connection (no connection pooling).

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
    ) -> None:
        self._base_headers = headers or {}
        self._timeout = timeout
        self._max_redirects = max_redirects
        self._verify = verify
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

    def __enter__(self) -> Client:
        return self

    def __exit__(self, *args: Any) -> None:
        pass


class AsyncClient:
    """Asynchronous HTTP client session.

    Each request creates a new connection (no connection pooling).
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
    ) -> None:
        self._base_headers = headers or {}
        self._timeout = timeout
        self._max_redirects = max_redirects
        self._verify = verify
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

    async def __aenter__(self) -> AsyncClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        pass
