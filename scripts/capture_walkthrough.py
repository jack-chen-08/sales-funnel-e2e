"""Capture the walkthrough screenshots referenced from README.md.

Usage: .venv/bin/python scripts/capture_walkthrough.py
Writes docs/screenshots/*.png
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from playwright.sync_api import sync_playwright

from app.harness import stub_server
from chain.runner import ChainRunner

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "docs" / "screenshots"
SHOTS.mkdir(parents=True, exist_ok=True)
VIEWPORT = {"width": 1280, "height": 860}


def main() -> None:
    with stub_server() as base:
        report = ChainRunner(base, run_tag="walkthrough").run()
        assert report["ok"], f"chain failed: {report.get('failed_step')} {report.get('error')}"
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport=VIEWPORT)
            page.goto(f"{base}/apply", wait_until="load")
            page.screenshot(path=str(SHOTS / "01_apply_form.png"), full_page=True)

            page.goto(f"{base}/desk/verify", wait_until="load")
            page.screenshot(path=str(SHOTS / "02_desk_verify.png"), full_page=True)

            # publish the successful run's step table, then shoot it
            import httpx
            httpx.post(f"{base}/api/_test/chain-status",
                       json={"run_id": report["run_id"], "steps": report["steps"]}, timeout=10)
            page.goto(f"{base}/_diag/chain?run_id={report['run_id']}", wait_until="load")
            page.screenshot(path=str(SHOTS / "03_chain_all_passed.png"), full_page=True)
            browser.close()
    print(json.dumps({"screenshots": sorted(p.name for p in SHOTS.glob("*.png")),
                      "run_id": report["run_id"], "total_ms": report["total_ms"]},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
