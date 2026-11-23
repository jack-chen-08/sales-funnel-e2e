#!/usr/bin/env bash
# AC3 取证：清理前（数据库直查非 0）→ 调 DELETE 接口按 run_id 清理 → 清理后（数据库直查为 0）
set -euo pipefail
cd "$(dirname "$0")/.."

set -a
# shellcheck disable=SC1091
source .env
set +a

OUT="EVIDENCE/cleanup"
mkdir -p "$OUT"

echo "== 1. 跑完整链并保留数据 =="
SMOKE_KEEP_DATA=1 .venv/bin/python scripts/cleanup_proof.py --run-tag ac3-before 2>&1 | tee "$OUT/before.log"
RUN_ID="$(grep -oP '^RUN_ID=\K.*' "$OUT/before.log" | head -1)"
echo "$RUN_ID" > "$OUT/run_id_before_after.txt"

echo "== 2. 清理前数据库直查 =="
bash scripts/check_cleanup.sh "$RUN_ID" 2>&1 | tee "$OUT/psql_before_cleanup.log"

echo "== 3. 调清理接口 DELETE /api/admin/run/${RUN_ID} =="
curl -s -X DELETE "http://127.0.0.1:${SMOKE_PLATFORM_PORT:-5600}/api/admin/run/${RUN_ID}" | tee "$OUT/delete_api_response.json"
echo

echo "== 4. 清理后数据库直查 =="
bash scripts/check_cleanup.sh "$RUN_ID" 2>&1 | tee "$OUT/psql_after_cleanup.log"

echo "== 结论：见 $OUT/psql_before_cleanup.log 与 $OUT/psql_after_cleanup.log =="
