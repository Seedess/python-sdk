#!/usr/bin/env python3
"""Full working Seedess example for Python.

    SEEDESS_API_KEY=key_... python3 examples/server.py
    open http://localhost:8787

Creates one stream on first request, serves the page, and hands the browser a
public token plus absolute playback URLs.
"""

from __future__ import annotations

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from seedess_sdk import Seedess, SeedessError

PORT = int(os.environ.get("PORT", "8787"))
ORIGIN = "https://seedess.com"
HERE = Path(__file__).resolve().parent
API_KEY = os.environ.get("SEEDESS_API_KEY")
STREAM_URL = os.environ.get("SEEDESS_STREAM_URL", "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8")
STREAM_ID = os.environ.get("SEEDESS_STREAM_ID", "sdk-example")

if not API_KEY:
    raise SystemExit("Set SEEDESS_API_KEY (a server key, key_...) before running this example.")

seedess = Seedess(API_KEY, base_url=os.environ.get("SEEDESS_API_BASE", "https://seedess.com"))
cached: dict | None = None


def handoff() -> dict:
    global cached
    if cached is not None:
        return cached

    stream = seedess.create_stream(STREAM_URL, id=STREAM_ID, title="Seedess Python SDK example")
    token = stream["publicToken"]
    playback = stream.get("playback", {})
    cached = {
        "ok": True,
        "stream": stream["id"],
        "token": token,
        "playback": {
            "master": ORIGIN + playback["master"],
            "signaling": ORIGIN + playback["signaling"],
            "config": f"{ORIGIN}/signaling/config?token={quote(token)}",
        },
    }
    return cached


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        try:
            if self.path == "/api/seedess":
                body = json.dumps(handoff()).encode()
                self.send_response(200)
                self.send_header("content-type", "application/json")
                self.send_header("content-length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return

            if self.path in ("/", "/index.html"):
                body = (HERE / "public" / "index.html").read_bytes()
                self.send_response(200)
                self.send_header("content-type", "text/html; charset=utf-8")
                self.send_header("content-length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return

            self.send_error(404)
        except SeedessError as error:
            body = json.dumps({"ok": False, "error": f"{error.status} {error.code}: {error}"}).encode()
            self.send_response(500)
            self.send_header("content-type", "application/json")
            self.send_header("content-length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:  # noqa: A003
        print("%s - %s" % (self.address_string(), format % args))


if __name__ == "__main__":
    print(f"Seedess example on http://localhost:{PORT}")
    print("The first /api/seedess request creates the stream.")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
