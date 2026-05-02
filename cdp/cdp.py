# /// zerodep
# version = "0.1.0"
# deps = ["websocket"]
# tier = "medium"
# category = "protocol"
# ///
"""Zero-dependency Chrome DevTools Protocol (CDP) client.

Part of zerodep: https://github.com/Oaklight/zerodep
Copyright (c) 2026 Peng Ding. MIT License.

Provides sync and async CDP clients for communicating with CDP-compatible
browsers (Chrome, Chromium, Lightpanda, etc.) over WebSocket. Supports
tab management, page navigation, JavaScript evaluation, and high-level
rendered content extraction.

Usage::

    # High-level: extract rendered text from an SPA
    from cdp import CDPClient

    with CDPClient("ws://localhost:9222") as client:
        text = client.get_rendered_text("https://react.dev", timeout=15)
        print(text)

    # Low-level: manage targets and evaluate JS
    from cdp import CDPClient

    with CDPClient("ws://localhost:9222") as client:
        target_id = client.create_target("https://example.com")
        client.wait_for_load(target_id, timeout=10)
        html = client.evaluate(target_id, "document.documentElement.outerHTML")
        client.close_target(target_id)

    # Async
    from cdp import AsyncCDPClient

    async with AsyncCDPClient("ws://localhost:9222") as client:
        text = await client.get_rendered_text("https://example.com")

Requires Python 3.10+.
"""

from __future__ import annotations

import collections
import itertools
import json
import logging
import os
import sys
import time

__all__ = [
    # Constants
    "DEFAULT_TIMEOUT",
    "DEFAULT_PAGE_LOAD_TIMEOUT",
    # Exceptions
    "CDPError",
    "CDPConnectionError",
    "CDPTimeoutError",
    "CDPProtocolError",
    # Clients
    "CDPClient",
    "AsyncCDPClient",
]

logger = logging.getLogger(__name__)


# ── Sibling websocket import (guarded) ─────────────────────────────────────


def _ensure_sibling_path(name: str) -> str:
    """Return the sibling module directory and prepend it to ``sys.path``."""
    sibling_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", name)
    if sibling_dir not in sys.path:
        sys.path.insert(0, sibling_dir)
    return sibling_dir


try:
    _websocket_dir = _ensure_sibling_path("websocket")
    from websocket import AsyncWebSocketClient as _AsyncWebSocketClient
    from websocket import WebSocketClient as _WebSocketClient
    from websocket import WebSocketConnectionError as _WebSocketConnectionError
    from websocket import WebSocketError as _WebSocketError
    from websocket import WebSocketTimeoutError as _WebSocketTimeoutError

    _HAS_WEBSOCKET = True
except (ImportError, AttributeError):
    _HAS_WEBSOCKET = False


# ── Constants ──────────────────────────────────────────────────────────────

DEFAULT_TIMEOUT: float = 30.0
DEFAULT_PAGE_LOAD_TIMEOUT: float = 30.0


# ── Exceptions ─────────────────────────────────────────────────────────────


class CDPError(Exception):
    """Base exception for all CDP operations."""


class CDPConnectionError(CDPError):
    """Raised on WebSocket connection failures to the CDP endpoint."""

    def __init__(self, message: str, *, url: str = "") -> None:
        self.url = url
        super().__init__(message)


class CDPTimeoutError(CDPError):
    """Raised when a CDP operation times out."""

    def __init__(self, message: str, *, timeout: float = 0.0) -> None:
        self.timeout = timeout
        super().__init__(message)


class CDPProtocolError(CDPError):
    """Raised on CDP error responses."""

    def __init__(
        self,
        code: int,
        message: str,
        *,
        data: str | None = None,
    ) -> None:
        self.code = code
        self.error_message = message
        self.data = data
        super().__init__(f"CDP error {code}: {message}")


# ── Sync CDP Client ───────────────────────────────────────────────────────


