"""Chain-of-steps use case mapped 1:1 to the four acceptance criteria.

AC1 链式用例连续运行 5 次全部通过，平均耗时 <= 10 min   -> test_ac1_*  + scripts/run_5x.py
AC2 电子签桩拒签时报告指出失败步骤「电子签」并附 trace   -> test_ac2_*
AC3 运行结束后该 run_id 数据被清理，查询结果为 0          -> test_ac3_*
AC4 跳过小程序步骤后其余 10 步照常执行并通过              -> test_ac4_*
"""
import httpx

from chain.runner import ChainRunner
from tests.conftest import dump


def test_ac1_chain_passes_within_10_minutes(base_url):
    report = ChainRunner(base_url, run_tag="ac1-single").run()
    dump("report_ac1_single.json", report)

    assert report["ok"] is True, f"chain failed at {report.get('failed_step')}: {report.get('error')}"
    assert len(report["steps"]) == 12, f"expected 12 steps, got {len(report['steps'])}"
    passed = [s for s in report["steps"] if s["status"] == "passed"]
    assert len(passed) == 12, [s["name"] for s in report["steps"] if s["status"] != "passed"]
    assert report["total_ms"] <= 600_000, f"chain took {report['total_ms']} ms > 10 min"
    # every step must report its own duration
    assert all(s["duration_ms"] >= 0 for s in report["steps"])
    names = [s["name"] for s in report["steps"]]
    assert names[0] == "官网提交申请" and names[-1] == "小程序首页资源推荐", names


def test_ac2_esign_rejection_reports_step_name_and_trace(base_url):
    report = ChainRunner(base_url, run_tag="ac2-esign-reject",
                         esign_reject=True).run()
    dump("report_ac2_esign_reject.json", report)

    assert report["ok"] is False, "rejected contract must not pass the chain"
    assert report["failed_step"] == "电子签", f"failed_step={report.get('failed_step')}"
    assert report["failed_step_index"] == 8, report.get("failed_step_index")
    assert "ESIGN_REJECTED" in report["error"], report["error"]
    trace = report["trace"]
    assert any(t.get("status") == 422 for t in trace), f"trace has no 422: {trace}"
    assert any("ESIGN_REJECTED" in t.get("body", "") for t in trace), trace
    # already-created data ids are reported so the failed run can be traced back
    ids = report["data_ids"]
    for key in ("run_id", "application_id", "lead_id", "visit_id", "quote_id"):
        assert ids.get(key), f"data_ids missing {key}"
    # steps 1-7 passed, step 8 failed, 9-12 never ran
    statuses = [s["status"] for s in report["steps"]]
    assert statuses[:7] == ["passed"] * 7, statuses
    assert statuses[7] == "failed"
    assert len(report["steps"]) == 8, "chain must fail fast and not execute steps 9-12"


def test_ac3_run_data_purged_after_run(base_url):
    runner = ChainRunner(base_url, run_tag="ac3-cleanup")
    report = runner.run()
    dump("report_ac3_cleanup.json", report)
    assert report["ok"] is True, f"chain failed: {report.get('error')}"

    counts = report["counts_after_cleanup"]
    assert counts["total"] == 0, f"run_id data still present: {counts}"
    assert all(v == 0 for v in counts["counts"].values()), counts

    # independent second query, outside the runner's own client
    r = httpx.get(f"{base_url}/api/_test/count", params={"run_id": report["run_id"]}, timeout=10)
    assert r.status_code == 200
    assert r.json()["total"] == 0, r.json()


def test_ac4_skip_mini_runs_remaining_10_steps(base_url):
    report = ChainRunner(base_url, run_tag="ac4-skip-mini", skip_mini=True).run()
    dump("report_ac4_skip_mini.json", report)

    assert report["ok"] is True, f"chain failed: {report.get('failed_step')} {report.get('error')}"
    statuses = {s["index"]: s["status"] for s in report["steps"]}
    assert statuses[11] == "skipped" and statuses[12] == "skipped", statuses
    executed = [i for i, st in statuses.items() if st == "passed"]
    assert len(executed) == 10, f"expected 10 executed steps, got {len(executed)}"
    assert report["skip_mini"] is True


def test_quote_below_9_5_discount_is_rejected(base_url):
    """Guard rail for step 7: anything past 9.5 折 must be refused, not silently accepted."""
    runner = ChainRunner(base_url, run_tag="floor-guard")
    lead_id = None
    try:
        # walk steps 1-6 with the chain itself, then try an out-of-authority quote
        import json as _json
        r = runner.client.post("/api/site/applications", json={
            "run_id": runner.run_id, "company": "虚构折扣护栏企业",
            "contact_name": "李测试", "contact_phone": "13900000000", "intent": "60㎡"})
        lead_id = r.json()["lead_id"]
        runner.client.post(f"/api/sales/leads/{lead_id}/contact", json={"note": "x"})
        runner.client.post(f"/api/sales/leads/{lead_id}/visit", json={"scheduled_at": "2026-12-02T10:00:00"})
        code = runner.client.get("/api/_test/visit-code", params={"lead_id": lead_id}).json()["code"]
        runner.client.post("/api/site/visits/verify", json={"code": code})
        runner.client.post(f"/api/sales/leads/{lead_id}/minutes", json={"summary": "纪要"})

        bad = runner.client.post(f"/api/sales/leads/{lead_id}/quotes",
                                 json={"monthly_cents": 1_000_000, "discount_bps": 9000})
        assert bad.status_code == 422, bad.text
        assert bad.json()["error"]["code"] == "BELOW_FLOOR", bad.text
        ok = runner.client.post(f"/api/sales/leads/{lead_id}/quotes",
                                json={"monthly_cents": 1_000_000, "discount_bps": 9500})
        assert ok.status_code == 200, ok.text
        assert _json.loads(ok.text)["net_monthly_cents"] == 950_000
    finally:
        runner.cleanup()
        runner.client.close()
