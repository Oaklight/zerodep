"""Zero-dependency sync + async HTTP REST client.

Part of zerodep: https://github.com/Oaklight/zerodep
Copyright (c) 2026 Peng Ding. MIT License.

Sync (http.client) and async (asyncio streams) HTTP/1.1 client
for REST API consumption. Thread-safe by design.

Sync usage:
    >>> response = get("https://httpbin.org/get")
    >>> response.json()

Async usage:
    >>> response = await async_get("https://httpbin.org/get")
    >>> response.json()

Session usage:
    >>> with Client() as client:
    ...     r = client.get("https://httpbin.org/get")

    >>> async with AsyncClient() as client:
    ...     r = await client.get("https://httpbin.org/get")
"""

from __future__ import annotations

import asyncio
import http.client
import json as _json
import ssl
import threading
from typing import Any
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
        ct = self.headers.get("content-type", "")
        for part in ct.split(";"):
            part = part.strip()
            if part.startswith("charset="):
                return part[8:].strip().strip('"')
        return "utf-8"

    def __repr__(self) -> str:
        return f"<Response [{self.status_code}]>"


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
    data: bytes | str | None = None,
    json: Any = None,
) -> tuple[bytes | None, str | None]:
    """Prepare request body and content-type header.

    Returns:
        (body_bytes, content_type) tuple.
    """
    if json is not None:
        return _json.dumps(json, ensure_ascii=False).encode("utf-8"), "application/json"
    if isinstance(data, str):
        return data.encode("utf-8"), "application/x-www-form-urlencoded"
    if isinstance(data, bytes):
        return data, "application/octet-stream"
    return None, None


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
    data: bytes | str | None = None,
    json: Any = None,
    params: dict[str, Any] | None = None,
    timeout: float = DEFAULT_TIMEOUT,
    max_redirects: int = DEFAULT_MAX_REDIRECTS,
    verify: bool = True,
) -> Response:
    """Perform a synchronous HTTP request."""
    url = _build_url(url, params)
    body, content_type = _prepare_body(data, json)

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
                conn = http.client.HTTPSConnection(
                    host, port, timeout=timeout, context=ctx
                )
            else:
                conn = http.client.HTTPConnection(host, port, timeout=timeout)

            try:
                conn.request(method, path, body=body, headers=req_headers)
                resp = conn.getresponse()
                resp_headers = {k.lower(): v for k, v in resp.getheaders()}
                resp_body = resp.read()
                status = resp.status
            finally:
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

        # Handle redirects
        if status in (301, 302, 303, 307, 308) and "location" in resp_headers:
            redirects += 1
            if redirects > max_redirects:
                raise TooManyRedirects(url, max_redirects)
            location = resp_headers["location"]
            if location.startswith("/"):
                url = f"{scheme}://{host}:{port}{location}"
            else:
                url = location
            # 303: always GET after redirect; 301/302: convert POST to GET
            if status == 303 or (status in (301, 302) and method == "POST"):
                method = "GET"
                body = None
                req_headers.pop("Content-Type", None)
                req_headers.pop("Content-Length", None)
            continue

        return Response(status, resp_headers, resp_body, url)


# ── Async implementation (asyncio streams) ──


