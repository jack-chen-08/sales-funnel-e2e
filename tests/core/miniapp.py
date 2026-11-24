"""小程序两步（第 11、12 步）的真实执行入口 —— 双执行器。

执行器（executor）
- ``automator``（主执行器，订单指定框架）：微信官方 ``miniprogram-automator`` 经开发者工具
  自动化端口驱动**整个小程序项目**。真实页面（pages/entry → pages/home）、真实
  ``<input>``/``<button>`` 事件、真实 ``wx.navigateTo`` 路由、真实渲染节点、真实截图。
- ``simulate``（补充执行器）：Node 端官方 ``miniprogram-simulate`` 单独加载
  ``miniapp/components/member-entry`` 组件，验证组件逻辑与渲染树；不经过页面壳与路由，
  因此**不能替代**页面级验收，只作为无开发者工具环境（CI）下的补充验证。
- ``auto``（默认）：能用 automator 就用 automator（开发者工具 + 依赖齐备），否则回退 simulate
  并把实际执行器与回退原因写进报告，绝不静默声称 automator 跑过。

能力边界（与 DELIVERY.md、README「小程序两步」章节保持一致）
- 两个执行器都**非真机**：执行环境是开发者工具/Node 模拟器，不是手机微信客户端。
- 无微信登录态：``code2session`` 由平台侧桩替代，openid 为确定性桩值。
- automator 有真实像素截图；simulate 只有渲染树（WXML 解析结果），无位图。

依赖缺失时的行为：由调用方（pytest fixture ``miniapp_ready``）先行判定并 skip，
不允许静默回退为接口桩 —— 回退会让报告谎称 12 步全跑。
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MINIAPP_DIR = ROOT / "miniapp"
DRIVERS = {
    "automator": ROOT / "scripts" / "miniapp_automator.js",
    "simulate": ROOT / "scripts" / "miniapp_smoke.js",
}
EXECUTORS = ("auto", "automator", "simulate")

# 执行环境可覆盖（默认：仓库内 miniapp/ + WSL 的 node）。
# 为什么需要覆盖：自动化通道（`cli auto`）会向服务端校验 AppID 归属，而仓库为了可移植性
# 把 project.config.json 的 appid 保持为 touristappid；真实跑通时把小程序工程镜像到装有
# 微信开发者工具的 Windows 侧，并用 Windows 的 node.exe 执行驱动脚本，三者必须一致。
#   MINIAPP_NODE               node 可执行文件（默认 PATH 中的 node；Windows 侧可传 node.exe 绝对路径）
#   MINIAPP_PROJECT_DIR        小程序工程目录（默认仓库 miniapp/；Windows 侧镜像目录）
#   MINIAPP_AUTOMATOR_DRIVER   automator 驱动脚本（默认仓库 scripts/miniapp_automator.js）
NODE_BIN = (os.environ.get("MINIAPP_NODE") or "node").strip()
PROJECT_DIR_RAW = (os.environ.get("MINIAPP_PROJECT_DIR") or "").strip()
AUTOMATOR_DRIVER_RAW = (os.environ.get("MINIAPP_AUTOMATOR_DRIVER") or "").strip()
# 自动化端口直连：开发者工具已用 `cli auto --project <dir> --auto-port <port>` 打开时，
# 传 ws://127.0.0.1:<port> 让驱动直接连接（Node 新版不能 spawn cli.bat，这是等价路径）。
AUTOMATOR_WS = (os.environ.get("MINIAPP_AUTOMATOR_WS") or "").strip()


def _local_path(raw: str, default: Path) -> Path:
    """把可能是 Windows 形式（C:\\... 或 .exe 路径）的配置转成 WSL 可检查的本地路径。"""
    if not raw:
        return default
    if re.match(r"^[A-Za-z]:[\\/]", raw) or raw.startswith("\\\\"):
        try:
            out = subprocess.run(
                ["wslpath", "-u", raw], capture_output=True, text=True, check=True
            ).stdout.strip()
            if out:
                return Path(out)
        except Exception:
            pass
    return Path(raw)


def project_dir() -> Path:
    """小程序工程目录（automator 用它做 node_modules/AppID 判定与 projectPath）。"""
    return _local_path(PROJECT_DIR_RAW, MINIAPP_DIR)


def automator_driver() -> Path:
    """automator 驱动脚本路径（Windows 侧执行时指向 Windows 镜像内的副本）。"""
    return _local_path(AUTOMATOR_DRIVER_RAW, DRIVERS["automator"])


def _is_windows_bin(bin_path: str) -> bool:
    return bool(re.match(r"^[A-Za-z]:[\\/]", bin_path)) or bin_path.lower().endswith(
        (".exe", ".bat", ".cmd")
    )


def _node_arg(path: Path) -> str:
    """传给 node 的路径参数：Windows 侧 node 需要 Windows/UNC 形式，WSL node 保持原样。"""
    if not _is_windows_bin(NODE_BIN):
        return str(path)
    try:
        return subprocess.run(
            ["wslpath", "-w", str(path)], capture_output=True, text=True, check=True
        ).stdout.strip() or str(path)
    except Exception:
        return str(path)


def _node_available() -> bool:
    if _is_windows_bin(NODE_BIN):
        return Path(NODE_BIN).exists() or _local_path(NODE_BIN, Path(NODE_BIN)).exists()
    return shutil.which(NODE_BIN) is not None

# 微信开发者工具 CLI 的常见位置（WSL 下通过 /mnt/c 访问 Windows 安装目录）
DEVTOOLS_CLI_CANDIDATES = (
    "/mnt/c/Program Files (x86)/Tencent/微信web开发者工具/cli.bat",
    "/mnt/c/Program Files/Tencent/微信web开发者工具/cli.bat",
    "/mnt/d/Program Files (x86)/Tencent/微信web开发者工具/cli.bat",
    "/mnt/d/Program Files/Tencent/微信web开发者工具/cli.bat",
    "C:\\Program Files (x86)\\Tencent\\微信web开发者工具\\cli.bat",
    "C:\\Program Files\\Tencent\\微信web开发者工具\\cli.bat",
)


def devtools_cli() -> str | None:
    """返回可用的开发者工具 CLI 路径；环境变量优先（可传 Windows 形式路径）。"""
    env = (os.environ.get("WECHAT_DEVTOOLS_CLI") or "").strip()
    if env and _local_path(env, Path(env)).exists():
        return env
    for candidate in DEVTOOLS_CLI_CANDIDATES:
        if Path(candidate).exists():
            return candidate
    return None


def _automator_availability() -> tuple[bool, str]:
    if not _node_available():
        return False, f"automator 执行器需要 Node.js ≥ 16（当前配置的 node 不可用：{NODE_BIN}）"
    if not (project_dir() / "node_modules" / "miniprogram-automator").exists():
        return False, (
            f"未安装 miniprogram-automator：请在 {project_dir()} 执行 `npm install`"
            "（或 bash scripts/setup_miniapp.sh）"
        )
    if devtools_cli() is None and not AUTOMATOR_WS:
        return False, (
            "未找到微信开发者工具 CLI：请安装微信开发者工具并开启「设置 → 安全设置 → 服务端口」，"
            "用环境变量 WECHAT_DEVTOOLS_CLI 指向 cli.bat，或用 MINIAPP_AUTOMATOR_WS 直连自动化端口"
            "（如 ws://127.0.0.1:9420）"
        )
    if not automator_driver().exists():
        return False, f"缺少 automator 驱动脚本：{automator_driver()}"
    appid = _miniapp_appid()
    if appid in ("", "touristappid"):
        return False, (
            "automator 执行器需要真实小程序 AppID：自动化通道（cli auto）会向服务端校验 AppID，"
            f"当前 miniapp/project.config.json 的 appid={appid!r} 会被拒（APPID_ERROR）。"
            "请在 project.config.json 填入真实 AppID 或「小程序测试号」AppID"
            "（测试号申请：https://mp.weixin.qq.com/wxamp/sandbox），并保持开发者工具已扫码登录"
        )
    return True, "ok"


def _miniapp_appid() -> str:
    """读取小程序工程 project.config.json 的 appid（小写）。"""
    cfg = project_dir() / "project.config.json"
    try:
        data = json.loads(cfg.read_text(encoding="utf-8"))
    except Exception:
        return ""
    return str(data.get("appid") or "").strip()


def _simulate_availability() -> tuple[bool, str]:
    if shutil.which("node") is None:
        return False, (
            "小程序两步需要 Node.js 执行微信官方模拟器：请安装 Node.js ≥ 16 后执行 "
            "`bash scripts/setup_miniapp.sh`；仅需接口级验证时用 --skip-miniprogram 显式跳过"
        )
    if not (MINIAPP_DIR / "node_modules" / "miniprogram-simulate").exists():
        return False, "小程序执行依赖未安装：请先执行 `bash scripts/setup_miniapp.sh`"
    if not DRIVERS["simulate"].exists():
        return False, f"缺少小程序驱动脚本：{DRIVERS['simulate']}"
    if not (MINIAPP_DIR / "components" / "member-entry" / "index.js").exists():
        return False, "缺少小程序组件 miniapp/components/member-entry/index.js"
    return True, "ok"


def resolve(requested: str = "auto") -> tuple[str | None, str, str]:
    """决定实际执行器。返回 (executor|None, 原因, 回退说明)。"""
    requested = (requested or "auto").strip().lower()
    if requested not in EXECUTORS:
        return None, f"未知执行器 {requested!r}，可选 {EXECUTORS}", ""
    auto_ok, auto_reason = _automator_availability()
    sim_ok, sim_reason = _simulate_availability()

    if requested == "automator":
        return ("automator", "ok", "") if auto_ok else (None, auto_reason, "")
    if requested == "simulate":
        return ("simulate", "ok", "") if sim_ok else (None, sim_reason, "")
    # auto
    if auto_ok:
        return "automator", "ok", ""
    if sim_ok:
        return "simulate", "ok", f"automator 不可用（{auto_reason}），已回退 simulate 执行器"
    return None, f"automator 不可用（{auto_reason}）；simulate 亦不可用（{sim_reason}）", ""


def availability(requested: str = "auto") -> tuple[bool, str, str, str]:
    """返回 (是否可执行, 原因, 实际执行器, 回退说明)。原因须能指导修复。"""
    executor, reason, fallback = resolve(requested)
    if executor is None:
        return False, reason, "", fallback
    return True, "ok", executor, fallback


def run(
    base_url: str,
    run_id: str,
    member_id: str,
    out_dir: Path,
    timeout: int = 240,
    executor: str = "simulate",
    devtools_cli_path: str | None = None,
    port: int = 9420,
) -> dict:
    """执行小程序两步，返回 trace（真实响应回读、事件序列、断言明细、截图/渲染树）。"""
    if executor not in DRIVERS:
        raise ValueError(f"run() 需要具体执行器，收到 {executor!r}")
    driver = automator_driver() if executor == "automator" else DRIVERS[executor]
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for stale in ("trace.json", "requests.jsonl", "summary.md"):
        target = out_dir / stale
        if target.exists():
            target.unlink()

    windows_side = executor == "automator" and _is_windows_bin(NODE_BIN)
    node_exe = str(_local_path(NODE_BIN, Path(NODE_BIN))) if _is_windows_bin(NODE_BIN) else NODE_BIN
    cmd = [
        node_exe,
        _node_arg(driver),
        "--base-url",
        base_url,
        "--run-id",
        run_id,
        "--member-id",
        str(member_id),
        "--out",
        _node_arg(out_dir) if windows_side else str(out_dir),
    ]
    if executor == "automator":
        # cli 路径始终显式传给驱动：Windows 侧 node 是跨 WSL 启动的，
        # 不依赖环境变量能否被正确继承（--ws 模式下它用于"端口没开就自己开"）。
        cli = devtools_cli_path or devtools_cli()
        if AUTOMATOR_WS:
            cmd += ["--ws", AUTOMATOR_WS]
            if cli:
                cmd += ["--devtools-cli", cli]
        else:
            if not cli:
                raise RuntimeError(
                    "automator 执行器缺少开发者工具 CLI（WECHAT_DEVTOOLS_CLI）或自动化端口（MINIAPP_AUTOMATOR_WS）"
                )
            cmd += ["--devtools-cli", cli, "--port", str(port)]
        timeout = max(timeout, 300)

    cwd = str(project_dir().parent) if windows_side else str(ROOT)
    proc = subprocess.run(
        cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace"
    )

    trace_file = out_dir / "trace.json"
    if not trace_file.exists():
        detail = (proc.stderr or proc.stdout or "").strip()[-1200:]
        raise RuntimeError(f"小程序执行未产出 trace（退出码 {proc.returncode}）：{detail}")

    trace = json.loads(trace_file.read_text(encoding="utf-8"))
    trace["_driver_exit_code"] = proc.returncode
    trace["_driver_stdout"] = (proc.stdout or "").strip()
    trace["_executor"] = executor
    if proc.returncode != 0:
        failed = trace.get("failedAssertions") or []
        raise RuntimeError(f"小程序两步断言失败（{executor}）：{failed}（证据见 {out_dir}）")
    return trace


def rel(path: Path) -> str:
    """仓库内相对路径，用于报告里的 artifacts 字段。"""
    try:
        return str(Path(path).resolve().relative_to(ROOT))
    except ValueError:
        return str(path)
