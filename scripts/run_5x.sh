#!/usr/bin/env bash
# AC1：连续跑 5 次完整 12 步链式用例，逐次留存报告、日志与产物到 EVIDENCE/run_5x/
set -euo pipefail
cd "$(dirname "$0")/.."

OUT="EVIDENCE/run_5x"
rm -rf "$OUT"
mkdir -p "$OUT"

for i in 1 2 3 4 5; do
  echo "==================== 第 ${i} / 5 次 ===================="
  mkdir -p "$OUT/run_${i}"
  if ! .venv/bin/python -m pytest -m chain -q --run-tag "5x-r${i}" 2>&1 | tee "$OUT/run_${i}/pytest.log"; then
    echo "第 ${i} 次未通过，终止"
    exit 1
  fi
  LATEST_JSON="$(ls -t reports/run_smk-5x-r${i}-*.json | head -1)"
  RID="$(basename "$LATEST_JSON" .json)"
  RID="${RID#run_}"
  cp "$LATEST_JSON" "$OUT/run_${i}/report.json"
  cp "reports/run_${RID}.md" "$OUT/run_${i}/report.md"
  mkdir -p "$OUT/run_${i}/artifacts"
  cp -r "reports/artifacts/${RID}/." "$OUT/run_${i}/artifacts/"
  echo "$RID" > "$OUT/run_${i}/run_id.txt"
  .venv/bin/python - "$OUT/run_${i}/report.json" <<'PY'
import json, sys
r = json.load(open(sys.argv[1], encoding="utf-8"))
print(
    f"第 {r['run_id']}: status={r['status']} 通过={r['counts']['passed']} "
    f"总耗时={r['total_duration_ms'] / 1000:.2f}s 清理残留={r['cleanup']['remaining_total']}"
)
PY
done

echo "==================== 汇总 ===================="
.venv/bin/python - "$OUT" <<'PY'
import json, sys
from pathlib import Path

out = Path(sys.argv[1])
rows = []
for i in range(1, 6):
    r = json.load(open(out / f"run_{i}" / "report.json", encoding="utf-8"))
    rows.append(
        {
            "run": i,
            "run_id": r["run_id"],
            "status": r["status"],
            "passed": r["counts"]["passed"],
            "failed": r["counts"]["failed"],
            "skipped": r["counts"]["skipped"],
            "total_duration_ms": r["total_duration_ms"],
            "total_duration_s": round(r["total_duration_ms"] / 1000, 2),
            "cleanup_remaining": r["cleanup"]["remaining_total"],
            "cleanup_deleted": r["cleanup"]["deleted_total"],
            "ui_steps": [s["no"] for s in r["steps"] if s["mode"] == "ui"],
            "miniapp_steps": [s["no"] for s in r["steps"] if s["mode"] == "miniapp"],
            "miniapp_executors": sorted(
                {
                    (s.get("evidence") or {}).get("evidence", {}).get("executor")
                    for s in r["steps"]
                    if s["mode"] == "miniapp"
                }
            ),
            "step_durations_s": {s["no"]: round(s["duration_ms"] / 1000, 2) for s in r["steps"]},
        }
    )
avg = sum(x["total_duration_ms"] for x in rows) / len(rows)
summary = {
    "runs": rows,
    "passed_runs": sum(1 for x in rows if x["status"] == "passed"),
    "avg_duration_ms": round(avg, 1),
    "avg_duration_s": round(avg / 1000, 2),
    "max_duration_s": round(max(x["total_duration_ms"] for x in rows) / 1000, 2),
    "limit_s": 600,
    "all_within_limit": all(x["total_duration_ms"] <= 600_000 for x in rows),
    "all_cleanup_zero": all(x["cleanup_remaining"] == 0 for x in rows),
    "all_miniapp_executed": all(x["miniapp_steps"] == [11, 12] for x in rows),
    "miniapp_executor": sorted({e for x in rows for e in x["miniapp_executors"]}),
}
(out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

lines = [
    "| 次数 | run_id | 结果 | 通过 | 总耗时(s) | 清理后残留 | 小程序两步执行方式 |",
    "| --- | --- | --- | --- | --- | --- | --- |",
]
for x in rows:
    mini = (
        f"步骤 {x['miniapp_steps']} 由 {', '.join(str(e) for e in x['miniapp_executors'])} 执行"
        if x["miniapp_steps"]
        else "未执行"
    )
    lines.append(
        f"| {x['run']} | `{x['run_id']}` | {x['status']} | {x['passed']}/12 | {x['total_duration_s']} | {x['cleanup_remaining']} | {mini} |"
    )
lines.append("")
lines.append(f"- 通过次数：{summary['passed_runs']}/5")
lines.append(f"- 平均耗时：{summary['avg_duration_s']}s（上限 600s）")
lines.append(f"- 最长单次：{summary['max_duration_s']}s")
lines.append(
    f"- 小程序两步（11、12）均真实执行：{summary['all_miniapp_executed']}"
    f"（执行器：{', '.join(str(e) for e in summary['miniapp_executor'])}）"
)
(out / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))
PY
