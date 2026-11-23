"""Turn the JSON reports into the human-readable artefacts the ACs ask for.

输入：reports/_runtime/（每次运行生成，已 gitignore）
输出（固定命名，进版本库，作为交付样例）：
  reports/step_duration_report.md            步骤耗时报告样例（每步 + 合计）
  reports/step_duration_report_skip_mini.md  SKIP_MINI=1 时 10 步的耗时报告
  reports/failure_report_esign.md            电子签拒签失败报告（步骤名 + trace + 已建数据 ID）
  reports/run_report.md                      运行报告（5 连跑汇总 + AC 对照）
  reports/chain_5x_summary.json              5 连跑机器可读汇总（样例）
  reports/sample_report_ac1.json             单次运行完整 JSON（样例）
  reports/artifacts/failure_step8_example.png 失败截图（样例，固定名）
"""
from __future__ import annotations

import json
import platform
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
RUNTIME = REPORTS / "_runtime"
SAMPLE_SHOT = "artifacts/failure_step8_example.png"


def load(name: str) -> dict:
    path = RUNTIME / name
    if not path.exists():
        raise SystemExit(
            f"缺少运行时产物 {path.relative_to(ROOT)}。\n"
            "先跑：.venv/bin/pytest -q && .venv/bin/python scripts/run_5x.py")
    return json.loads(path.read_text(encoding="utf-8"))


def step_table(report: dict) -> str:
    lines = [
        "| # | 步骤 | 结果 | 耗时 (ms) | 占比 |",
        "|---|------|------|-----------|------|",
    ]
    total = report["total_ms"] or 1
    for s in report["steps"]:
        share = s["duration_ms"] / total * 100
        lines.append(f"| {s['index']} | {s['name']} | {s['status']} | "
                     f"{s['duration_ms']:.1f} | {share:.1f}% |")
    lines.append(f"| — | **合计（{len(report['steps'])} 步 + 收尾）** | "
                 f"{'passed' if report['ok'] else 'failed'} | "
                 f"**{report['total_ms']:.1f}** | 100% |")
    return "\n".join(lines)


def duration_report(report: dict, title: str) -> str:
    ui = [s for s in report["steps"] if any(t.get("method") == "BROWSER" for t in s["trace"])]
    ui_ms = sum(s["duration_ms"] for s in ui)
    return f"""# {title}

- run_id：`{report['run_id']}`
- 开始：{report['started_at']}　结束：{report['finished_at']}
- 小程序执行器：`{report.get('mini_driver', '-')}`　跳过小程序：{report['skip_mini']}
- 总耗时：**{report['total_ms'] / 1000:.2f} s**（红线 600 s，余量 {600 - report['total_ms'] / 1000:.0f} s）

## 每步耗时

{step_table(report)}

## 读数说明

- 浏览器步（真实 Playwright 驱动）：{", ".join(s['name'] for s in ui) or "无"}，合计 {ui_ms:.0f} ms。
- 其余步骤走真实 HTTP 请求，毫秒级，说明瓶颈在 UI 渲染而非接口。
- 总耗时为单次链式运行；AC1 的「平均 ≤ 10 min」由 5 连跑实测数据支撑，见 run_report.md。
"""


def failure_report(report: dict, shot_rel: str) -> str:
    failed_view = {**report, "ok": False}
    steps_tbl = step_table(failed_view)
    trace_lines = []
    for i, t in enumerate(report["trace"], 1):
        if "traceback" in t:
            trace_lines.append(f"### 异常栈（尾部）\n\n```\n{t['traceback']}\n```")
        else:
            trace_lines.append(
                f"### 请求 {i}：`{t.get('method')} {t.get('path')}` → {t.get('status')}\n\n"
                f"- 耗时：{t.get('ms')} ms\n- 响应体：\n\n```json\n{t.get('body', '')}\n```")
    ids = "\n".join(f"| {k} | `{v}` |" for k, v in report["data_ids"].items()
                    if k != "recommendation_count")
    return f"""# 失败注入报告样例：电子签拒签

注入方式：`ChainRunner(..., esign_reject=True)`（等价于电子签桩返回 422 ESIGN_REJECTED）。

| 项 | 值 |
|----|----|
| 结论 | **失败（预期）** |
| 失败步骤 | **第 {report['failed_step_index']} 步「{report['failed_step']}」** |
| 错误 | `{report['error'][:160]}` |
| 已执行步数 | {len(report['steps'])}（失败即停，后续步骤未执行） |
| 收尾 | run_id 数据已清理，残留 {report['counts_after_cleanup']['total']} 条 |

## 失败点之前的步骤

{steps_tbl}

## 该步的请求 trace

{chr(10).join(trace_lines)}

## 失败截图

![失败步骤截图]({shot_rel})

> 截图为运行时 Playwright 打开的步骤状态页，失败步骤一行标红。

## 本次运行已创建的数据 ID（用于回溯清理）

| 实体 | ID |
|------|----|
{ids}

## 判读

报告在**步骤名 + HTTP 状态 + 业务错误码 + 异常栈**四个层面同时指出「电子签」这一环，
不是笼统的「链路失败」；trace 内 `ESIGN_REJECTED` 可直接对应到电子签桩的拒签分支。
"""


