#!/usr/bin/env bash
# 跳过小程序两步（11/12），其余 10 步照常执行；报告与产物自动收进 EVIDENCE/skip_miniprogram/
set -euo pipefail
cd "$(dirname "$0")/.."

OUT="EVIDENCE/skip_miniprogram"
# 纯语义 tag：make_run_id 自身已拼 <日期>-<时间>-<uuid>，tag 再带数字就会双时间戳
TAG="skipmode"
mkdir -p "$OUT" reports

MARK="$(mktemp)"
trap 'rm -f "$MARK"' EXIT

.venv/bin/python -m pytest -m skip_mode -q --skip-miniprogram --run-tag "$TAG" "$@" 2>&1 \
  | tee "$OUT/pytest.log"

# 本次运行产出的报告（按 mtime 过滤，避免历史 run 混入），先命令行开关、后 marker
mapfile -t REPORTS < <(find reports -maxdepth 1 -name "run_smk-${TAG}-*.json" -newer "$MARK" | sort)
if [ "${#REPORTS[@]}" -lt 1 ]; then
  echo "未找到本次运行的报告：reports/run_smk-${TAG}-*.json" >&2
  exit 1
fi

collect() {
  local report="$1" name="$2"
  local rid
  rid="$(basename "$report" .json)"
  rid="${rid#run_}"
  cp "$report" "$OUT/${name}.json"
  cp "reports/run_${rid}.md" "$OUT/${name}.md"
  rm -rf "$OUT/${name}_artifacts"
  mkdir -p "$OUT/${name}_artifacts"
  cp -r "reports/artifacts/${rid}/." "$OUT/${name}_artifacts/"
  echo "$rid" > "$OUT/${name}_run_id.txt"
}

collect "${REPORTS[0]}" "report"
if [ "${#REPORTS[@]}" -ge 2 ]; then
  collect "${REPORTS[1]}" "report_marker"
fi

# 兼容旧引用：主报告同时以 run_id.txt 记录
cp "$OUT/report_run_id.txt" "$OUT/run_id.txt"

echo "== 已收集到 ${OUT}/ =="
ls -1 "$OUT"
