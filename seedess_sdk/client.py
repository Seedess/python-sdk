"""Seedess control-plane client.

Server-side only: uses a secret API key (``key_…``). Playback uses the
``@seedess/*-p2p`` packages and a per-stream public token (``pk_…``).
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Callable, Optional
from urllib.parse import quote

from .errors import SeedessError

DEFAULT_BASE_URL = "https://seedess.com"

Transport = Callable[[str, str, dict, Optional[bytes]], tuple[int, bytes]]


class Seedess:
    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        *,
        transport: Optional[Transport] = None,
        timeout: float = 30.0,
    ) -> None:
        if not api_key or not api_key.startswith("key_"):
            raise ValueError("Seedess: api_key must be a server API key (key_…)")
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._transport = transport or self._http
        self._timeout = timeout

    def _http(self, method: str, url: str, headers: dict, body: Optional[bytes]) -> tuple[int, bytes]:
        request = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=self._timeout) as response:
                return response.status, response.read()
        except urllib.error.HTTPError as error:
            return error.code, error.read()

    def request(
        self,
        method: str,
        path: str,
        body: Any = None,
        *,
        auth: bool = True,
    ) -> Any:
        """Raw JSON request. ``path`` is appended to the base URL."""
        url = f"{self._base_url}{path if path.startswith('/') else '/' + path}"
        headers = {"accept": "application/json"}
        payload = None
        if body is not None:
            headers["content-type"] = "application/json"
            payload = json.dumps(body).encode()
        if auth:
            headers["authorization"] = f"Bearer {self._api_key}"

        status, raw = self._transport(method, url, headers, payload)
        text = raw.decode("utf-8", errors="replace") if raw else ""
        data = None
        if text:
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                data = {"error": {"code": "invalid_json", "message": text[:200]}}

        if status < 200 or status >= 300:
            error = (data or {}).get("error", {}) if isinstance(data, dict) else {}
            raise SeedessError(
                status,
                error.get("code", "http_error"),
                error.get("message", f"HTTP {status}"),
                data,
            )
        return data

    def create_stream(
        self,
        url: str,
        *,
        id: Optional[str] = None,
        title: Optional[str] = None,
        live: Optional[bool] = None,
    ) -> dict:
        body: dict[str, Any] = {"url": url}
        if id is not None:
            body["id"] = id
        if title is not None:
            body["title"] = title
        if live is not None:
            body["live"] = live
        return self.request("POST", "/api/v1/streams", body)

    def get_stream(self, stream_id: str) -> dict:
        return self.request("GET", f"/api/v1/streams/{quote(str(stream_id), safe='')}")

    def list_streams(self) -> dict:
        return self.request("GET", "/api/v1/streams")

    def refresh_stream(self, stream_id: str) -> dict:
        return self.request("POST", f"/api/v1/streams/{quote(str(stream_id), safe='')}/refresh")

    def disable_peers(self, stream_id: str) -> dict:
        return self.request("POST", f"/api/v1/streams/{quote(str(stream_id), safe='')}/kill")

    def enable_peers(self, stream_id: str) -> dict:
        return self.request("POST", f"/api/v1/streams/{quote(str(stream_id), safe='')}/revive")

    def get_metrics(self, stream_id: str) -> dict:
        return self.request("GET", f"/api/v1/streams/{quote(str(stream_id), safe='')}/metrics")

    def send_telemetry(
        self,
        session_id: str,
        stream_id: str,
        *,
        cdn_bytes: int = 0,
        p2p_bytes: int = 0,
        hash_failures: int = 0,
        fallbacks: int = 0,
        rebuffers: int = 0,
        peak_peers: int = 0,
    ) -> None:
        self.request(
            "POST",
            "/api/v1/telemetry",
            {
                "sessionId": session_id,
                "streamId": stream_id,
                "cdnBytes": cdn_bytes,
                "p2pBytes": p2p_bytes,
                "hashFailures": hash_failures,
                "fallbacks": fallbacks,
                "rebuffers": rebuffers,
                "peakPeers": peak_peers,
            },
            auth=False,
        )
