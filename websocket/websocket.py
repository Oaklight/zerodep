# /// zerodep
# version = "0.1.0"
# deps = []
# tier = "medium"
# category = "network"
# ///
"""Zero-dependency WebSocket client (RFC 6455).

Part of zerodep: https://github.com/Oaklight/zerodep
Copyright (c) 2026 Peng Ding. MIT License.

Provides sync and async WebSocket clients for ``ws://`` and ``wss://``
connections. Implements the core WebSocket protocol including text frames,
ping/pong, close handshake, and client-side masking.

Usage::

    # Sync
    from websocket import WebSocketClient

    with WebSocketClient("ws://localhost:9222/") as ws:
        ws.send("hello")
        response = ws.recv()
        print(response)

    # Async
    from websocket import AsyncWebSocketClient

    async with AsyncWebSocketClient("wss://example.com/ws") as ws:
        await ws.send('{"type": "subscribe"}')
        data = await ws.recv()
        print(data)

Requires Python 3.10+.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import logging
import os
import socket
import ssl
import struct
import urllib.parse

__all__ = [
    # Constants
    "DEFAULT_TIMEOUT",
    # Exceptions
    "WebSocketError",
    "WebSocketConnectionError",
    "WebSocketTimeoutError",
    "WebSocketProtocolError",
    # Clients
    "WebSocketClient",
    "AsyncWebSocketClient",
]

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────

DEFAULT_TIMEOUT: float = 30.0

_WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
_OPCODE_CONT = 0x0
_OPCODE_TEXT = 0x1
_OPCODE_BINARY = 0x2
_OPCODE_CLOSE = 0x8
_OPCODE_PING = 0x9
_OPCODE_PONG = 0xA
_MAX_PAYLOAD_SIZE = 2**23  # 8 MiB default max payload


# ── Exceptions ─────────────────────────────────────────────────────────────


class WebSocketError(Exception):
    """Base exception for all websocket operations."""


class WebSocketConnectionError(WebSocketError):
    """Raised on connection failures (TCP connect, handshake reject)."""

    def __init__(self, message: str, *, host: str = "", port: int = 0) -> None:
        self.host = host
        self.port = port
        super().__init__(message)


class WebSocketTimeoutError(WebSocketError):
    """Raised when an operation times out."""

    def __init__(self, message: str, *, url: str = "", timeout: float = 0.0) -> None:
        self.url = url
        self.timeout = timeout
        super().__init__(message)


class WebSocketProtocolError(WebSocketError):
    """Raised on protocol violations (bad frame, unexpected opcode)."""


# ── Shared protocol helpers (sync/async) ───────────────────────────────────


def _parse_ws_url(url: str) -> tuple[str, int, str, bool]:
    """Parse a WebSocket URL into (host, port, path, is_secure).

    Args:
        url: WebSocket URL (ws:// or wss://).

    Returns:
        Tuple of (host, port, resource_path, is_secure).

    Raises:
        ValueError: If the URL scheme is not ws or wss.
    """
    parsed = urllib.parse.urlparse(url)
    scheme = parsed.scheme.lower()
    if scheme not in ("ws", "wss"):
        raise ValueError(f"unsupported scheme: {scheme!r} (expected ws or wss)")
    is_secure = scheme == "wss"
    host = parsed.hostname or "localhost"
    default_port = 443 if is_secure else 80
    port = parsed.port or default_port
    path = parsed.path or "/"
    if parsed.query:
        path = f"{path}?{parsed.query}"
    return host, port, path, is_secure


def _make_ssl_context(verify: bool) -> ssl.SSLContext:
    """Create an SSL context based on verification setting."""
    if verify:
        return ssl.create_default_context()
    return ssl._create_unverified_context()


def _build_handshake_request(
    host: str,
    port: int,
    path: str,
    key: str,
    *,
    headers: dict[str, str] | None = None,
    subprotocols: list[str] | None = None,
    is_secure: bool = False,
) -> bytes:
    """Build the HTTP/1.1 WebSocket upgrade request.

    Args:
        host: Server hostname.
        port: Server port.
        path: Resource path.
        key: Base64-encoded 16-byte random key.
        headers: Optional extra headers to include.
        subprotocols: Optional list of subprotocols to negotiate.
        is_secure: Whether the connection uses TLS.

    Returns:
        The raw HTTP upgrade request as bytes.
    """
    default_port = 443 if is_secure else 80
    if port == default_port:
        host_header = host
    else:
        host_header = f"{host}:{port}"

    lines = [
        f"GET {path} HTTP/1.1",
        f"Host: {host_header}",
        "Upgrade: websocket",
        "Connection: Upgrade",
        f"Sec-WebSocket-Key: {key}",
        "Sec-WebSocket-Version: 13",
    ]
    if subprotocols:
        lines.append(f"Sec-WebSocket-Protocol: {', '.join(subprotocols)}")
    if headers:
        for k, v in headers.items():
            lines.append(f"{k}: {v}")
    lines.append("")
    lines.append("")
    return "\r\n".join(lines).encode("latin-1")


def _compute_accept_key(key: str) -> str:
    """Compute the expected Sec-WebSocket-Accept value."""
    digest = hashlib.sha1((key + _WS_GUID).encode("ascii")).digest()
    return base64.b64encode(digest).decode("ascii")


def _validate_handshake_response(data: bytes, key: str) -> dict[str, str]:
    """Parse and validate the HTTP upgrade response.

    Args:
        data: Raw HTTP response bytes (up to and including the blank line).
        key: The Sec-WebSocket-Key sent in the request.

    Returns:
        Parsed response headers (lowercase keys).

    Raises:
        WebSocketConnectionError: If the handshake fails validation.
    """
    try:
        text = data.decode("latin-1")
    except UnicodeDecodeError as exc:
        raise WebSocketConnectionError(
            "handshake response is not valid latin-1"
        ) from exc

    header_end = text.find("\r\n\r\n")
    if header_end < 0:
        raise WebSocketConnectionError("incomplete handshake response")
    header_block = text[: header_end + 2]  # include trailing \r\n

    lines = header_block.split("\r\n")
    if not lines:
        raise WebSocketConnectionError("empty handshake response")

    # Status line
    status_line = lines[0]
    parts = status_line.split(" ", 2)
    if len(parts) < 2:
        raise WebSocketConnectionError(f"malformed status line: {status_line!r}")
    try:
        status_code = int(parts[1])
    except ValueError:
        raise WebSocketConnectionError(f"non-integer status code: {parts[1]!r}")
    if status_code != 101:
        raise WebSocketConnectionError(
            f"server rejected upgrade with status {status_code}"
        )

    # Headers
    headers: dict[str, str] = {}
    for line in lines[1:]:
        if not line:
            continue
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        headers[k.strip().lower()] = v.strip()

    # Validate required headers
    upgrade = headers.get("upgrade", "")
    if upgrade.lower() != "websocket":
        raise WebSocketConnectionError(
            f"missing or invalid Upgrade header: {upgrade!r}"
        )
    connection = headers.get("connection", "")
    if "upgrade" not in connection.lower():
        raise WebSocketConnectionError(
            f"missing or invalid Connection header: {connection!r}"
        )
    expected_accept = _compute_accept_key(key)
    actual_accept = headers.get("sec-websocket-accept", "")
    if actual_accept != expected_accept:
        raise WebSocketConnectionError(
            f"Sec-WebSocket-Accept mismatch: "
            f"expected {expected_accept!r}, got {actual_accept!r}"
        )

    return headers


def _make_frame(opcode: int, payload: bytes, *, mask: bool = True) -> bytes:
    """Build a WebSocket frame.

    Args:
        opcode: Frame opcode (text, close, ping, pong, etc.).
        payload: Frame payload bytes.
        mask: Whether to apply client-side masking (required for client→server).

    Returns:
        The complete frame as bytes.
    """
    header = bytearray()
    # First byte: FIN=1, RSV=0, opcode
    header.append(0x80 | opcode)

    length = len(payload)
    mask_bit = 0x80 if mask else 0x00

    if length < 126:
        header.append(mask_bit | length)
    elif length < 65536:
        header.append(mask_bit | 126)
        header.extend(struct.pack(">H", length))
    else:
        header.append(mask_bit | 127)
        header.extend(struct.pack(">Q", length))

    if mask:
        mask_key = os.urandom(4)
        header.extend(mask_key)
        masked = _mask_payload(mask_key, payload)
        return bytes(header) + masked
    return bytes(header) + payload


def _mask_payload(mask_key: bytes, data: bytes) -> bytes:
    """Apply XOR masking to payload data.

    Args:
        mask_key: 4-byte mask key.
        data: Payload bytes to mask/unmask.

    Returns:
        Masked/unmasked payload bytes.
    """
    result = bytearray(len(data))
    for i, b in enumerate(data):
        result[i] = b ^ mask_key[i & 3]
    return bytes(result)


def _parse_frame_header(
    header_bytes: bytes,
) -> tuple[bool, int, bool, int]:
    """Parse the first 2 bytes of a WebSocket frame.

    Args:
        header_bytes: Exactly 2 bytes of frame header.

    Returns:
        Tuple of (fin, opcode, is_masked, payload_length_indicator).
    """
    b0 = header_bytes[0]
    b1 = header_bytes[1]
    fin = bool(b0 & 0x80)
    opcode = b0 & 0x0F
    is_masked = bool(b1 & 0x80)
    length = b1 & 0x7F
    return fin, opcode, is_masked, length


def _make_close_payload(code: int, reason: str) -> bytes:
    """Build the payload for a close frame.

    Args:
        code: Close status code (e.g. 1000 for normal closure).
        reason: Human-readable close reason.

    Returns:
        Close frame payload bytes.
    """
    payload = struct.pack(">H", code)
    if reason:
        payload += reason.encode("utf-8")
    return payload


# ── Sync WebSocket Client ──────────────────────────────────────────────────


class WebSocketClient:
    """Synchronous WebSocket client.

    Args:
        url: WebSocket URL (``ws://`` or ``wss://``).
        headers: Optional extra headers for the upgrade request.
        subprotocols: Optional list of subprotocols to negotiate.

    Example::

        with WebSocketClient("ws://localhost:9222/") as ws:
            ws.send("hello")
            print(ws.recv())
    """

    def __init__(
        self,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        subprotocols: list[str] | None = None,
    ) -> None:
        self._url = url
        self._headers = headers
        self._subprotocols = subprotocols
        self._host, self._port, self._path, self._is_secure = _parse_ws_url(url)
        self._sock: socket.socket | None = None
        self._connected = False
        self._closing = False
        self._accepted_subprotocol: str | None = None

    @property
    def connected(self) -> bool:
        """Whether the WebSocket connection is active."""
        return self._connected

    @property
    def accepted_subprotocol(self) -> str | None:
        """The subprotocol accepted by the server, if any."""
        return self._accepted_subprotocol

    def connect(
        self,
        *,
        timeout: float = DEFAULT_TIMEOUT,
        verify: bool = True,
    ) -> None:
        """Open the WebSocket connection.

        Args:
            timeout: Connection timeout in seconds.
            verify: Whether to verify TLS certificates (for ``wss://``).

        Raises:
            WebSocketConnectionError: If the TCP connection or handshake fails.
            WebSocketTimeoutError: If the connection times out.
        """
        if self._connected:
            return

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((self._host, self._port))

            if self._is_secure:
                ctx = _make_ssl_context(verify)
                sock = ctx.wrap_socket(sock, server_hostname=self._host)

            # Send upgrade request
            key = base64.b64encode(os.urandom(16)).decode("ascii")
            request = _build_handshake_request(
                self._host,
                self._port,
                self._path,
                key,
                headers=self._headers,
                subprotocols=self._subprotocols,
                is_secure=self._is_secure,
            )
            sock.sendall(request)

            # Read response until \r\n\r\n
            response = self._read_handshake_response(sock)
            resp_headers = _validate_handshake_response(response, key)

            # Check subprotocol
            if self._subprotocols:
                accepted = resp_headers.get("sec-websocket-protocol", "")
                if accepted:
                    self._accepted_subprotocol = accepted

            self._sock = sock
            self._connected = True
            self._closing = False

        except socket.timeout as exc:
            raise WebSocketTimeoutError(
                f"connection to {self._url} timed out after {timeout}s",
                url=self._url,
                timeout=timeout,
            ) from exc
        except OSError as exc:
            raise WebSocketConnectionError(
                f"failed to connect to {self._host}:{self._port}: {exc}",
                host=self._host,
                port=self._port,
            ) from exc

    def send(self, data: str) -> None:
        """Send a text message.

        Args:
            data: Text message to send.

        Raises:
            WebSocketError: If not connected.
        """
        self._ensure_connected()
        payload = data.encode("utf-8")
        frame = _make_frame(_OPCODE_TEXT, payload, mask=True)
        assert self._sock is not None
        self._sock.sendall(frame)

    def recv(self, *, timeout: float | None = None) -> str:
        """Receive a text message.

        Automatically handles ping frames by sending pong responses.
        Raises on close frames.

        Args:
            timeout: Receive timeout in seconds. ``None`` uses the socket's
                current timeout.

        Returns:
            The received text message.

        Raises:
            WebSocketTimeoutError: If the receive times out.
            WebSocketProtocolError: On protocol errors.
            WebSocketConnectionError: If the connection is closed.
        """
        self._ensure_connected()
        assert self._sock is not None
        old_timeout = self._sock.gettimeout()
        if timeout is not None:
            self._sock.settimeout(timeout)
        try:
            return self._recv_message()
        except socket.timeout as exc:
            raise WebSocketTimeoutError(
                f"recv timed out after {timeout}s",
                url=self._url,
                timeout=timeout or 0.0,
            ) from exc
        finally:
            if timeout is not None:
                self._sock.settimeout(old_timeout)

    def ping(self, data: bytes = b"") -> None:
        """Send a ping frame.

        Args:
            data: Optional ping payload (max 125 bytes).
        """
        self._ensure_connected()
        assert self._sock is not None
        frame = _make_frame(_OPCODE_PING, data, mask=True)
        self._sock.sendall(frame)

    def close(self, code: int = 1000, reason: str = "") -> None:
        """Close the WebSocket connection.

        Sends a close frame, waits for the server's close frame response,
        then closes the underlying socket.

        Args:
            code: Close status code (default 1000 for normal closure).
            reason: Human-readable close reason.
        """
        if not self._connected or self._sock is None:
            return

        try:
            if not self._closing:
                self._closing = True
                payload = _make_close_payload(code, reason)
                frame = _make_frame(_OPCODE_CLOSE, payload, mask=True)
                self._sock.sendall(frame)

                # Try to receive server's close frame
                old_timeout = self._sock.gettimeout()
                self._sock.settimeout(2.0)
                try:
                    while True:
                        opcode, _, _ = self._read_frame()
                        if opcode == _OPCODE_CLOSE:
                            break
                except (socket.timeout, WebSocketError, OSError):
                    pass
                finally:
                    try:
                        self._sock.settimeout(old_timeout)
                    except OSError:
                        pass
        except OSError:
            pass
        finally:
            self._shutdown()

    def __enter__(self) -> WebSocketClient:
        self.connect()
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    # ── Sync internal helpers ──

    def _ensure_connected(self) -> None:
        if not self._connected or self._sock is None:
            raise WebSocketError("not connected")

    def _shutdown(self) -> None:
        """Close the socket and reset state."""
        if self._sock is not None:
            try:
                self._sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None
        self._connected = False
        self._closing = False

    def _recv_message(self) -> str:
        """Read frames until a complete text message is received."""
        assert self._sock is not None
        while True:
            opcode, payload, fin = self._read_frame()

            if opcode == _OPCODE_TEXT:
                if not fin:
                    raise WebSocketProtocolError(
                        "fragmented messages are not supported"
                    )
                return payload.decode("utf-8")

            if opcode == _OPCODE_PING:
                pong = _make_frame(_OPCODE_PONG, payload, mask=True)
                self._sock.sendall(pong)
                continue

            if opcode == _OPCODE_PONG:
                continue

            if opcode == _OPCODE_CLOSE:
                close_code = 1005
                close_reason = ""
                if len(payload) >= 2:
                    close_code = struct.unpack(">H", payload[:2])[0]
                    close_reason = payload[2:].decode("utf-8", errors="replace")
                # Send close response if we didn't initiate
                if not self._closing:
                    self._closing = True
                    resp_payload = _make_close_payload(close_code, "")
                    resp_frame = _make_frame(_OPCODE_CLOSE, resp_payload, mask=True)
                    try:
                        self._sock.sendall(resp_frame)
                    except OSError:
                        pass
                self._shutdown()
                raise WebSocketConnectionError(
                    f"connection closed by server: {close_code} {close_reason}",
                    host=self._host,
                    port=self._port,
                )

            if opcode == _OPCODE_BINARY:
                raise WebSocketProtocolError("binary frames are not supported")

            raise WebSocketProtocolError(f"unexpected opcode: {opcode:#x}")

    def _read_frame(self) -> tuple[int, bytes, bool]:
        """Read a single WebSocket frame from the socket.

        Returns:
            Tuple of (opcode, payload, fin).
        """
        assert self._sock is not None
        header = _recv_exact(self._sock, 2)
        fin, opcode, is_masked, length = _parse_frame_header(header)

        # Extended payload length
        if length == 126:
            ext = _recv_exact(self._sock, 2)
            length = struct.unpack(">H", ext)[0]
        elif length == 127:
            ext = _recv_exact(self._sock, 8)
            length = struct.unpack(">Q", ext)[0]

        if length > _MAX_PAYLOAD_SIZE:
            raise WebSocketProtocolError(
                f"payload too large: {length} bytes (max {_MAX_PAYLOAD_SIZE})"
            )

        # Mask key (server should not mask, but handle it)
        mask_key = None
        if is_masked:
            mask_key = _recv_exact(self._sock, 4)

        # Payload
        payload = _recv_exact(self._sock, length) if length > 0 else b""
        if mask_key:
            payload = _mask_payload(mask_key, payload)

        return opcode, payload, fin

    @staticmethod
    def _read_handshake_response(sock: socket.socket) -> bytes:
        """Read the HTTP handshake response until \\r\\n\\r\\n."""
        buf = bytearray()
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                raise WebSocketConnectionError("connection closed during handshake")
            buf.extend(chunk)
            if b"\r\n\r\n" in buf:
                return bytes(buf)
            if len(buf) > 65536:
                raise WebSocketConnectionError("handshake response too large")


def _recv_exact(sock: socket.socket, n: int) -> bytes:
    """Read exactly *n* bytes from a socket, handling partial reads.

    Args:
        sock: Connected socket.
        n: Number of bytes to read.

    Returns:
        Exactly *n* bytes.

    Raises:
        WebSocketConnectionError: If the socket closes before *n* bytes arrive.
    """
    if n == 0:
        return b""
    buf = bytearray()
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise WebSocketConnectionError(
                f"connection closed: expected {n} bytes, got {len(buf)}"
            )
        buf.extend(chunk)
    return bytes(buf)


# ── Async WebSocket Client ─────────────────────────────────────────────────


class AsyncWebSocketClient:
    """Asynchronous WebSocket client.

    Args:
        url: WebSocket URL (``ws://`` or ``wss://``).
        headers: Optional extra headers for the upgrade request.
        subprotocols: Optional list of subprotocols to negotiate.

    Example::

        async with AsyncWebSocketClient("wss://example.com/ws") as ws:
            await ws.send("hello")
            print(await ws.recv())
    """

    def __init__(
        self,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        subprotocols: list[str] | None = None,
    ) -> None:
        self._url = url
        self._headers = headers
        self._subprotocols = subprotocols
        self._host, self._port, self._path, self._is_secure = _parse_ws_url(url)
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._connected = False
        self._closing = False
        self._accepted_subprotocol: str | None = None

    @property
    def connected(self) -> bool:
        """Whether the WebSocket connection is active."""
        return self._connected

    @property
    def accepted_subprotocol(self) -> str | None:
        """The subprotocol accepted by the server, if any."""
        return self._accepted_subprotocol

    async def connect(
        self,
        *,
        timeout: float = DEFAULT_TIMEOUT,
        verify: bool = True,
    ) -> None:
        """Open the WebSocket connection.

        Args:
            timeout: Connection timeout in seconds.
            verify: Whether to verify TLS certificates (for ``wss://``).

        Raises:
            WebSocketConnectionError: If the TCP connection or handshake fails.
            WebSocketTimeoutError: If the connection times out.
        """
        if self._connected:
            return

        try:
            ssl_ctx = _make_ssl_context(verify) if self._is_secure else None
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self._host, self._port, ssl=ssl_ctx),
                timeout=timeout,
            )

            # Send upgrade request
            key = base64.b64encode(os.urandom(16)).decode("ascii")
            request = _build_handshake_request(
                self._host,
                self._port,
                self._path,
                key,
                headers=self._headers,
                subprotocols=self._subprotocols,
                is_secure=self._is_secure,
            )
            writer.write(request)
            await writer.drain()

            # Read response until \r\n\r\n
            response = await asyncio.wait_for(
                self._async_read_handshake_response(reader),
                timeout=timeout,
            )
            resp_headers = _validate_handshake_response(response, key)

            # Check subprotocol
            if self._subprotocols:
                accepted = resp_headers.get("sec-websocket-protocol", "")
                if accepted:
                    self._accepted_subprotocol = accepted

            self._reader = reader
            self._writer = writer
            self._connected = True
            self._closing = False

        except asyncio.TimeoutError as exc:
            raise WebSocketTimeoutError(
                f"connection to {self._url} timed out after {timeout}s",
                url=self._url,
                timeout=timeout,
            ) from exc
        except OSError as exc:
            raise WebSocketConnectionError(
                f"failed to connect to {self._host}:{self._port}: {exc}",
                host=self._host,
                port=self._port,
            ) from exc

    async def send(self, data: str) -> None:
        """Send a text message.

        Args:
            data: Text message to send.

        Raises:
            WebSocketError: If not connected.
        """
        self._ensure_connected()
        assert self._writer is not None
        payload = data.encode("utf-8")
        frame = _make_frame(_OPCODE_TEXT, payload, mask=True)
        self._writer.write(frame)
        await self._writer.drain()

    async def recv(self, *, timeout: float | None = None) -> str:
        """Receive a text message.

        Automatically handles ping frames by sending pong responses.
        Raises on close frames.

        Args:
            timeout: Receive timeout in seconds. ``None`` waits indefinitely.

        Returns:
            The received text message.

        Raises:
            WebSocketTimeoutError: If the receive times out.
            WebSocketProtocolError: On protocol errors.
            WebSocketConnectionError: If the connection is closed.
        """
        self._ensure_connected()
        try:
            if timeout is not None:
                return await asyncio.wait_for(self._recv_message(), timeout=timeout)
            return await self._recv_message()
        except asyncio.TimeoutError as exc:
            raise WebSocketTimeoutError(
                f"recv timed out after {timeout}s",
                url=self._url,
                timeout=timeout or 0.0,
            ) from exc

    async def ping(self, data: bytes = b"") -> None:
        """Send a ping frame.

        Args:
            data: Optional ping payload (max 125 bytes).
        """
        self._ensure_connected()
        assert self._writer is not None
        frame = _make_frame(_OPCODE_PING, data, mask=True)
        self._writer.write(frame)
        await self._writer.drain()

    async def close(self, code: int = 1000, reason: str = "") -> None:
        """Close the WebSocket connection.

        Sends a close frame, waits for the server's close frame response,
        then closes the underlying transport.

        Args:
            code: Close status code (default 1000 for normal closure).
            reason: Human-readable close reason.
        """
        if not self._connected or self._writer is None:
            return

        try:
            if not self._closing:
                self._closing = True
                payload = _make_close_payload(code, reason)
                frame = _make_frame(_OPCODE_CLOSE, payload, mask=True)
                self._writer.write(frame)
                await self._writer.drain()

                # Try to receive server's close frame
                try:
                    while True:
                        opcode, _, _ = await asyncio.wait_for(
                            self._read_frame(), timeout=2.0
                        )
                        if opcode == _OPCODE_CLOSE:
                            break
                except (asyncio.TimeoutError, WebSocketError, OSError):
                    pass
        except OSError:
            pass
        finally:
            await self._shutdown()

    async def __aenter__(self) -> AsyncWebSocketClient:
        await self.connect()
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()

    # ── Async internal helpers ──

    def _ensure_connected(self) -> None:
        if not self._connected or self._reader is None or self._writer is None:
            raise WebSocketError("not connected")

    async def _shutdown(self) -> None:
        """Close the transport and reset state."""
        if self._writer is not None:
            try:
                self._writer.close()
                await self._writer.wait_closed()
            except OSError:
                pass
            self._writer = None
        self._reader = None
        self._connected = False
        self._closing = False

    async def _recv_message(self) -> str:
        """Read frames until a complete text message is received."""
        assert self._writer is not None
        while True:
            opcode, payload, fin = await self._read_frame()

            if opcode == _OPCODE_TEXT:
                if not fin:
                    raise WebSocketProtocolError(
                        "fragmented messages are not supported"
                    )
                return payload.decode("utf-8")

            if opcode == _OPCODE_PING:
                pong = _make_frame(_OPCODE_PONG, payload, mask=True)
                self._writer.write(pong)
                await self._writer.drain()
                continue

            if opcode == _OPCODE_PONG:
                continue

            if opcode == _OPCODE_CLOSE:
                close_code = 1005
                close_reason = ""
                if len(payload) >= 2:
                    close_code = struct.unpack(">H", payload[:2])[0]
                    close_reason = payload[2:].decode("utf-8", errors="replace")
                # Send close response if we didn't initiate
                if not self._closing:
                    self._closing = True
                    resp_payload = _make_close_payload(close_code, "")
                    resp_frame = _make_frame(_OPCODE_CLOSE, resp_payload, mask=True)
                    try:
                        self._writer.write(resp_frame)
                        await self._writer.drain()
                    except OSError:
                        pass
                await self._shutdown()
                raise WebSocketConnectionError(
                    f"connection closed by server: {close_code} {close_reason}",
                    host=self._host,
                    port=self._port,
                )

            if opcode == _OPCODE_BINARY:
                raise WebSocketProtocolError("binary frames are not supported")

            raise WebSocketProtocolError(f"unexpected opcode: {opcode:#x}")

    async def _read_frame(self) -> tuple[int, bytes, bool]:
        """Read a single WebSocket frame from the stream.

        Returns:
            Tuple of (opcode, payload, fin).
        """
        assert self._reader is not None
        header = await self._reader.readexactly(2)
        fin, opcode, is_masked, length = _parse_frame_header(header)

        # Extended payload length
        if length == 126:
            ext = await self._reader.readexactly(2)
            length = struct.unpack(">H", ext)[0]
        elif length == 127:
            ext = await self._reader.readexactly(8)
            length = struct.unpack(">Q", ext)[0]

        if length > _MAX_PAYLOAD_SIZE:
            raise WebSocketProtocolError(
                f"payload too large: {length} bytes (max {_MAX_PAYLOAD_SIZE})"
            )

        # Mask key (server should not mask, but handle it)
        mask_key = None
        if is_masked:
            mask_key = await self._reader.readexactly(4)

        # Payload
        payload = await self._reader.readexactly(length) if length > 0 else b""
        if mask_key:
            payload = _mask_payload(mask_key, payload)

        return opcode, payload, fin

    @staticmethod
    async def _async_read_handshake_response(
        reader: asyncio.StreamReader,
    ) -> bytes:
        """Read the HTTP handshake response until \\r\\n\\r\\n."""
        buf = bytearray()
        while True:
            chunk = await reader.read(4096)
            if not chunk:
                raise WebSocketConnectionError("connection closed during handshake")
            buf.extend(chunk)
            if b"\r\n\r\n" in buf:
                return bytes(buf)
            if len(buf) > 65536:
                raise WebSocketConnectionError("handshake response too large")
