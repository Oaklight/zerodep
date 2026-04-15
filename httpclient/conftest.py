"""Local httpbin-compatible HTTP server for offline testing.

Provides a session-scoped ``httpbin_url`` fixture that starts a threaded
HTTP server mimicking the httpbin.org endpoints used by the test suite.
The server runs on localhost with an OS-assigned port and is torn down
after all tests finish.
"""

import base64
import gzip
import hashlib
import json
import os
import select
import socket
import threading
import zlib
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import pytest

# ── httpbin-compatible handler ──

_SAMPLE_JSON = {
    "slideshow": {
        "author": "Yours Truly",
        "date": "date of publication",
        "slides": [
            {"title": "Wake up to WonderWidgets!", "type": "all"},
            {"items": ["Why ?", "Because"], "title": "Overview", "type": "all"},
        ],
        "title": "Sample Slide Show",
    }
}

_SAMPLE_HTML = (
    b"<html><body><h1>Herman Melville - Moby Dick</h1>"
    b"<p>Call me Ishmael.</p></body></html>"
)


class _HttpBinHandler(BaseHTTPRequestHandler):
    """Minimal httpbin-compatible request handler."""

    def log_message(self, format, *args):  # noqa: A002
        pass  # suppress request logs during tests

    # ── helpers ──

    def _headers_dict(self):
        return {k: v for k, v in self.headers.items()}

    def _request_url(self):
        return f"http://{self.headers['Host']}{self.path}"

    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        return self.rfile.read(length) if length else b""

    def _parse_body(self):
        """Parse request body into (json_data, form_data, files_data)."""
        ct = self.headers.get("Content-Type", "")
        raw = self._read_body()
        json_data = None
        form_data = {}
        files_data = {}

        if "application/json" in ct:
            json_data = json.loads(raw) if raw else None
        elif "application/x-www-form-urlencoded" in ct:
            form_data = {k: v[0] for k, v in parse_qs(raw.decode()).items()}
        elif "multipart/form-data" in ct:
            boundary = ct.split("boundary=")[1].strip().strip('"')
            self._parse_multipart(raw, boundary, form_data, files_data)

        return json_data, form_data, files_data

    @staticmethod
    def _parse_multipart(raw, boundary, form_data, files_data):
        delimiter = f"--{boundary}".encode()
        parts = raw.split(delimiter)
        for part in parts:
            part = part.strip(b"\r\n")
            if not part or part == b"--":
                continue
            if b"\r\n\r\n" not in part:
                continue
            header_section, body = part.split(b"\r\n\r\n", 1)
            if body.endswith(b"\r\n"):
                body = body[:-2]

            name = filename = None
            for line in header_section.decode("latin-1").split("\r\n"):
                if "Content-Disposition" not in line:
                    continue
                for item in line.split(";"):
                    item = item.strip()
                    if item.startswith("name="):
                        name = item.split("=", 1)[1].strip('"')
                    elif item.startswith("filename="):
                        filename = item.split("=", 1)[1].strip('"')

            if name is None:
                continue
            if filename is not None:
                files_data[name] = body.decode(errors="replace")
            else:
                form_data[name] = body.decode()

    def _handle_echo(self):
        """Echo endpoint for POST/PUT/PATCH."""
        parsed = urlparse(self.path)
        json_data, form_data, files_data = self._parse_body()
        self._send_json(
            {
                "args": {k: v[0] for k, v in parse_qs(parsed.query).items()},
                "headers": self._headers_dict(),
                "url": self._request_url(),
                "json": json_data,
                "form": form_data,
                "files": files_data,
            }
        )

    # ── HTTP methods ──

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path == "/get":
            args = {k: v[0] for k, v in parse_qs(parsed.query).items()}
            self._send_json(
                {
                    "args": args,
                    "headers": self._headers_dict(),
                    "url": self._request_url(),
                }
            )
        elif path == "/json":
            self._send_json(_SAMPLE_JSON)
        elif path == "/html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(_SAMPLE_HTML)))
            self.end_headers()
            self.wfile.write(_SAMPLE_HTML)
        elif path.startswith("/redirect/"):
            n = int(path.rsplit("/", 1)[1])
            target = "/get" if n <= 1 else f"/redirect/{n - 1}"
            self.send_response(302)
            self.send_header("Location", target)
            self.send_header("Content-Length", "0")
            self.end_headers()
        elif path.startswith("/absolute-redirect/"):
            n = int(path.rsplit("/", 1)[1])
            host = self.headers["Host"]
            if n <= 1:
                target = f"http://{host}/get"
            else:
                target = f"http://{host}/absolute-redirect/{n - 1}"
            self.send_response(302)
            self.send_header("Location", target)
            self.send_header("Content-Length", "0")
            self.end_headers()
        elif path.startswith("/status/"):
            code = int(path.rsplit("/", 1)[1])
            self.send_response(code)
            self.send_header("Content-Length", "0")
            self.end_headers()
        elif path == "/gzip":
            payload = json.dumps(
                {"gzipped": True, "method": "GET", "origin": "127.0.0.1"}
            ).encode()
            compressed = gzip.compress(payload)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Encoding", "gzip")
            self.send_header("Content-Length", str(len(compressed)))
            self.end_headers()
            self.wfile.write(compressed)
        elif path == "/deflate":
            payload = json.dumps(
                {"deflated": True, "method": "GET", "origin": "127.0.0.1"}
            ).encode()
            compressed = zlib.compress(payload)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Encoding", "deflate")
            self.send_header("Content-Length", str(len(compressed)))
            self.end_headers()
            self.wfile.write(compressed)
        elif path == "/gzip-stream":
            payload = json.dumps(
                {"gzipped": True, "method": "GET", "origin": "127.0.0.1"}
            ).encode()
            compressed = gzip.compress(payload)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Encoding", "gzip")
            self.send_header("Transfer-Encoding", "chunked")
            self.end_headers()
            chunk_size = 32
            for i in range(0, len(compressed), chunk_size):
                chunk = compressed[i : i + chunk_size]
                self.wfile.write(f"{len(chunk):x}\r\n".encode())
                self.wfile.write(chunk)
                self.wfile.write(b"\r\n")
            self.wfile.write(b"0\r\n\r\n")
        elif path.startswith("/basic-auth/"):
            parts = path.split("/")
            expected_user, expected_pass = parts[2], parts[3]
            auth = self.headers.get("Authorization", "")
            if auth.startswith("Basic "):
                decoded = base64.b64decode(auth[6:]).decode()
                user, passwd = decoded.split(":", 1)
                if user == expected_user and passwd == expected_pass:
                    self._send_json({"authenticated": True, "user": user})
                    return
            self.send_response(401)
            self.send_header("WWW-Authenticate", 'Basic realm="Fake Realm"')
            self.send_header("Content-Length", "0")
            self.end_headers()
        elif path.startswith("/digest-auth/"):
            parts = path.split("/")
            qop, expected_user, expected_pass = parts[2], parts[3], parts[4]
            realm = "testrealm@host.com"
            nonce = "testnonce123"
            auth = self.headers.get("Authorization", "")
            if auth.startswith("Digest "):
                # Parse key=value pairs from the Digest header.
                auth_params = {}
                for item in auth[7:].split(","):
                    item = item.strip()
                    if "=" in item:
                        k, v = item.split("=", 1)
                        auth_params[k.strip()] = v.strip().strip('"')
                ha1 = hashlib.md5(
                    f"{expected_user}:{realm}:{expected_pass}".encode()
                ).hexdigest()
                ha2 = hashlib.md5(
                    f"GET:{auth_params.get('uri', '')}".encode()
                ).hexdigest()
                if qop == "auth":
                    expected_response = hashlib.md5(
                        f"{ha1}:{nonce}:{auth_params.get('nc', '')}:"
                        f"{auth_params.get('cnonce', '')}:{qop}:{ha2}".encode()
                    ).hexdigest()
                else:
                    expected_response = hashlib.md5(
                        f"{ha1}:{nonce}:{ha2}".encode()
                    ).hexdigest()
                if auth_params.get("response") == expected_response:
                    self._send_json({"authenticated": True, "user": expected_user})
                    return
            self.send_response(401)
            self.send_header(
                "WWW-Authenticate",
                f'Digest realm="{realm}", nonce="{nonce}", qop="auth", algorithm=MD5',
            )
            self.send_header("Content-Length", "0")
            self.end_headers()
        elif path.startswith("/stream-bytes/"):
            n = int(path.rsplit("/", 1)[1])
            data = os.urandom(n)
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Length", str(n))
            self.end_headers()
            self.wfile.write(data)
        elif path == "/keep-alive":
            body = json.dumps({"keep-alive": True}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Connection", "keep-alive")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.send_header("Content-Length", "0")
            self.end_headers()

    def do_POST(self):
        self._handle_echo()

    def do_PUT(self):
        self._handle_echo()

    def do_PATCH(self):
        self._handle_echo()

    def do_DELETE(self):
        self._send_json(
            {
                "headers": self._headers_dict(),
                "url": self._request_url(),
            }
        )


# ── proxy handler ──


class _ProxyHandler(BaseHTTPRequestHandler):
    """Simple forward HTTP proxy handler for testing."""

    def log_message(self, format, *args):  # noqa: A002
        pass  # suppress request logs during tests

    def _forward_request(self, method):
        """Forward an HTTP request to the target server.

        Args:
            method: The HTTP method to forward (e.g. "GET", "POST").
        """
        parsed = urlparse(self.path)
        host = parsed.hostname
        port = parsed.port or 80
        path = parsed.path
        if parsed.query:
            path = f"{path}?{parsed.query}"

        # Read request body if present.
        body = self._read_body()

        # Filter out proxy-specific and hop-by-hop headers.
        headers = {}
        for key, value in self.headers.items():
            lower = key.lower()
            if lower.startswith("proxy-") or lower == "host":
                continue
            headers[key] = value

        conn = HTTPConnection(host, port, timeout=10)
        try:
            conn.request(method, path, body=body or None, headers=headers)
            resp = conn.getresponse()
            resp_body = resp.read()
            self.send_response(resp.status)
            for key, value in resp.getheaders():
                lower = key.lower()
                if lower in ("transfer-encoding", "connection"):
                    continue
                self.send_header(key, value)
            self.send_header("Content-Length", str(len(resp_body)))
            self.end_headers()
            self.wfile.write(resp_body)
        finally:
            conn.close()

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        return self.rfile.read(length) if length else b""

    def do_GET(self):
        self._forward_request("GET")

    def do_POST(self):
        self._forward_request("POST")

    def do_CONNECT(self):
        """Handle HTTPS CONNECT tunneling."""
        host, port = self.path.split(":")
        port = int(port)
        target = socket.create_connection((host, port), timeout=10)
        self.send_response(200, "Connection Established")
        self.end_headers()

        self.connection.setblocking(False)
        target.setblocking(False)

        try:
            while True:
                readable, _, _ = select.select([self.connection, target], [], [], 1.0)
                if not readable:
                    continue
                for sock in readable:
                    try:
                        data = sock.recv(8192)
                    except (BlockingIOError, ConnectionResetError):
                        data = b""
                    if not data:
                        return
                    if sock is self.connection:
                        target.sendall(data)
                    else:
                        self.connection.sendall(data)
        except Exception:
            pass
        finally:
            target.close()


# ── pytest fixtures ──


@pytest.fixture(scope="session")
def httpbin_url():
    """Start a local httpbin-compatible server and yield its base URL."""
    server = ThreadingHTTPServer(("127.0.0.1", 0), _HttpBinHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()


@pytest.fixture(scope="session")
def proxy_url():
    """Start a local HTTP proxy server and yield its base URL."""
    server = ThreadingHTTPServer(("127.0.0.1", 0), _ProxyHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()
