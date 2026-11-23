#!/usr/bin/env bash
# AC3：按 run_id 清理校验。先查库内 12 张业务表 + smoke_runs 的行数，再调清理接口回查。
# 用法：scripts/check_cleanup.sh <run_id>
set -euo pipefail
cd "$(dirname "$0")/.."

RUN_ID="${1:?用法: scripts/check_cleanup.sh <run_id>}"
set -a
# shellcheck disable=SC1091
source .env
set +a

TABLES=(applications leads contacts visits visit_minutes quotes esign_envelopes rooms handovers members resource_recommendations audit_events)

SQL=""
for t in "${TABLES[@]}"; do
  [[ -n "$SQL" ]] && SQL+=" UNION ALL "
  SQL+="SELECT '$t' AS table_name, count(*) AS rows FROM $t WHERE run_id = '$RUN_ID'"
done

echo "== 数据库直查（psql）run_id=${RUN_ID} =="
docker exec smoke-pg psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -c "$SQL" \
  -c "SELECT count(*) AS smoke_runs_rows FROM smoke_runs WHERE run_id = '$RUN_ID'" \
  -c "SELECT coalesce(sum(rows), 0) AS remaining_rows_total FROM ($SQL) s"

echo "== 平台清理接口回查 =="
curl -s "http://127.0.0.1:${SMOKE_PLATFORM_PORT:-5600}/api/admin/run/${RUN_ID}/counts"
echo
