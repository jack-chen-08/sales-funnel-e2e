import json
import os
from pathlib import Path

import pytest

from app.harness import stub_server

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
REPORTS.mkdir(exist_ok=True)


@pytest.fixture(scope="session")
def base_url():
    ext = os.environ.get("E2E_BASE_URL")
    if ext:  # 指向真实平台时不再起参考桩
        yield ext.rstrip("/")
        return
    with stub_server() as url:
        yield url


@pytest.fixture(scope="session")
def stub_process(base_url):
    """Kept for tests that need the raw URL plus a live server for extra assertions."""
    return base_url


def dump(name: str, report: dict) -> Path:
    path = REPORTS / name
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
