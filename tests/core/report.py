"""报告输出：reports/run_<run_id>.json 与同名 .md。"""

from __future__ import annotations

import json
from pathlib import Path


def write_reports(report: dict, reports_dir: Path) -> tuple[Path, Path]:
    reports_dir.mkdir(parents=True, exist_ok=True)
    run_id = report["run_id"]
    json_path = reports_dir / f"run_{run_id}.json"
    md_path = reports_dir / f"run_{run_id}.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return json_path, md_path


def _fmt_ms(value: float | int | None) -> str:
    if value is None:
        return "-"
    return f"{value / 1000:.2f}s"


def render_markdown(report: dict) -> str:
    lines: list[str] = []
    total_s = report.get("total_duration_ms", 0) / 1000
    lines.append(f"# 招商全链路冒烟报告 · {report['run_id']}")
    lines.append("")
    lines.append(f"- 结论：**{_status_cn(report['status'])}**")
    lines.append(f"- 模式：{report['mode']}（小程序步骤{'跳过' if report['skip_miniprogram'] else '执行'}）")
    lines.append(f"- 平台地址：{report['base_url']}")
    lines.append(f"- 开始：{report['started_at']}　结束：{report['finished_at']}")
    lines.append(f"- 总耗时：**{total_s:.2f}s**（阈值 600s）")
    lines.append(f"- 通过 / 跳过 / 失败：{report['counts']['passed']} / {report['counts']['skipped']} / {report['counts']['failed']}")
    if report.get("failed_step"):
        fs = report["failed_step"]
        lines.append("")
        lines.append(f"> 失败步骤：**{fs['no']}. {fs['name']}**　原因：`{fs['reason']}`")
    lines.append("")
    lines.append("| # | 步骤 | 执行方 | 方式 | 状态 | 耗时 | 关键断言 |")
    lines.append("|---|------|--------|------|------|------|----------|")
    for step in report["steps"]:
        lines.append(
            f"| {step['no']} | {step['name']} | {step['actor']} | {step['mode']} | "
            f"{_status_cn(step['status'])} | {_fmt_ms(step['duration_ms'])} | {step['assertion']} |"
        )
    lines.append("")
    lines.append("## 已创建数据 ID")
    lines.append("")
    lines.append("```json")
    lines.append(json.dumps(report.get("created_ids", {}), ensure_ascii=False, indent=2))
    lines.append("```")
    cleanup = report.get("cleanup")
    lines.append("")
    lines.append("## run_id 清理校验")
    lines.append("")
    if cleanup:
        lines.append(f"- 清理时间：{cleanup['cleaned_at']}")
        lines.append(f"- 删除行数合计：{cleanup['deleted_total']}")
        lines.append(f"- 剩余行数合计：**{cleanup['remaining_total']}**")
        lines.append("")
        lines.append("| 表 | 删除 | 剩余 |")
        lines.append("|----|------|------|")
        for table, deleted in cleanup["deleted"].items():
            lines.append(f"| {table} | {deleted} | {cleanup['remaining'][table]} |")
    else:
        lines.append("- 未执行清理")
    artifacts = report.get("artifacts", {})
    if artifacts:
        lines.append("")
        lines.append("## 证据文件")
        lines.append("")
        for name, path in artifacts.items():
            lines.append(f"- {name}: `{path}`")
    lines.append("")
    return "\n".join(lines)


def _status_cn(status: str) -> str:
    return {"passed": "通过", "failed": "失败", "skipped": "跳过", "running": "运行中"}.get(status, status)
