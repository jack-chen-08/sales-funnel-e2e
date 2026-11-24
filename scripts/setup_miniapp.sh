#!/usr/bin/env bash
# 安装小程序自动化执行依赖（Node 侧，仅用于自动化，不影响小程序运行）。
# 幂等：已安装则不重复拉取。
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
MINIAPP="$ROOT/miniapp"

if ! command -v node >/dev/null 2>&1; then
  echo "[setup-miniapp] 未检测到 node，请先安装 Node.js ≥ 16" >&2
  exit 1
fi

echo "[setup-miniapp] node $(node -v) / npm $(npm -v)"

if [ -d "$MINIAPP/node_modules/miniprogram-simulate" ] \
  && [ -d "$MINIAPP/node_modules/jsdom-global" ] \
  && [ -d "$MINIAPP/node_modules/miniprogram-automator" ]; then
  echo "[setup-miniapp] 依赖已就绪，跳过安装"
  exit 0
fi

cd "$MINIAPP"
if [ -f package-lock.json ]; then
  npm ci --silent
else
  npm install --silent
fi

echo "[setup-miniapp] 依赖安装完成：$(ls node_modules | wc -l) 个包"
