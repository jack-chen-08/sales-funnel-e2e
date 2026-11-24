"""测试入口：12 步链式冒烟（AC1）、跳过小程序模式（AC4）、电子签拒签失败路径（AC2）。

run_id 清理校验（AC3）在主链路与跳过模式两条用例中都做断言：报告 cleanup.remaining_total == 0。
"""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from tests.core.runner import ROOT, ChainRunner, run_chain

FULL_STEP_COUNT = 12
SKIP_STEP_COUNT = 10
DURATION_LIMIT_MS = 600_000

# 执行器 → trace 里的 tool 标识 / 证据文件（页面级 automator 出截图，组件级 simulate 出渲染树）
EXECUTOR_TOOL = {"automator": "miniprogram-automator", "simulate": "miniprogram-simulate"}


def _report_path(report: dict) -> Path:
    return ROOT / "reports" / f"run_{report['run_id']}.json"


@pytest.mark.chain
def test_recruitment_chain_all_12_steps(
    base_url, make_run_id, skip_miniprogram, headless, miniapp_ready, miniapp_executor
):
    """AC1：12 步链式用例按顺序全部通过，总耗时不超过 10 分钟，结束后 run_id 数据清零（AC3）。

    小程序两步（11、12）由 miniapp_executor 指定的执行器真实执行：
    automator = 页面级（订单指定框架，真实页面 + 真实路由 + 真实节点），simulate = 组件级补充。
    """
    if not skip_miniprogram and not miniapp_ready[0]:
        pytest.skip(f"小程序两步无法真实执行，本用例不做接口桩降级：{miniapp_ready[1]}")

    run_id = make_run_id("chain")
    runner, report, failure = run_chain(
        base_url,
        run_id,
        skip_miniprogram=skip_miniprogram,
        headless=headless,
        scenario="chain",
        miniapp_executor=miniapp_ready[2] or miniapp_executor,
    )

    assert failure is None, f"链路失败：{failure}（证据：{failure.artifacts if failure else {}}）"
    assert report["status"] == "passed", json.dumps(report["failed_step"], ensure_ascii=False)

    expected = SKIP_STEP_COUNT if skip_miniprogram else FULL_STEP_COUNT
    assert report["counts"]["passed"] == expected, f"通过步数应为 {expected}，实际 {report['counts']}"
    assert report["counts"]["failed"] == 0
    assert report["total_duration_ms"] <= DURATION_LIMIT_MS, f"总耗时超限：{report['total_duration_ms']}ms"

    # 每步都要有关键状态断言与耗时
    for step in report["steps"]:
        assert step["duration_ms"] >= 0
        assert step["assertion"], f"步骤 {step['no']} 缺少断言记录"

    # 真实浏览器覆盖：1 官网申请、3 顾问首次联系、5 前台核销、8 电子签
    ui_steps = [s["no"] for s in report["steps"] if s["mode"] == "ui"]
    assert ui_steps == [1, 3, 5, 8], f"浏览器步骤覆盖异常：{ui_steps}"

    # 第 11、12 步必须由小程序模拟器真实交互执行，不允许接口桩冒充
    miniapp_steps = [s["no"] for s in report["steps"] if s["mode"] == "miniapp"]
    assert miniapp_steps == ([] if skip_miniprogram else [11, 12]), f"小程序步骤执行方式异常：{miniapp_steps}"

    if not skip_miniprogram:
        expected_phase = {11: "certified", 12: "home"}
        for step in report["steps"]:
            if step["no"] not in (11, 12):
                continue
            # 仓内既有约定：报告里步骤证据为 {"evidence": {...}} 结构
            payload = step["evidence"].get("evidence", {})
            expected_tool = EXECUTOR_TOOL[report["miniapp_executor"]]
            assert payload.get("executor") == expected_tool, (
                f"步骤 {step['no']} 执行器不符：{payload.get('executor')}（应为 {expected_tool}）"
            )
            assert payload.get("request", {}).get("statusCode") == 200, f"步骤 {step['no']} 请求未成功"
            assert payload.get("dom_sha256"), f"步骤 {step['no']} 缺少渲染树/页面数据哈希"
            assert payload.get("events"), f"步骤 {step['no']} 缺少交互事件序列"
            assert payload.get("component_phase") == expected_phase[step["no"]], (
                f"步骤 {step['no']} 页面阶段异常：{payload.get('component_phase')}"
            )
            keys = ["miniapp_trace", "miniapp_summary", "miniapp_requests"]
            if report["miniapp_executor"] == "automator":
                keys += ["screenshot_entry", "screenshot_home"]
            else:
                keys += ["render_after_home"]
            for key in keys:
                artifact = ROOT / step["artifacts"][key]
                assert artifact.exists() and artifact.stat().st_size > 0, f"小程序证据文件缺失：{artifact}"

    # AC3：run_id 数据清理后为 0
    assert report["cleanup"]["deleted_total"] > 0, "清理接口未删除任何数据"
    assert report["cleanup"]["remaining_total"] == 0, f"清理后仍有残留：{report['cleanup']['remaining']}"
    assert _report_path(report).exists()


