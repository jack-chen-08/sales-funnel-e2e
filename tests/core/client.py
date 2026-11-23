"""对 mock 平台的 HTTP 客户端：自动带上 X-Run-Id，并记录每一步的请求/响应作为 trace 依据。"""

from __future__ import annotations

import json
from typing import Any

import httpx


class ApiError(AssertionError):
    def __init__(self, method: str, path: str, status: int, body: Any) -> None:
        self.method = method
        self.path = path
        self.status = status
        self.body = body
        super().__init__(f"{method} {path} -> HTTP {status}: {json.dumps(body, ensure_ascii=False)[:600]}")


class SmokeClient:
    def __init__(self, base_url: str, run_id: str, timeout: float = 20.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.run_id = run_id
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={"X-Run-Id": run_id},
            timeout=timeout,
            follow_redirects=True,
        )
        self.calls: list[dict[str, Any]] = []

    def close(self) -> None:
        self._client.close()

    def request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        response = self._client.request(method, path, **kwargs)
        self.calls.append(
            {
                "method": method,
                "path": path,
                "request": _safe(kwargs.get("json") or kwargs.get("data")),
                "status": response.status_code,
                "response": _safe(_maybe_json(response)),
                "elapsed_ms": round(response.elapsed.total_seconds() * 1000, 2),
            }
        )
        return response

    def get(self, path: str, **kwargs: Any) -> httpx.Response:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> httpx.Response:
        return self.request("POST", path, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> httpx.Response:
        return self.request("DELETE", path, **kwargs)

    def json(self, method: str, path: str, **kwargs: Any) -> dict:
        response = self.request(method, path, **kwargs)
        body = _maybe_json(response)
        if response.status_code >= 400:
            raise ApiError(method, path, response.status_code, body)
        return body

    def drain_calls(self) -> list[dict[str, Any]]:
        calls, self.calls = self.calls, []
        return calls


def _maybe_json(response: httpx.Response) -> Any:
    ctype = response.headers.get("content-type", "")
    if "application/json" in ctype:
        try:
            return response.json()
        except ValueError:
            return response.text[:2000]
    return {"content_type": ctype, "bytes": len(response.content)}


def _safe(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, dict):
        return {k: _safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_safe(v) for v in value]
    return value