class CDPClient:
    """Synchronous Chrome DevTools Protocol client.

    Args:
        url: CDP WebSocket endpoint URL (e.g. ``ws://localhost:9222``).
            If the URL does not contain a path, the client will auto-discover
            the browser's debugger WebSocket URL via the ``/json/version``
            endpoint.
        timeout: Default timeout for CDP commands in seconds.

    Example::

        with CDPClient("ws://localhost:9222") as client:
            text = client.get_rendered_text("https://example.com")
            print(text)
    """

    def __init__(
        self,
        url: str,
        *,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self._url = url
        self._timeout = timeout
        self._ws: _WebSocketClient | None = None
        self._cmd_id = itertools.count(1)
        self._targets: dict[str, str] = {}  # target_id -> session_id
        self._event_buffer: collections.deque[dict] = collections.deque()

    def connect(self, *, timeout: float | None = None) -> None:
        """Open the WebSocket connection to the CDP endpoint.

        Args:
            timeout: Connection timeout in seconds. Defaults to the
                client's default timeout.

        Raises:
            CDPConnectionError: If the connection fails.
            ImportError: If the websocket module is not available.
        """
        if self._ws is not None:
            return

        if not _HAS_WEBSOCKET:
            raise ImportError(
                "cdp module requires sibling 'websocket' module; "
                "install it with: zerodep add websocket"
            )

        ws_url = self._resolve_ws_url(self._url, timeout=timeout or self._timeout)

        try:
            ws = _WebSocketClient(ws_url)
            ws.connect(timeout=timeout or self._timeout)
            self._ws = ws
        except _WebSocketConnectionError as exc:
            raise CDPConnectionError(
                f"failed to connect to CDP endpoint: {exc}",
                url=ws_url,
            ) from exc
        except _WebSocketTimeoutError as exc:
            raise CDPTimeoutError(
                f"connection to CDP endpoint timed out: {exc}",
                timeout=timeout or self._timeout,
            ) from exc

    def send_command(
        self,
        method: str,
        params: dict | None = None,
        *,
        session_id: str | None = None,
        timeout: float | None = None,
    ) -> dict:
        """Send a CDP command and wait for the response.

        Args:
            method: CDP method name (e.g. ``Page.navigate``).
            params: Optional command parameters.
            session_id: Optional session ID for target-specific commands.
            timeout: Command timeout in seconds.

        Returns:
            The ``result`` dict from the CDP response.

        Raises:
            CDPTimeoutError: If the command times out.
            CDPProtocolError: If the CDP response contains an error.
            CDPError: If not connected.
        """
        self._ensure_connected()
        assert self._ws is not None

        cmd_id = next(self._cmd_id)
        msg: dict = {"id": cmd_id, "method": method}
        if params:
            msg["params"] = params
        if session_id:
            msg["sessionId"] = session_id

        self._ws.send(json.dumps(msg))
        return self._recv_response(cmd_id, timeout=timeout or self._timeout)

    def create_target(self, url: str = "about:blank") -> str:
        """Create a new browser target (tab) and attach to it.

        Args:
            url: Initial URL to load in the new target.

        Returns:
            The target ID.
        """
        result = self.send_command("Target.createTarget", {"url": url})
        target_id = result["targetId"]

        attach_result = self.send_command(
            "Target.attachToTarget",
            {"targetId": target_id, "flatten": True},
        )
        session_id = attach_result["sessionId"]
        self._targets[target_id] = session_id
        logger.debug("created target %s with session %s", target_id, session_id)
        return target_id

    def close_target(self, target_id: str) -> None:
        """Close a browser target (tab).

        Args:
            target_id: The target ID to close.
        """
        if target_id not in self._targets:
            return
        try:
            self.send_command("Target.closeTarget", {"targetId": target_id})
        except CDPError:
            logger.debug("failed to close target %s", target_id, exc_info=True)
        self._targets.pop(target_id, None)

    def navigate(
        self,
        target_id: str,
        url: str,
        *,
        timeout: float | None = None,
    ) -> None:
        """Navigate a target to a URL and wait for the page to load.

        Args:
            target_id: The target ID.
            url: URL to navigate to.
            timeout: Page load timeout in seconds.
        """
        session_id = self._get_session_id(target_id)
        load_timeout = timeout or DEFAULT_PAGE_LOAD_TIMEOUT

        self.send_command("Page.enable", session_id=session_id)
        self.send_command("Page.navigate", {"url": url}, session_id=session_id)
        self._wait_for_event(
            "Page.loadEventFired",
            session_id=session_id,
            timeout=load_timeout,
        )

    def wait_for_load(
        self,
        target_id: str,
        *,
        timeout: float | None = None,
    ) -> None:
        """Wait for a target's page to finish loading.

        Args:
            target_id: The target ID.
            timeout: Page load timeout in seconds.
        """
        session_id = self._get_session_id(target_id)
        self.send_command("Page.enable", session_id=session_id)
        self._wait_for_event(
            "Page.loadEventFired",
            session_id=session_id,
            timeout=timeout or DEFAULT_PAGE_LOAD_TIMEOUT,
        )

    def evaluate(self, target_id: str, expression: str) -> object:
        """Evaluate a JavaScript expression in a target.

        Args:
            target_id: The target ID.
            expression: JavaScript expression to evaluate.

        Returns:
            The result value.

        Raises:
            CDPProtocolError: If the evaluation throws an exception.
        """
        session_id = self._get_session_id(target_id)
        result = self.send_command(
            "Runtime.evaluate",
            {"expression": expression, "returnByValue": True},
            session_id=session_id,
        )

        if "exceptionDetails" in result:
            exc_details = result["exceptionDetails"]
            text = exc_details.get("text", "evaluation failed")
            raise CDPProtocolError(-1, text)

        return result.get("result", {}).get("value")

    def get_rendered_text(
        self,
        url: str,
        *,
        timeout: float | None = None,
    ) -> str:
        """Navigate to a URL and extract the rendered text content.

        Creates a temporary target, navigates to the URL, waits for load,
        extracts ``document.body.innerText``, and closes the target.

        Args:
            url: URL to render.
            timeout: Page load timeout in seconds.

        Returns:
            The rendered text content of the page.
        """
        target_id = self.create_target()
        try:
            self.navigate(target_id, url, timeout=timeout)
            result = self.evaluate(target_id, "document.body.innerText")
            return result if isinstance(result, str) else str(result or "")
        finally:
            self.close_target(target_id)

    def get_rendered_html(
        self,
        url: str,
        *,
        timeout: float | None = None,
    ) -> str:
        """Navigate to a URL and extract the rendered HTML.

        Creates a temporary target, navigates to the URL, waits for load,
        extracts ``document.documentElement.outerHTML``, and closes the target.

        Args:
            url: URL to render.
            timeout: Page load timeout in seconds.

        Returns:
            The rendered outer HTML of the page.
        """
        target_id = self.create_target()
        try:
            self.navigate(target_id, url, timeout=timeout)
            result = self.evaluate(target_id, "document.documentElement.outerHTML")
            return result if isinstance(result, str) else str(result or "")
        finally:
            self.close_target(target_id)

    def set_user_agent(self, target_id: str, user_agent: str) -> None:
        """Override the User-Agent for a target.

        Args:
            target_id: The target ID.
            user_agent: The User-Agent string to set.
        """
        session_id = self._get_session_id(target_id)
        self.send_command(
            "Network.setUserAgentOverride",
            {"userAgent": user_agent},
            session_id=session_id,
        )

    def close(self) -> None:
        """Close all targets and the WebSocket connection."""
        if self._ws is None:
            return

        # Close all targets (best-effort)
        for target_id in list(self._targets):
            try:
                self.send_command("Target.closeTarget", {"targetId": target_id})
            except (CDPError, _WebSocketError):
                pass
        self._targets.clear()
        self._event_buffer.clear()

        try:
            self._ws.close()
        except _WebSocketError:
            pass
        self._ws = None

    def __enter__(self) -> CDPClient:
        self.connect()
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    # ── Sync internal helpers ──

    def _ensure_connected(self) -> None:
        if self._ws is None:
            raise CDPError("not connected")

    def _get_session_id(self, target_id: str) -> str:
        session_id = self._targets.get(target_id)
        if session_id is None:
            raise CDPError(f"unknown target: {target_id}")
        return session_id

    def _recv_response(self, cmd_id: int, *, timeout: float) -> dict:
        """Receive messages until the response matching *cmd_id* arrives.

        Non-matching messages (events or other responses) are buffered.
        """
        assert self._ws is not None
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise CDPTimeoutError(
                    f"command {cmd_id} timed out after {timeout}s",
                    timeout=timeout,
                )
            try:
                raw = self._ws.recv(timeout=remaining)
            except _WebSocketTimeoutError as exc:
                raise CDPTimeoutError(
                    f"command {cmd_id} timed out after {timeout}s",
                    timeout=timeout,
                ) from exc

            msg = json.loads(raw)
            if msg.get("id") == cmd_id:
                if "error" in msg:
                    err = msg["error"]
                    raise CDPProtocolError(
                        err.get("code", -1),
                        err.get("message", "unknown error"),
                        data=err.get("data"),
                    )
                return msg.get("result", {})
            # Not our response -- buffer it
            self._event_buffer.append(msg)

    def _wait_for_event(
        self,
        event_name: str,
        *,
        session_id: str | None = None,
        timeout: float,
    ) -> dict:
        """Wait for a specific CDP event.

        First checks the event buffer, then reads from the WebSocket.
        """
        assert self._ws is not None
        # Check buffer first
        for i, msg in enumerate(self._event_buffer):
            if self._matches_event(msg, event_name, session_id):
                del self._event_buffer[i]
                return msg.get("params", {})

        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise CDPTimeoutError(
                    f"event {event_name} timed out after {timeout}s",
                    timeout=timeout,
                )
            try:
                raw = self._ws.recv(timeout=remaining)
            except _WebSocketTimeoutError as exc:
                raise CDPTimeoutError(
                    f"event {event_name} timed out after {timeout}s",
                    timeout=timeout,
                ) from exc

            msg = json.loads(raw)
            if self._matches_event(msg, event_name, session_id):
                return msg.get("params", {})
            self._event_buffer.append(msg)

    @staticmethod
    def _matches_event(
        msg: dict,
        event_name: str,
        session_id: str | None,
    ) -> bool:
        """Check if a message matches the expected event."""
        if msg.get("method") != event_name:
            return False
        if session_id is not None and msg.get("sessionId") != session_id:
            return False
        return True

    @staticmethod
    def _resolve_ws_url(url: str, *, timeout: float) -> str:
        """Resolve the browser's debugger WebSocket URL.

        If the URL already has a path (e.g. ``/devtools/browser/...``),
        return it as-is. Otherwise, query the ``/json/version`` endpoint
        to discover the WebSocket debugger URL.
        """
        import urllib.parse

        parsed = urllib.parse.urlparse(url)
        if parsed.path and parsed.path != "/":
            return url

        # Auto-discover via /json/version
        host = parsed.hostname or "localhost"
        port = parsed.port or 9222
        http_url = f"http://{host}:{port}/json/version"

        import http.client

        try:
            conn = http.client.HTTPConnection(host, port, timeout=timeout)
            conn.request("GET", "/json/version")
            resp = conn.getresponse()
            data = json.loads(resp.read())
            conn.close()
            ws_url = data.get("webSocketDebuggerUrl", "")
            if ws_url:
                logger.debug("auto-discovered CDP endpoint: %s", ws_url)
                return ws_url
        except Exception:
            logger.debug(
                "failed to auto-discover CDP endpoint from %s",
                http_url,
                exc_info=True,
            )

        return url


# ── Async CDP Client ──────────────────────────────────────────────────────


class AsyncCDPClient:
    """Asynchronous Chrome DevTools Protocol client.

    Args:
        url: CDP WebSocket endpoint URL (e.g. ``ws://localhost:9222``).
        timeout: Default timeout for CDP commands in seconds.

    Example::

        async with AsyncCDPClient("ws://localhost:9222") as client:
            text = await client.get_rendered_text("https://example.com")
            print(text)
    """

    def __init__(
        self,
        url: str,
        *,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self._url = url
        self._timeout = timeout
        self._ws: _AsyncWebSocketClient | None = None
        self._cmd_id = itertools.count(1)
        self._targets: dict[str, str] = {}
        self._event_buffer: collections.deque[dict] = collections.deque()

    async def connect(self, *, timeout: float | None = None) -> None:
        """Open the WebSocket connection to the CDP endpoint.

        Args:
            timeout: Connection timeout in seconds.

        Raises:
            CDPConnectionError: If the connection fails.
            ImportError: If the websocket module is not available.
        """
        if self._ws is not None:
            return

        if not _HAS_WEBSOCKET:
            raise ImportError(
                "cdp module requires sibling 'websocket' module; "
                "install it with: zerodep add websocket"
            )

        ws_url = self._resolve_ws_url(self._url, timeout=timeout or self._timeout)

        try:
            ws = _AsyncWebSocketClient(ws_url)
            await ws.connect(timeout=timeout or self._timeout)
            self._ws = ws
        except _WebSocketConnectionError as exc:
            raise CDPConnectionError(
                f"failed to connect to CDP endpoint: {exc}",
                url=ws_url,
            ) from exc
        except _WebSocketTimeoutError as exc:
            raise CDPTimeoutError(
                f"connection to CDP endpoint timed out: {exc}",
                timeout=timeout or self._timeout,
            ) from exc

    async def send_command(
        self,
        method: str,
        params: dict | None = None,
        *,
        session_id: str | None = None,
        timeout: float | None = None,
    ) -> dict:
        """Send a CDP command and wait for the response.

        Args:
            method: CDP method name.
            params: Optional command parameters.
            session_id: Optional session ID for target-specific commands.
            timeout: Command timeout in seconds.

        Returns:
            The ``result`` dict from the CDP response.
        """
        self._ensure_connected()
        assert self._ws is not None

        cmd_id = next(self._cmd_id)
        msg: dict = {"id": cmd_id, "method": method}
        if params:
            msg["params"] = params
        if session_id:
            msg["sessionId"] = session_id

        await self._ws.send(json.dumps(msg))
        return await self._recv_response(cmd_id, timeout=timeout or self._timeout)

    async def create_target(self, url: str = "about:blank") -> str:
        """Create a new browser target (tab) and attach to it.

        Args:
            url: Initial URL to load in the new target.

        Returns:
            The target ID.
        """
        result = await self.send_command("Target.createTarget", {"url": url})
        target_id = result["targetId"]

        attach_result = await self.send_command(
            "Target.attachToTarget",
            {"targetId": target_id, "flatten": True},
        )
        session_id = attach_result["sessionId"]
        self._targets[target_id] = session_id
        logger.debug("created target %s with session %s", target_id, session_id)
        return target_id

    async def close_target(self, target_id: str) -> None:
        """Close a browser target (tab).

        Args:
            target_id: The target ID to close.
        """
        if target_id not in self._targets:
            return
        try:
            await self.send_command("Target.closeTarget", {"targetId": target_id})
        except CDPError:
            logger.debug("failed to close target %s", target_id, exc_info=True)
        self._targets.pop(target_id, None)

    async def navigate(
        self,
        target_id: str,
        url: str,
        *,
        timeout: float | None = None,
    ) -> None:
        """Navigate a target to a URL and wait for the page to load.

        Args:
            target_id: The target ID.
            url: URL to navigate to.
            timeout: Page load timeout in seconds.
        """
        session_id = self._get_session_id(target_id)
        load_timeout = timeout or DEFAULT_PAGE_LOAD_TIMEOUT

        await self.send_command("Page.enable", session_id=session_id)
        await self.send_command("Page.navigate", {"url": url}, session_id=session_id)
        await self._wait_for_event(
            "Page.loadEventFired",
            session_id=session_id,
            timeout=load_timeout,
        )

    async def wait_for_load(
        self,
        target_id: str,
        *,
        timeout: float | None = None,
    ) -> None:
        """Wait for a target's page to finish loading.

        Args:
            target_id: The target ID.
            timeout: Page load timeout in seconds.
        """
        session_id = self._get_session_id(target_id)
        await self.send_command("Page.enable", session_id=session_id)
        await self._wait_for_event(
            "Page.loadEventFired",
            session_id=session_id,
            timeout=timeout or DEFAULT_PAGE_LOAD_TIMEOUT,
        )

    async def evaluate(self, target_id: str, expression: str) -> object:
        """Evaluate a JavaScript expression in a target.

        Args:
            target_id: The target ID.
            expression: JavaScript expression to evaluate.

        Returns:
            The result value.

        Raises:
            CDPProtocolError: If the evaluation throws an exception.
        """
        session_id = self._get_session_id(target_id)
        result = await self.send_command(
            "Runtime.evaluate",
            {"expression": expression, "returnByValue": True},
            session_id=session_id,
        )

        if "exceptionDetails" in result:
            exc_details = result["exceptionDetails"]
            text = exc_details.get("text", "evaluation failed")
            raise CDPProtocolError(-1, text)

        return result.get("result", {}).get("value")

    async def get_rendered_text(
        self,
        url: str,
        *,
        timeout: float | None = None,
    ) -> str:
        """Navigate to a URL and extract the rendered text content.

        Args:
            url: URL to render.
            timeout: Page load timeout in seconds.

        Returns:
            The rendered text content of the page.
        """
        target_id = await self.create_target()
        try:
            await self.navigate(target_id, url, timeout=timeout)
            result = await self.evaluate(target_id, "document.body.innerText")
            return result if isinstance(result, str) else str(result or "")
        finally:
            await self.close_target(target_id)

    async def get_rendered_html(
        self,
        url: str,
        *,
        timeout: float | None = None,
    ) -> str:
        """Navigate to a URL and extract the rendered HTML.

        Args:
            url: URL to render.
            timeout: Page load timeout in seconds.

        Returns:
            The rendered outer HTML of the page.
        """
        target_id = await self.create_target()
        try:
            await self.navigate(target_id, url, timeout=timeout)
            result = await self.evaluate(
                target_id, "document.documentElement.outerHTML"
            )
            return result if isinstance(result, str) else str(result or "")
        finally:
            await self.close_target(target_id)

    async def set_user_agent(self, target_id: str, user_agent: str) -> None:
        """Override the User-Agent for a target.

        Args:
            target_id: The target ID.
            user_agent: The User-Agent string to set.
        """
        session_id = self._get_session_id(target_id)
        await self.send_command(
            "Network.setUserAgentOverride",
            {"userAgent": user_agent},
            session_id=session_id,
        )

    async def close(self) -> None:
        """Close all targets and the WebSocket connection."""
        if self._ws is None:
            return

        for target_id in list(self._targets):
            try:
                await self.send_command("Target.closeTarget", {"targetId": target_id})
            except (CDPError, _WebSocketError):
                pass
        self._targets.clear()
        self._event_buffer.clear()

        try:
            await self._ws.close()
        except _WebSocketError:
            pass
        self._ws = None

    async def __aenter__(self) -> AsyncCDPClient:
        await self.connect()
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()

    # ── Async internal helpers ──

    def _ensure_connected(self) -> None:
        if self._ws is None:
            raise CDPError("not connected")

    def _get_session_id(self, target_id: str) -> str:
        session_id = self._targets.get(target_id)
        if session_id is None:
            raise CDPError(f"unknown target: {target_id}")
        return session_id

    async def _recv_response(self, cmd_id: int, *, timeout: float) -> dict:
        """Receive messages until the response matching *cmd_id* arrives."""
        assert self._ws is not None
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise CDPTimeoutError(
                    f"command {cmd_id} timed out after {timeout}s",
                    timeout=timeout,
                )
            try:
                raw = await self._ws.recv(timeout=remaining)
            except _WebSocketTimeoutError as exc:
                raise CDPTimeoutError(
                    f"command {cmd_id} timed out after {timeout}s",
                    timeout=timeout,
                ) from exc

            msg = json.loads(raw)
            if msg.get("id") == cmd_id:
                if "error" in msg:
                    err = msg["error"]
                    raise CDPProtocolError(
                        err.get("code", -1),
                        err.get("message", "unknown error"),
                        data=err.get("data"),
                    )
                return msg.get("result", {})
            self._event_buffer.append(msg)

    async def _wait_for_event(
        self,
        event_name: str,
        *,
        session_id: str | None = None,
        timeout: float,
    ) -> dict:
        """Wait for a specific CDP event."""
        assert self._ws is not None
        # Check buffer first
        for i, msg in enumerate(self._event_buffer):
            if self._matches_event(msg, event_name, session_id):
                del self._event_buffer[i]
                return msg.get("params", {})

        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise CDPTimeoutError(
                    f"event {event_name} timed out after {timeout}s",
                    timeout=timeout,
                )
            try:
                raw = await self._ws.recv(timeout=remaining)
            except _WebSocketTimeoutError as exc:
                raise CDPTimeoutError(
                    f"event {event_name} timed out after {timeout}s",
                    timeout=timeout,
                ) from exc

            msg = json.loads(raw)
            if self._matches_event(msg, event_name, session_id):
                return msg.get("params", {})
            self._event_buffer.append(msg)

    @staticmethod
    def _matches_event(
        msg: dict,
        event_name: str,
        session_id: str | None,
    ) -> bool:
        """Check if a message matches the expected event."""
        if msg.get("method") != event_name:
            return False
        if session_id is not None and msg.get("sessionId") != session_id:
            return False
        return True

    @staticmethod
    def _resolve_ws_url(url: str, *, timeout: float) -> str:
        """Resolve the browser's debugger WebSocket URL."""
        # Reuse the sync implementation
        return CDPClient._resolve_ws_url(url, timeout=timeout)
