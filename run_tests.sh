#!/usr/bin/env bash
# 一键跑通：建 venv -> 装依赖 -> 装浏览器 -> 跑 5 条用例
set -euo pipefail
cd "$(dirname "$0")"

[ -d .venv ] || python3 -m venv .venv
.venv/bin/pip install -q -r requirements.txt
.venv/bin/playwright install chromium >/dev/null 2>&1 || \
  echo "WARN: chromium 下载失败，浏览器步会失败；可用 PLAYWRIGHT_DOWNLOAD_HOST 指定镜像"

.venv/bin/pytest -q "$@"