def run_report() -> str:
    summary = load("chain_5x_summary.json")
    ac2 = load("report_ac2_esign_reject.json")
    ac4 = load("report_ac4_skip_mini.json")
    rows = "\n".join(
        f"| {r['run']} | `{r['run_id']}` | {'✅ 通过' if r['ok'] else '❌ 失败'} | "
        f"{r['passed_steps']}/{r['total_steps']} | {r['chain_ms'] / 1000:.2f} | "
        f"{r['wall_s']:.2f} | {r['leftover_after_cleanup']} |"
        for r in summary["runs"])
    a4_rows = "\n".join(
        f"| {s['index']} | {s['name']} | {s['status']} |" for s in ac4["steps"])
    return f"""# 链式用例运行报告

- 生成时间：{ac2['started_at'][:10]}
- 被测对象：本仓 `app/` 参考桩（对外接口约定与真实平台一致，替换 base_url 即可对接）
- 用例：#1–#12 招商闭环，单一 run_id 串联
- 环境：{platform.platform()} · Python {platform.python_version()} · Playwright chromium · FastAPI(uvicorn)

## AC1 连续 {summary['attempts']} 次运行

| 次序 | run_id | 结果 | 通过步数 | 链耗时 (s) | 实际耗时 (s) | 残留数据 |
|------|--------|------|----------|------------|--------------|----------|
{rows}

- {summary['attempts']} 次全部通过：**{summary['all_passed']}**
- 平均链耗时：**{summary['avg_chain_seconds']} s**（红线 600 s，余量 {600 - summary['avg_chain_seconds']:.0f} s）
- 最大单次：{summary['max_chain_ms'] / 1000:.2f} s
- {summary['attempts']} 次合计残留数据：**{summary['leftover_total']}** 条

复现命令：

```bash
.venv/bin/python scripts/run_5x.py          # 输出上表并落盘 reports/_runtime/chain_5x_summary.json
```

## AC2 电子签拒签报告

| 项 | 实测值 |
|----|--------|
| failed_step | **{ac2['failed_step']}** |
| failed_step_index | {ac2['failed_step_index']} |
| 错误码 | 命中 `ESIGN_REJECTED`：{str('ESIGN_REJECTED' in ac2['error'])} |
| trace 条数 | {len(ac2['trace'])}（含 422 响应与异常栈） |
| 失败即停 | 仅执行 {len(ac2['steps'])} 步 |
| 明细 | 见 `reports/failure_report_esign.md` |

## AC3 run_id 数据清理

- 单次运行收尾会调用 `POST /api/_test/purge?run_id=…`，并用**独立于 runner 的第二个 HTTP 客户端**复查 `GET /api/_test/count`。
- 实测：5 次运行合计残留 **{summary['leftover_total']}** 条；单次校验见 `test_ac3_run_data_purged_after_run`。

## AC4 跳过小程序后其余 10 步

`SKIP_MINI=1`（或 `ChainRunner(skip_mini=True)`）实测：

| # | 步骤 | 结果 |
|---|------|------|
{a4_rows}

- 跳过 2 步、执行 10 步，整链结果：**{'通过' if ac4['ok'] else '失败'}**

## 复现

```bash
.venv/bin/pytest -q                                       # 全部用例
.venv/bin/python scripts/run_5x.py                        # AC1 证据（5 连跑）
SKIP_MINI=1 .venv/bin/python scripts/run_5x.py --runs 1   # AC4 证据（可选）
.venv/bin/python scripts/make_reports.py                  # 从 _runtime 生成上述样例
```
"""


def main() -> None:
    single = load("report_ac1_single.json")
    ac2 = load("report_ac2_esign_reject.json")
    ac4 = load("report_ac4_skip_mini.json")

    (REPORTS / "step_duration_report.md").write_text(
        duration_report(single, "步骤耗时报告样例（12 步全链）"), encoding="utf-8")
    (REPORTS / "step_duration_report_skip_mini.md").write_text(
        duration_report(ac4, "步骤耗时报告样例（SKIP_MINI=1，执行 10 步）"), encoding="utf-8")
    (REPORTS / "failure_report_esign.md").write_text(
        failure_report(ac2, SAMPLE_SHOT), encoding="utf-8")
    (REPORTS / "run_report.md").write_text(run_report(), encoding="utf-8")

    # 机器可读样例（固定名，避免每次运行新增文件）
    arts = REPORTS / "artifacts"
    arts.mkdir(parents=True, exist_ok=True)
    src = ac2.get("screenshot")
    if src:
        src_path = (ROOT / src)
        if src_path.exists():
            shutil.copyfile(src_path, arts / Path(SAMPLE_SHOT).name)
    for src_name, dst_name in (("report_ac1_single.json", "sample_report_ac1.json"),
                               ("chain_5x_summary.json", "chain_5x_summary.json")):
        (REPORTS / dst_name).write_text(
            json.dumps(load(src_name), ensure_ascii=False, indent=2), encoding="utf-8")

    print("written:", *(p.name for p in sorted(REPORTS.glob("*.md"))),
          *(p.name for p in sorted(REPORTS.glob("*.json"))))


if __name__ == "__main__":
    main()
