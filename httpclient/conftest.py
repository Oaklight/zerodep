"""Local httpbin-compatible HTTP server for offline testing.

Provides a session-scoped ``httpbin_url`` fixture that starts a threaded
HTTP server mimicking the httpbin.org endpoints used by the test suite.
The server runs on localhost with an OS-assigned port and is torn down
after all tests finish.
"""

import json
import threading
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


# ── pytest fixture ──


@pytest.fixture(scope="session")
def httpbin_url():
    """Start a local httpbin-compatible server and yield its base URL."""
    server = ThreadingHTTPServer(("127.0.0.1", 0), _HttpBinHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()
