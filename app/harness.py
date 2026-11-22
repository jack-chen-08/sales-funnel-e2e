"""Test harness: run the reference stub on a free port for tests and scripts."""
from __future__ import annotations

import contextlib
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def wait_healthy(url: str, timeout: float = 30.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if httpx.get(f"{url}/healthz", timeout=1.0).status_code == 200:
                return True
        except Exception:  # noqa: BLE001 - still booting
            pass
        time.sleep(0.1)
    return False


@contextlib.contextmanager
def stub_server(port: int | None = None, env_extra: dict[str, str] | None = None):
    port = port or free_port()
    env = {**os.environ, "PYTHONPATH": str(ROOT), "PYTHONUNBUFFERED": "1"}
    env.pop("FAIL_STEP", None)
    if env_extra:
        env.update(env_extra)
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.api:app",
         "--host", "127.0.0.1", "--port", str(port), "--log-level", "warning"],
        cwd=str(ROOT), env=env,
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
    )
    url = f"http://127.0.0.1:{port}"
    try:
        if not wait_healthy(url):
            err = proc.stderr.read().decode(errors="replace")[-2000:] if proc.stderr else ""
            raise RuntimeError(f"stub failed to start on {port}\n{err}")
        yield url
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
