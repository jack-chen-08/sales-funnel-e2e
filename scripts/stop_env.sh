#!/usr/bin/env bash
# 停掉 mock 平台与数据库容器
set -euo pipefail
cd "$(dirname "$0")/.."

if [[ -f .platform.pid ]]; then
  kill "$(cat .platform.pid)" 2>/dev/null || true
  rm -f .platform.pid
fi
docker compose down