async def _async_request(
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    data: bytes | str | None = None,
    json: Any = None,
    params: dict[str, Any] | None = None,
    timeout: float = DEFAULT_TIMEOUT,
    max_redirects: int = DEFAULT_MAX_REDIRECTS,
    verify: bool = True,
) -> Response:
    """Perform an asynchronous HTTP request using asyncio streams."""
    url = _build_url(url, params)
    body, content_type = _prepare_body(data, json)

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

            # Read response
            raw_response = await asyncio.wait_for(
                reader.read(1024 * 1024 * 10),  # 10 MB max
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            raise TimeoutError(f"Request to {url} timed out after {timeout}s")
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass

        # Parse response
        status, resp_headers, resp_body = _parse_raw_response(raw_response)

        # Handle redirects
        if status in (301, 302, 303, 307, 308) and "location" in resp_headers:
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

        return Response(status, resp_headers, resp_body, url)


def _parse_raw_response(
    raw: bytes,
) -> tuple[int, dict[str, str], bytes]:
    """Parse raw HTTP/1.1 response bytes.

    Returns:
        (status_code, headers_dict, body_bytes).
    """
    # Split headers from body
    header_end = raw.find(b"\r\n\r\n")
    if header_end == -1:
        raise ConnectionError("Malformed HTTP response: no header terminator")

    header_section = raw[:header_end].decode("latin-1")
    body_section = raw[header_end + 4 :]

    lines = header_section.split("\r\n")
    # Parse status line: "HTTP/1.1 200 OK"
    status_line = lines[0]
    parts = status_line.split(" ", 2)
    if len(parts) < 2:
        raise ConnectionError(f"Malformed status line: {status_line}")
    status_code = int(parts[1])

    # Parse headers
    headers: dict[str, str] = {}
    for line in lines[1:]:
        if ":" in line:
            k, v = line.split(":", 1)
            headers[k.strip().lower()] = v.strip()

    # Handle chunked transfer encoding
    if headers.get("transfer-encoding", "").lower() == "chunked":
        body_section = _decode_chunked(body_section)

    return status_code, headers, body_section


def _decode_chunked(data: bytes) -> bytes:
    """Decode chunked transfer encoding."""
    result = bytearray()
    pos = 0
    while pos < len(data):
        # Find end of chunk size line
        line_end = data.find(b"\r\n", pos)
        if line_end == -1:
            break
        # Parse chunk size (hex)
        size_str = data[pos:line_end].decode("latin-1").split(";")[0].strip()
        if not size_str:
            break
        chunk_size = int(size_str, 16)
        if chunk_size == 0:
            break
        # Extract chunk data
        chunk_start = line_end + 2
        chunk_end = chunk_start + chunk_size
        if chunk_end > len(data):
            result.extend(data[chunk_start:])
            break
        result.extend(data[chunk_start:chunk_end])
        pos = chunk_end + 2  # skip trailing \r\n
    return bytes(result)


# ── Sync convenience functions ──


def get(url: str, **kwargs: Any) -> Response:
    """Send a GET request."""
    return _sync_request("GET", url, **kwargs)


def post(url: str, **kwargs: Any) -> Response:
    """Send a POST request."""
    return _sync_request("POST", url, **kwargs)


def put(url: str, **kwargs: Any) -> Response:
    """Send a PUT request."""
    return _sync_request("PUT", url, **kwargs)


def patch(url: str, **kwargs: Any) -> Response:
    """Send a PATCH request."""
    return _sync_request("PATCH", url, **kwargs)


def delete(url: str, **kwargs: Any) -> Response:
    """Send a DELETE request."""
    return _sync_request("DELETE", url, **kwargs)


def head(url: str, **kwargs: Any) -> Response:
    """Send a HEAD request."""
    return _sync_request("HEAD", url, **kwargs)


def options(url: str, **kwargs: Any) -> Response:
    """Send an OPTIONS request."""
    return _sync_request("OPTIONS", url, **kwargs)


# ── Async convenience functions ──


async def async_get(url: str, **kwargs: Any) -> Response:
    """Send an async GET request."""
    return await _async_request("GET", url, **kwargs)


async def async_post(url: str, **kwargs: Any) -> Response:
    """Send an async POST request."""
    return await _async_request("POST", url, **kwargs)


async def async_put(url: str, **kwargs: Any) -> Response:
    """Send an async PUT request."""
    return await _async_request("PUT", url, **kwargs)


async def async_patch(url: str, **kwargs: Any) -> Response:
    """Send an async PATCH request."""
    return await _async_request("PATCH", url, **kwargs)


async def async_delete(url: str, **kwargs: Any) -> Response:
    """Send an async DELETE request."""
    return await _async_request("DELETE", url, **kwargs)


async def async_head(url: str, **kwargs: Any) -> Response:
    """Send an async HEAD request."""
    return await _async_request("HEAD", url, **kwargs)


async def async_options(url: str, **kwargs: Any) -> Response:
    """Send an async OPTIONS request."""
    return await _async_request("OPTIONS", url, **kwargs)


# ── Session classes ──


class Client:
    """Synchronous HTTP client session.

    Thread-safe: uses a threading.Lock internally. Each request creates
    a new connection (no connection pooling).

    Usage:
        >>> with Client(headers={"Authorization": "Bearer token"}) as c:
        ...     r = c.get("https://api.example.com/data")
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
    ) -> Response:
        """Send an HTTP request."""
        kwargs.setdefault("timeout", self._timeout)
        kwargs.setdefault("max_redirects", self._max_redirects)
        kwargs.setdefault("verify", self._verify)
        kwargs["headers"] = _merge_headers(self._base_headers, kwargs.get("headers"))
        with self._lock:
            return _sync_request(method, url, **kwargs)

    def get(self, url: str, **kwargs: Any) -> Response:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> Response:
        return self.request("POST", url, **kwargs)

    def put(self, url: str, **kwargs: Any) -> Response:
        return self.request("PUT", url, **kwargs)

    def patch(self, url: str, **kwargs: Any) -> Response:
        return self.request("PATCH", url, **kwargs)

    def delete(self, url: str, **kwargs: Any) -> Response:
        return self.request("DELETE", url, **kwargs)

    def head(self, url: str, **kwargs: Any) -> Response:
        return self.request("HEAD", url, **kwargs)

    def options(self, url: str, **kwargs: Any) -> Response:
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

    Usage:
        >>> async with AsyncClient(headers={"Authorization": "Bearer token"}) as c:
        ...     r = await c.get("https://api.example.com/data")
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
    ) -> Response:
        """Send an async HTTP request."""
        kwargs.setdefault("timeout", self._timeout)
        kwargs.setdefault("max_redirects", self._max_redirects)
        kwargs.setdefault("verify", self._verify)
        kwargs["headers"] = _merge_headers(self._base_headers, kwargs.get("headers"))
        async with self._lock:
            return await _async_request(method, url, **kwargs)

    async def get(self, url: str, **kwargs: Any) -> Response:
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs: Any) -> Response:
        return await self.request("POST", url, **kwargs)

    async def put(self, url: str, **kwargs: Any) -> Response:
        return await self.request("PUT", url, **kwargs)

    async def patch(self, url: str, **kwargs: Any) -> Response:
        return await self.request("PATCH", url, **kwargs)

    async def delete(self, url: str, **kwargs: Any) -> Response:
        return await self.request("DELETE", url, **kwargs)

    async def head(self, url: str, **kwargs: Any) -> Response:
        return await self.request("HEAD", url, **kwargs)

    async def options(self, url: str, **kwargs: Any) -> Response:
        return await self.request("OPTIONS", url, **kwargs)

    async def __aenter__(self) -> AsyncClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        pass
