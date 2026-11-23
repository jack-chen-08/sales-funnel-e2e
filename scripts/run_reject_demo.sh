#!/usr/bin/env bash
# 电子签桩拒签失败路径演示（AC2）：起一个 SIGN_STUB_MODE=reject 的平台实例（5601），
# 跑 esign_reject 用例，把报告 / trace / 截图 收进 EVIDENCE/esign_reject/。
set -euo pipefail
cd "$(dirname "$0")/.."

set -a
# shellcheck disable=SC1091
source .env
set +a

PORT="${REJECT_PORT:-5601}"
OUT="EVIDENCE/esign_reject"
mkdir -p "$OUT" reports

echo "== 启动拒签桩实例 http://127.0.0.1:${PORT}（SIGN_STUB_MODE=reject）=="
SIGN_STUB_MODE=reject .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port "$PORT" \
  > "reports/platform_reject.log" 2>&1 &
PID=$!
trap 'kill $PID 2>/dev/null || true' EXIT

for _ in $(seq 1 40); do
  if curl -sf "http://127.0.0.1:${PORT}/healthz" | grep -q '"sign_stub_mode":"reject"'; then
    break
  fi
  sleep 0.5
done
echo "健康检查：$(curl -s "http://127.0.0.1:${PORT}/healthz")"

echo "== 跑拒签失败路径用例 =="
set +e
.venv/bin/python -m pytest -m esign_reject -q --smoke-base-url "http://127.0.0.1:${PORT}" 2>&1 | tee "$OUT/pytest.log"
RC=${PIPESTATUS[0]}
set -e

LATEST_JSON="$(ls -t reports/run_smk-reject-*.json | head -1)"
RID="$(basename "$LATEST_JSON" .json)"
RID="${RID#run_}"
mkdir -p "$OUT/artifacts"
cp "$LATEST_JSON" "$OUT/report.json"
cp "reports/run_${RID}.md" "$OUT/report.md"
cp -r "reports/artifacts/${RID}/." "$OUT/artifacts/"
echo "$RID" > "$OUT/run_id.txt"

echo "== 失败步骤摘要 =="
.venv/bin/python - "$OUT/report.json" <<'PY'
import json, sys
r = json.load(open(sys.argv[1], encoding="utf-8"))
f = r["failed_step"]
print(f"run_id={r['run_id']} status={r['status']}")
print(f"失败步骤：#{f['no']}「{f['name']}」原因：{f['reason']}")
s8 = next(s for s in r["steps"] if s["no"] == 8)
print(f"步骤8 证据：trace={s8['artifacts'].get('trace')} screenshot={s8['artifacts'].get('screenshot')}")
print(f"清理后残留行数：{r['cleanup']['remaining_total']}")
PY

echo "退出码：$RC（0 表示成功检出拒签并点名「电子签」步骤）"
exit "$RC"
