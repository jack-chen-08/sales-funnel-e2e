#!/usr/bin/env bash
# 跑 1 次 12 步链式用例（默认全 12 步）
set -euo pipefail
cd "$(dirname "$0")/.."
.venv/bin/python -m pytest -m chain -q "$@"
