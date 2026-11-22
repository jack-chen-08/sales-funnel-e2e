"""The chain-of-steps use case: 12 steps, one run_id, one report.

Fails fast: on the first failing step the report carries the failing step name,
that step's request trace, and every entity id created so far.
"""
from __future__ import annotations

import os
import time
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import httpx
from playwright.sync_api import sync_playwright

from chain.mini_driver import make_driver

ROOT = Path(__file__).resolve().parents[1]

STEP_NAMES = [
    "官网提交申请", "线索按规则分配", "顾问首次联系", "推进到预约参观", "前台核销访客码",
    "纪要确认", "9.5折以内报价", "电子签", "房态变为已租", "会员经理领取交接",
    "小程序认证", "小程序首页资源推荐",
]
MINI_STEPS = {11, 12}  # 小程序执行机不可用时可跳过


class StepFailed(Exception):
    def __init__(self, step: str, index: int, cause: BaseException,
                 trace: list[dict[str, Any]], data_ids: dict[str, Any]):
        super().__init__(f"step {index} 「{step}」 failed: {type(cause).__name__}: {cause}")
        self.step = step
        self.index = index
        self.cause = cause
        self.trace = trace
        self.data_ids = data_ids


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class ChainRunner:
    def __init__(self, base_url: str, *, run_id: str | None = None,
                 skip_mini: bool | None = None, esign_reject: bool = False,
                 headless: bool = True, timeout: float = 20.0,
                 run_tag: str = "chain", mini_driver: str | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.run_id = run_id or f"run-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"
        self.run_tag = run_tag
        self.skip_mini = (os.getenv("SKIP_MINI") == "1") if skip_mini is None else skip_mini
        self.esign_reject = esign_reject
        self.mini = make_driver(mini_driver)
        self.headless = headless
        self.timeout = timeout
        self.client = httpx.Client(base_url=self.base_url, timeout=timeout)
        self.steps: list[dict[str, Any]] = []
        self.data_ids: dict[str, Any] = {"run_id": self.run_id}
        self._global_trace: list[dict[str, Any]] = []
        self._step_trace: list[dict[str, Any]] = []
        self.page = None

    # ------------------------------------------------------------- utils
    def call(self, method: str, path: str, **kw) -> httpx.Response:
        t0 = time.perf_counter()
        resp = self.client.request(method, path, **kw)
        rec = {
            "method": method, "path": path, "status": resp.status_code,
            "ms": round((time.perf_counter() - t0) * 1000, 1),
            "body": resp.text[:400],
        }
        self._step_trace.append(rec)
        self._global_trace.append(rec)
        return resp

    def ui(self, label: str, detail: dict[str, Any] | None = None) -> None:
        rec = {"method": "BROWSER", "path": label, "status": "ok", **(detail or {})}
        self._step_trace.append(rec)
        self._global_trace.append(rec)

    def expect(self, cond: bool, message: str) -> None:
        if not cond:
            raise AssertionError(message)

    def _exec(self, index: int, name: str, fn: Callable[[], None]) -> None:
        self._step_trace = []
        t0 = time.perf_counter()
        try:
            fn()
        except StepFailed:
            raise
        except BaseException as cause:  # noqa: BLE001 - report, don't swallow
            self.steps.append({
                "index": index, "name": name, "status": "failed",
                "duration_ms": round((time.perf_counter() - t0) * 1000, 1),
                "trace": self._step_trace,
            })
            tb = "".join(traceback.format_exception(type(cause), cause, cause.__traceback__))
            # 报告里的异常栈去掉本机绝对路径，保证 clone 即可复现、不泄漏运行环境
            tb = tb.replace(str(ROOT) + "/", "").replace(str(ROOT), ".")
            raise StepFailed(name, index, cause,
                             list(self._step_trace) + [{"traceback": tb[-2000:]}],
                             dict(self.data_ids)) from cause
        else:
            self.steps.append({
                "index": index, "name": name, "status": "passed",
                "duration_ms": round((time.perf_counter() - t0) * 1000, 1),
                "trace": self._step_trace,
            })

    # ------------------------------------------------------------- steps
    def s1_apply(self) -> None:
        pg = self.page
        pg.goto(f"{self.base_url}/apply?run_id={self.run_id}")
        pg.fill("#company", f"虚构会员企业-{self.run_id[-6:]}")
        pg.fill("#contact_name", "张测试")
        pg.fill("#contact_phone", "13800000000")
        pg.fill("#intent", "100-300㎡")
        pg.click("#submit-apply")
        pg.wait_for_selector("#ok", timeout=self.timeout * 1000)
        app_id = pg.inner_text("#application-id").strip()
        lead_id = pg.inner_text("#lead-id").strip()
        assigned = pg.inner_text("#assigned-to").strip()
        self.data_ids.update(application_id=app_id, lead_id=lead_id)
        self.expect(app_id.startswith("app-"), f"application_id shape: {app_id}")
        self.expect(lead_id.startswith("lead-"), f"lead_id shape: {lead_id}")
        self.expect(bool(assigned), "lead has no assignee")
        self.ui("POST /apply (form submit)", {"application_id": app_id, "lead_id": lead_id})

    def s2_assign(self) -> None:
        r = self.call("GET", f"/api/crm/leads/{self.data_ids['lead_id']}")
        self.expect(r.status_code == 200, f"GET lead -> {r.status_code}")
        lead = r.json()
        self.expect(lead["status"] == "assigned", f"lead.status={lead['status']}, expected assigned")
        self.expect(lead["assigned_to"] in ("sp-alice", "sp-bob"),
                    f"assigned_to={lead['assigned_to']} not in active sales pool")
        self.expect(bool(lead.get("created_at")) and bool(lead.get("site_id")),
                    "lead missing created_at/site_id")
        self.data_ids["assigned_to"] = lead["assigned_to"]

    def s3_contact(self) -> None:
        r = self.call("POST", f"/api/sales/leads/{self.data_ids['lead_id']}/contact",
                      json={"note": "首次电话联系，约定到店时间"})
        self.expect(r.status_code == 200, f"contact -> {r.status_code} {r.text[:200]}")
        body = r.json()
        self.expect(body["status"] == "contacted", f"status={body['status']}")
        self.expect(bool(body.get("first_contact_at")), "first_contact_at missing")

    def s4_visit(self) -> None:
        r = self.call("POST", f"/api/sales/leads/{self.data_ids['lead_id']}/visit",
                      json={"scheduled_at": "2026-12-01T10:00:00+08:00"})
        self.expect(r.status_code == 200, f"visit -> {r.status_code} {r.text[:200]}")
        body = r.json()
        self.expect(body["lead_status"] == "visit_scheduled", f"lead={body['lead_status']}")
        self.expect(len(str(body["code"])) == 6, f"visitor code shape: {body['code']}")
        self.data_ids.update(visit_id=body["visit_id"])

    def s5_verify_visit(self) -> None:
        pg = self.page
        code = self._visitor_code()  # generated in step 4, only known at runtime
        pg.goto(f"{self.base_url}/desk/verify")
        pg.fill("#code", code)
        pg.click("#submit-verify")
        pg.wait_for_selector("#ok, #fail", timeout=self.timeout * 1000)
        self.expect(pg.locator("#ok").count() == 1,
                    f"前台核销 UI 未成功: {pg.inner_text('body')[:160]}")
        visit_id = pg.inner_text("#visit-id").strip()
        self.expect(visit_id.startswith("visit-"), f"visit_id shape: {visit_id}")
        self.data_ids["checked_in_visit_id"] = visit_id
        self.ui("POST /desk/verify (form submit)", {"code": code, "visit_id": visit_id})

    def s6_minutes(self) -> None:
        r = self.call("POST", f"/api/sales/leads/{self.data_ids['lead_id']}/minutes",
                      json={"summary": "参观完成，客户关注 1201 房，需求 6 人位"})
        self.expect(r.status_code == 200, f"minutes -> {r.status_code} {r.text[:200]}")
        self.expect(r.json()["confirmed"] is True, "minutes not confirmed")

    def s7_quote(self) -> None:
        r = self.call("POST", f"/api/sales/leads/{self.data_ids['lead_id']}/quotes",
                      json={"monthly_cents": 1_200_000, "discount_bps": 9500})
        self.expect(r.status_code == 200, f"quote -> {r.status_code} {r.text[:200]}")
        body = r.json()
        self.expect(body["discount_bps"] <= 10000 and body["discount_bps"] >= 9500,
                    f"discount_bps={body['discount_bps']} outside 9.5折 authority")
        self.expect(body["net_monthly_cents"] == 1_140_000,
                    f"net_monthly_cents={body['net_monthly_cents']} != 1140000")
        self.data_ids["quote_id"] = body["quote_id"]

    def s8_esign(self) -> None:
        r = self.call("POST", "/api/contracts/esign",
                      json={"quote_id": self.data_ids["quote_id"],
                            "reject": self.esign_reject})
        self.expect(r.status_code == 200, f"esign -> {r.status_code} {r.text[:200]}")
        body = r.json()
        self.expect(body["status"] == "signed", f"contract status={body['status']}")
        self.expect(body["signed_by_applicant"] and body["signed_by_org"],
                    "contract not signed by both parties")
        self.data_ids.update(contract_id=body["contract_id"], room_id=body["room_id"])

    def s9_room_rented(self) -> None:
        r = self.call("GET", f"/api/site/rooms/{self.data_ids['room_id']}")
        self.expect(r.status_code == 200, f"GET room -> {r.status_code}")
        room = r.json()
        self.expect(room["status"] == "rented", f"room.status={room['status']}")
        self.expect(room["contract_id"] == self.data_ids["contract_id"],
                    "room not bound to this contract")

    def s10_handover(self) -> None:
        r = self.call("POST", "/api/ops/handovers",
                      json={"room_id": self.data_ids["room_id"], "manager_id": "mm-cathy"})
        self.expect(r.status_code == 200, f"handover -> {r.status_code} {r.text[:200]}")
        body = r.json()
        self.expect(body["status"] == "claimed", f"handover={body['status']}")
        self.expect(body["lead_status"] == "handover_claimed", f"lead={body['lead_status']}")
        self.data_ids["handover_id"] = body["handover_id"]

    def s11_mini_auth(self) -> None:
        member_id = self.mini.verify(
            page=self.page, base_url=self.base_url, lead_id=self.data_ids["lead_id"],
            phone="13800000000", code="246810",
        )
        self.expect(member_id.startswith("mb-"), f"member_id shape: {member_id}")
        self.data_ids["member_id"] = member_id
        self.ui(f"mini auth via {self.mini.name}", {"member_id": member_id})

    def s12_mini_home(self) -> None:
        r = self.call("GET", "/api/mini/home/recommendations",
                      params={"member_id": self.data_ids["member_id"]})
        self.expect(r.status_code == 200, f"recommendations -> {r.status_code}")
        body = r.json()
        self.expect(len(body["items"]) >= 1, "首月资源推荐为空")
        self.data_ids["recommendation_count"] = len(body["items"])

    # -------------------------------------------------------------- run
    def _visitor_code(self) -> str:
        """The visitor code lives on the visit entity; surface it through the CRM lead view."""
        r = self.client.get(f"/api/_test/visit-code",
                            params={"lead_id": self.data_ids["lead_id"]})
        self.expect(r.status_code == 200, f"visit-code -> {r.status_code}")
        return r.json()["code"]

    def run(self) -> dict[str, Any]:
        started = time.perf_counter()
        report: dict[str, Any] = {
            "run_id": self.run_id, "tag": self.run_tag, "base_url": self.base_url,
            "started_at": _now(), "skip_mini": self.skip_mini,
            "mini_driver": self.mini.name,
            "esign_reject": self.esign_reject, "ok": False,
        }
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=self.headless)
                try:
                    self.page = browser.new_page(viewport={"width": 1280, "height": 800})
                    for idx, (name, fn) in enumerate(self._step_defs(), 1):
                        if self.skip_mini and idx in MINI_STEPS:
                            self.steps.append({"index": idx, "name": name,
                                               "status": "skipped", "duration_ms": 0.0,
                                               "trace": [{"note": "SKIP_MINI=1"}],
                                               "asserted": "skipped by marker"})
                            continue
                        self._exec(idx, name, fn)
                except StepFailed as exc:
                    # screenshot while the browser is still alive
                    report["screenshot"] = self._capture_failure(exc)
                    raise
                finally:
                    browser.close()
            report["ok"] = True
        except StepFailed as exc:
            report.update({
                "ok": False,
                "failed_step": exc.step,
                "failed_step_index": exc.index,
                "error": f"{type(exc.cause).__name__}: {exc.cause}",
                "trace": exc.trace,
                "data_ids": exc.data_ids,
            })
        finally:
            report["steps"] = self.steps
            report["total_ms"] = round((time.perf_counter() - started) * 1000, 1)
            report["finished_at"] = _now()
            report.setdefault("data_ids", dict(self.data_ids))
            report["cleanup"] = self.cleanup()
            report["counts_after_cleanup"] = self.count()
            self.client.close()
        return report

    def _capture_failure(self, exc: StepFailed) -> str | None:
        """Publish step status to the stub, open the diagnostic page, screenshot it."""
        try:
            arts = ROOT / "reports" / "artifacts"
            arts.mkdir(parents=True, exist_ok=True)
            self.client.post("/api/_test/chain-status",
                             json={"run_id": self.run_id, "steps": self.steps})
            self.page.goto(f"{self.base_url}/_diag/chain?run_id={self.run_id}",
                           wait_until="load", timeout=self.timeout * 1000)
            path = arts / f"failure_step{exc.index}_{self.run_id.rsplit('-', 1)[-1]}.png"
            self.page.screenshot(path=str(path), full_page=True)
            return str(path.relative_to(ROOT))
        except Exception:  # noqa: BLE001 - a missing screenshot must not mask the real failure
            return None

    def _step_defs(self) -> list[tuple[str, Callable[[], None]]]:
        return list(zip(STEP_NAMES, [
            self.s1_apply, self.s2_assign, self.s3_contact, self.s4_visit,
            self.s5_verify_visit, self.s6_minutes, self.s7_quote, self.s8_esign,
            self.s9_room_rented, self.s10_handover, self.s11_mini_auth, self.s12_mini_home,
        ]))

    def cleanup(self) -> dict[str, Any]:
        try:
            with httpx.Client(base_url=self.base_url, timeout=self.timeout) as c:
                r = c.post("/api/_test/purge", params={"run_id": self.run_id})
                return r.json() if r.status_code == 200 else {"error": r.status_code}
        except Exception as exc:  # noqa: BLE001
            return {"error": str(exc)}

    def count(self) -> dict[str, Any]:
        try:
            with httpx.Client(base_url=self.base_url, timeout=self.timeout) as c:
                r = c.get("/api/_test/count", params={"run_id": self.run_id})
                return r.json() if r.status_code == 200 else {"error": r.status_code}
        except Exception as exc:  # noqa: BLE001
            return {"error": str(exc)}
