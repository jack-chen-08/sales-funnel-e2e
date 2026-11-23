"""小程序两步（第 11、12 步）的真实执行入口。

执行方式
- 调用 Node 端微信官方 `miniprogram-simulate`，加载仓库内 `miniapp/components/member-entry`
  组件，得到真实渲染树、真实事件派发、真实 setData 逻辑。
- 组件内的 `wx.request` 由驱动脚本用 Node http 桥接，经 loopback 打到本仓自起的 mock
  平台（不出公网），响应为服务端真实返回。

能力边界（与 DELIVERY.md、EVIDENCE/miniprogram/summary.md 保持一致）
- 非真机：执行环境是 Node 上的官方模拟器，不是微信客户端。
- 无像素截图：模拟器产出渲染树（WXML 解析结果），不产生位图。
- 无微信登录态：`code2session` 由平台侧桩替代，openid 为确定性桩值。

依赖缺失时的行为：由调用方（pytest fixture `miniapp_ready`）先行判定并 skip，
不允许静默回退为接口桩 —— 回退会让报告谎称 12 步全跑。
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MINIAPP_DIR = ROOT / "miniapp"
DRIVER = ROOT / "scripts" / "miniapp_smoke.js"


def availability() -> tuple[bool, str]:
    """返回 (是否可执行, 原因)。原因用于 skip 提示，必须能指导修复。"""
    if shutil.which("node") is None:
        return False, (
            "小程序两步需要 Node.js 执行微信官方模拟器：请安装 Node.js ≥ 16 后执行 "
            "`bash scripts/setup_miniapp.sh`；仅需接口级验证时用 --skip-miniprogram 显式跳过"
        )
    if not (MINIAPP_DIR / "node_modules" / "miniprogram-simulate").exists():
        return False, "小程序执行依赖未安装：请先执行 `bash scripts/setup_miniapp.sh`"
    if not DRIVER.exists():
        return False, f"缺少小程序驱动脚本：{DRIVER}"
    if not (MINIAPP_DIR / "components" / "member-entry" / "index.js").exists():
        return False, "缺少小程序组件 miniapp/components/member-entry/index.js"
    return True, "ok"


def run(base_url: str, run_id: str, member_id: str, out_dir: Path, timeout: int = 240) -> dict:
    """执行小程序两步，返回 trace（含渲染树快照哈希、事件序列、真实请求响应、断言明细）。"""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for stale in ("trace.json", "requests.jsonl", "summary.md"):
        target = out_dir / stale
        if target.exists():
            target.unlink()

    cmd = [
        "node",
        str(DRIVER),
        "--base-url",
        base_url,
        "--run-id",
        run_id,
        "--member-id",
        str(member_id),
        "--out",
        str(out_dir),
    ]
    proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=timeout)

    trace_file = out_dir / "trace.json"
    if not trace_file.exists():
        detail = (proc.stderr or proc.stdout or "").strip()[-1200:]
        raise RuntimeError(f"小程序执行未产出 trace（退出码 {proc.returncode}）：{detail}")

    trace = json.loads(trace_file.read_text(encoding="utf-8"))
    trace["_driver_exit_code"] = proc.returncode
    trace["_driver_stdout"] = (proc.stdout or "").strip()
    if proc.returncode != 0:
        failed = trace.get("failedAssertions") or []
        raise RuntimeError(f"小程序两步断言失败：{failed}（证据见 {out_dir}）")
    return trace


def rel(path: Path) -> str:
    """仓库内相对路径，用于报告里的 artifacts 字段。"""
    try:
        return str(Path(path).resolve().relative_to(ROOT))
    except ValueError:
        return str(path)