@pytest.mark.skip_mode
def test_skip_miniprogram_mode_runs_other_10_steps(base_url, make_run_id, headless):
    """AC4：跳过小程序两步时，其余 10 步照常执行并通过，小程序两步记为 skipped。"""
    run_id = make_run_id("skip")
    runner, report, failure = run_chain(
        base_url, run_id, skip_miniprogram=True, headless=headless, scenario="skip-miniprogram"
    )

    assert failure is None, f"跳过模式下链路失败：{failure}"
    assert report["counts"]["passed"] == SKIP_STEP_COUNT, f"跳过模式通过步数应为 10，实际 {report['counts']}"
    assert report["counts"]["skipped"] == 2
    skipped_nos = [s["no"] for s in report["steps"] if s["status"] == "skipped"]
    assert skipped_nos == [11, 12], f"被跳过的步骤应为 11、12，实际 {skipped_nos}"
    assert report["total_duration_ms"] <= DURATION_LIMIT_MS
    assert report["cleanup"]["remaining_total"] == 0, f"清理后仍有残留：{report['cleanup']['remaining']}"


@pytest.mark.esign_reject
def test_esign_reject_reports_failed_step_with_trace(base_url, make_run_id, headless):
    """AC2：SIGN_STUB_MODE=reject 时报告点名失败步骤「电子签」并附带该步 trace。"""
    health = httpx.get(f"{base_url}/healthz", timeout=10).json()
    if health.get("sign_stub_mode") != "reject":
        pytest.skip("当前服务不是 SIGN_STUB_MODE=reject，请用 scripts/run_reject_demo.sh 启动拒签环境")

    run_id = make_run_id("reject")
    runner = ChainRunner(base_url, run_id, skip_miniprogram=True, headless=headless, scenario="esign-reject")
    failure = None
    state: dict = {}
    try:
        runner.execute()
    except Exception as exc:  # noqa: BLE001
        failure = exc
        # 必须在清理前抓取主状态：finalize() 会按 run_id 删除业务行
        state = httpx.get(f"{base_url}/api/admin/run/{run_id}/state", timeout=10).json()
    finally:
        report = runner.finalize()

    assert failure is not None, "拒签模式下链路本应失败，但全部通过"
    assert report["status"] == "failed"
    failed = report["failed_step"]
    assert failed is not None
    assert failed["no"] == 8, f"失败步骤号应为 8，实际 {failed['no']}"
    assert failed["name"] == "电子签", f"失败步骤名应为「电子签」，实际 {failed['name']}"
    assert "拒签" in failed["reason"], f"失败原因未指向拒签：{failed['reason']}"

    step8 = next(s for s in report["steps"] if s["no"] == 8)
    trace = step8["artifacts"].get("trace")
    assert trace, f"步骤 8 未落盘 trace：{step8['artifacts']}"
    trace_file = ROOT / trace
    assert trace_file.exists() and trace_file.stat().st_size > 0, f"trace 文件为空：{trace_file}"
    assert step8["artifacts"].get("screenshot"), "失败步骤缺少截图"
    assert step8["artifacts"].get("http"), "失败步骤缺少接口响应留证"

    # 拒签后主状态停留在 quoted，不会推进到 signed / rented
    assert state.get("status") == "quoted", f"拒签后主状态应停在 quoted，实际 {state}"

    # 失败也要清理
    assert report["cleanup"]["remaining_total"] == 0, f"失败路径清理后仍有残留：{report['cleanup']['remaining']}"
    assert _report_path(report).exists()


@pytest.mark.skip_mode
@pytest.mark.skip_mini
def test_skip_mini_marker_skips_steps_11_12(base_url, make_run_id, skip_miniprogram, headless):
    """AC4（标记方式）：@pytest.mark.skip_mini 等价 --skip-miniprogram，不动命令行也能跳过小程序两步。"""
    assert skip_miniprogram is True, "skip_mini 标记未生效：fixture 仍返回 False"

    run_id = make_run_id("marker-skip")
    runner, report, failure = run_chain(
        base_url, run_id, skip_miniprogram=skip_miniprogram, headless=headless, scenario="skip-mini-marker"
    )
    assert failure is None, f"标记跳过模式下链路失败：{failure}"
    assert report["counts"]["passed"] == SKIP_STEP_COUNT, report["counts"]
    skipped_nos = [s["no"] for s in report["steps"] if s["status"] == "skipped"]
    assert skipped_nos == [11, 12], f"被跳过的步骤应为 11、12，实际 {skipped_nos}"
    assert report["cleanup"]["remaining_total"] == 0
