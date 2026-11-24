#!/usr/bin/env bash
# 打开微信开发者工具的「自动化端口」，让页面级 automator 用例能连上。
#
# 为什么单独一步、不让用例自己重开工具：
#   驱动半路重启开发者工具会让窗口状态不可预期（实测会挂在 getPageMetaByWebviewId
#   返回 null 上）。所以拆成显式两步：先开端口，再跑用例；没开就明确报错。
#
# 用法：
#   export WECHAT_DEVTOOLS_CLI='C:\Program Files (x86)\Tencent\微信web开发者工具\cli.bat'
#   export MINIAPP_PROJECT_DIR='C:\path\to\miniapp'      # 带真实 AppID 的小程序工程目录
#   bash scripts/open_automator_port.sh                  # 端口默认 9420，可用 MINIAPP_AUTOMATOR_PORT 覆盖
#
# 前置条件（只做一次）：
#   1) 微信开发者工具已安装并已用微信扫码登录（登录态会持久化，重启工具不用重扫）；
#   2) 工具内「设置 → 安全设置 → 服务端口」已打开；
#   3) 小程序工程 project.config.json 的 appid 是当前登录账号有权访问的（`cli auto` 会校验归属）。
set -euo pipefail

PORT="${MINIAPP_AUTOMATOR_PORT:-9420}"
CLI="${WECHAT_DEVTOOLS_CLI:-}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROJECT="${MINIAPP_PROJECT_DIR:-$ROOT/miniapp}"

die() { echo "[fail] $*" >&2; exit 1; }
[ -n "$CLI" ] || die "未设置 WECHAT_DEVTOOLS_CLI（微信开发者工具 cli.bat 路径）"

PS=/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe
CMD=/mnt/c/Windows/System32/cmd.exe

# 统一转成 Windows 形式路径：C:\... 原样保留，/mnt/c/... 或 WSL 路径用 wslpath 转
to_win() {
  case "$1" in
    [A-Za-z]:[\\/]*) printf '%s' "$1" ;;
    *) if command -v wslpath >/dev/null 2>&1; then wslpath -w "$1" 2>/dev/null || printf '%s' "$1"; else printf '%s' "$1"; fi ;;
  esac
}
CLI_WIN="$(to_win "$CLI")"
PROJECT_WIN="$(to_win "$PROJECT")"

# 端口探测：TcpClient 直连，比 Test-NetConnection 快一个数量级（后者每次 2~3s）
port_open() {
  "$PS" -NoProfile -Command "\$c=New-Object Net.Sockets.TcpClient; try{\$c.Connect('127.0.0.1',$PORT); 'true'}catch{'false'}finally{\$c.Close()}" 2>/dev/null | tr -d '\r' | grep -qi true
}

if port_open; then
  echo "[skip] 自动化端口 $PORT 已开启，直接用即可"
  exit 0
fi

# 通过临时 .bat 调用：cmd.exe 的工作目录不能是 UNC（WSL 路径），且 .bat 带空格路径易被引号吃掉
TEMP_WIN="$("$PS" -NoProfile -Command '$env:TEMP' 2>/dev/null | tr -d '\r')"
TEMP_WSL="$(wslpath -u "$TEMP_WIN")"
BAT_WSL="$TEMP_WSL/open_automator_port_${PORT}.bat"
BAT_WIN="$(to_win "$BAT_WSL")"
{
  echo '@echo off'
  echo '"'"$CLI_WIN"'" auto --project "'"$PROJECT_WIN"'" --auto-port '"$PORT"
} > "$BAT_WSL"

echo "[info] 端口 $PORT 未开启，调用 cli auto 打开项目窗口："
echo "       cli  = $CLI_WIN"
echo "       proj = $PROJECT_WIN"
out="$( (cd "$TEMP_WSL" && "$CMD" /c "$BAT_WIN") 2>&1 || true )"
echo "$out" | sed 's/^/       /'

for i in $(seq 1 60); do
  sleep 1
  if port_open; then
    echo "[ok] 自动化端口 $PORT 已开启（等待 ${i}s）"
    exit 0
  fi
done

die "60s 内端口 $PORT 未开启。检查：①开发者工具是否已登录（可能弹了扫码框）②「设置→安全设置→服务端口」是否打开 ③project.config.json 的 appid 是否属于当前登录账号。cli 输出见上。"
