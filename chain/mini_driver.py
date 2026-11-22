"""小程序两步的执行器抽象。

工单要求框架为 Playwright + pytest + miniprogram-automator，并允许在没有小程序
执行机的流水线上跳过小程序步骤。这里把「谁去点小程序」抽成可替换驱动：

- ``H5Driver``（默认，``MINI_DRIVER=playwright-h5``）
  用 Playwright 驱动会员端同一个认证表单的 H5 实现，覆盖同一条业务路径
  （手机号 + 验证码 -> 会员落库 -> 首月推荐），本机可完整复现。

- ``AutomatorDriver``（``MINI_DRIVER=miniprogram-automator``）
  调 ``miniprogram-automator`` 连微信开发者工具自动化端口，操作真小程序。
  **需要**微信开发者工具 CLI + 已登录 + 已开启自动化端口，本仓未在本机验证该路径；
  它在任何环境失败都会抛明确异常，不会静默降级。

- ``SKIP_MINI=1`` 或 ``ChainRunner(skip_mini=True)``：第 11/12 步标记 skipped，其余 10 步照跑。
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTOMATOR_JS = ROOT / "mini" / "automator_verify.js"


class MiniDriver:
    name = "base"
    requires_browser = True

    def verify(self, *, page, base_url: str, lead_id: str, phone: str, code: str) -> str:
        raise NotImplementedError


class H5Driver(MiniDriver):
    name = "playwright-h5"
    requires_browser = True

    def verify(self, *, page, base_url, lead_id, phone, code) -> str:
        page.goto(f"{base_url}/mini/login?lead_id={lead_id}")
        page.fill("#phone", phone)
        page.fill("#code", code)
        page.click("#submit-mini")
        page.wait_for_selector("#ok, #fail", timeout=30_000)
        if page.locator("#ok").count() != 1:
            raise AssertionError(f"小程序认证失败: {page.inner_text('body')[:160]}")
        return page.inner_text("#member-id").strip()


class AutomatorDriver(MiniDriver):
    """Drives the real WeChat mini program. Not exercised in this repo's CI."""

    name = "miniprogram-automator"
    requires_browser = False

    def __init__(self) -> None:
        if not shutil.which("node"):
            raise RuntimeError("miniprogram-automator driver needs node in PATH")
        if not AUTOMATOR_JS.exists():
            raise RuntimeError(f"missing {AUTOMATOR_JS}")

    def verify(self, *, page, base_url, lead_id, phone, code) -> str:
        env = {
            **os.environ,
            "MINI_BASE_URL": base_url,
            "MINI_LEAD_ID": lead_id,
            "MINI_PHONE": phone,
            "MINI_CODE": code,
            "WX_DEVTOOLS_CLI": os.getenv("WX_DEVTOOLS_CLI", ""),
            "MINI_PROJECT_PATH": os.getenv("MINI_PROJECT_PATH", str(ROOT / "mini" / "app")),
        }
        proc = subprocess.run(
            ["node", str(AUTOMATOR_JS)], capture_output=True, text=True,
            env=env, timeout=180,
        )
        if proc.returncode != 0:
            raise RuntimeError(
                "miniprogram-automator run failed (needs 微信开发者工具 with automation "
                f"port open): {proc.stderr[-800:] or proc.stdout[-800:]}")
        payload = json.loads(proc.stdout.strip().splitlines()[-1])
        member_id = payload.get("member_id")
        if not member_id:
            raise RuntimeError(f"automator returned no member_id: {payload}")
        return member_id


def make_driver(name: str | None = None) -> MiniDriver:
    name = (name or os.getenv("MINI_DRIVER") or "playwright-h5").strip()
    if name in ("playwright-h5", "h5", "playwright"):
        return H5Driver()
    if name in ("miniprogram-automator", "automator"):
        return AutomatorDriver()
    raise ValueError(f"unknown MINI_DRIVER={name!r}")
