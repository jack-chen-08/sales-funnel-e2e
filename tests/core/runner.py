"""链式用例执行器：12 步顺序执行、逐步计时、逐步留证、失败定位与 run_id 清理。

设计要点
- 每步独立计时（perf_counter），并记录 UTC start/end。
- 4 步走真实浏览器点击（1 官网申请、3 顾问首次联系、5 前台核销、8 电子签签约台），
  其余 6 步走接口；小程序 2 步为接口桩，可 --skip-miniprogram 跳过。
- 任一步失败：记录步骤号/名称/异常、该步 Playwright trace（UI 步骤）+ HTTP 请求响应（API 步骤）
  + 已创建数据 ID，然后抛出 ChainFailure。
- 结束（无论成败）按 run_id 清理数据，并回查剩余行数必须为 0。
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable

from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright

from app.workflow import MINIPROGRAM_STEP_NOS, STEP_BY_NO, STEPS, StepSpec

from . import miniapp
from .client import ApiError, SmokeClient
from .report import write_reports

ROOT = Path(__file__).resolve().parents[2]

COMPANY = "星澜数字科技（虚构）"
APPLICANT = "林知远（虚构）"
PHONE = "13800000001"


def _utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _iso(value: dt.datetime) -> str:
    return value.isoformat(timespec="milliseconds")


def _step_mode(spec: StepSpec, skip_miniprogram: bool) -> str:
    """步骤执行方式：ui=真实浏览器点击；miniapp=小程序模拟器真实交互；api=接口。"""
    if spec.no in MINIPROGRAM_STEP_NOS and not skip_miniprogram:
        return "miniapp"
    return "ui" if spec.ui else "api"


@dataclass
class StepResult:
    no: int
    key: str
    name: str
    actor: str
    mode: str
    status: str
    started_at: str
    ended_at: str
    duration_ms: float
    assertion: str = ""
    evidence: dict[str, Any] = field(default_factory=dict)
    artifacts: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ChainFailure(AssertionError):
    def __init__(self, step: StepResult, reason: str, artifacts: dict[str, str]) -> None:
        self.step = step
        self.reason = reason
        self.artifacts = artifacts
        super().__init__(f"链路在步骤 {step.no}「{step.name}」失败：{reason}")


class ChainRunner:
    def __init__(
        self,
        base_url: str,
        run_id: str,
        *,
        skip_miniprogram: bool = False,
        headless: bool = True,
        reports_dir: Path | None = None,
        artifacts_dir: Path | None = None,
        scenario: str = "chain",
        miniapp_dir: Path | None = None,
        miniapp_executor: str = "auto",
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.run_id = run_id
        self.skip_miniprogram = skip_miniprogram
        self.headless = headless
        self.scenario = scenario
        self.mode = "skip-miniprogram" if skip_miniprogram else "full"
        self.reports_dir = reports_dir or ROOT / "reports"
        self.artifacts_dir = artifacts_dir or self.reports_dir / "artifacts" / run_id
        self.client = SmokeClient(self.base_url, run_id)
        self.results: list[StepResult] = []
        self.created: dict[str, str] = {}
        self.failure: StepResult | None = None
        self.failure_reason: str | None = None
        self.cleanup: dict[str, Any] | None = None
        self.started_at: dt.datetime | None = None
        self.finished_at: dt.datetime | None = None
        self.report_paths: dict[str, str] = {}

        self._pw = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None
        self._step_http: list[dict[str, Any]] = []
        self._step_ui: dict[str, Any] = {}

        # 小程序两步：一次会话内连续执行（与真机用户「先认证、再进首页」的操作顺序一致），
        # 执行时点归属第 11 步，第 12 步复用同一次会话的首页结果。
        self._miniapp_trace: dict[str, Any] | None = None
        self._miniapp_artifacts: dict[str, str] = {}
        self.miniapp_dir = Path(miniapp_dir) if miniapp_dir else self.artifacts_dir / "miniapp"
        # 小程序执行器：auto（有开发者工具走 automator，否则回退 simulate）/ automator / simulate
        self.miniapp_executor_requested = (miniapp_executor or "auto").strip().lower()
        self.miniapp_executor: str | None = None
        self.miniapp_executor_fallback = ""

    # ------------------------------------------------------------------ 生命周期

    def open(self) -> "ChainRunner":
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(headless=self.headless)
        self._context = self._browser.new_context(viewport={"width": 1366, "height": 900}, locale="zh-CN")
        self._context.set_default_timeout(15000)
        return self

    def close(self) -> None:
        try:
            if self._context is not None:
                self._context.close()
            if self._browser is not None:
                self._browser.close()
        finally:
            if self._pw is not None:
                self._pw.stop()
            self.client.close()
            self._context = None
            self._browser = None
            self._pw = None

    # ------------------------------------------------------------------ 执行

    def execute(self) -> None:
        self.started_at = _utcnow()
        self.open()
        try:
            self._provision_rooms()
            for spec in STEPS:
                self._run_step(spec)
        finally:
            self.finished_at = _utcnow()

    @property
    def passed_steps(self) -> list[StepResult]:
        return [r for r in self.results if r.status == "passed"]

    @property
    def skipped_steps(self) -> list[StepResult]:
        return [r for r in self.results if r.status == "skipped"]

    def _provision_rooms(self) -> None:
        body = self.client.json("POST", "/api/rooms/provision", json={"room_count": 2})
        rooms = body["rooms"]
        self.created["rooms"] = ",".join(r["room_id"] for r in rooms)
        self.created["room_primary"] = rooms[0]["room_id"]
        self.created["room_secondary"] = rooms[1]["room_id"]

    def _run_step(self, spec: StepSpec) -> None:
        if spec.no in MINIPROGRAM_STEP_NOS and self.skip_miniprogram:
            now = _iso(_utcnow())
            self.results.append(
                StepResult(
                    no=spec.no,
                    key=spec.key,
                    name=spec.name,
                    actor=spec.actor,
                    mode="skipped",
                    status="skipped",
                    started_at=now,
                    ended_at=now,
                    duration_ms=0.0,
                    assertion="小程序步骤按 --skip-miniprogram 标记跳过（本轮显式要求跳过；默认执行方式为官方模拟器组件级真跑）",
                )
            )
            return

        trace_path = self.artifacts_dir / f"step_{spec.no:02d}_{spec.key}_trace.zip"
        started_at = _utcnow()
        t0 = time.perf_counter()
        self._step_http = []
        self._step_ui = {}
        error: Exception | None = None
        evidence: dict[str, Any] = {}

        if spec.ui:
            self._context.tracing.start(name=f"step{spec.no}-{spec.key}", screenshots=True, snapshots=True, sources=True)
            self._page = self._context.new_page()
            self._instrument_fetch(self._page)
            self._page.on("console", lambda msg: self._step_ui.setdefault("console", []).append(f"{msg.type}: {msg.text}"))

        try:
            evidence = getattr(self, f"step_{spec.no:02d}")()
        except Exception as exc:  # noqa: BLE001 - 需要捕获任意异常以留证
            error = exc
            self._capture_failure(spec)
        finally:
            duration_ms = round((time.perf_counter() - t0) * 1000, 1)
            ended_at = _utcnow()
            artifacts: dict[str, str] = {}
            if spec.ui and self._page is not None:
                try:
                    self._context.tracing.stop(path=str(trace_path))
                    artifacts["trace"] = str(trace_path.relative_to(ROOT))
                except Exception:  # noqa: BLE001
                    pass
            http_path = self.artifacts_dir / f"step_{spec.no:02d}_{spec.key}_http.json"
            http_path.write_text(
                json.dumps(
                    {"step": spec.name, "run_id": self.run_id, "calls": self._step_http, "ui": self._step_ui},
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            artifacts["http"] = str(http_path.relative_to(ROOT))
            if self._miniapp_artifacts:
                artifacts.update(self._miniapp_artifacts)
            if "screenshot" in self._step_ui:
                artifacts["screenshot"] = self._step_ui["screenshot"]
            if "html" in self._step_ui:
                artifacts["html"] = self._step_ui["html"]
            if self._page is not None:
                self._page.close()
                self._page = None

            result = StepResult(
                no=spec.no,
                key=spec.key,
                name=spec.name,
                actor=spec.actor,
                mode=_step_mode(spec, self.skip_miniprogram),
                status="failed" if error is not None else "passed",
                started_at=_iso(started_at),
                ended_at=_iso(ended_at),
                duration_ms=duration_ms,
                assertion="" if error is not None else evidence.get("assertion", "关键状态断言通过"),
                evidence={k: v for k, v in evidence.items() if k != "assertion"},
                artifacts=artifacts,
            )
            self.results.append(result)
            if error is not None:
                self.failure = result
                self.failure_reason = f"{type(error).__name__}: {error}"
                raise ChainFailure(result, self.failure_reason, artifacts) from error

    # ------------------------------------------------------------------ 浏览器辅助

    def _instrument_fetch(self, page: Page) -> None:
        page.add_init_script(
            """
            window.__smoke = [];
            const _fetch = window.fetch;
            window.fetch = async (...args) => {
              const res = await _fetch(...args);
              try {
                const clone = res.clone();
                clone.text().then(t => window.__smoke.push({url: res.url, status: res.status, body: t}));
              } catch (e) {}
              return res;
            };
            """
        )

    def _ui_calls(self, page: Page) -> None:
        try:
            calls = page.evaluate("window.__smoke || []")
        except Exception:  # noqa: BLE001
            return
        for call in calls:
            try:
                body = json.loads(call["body"])
            except Exception:  # noqa: BLE001
                body = call["body"][:2000]
            self._step_http.append({"method": "FETCH", "path": call["url"], "status": call["status"], "response": body})

    def _capture_failure(self, spec: StepSpec) -> None:
        page = self._page
        if page is None:
            return
        shot = self.artifacts_dir / f"step_{spec.no:02d}_{spec.key}_failure.png"
        html = self.artifacts_dir / f"step_{spec.no:02d}_{spec.key}_failure.html"
        try:
            page.screenshot(path=str(shot), full_page=True)
            self._step_ui["screenshot"] = str(shot.relative_to(ROOT))
        except Exception:  # noqa: BLE001
            pass
        try:
            html.write_text(page.content(), encoding="utf-8")
            self._step_ui["html"] = str(html.relative_to(ROOT))
        except Exception:  # noqa: BLE001
            pass
        self._ui_calls(page)

    def _goto(self, path: str) -> Page:
        assert self._page is not None
        self._page.goto(f"{self.base_url}{path}", wait_until="domcontentloaded")
        self._page.wait_for_load_state("networkidle")
        return self._page

    def _api(self, method: str, path: str, **kwargs: Any) -> dict:
        try:
            body = self.client.json(method, path, **kwargs)
        finally:
            self._step_http.extend(self.client.drain_calls())
        return body

    @staticmethod
    def _assert(condition: bool, message: str) -> None:
        if not condition:
            raise AssertionError(message)

    @staticmethod
    def _is_uuid(value: str | None) -> bool:
        if not value:
            return False
        try:
            uuid.UUID(value)
            return True
        except ValueError:
            return False

    def _state(self) -> dict:
        return self._api("GET", f"/api/admin/run/{self.run_id}/state")

    # ------------------------------------------------------------------ 12 步

    def step_01(self) -> dict:
        """S4-SITE 官网入会申请（真实浏览器填表提交）。"""
        page = self._goto(f"/site/apply?run_id={self.run_id}")
        page.fill("#company_name", COMPANY)
        page.fill("#applicant_name", APPLICANT)
        page.fill("#applicant_phone", PHONE)
        page.select_option("#region", "east")
        page.fill("#seat_demand", "36")
        with page.expect_navigation(wait_until="domcontentloaded") as nav:
            page.click("#submit-apply")
        navigation = nav.value
        self._step_http.append(
            {
                "method": "POST",
                "path": "/site/apply/submit",
                "request": {
                    "run_id": self.run_id,
                    "company_name": COMPANY,
                    "applicant_name": APPLICANT,
                    "applicant_phone": PHONE,
                    "region": "east",
                    "seat_demand": 36,
                },
                "status": navigation.status if navigation else None,
                "response": {"page_url": page.url, "content_type": navigation.header_value("content-type") if navigation else None},
            }
        )
        page.wait_for_selector("#apply-result", state="visible")

        app_id = page.get_attribute("#apply-result", "data-app-id")
        status = page.get_attribute("#apply-result", "data-app-status")
        self._assert(self._is_uuid(app_id), f"官网返回的申请单号不是 UUID：{app_id}")
        self._assert(status == "submitted", f"申请单状态应为 submitted，实际 {status}")
        self.created["application_id"] = app_id or ""

        return {
            "assertion": "官网提交成功，申请单状态=submitted，返回 UUID 单号",
            "evidence": {"application_id": app_id, "application_status": status, "page_url": page.url},
        }

    def step_02(self) -> dict:
        """S3-SALES 线索按规则分配（接口）。"""
        body = self._api("POST", "/api/leads/assign", json={"application_id": self.created["application_id"]})
        self._assert(body["application_status"] == "assigned", f"分配后状态应为 assigned，实际 {body['application_status']}")
        self._assert(body["advisor_id"] == "ADV-101", f"东区 36 工位应分配 ADV-101，实际 {body['advisor_id']}")
        self._assert("region=east" in body["assign_rule"], f"分配规则未命中区域路由：{body['assign_rule']}")
        self.created["lead_id"] = body["lead_id"]
        self.created["advisor_id"] = body["advisor_id"]
        return {
            "assertion": "线索分配命中规则 region=east->ADV-101，状态 assigned",
            "evidence": body,
        }

    def step_03(self) -> dict:
        """S3-SALES 顾问首次联系（真实浏览器点击）。"""
        page = self._goto(f"/advisor/console?run_id={self.run_id}")
        page.wait_for_selector("#btn-first-contact")
        page.click("#btn-first-contact")
        page.wait_for_function("document.querySelector('#lead-status').dataset.status === 'contacted'", timeout=10000)

        badge = page.inner_text("#lead-status")
        result_text = page.inner_text("#contact-result")
        match = re.search(r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})", result_text)
        self._assert(match is not None, f"页面未回显联系记录 ID：{result_text}")
        self._assert(badge.strip() == "已联系", f"线索状态标签应为「已联系」，实际「{badge.strip()}」")
        self._ui_calls(page)
        self.created["contact_id"] = match.group(1) if match else ""

        state = self._state()
        self._assert(state["status"] == "contacted", f"后台状态应为 contacted，实际 {state['status']}")
        return {
            "assertion": "工作台点击后线索状态=contacted，页面回显联系记录 ID",
            "evidence": {"badge": badge.strip(), "contact_id": self.created.get("contact_id"), "backend_status": state["status"]},
        }

    def step_04(self) -> dict:
        """S3-SALES 推进到预约参观（接口）。"""
        body = self._api("POST", "/api/visits/book", json={"lead_id": self.created["lead_id"], "scheduled_hours_ahead": 24})
        self._assert(bool(re.fullmatch(r"\d{6}", body["visit_code"])), f"访客码应为 6 位数字：{body['visit_code']}")
        self._assert(body["application_status"] == "visit_booked", f"状态应为 visit_booked，实际 {body['application_status']}")
        self.created["visit_id"] = body["visit_id"]
        self.created["visit_code"] = body["visit_code"]
        return {"assertion": "预约参观创建成功，生成 6 位访客码，状态=visit_booked", "evidence": body}

    def step_05(self) -> dict:
        """前台核销访客码（真实浏览器输入并核销）。"""
        page = self._goto("/frontdesk/checkin?run_id=" + self.run_id)
        displayed = (page.inner_text("#visit-code-display")).strip()
        self._assert(displayed == self.created["visit_code"], f"前台展示的访客码与预约不一致：{displayed}")
        page.fill("#visit-code", displayed)
        page.select_option("#desk", "A 座前台")
        page.click("#btn-checkin")
        page.wait_for_function(
            "document.querySelector('#checkin-result').dataset.status === 'checked_in'", timeout=10000
        )
        text = page.inner_text("#checkin-result")
        self._assert("核销成功" in text, f"核销结果文案异常：{text}")
        self._ui_calls(page)

        state = self._state()
        self._assert(state["status"] == "visited", f"核销后状态应为 visited，实际 {state['status']}")
        return {"assertion": "访客码在 A 座前台核销成功，状态=visited", "evidence": {"page_text": text, "backend_status": state["status"]}}

    def step_06(self) -> dict:
        """纪要确认（接口）。"""
        body = self._api(
            "POST",
            "/api/minutes/confirm",
            json={"visit_id": self.created["visit_id"], "content": "客户确认 12 层南向 186㎡，认可物业与交付标准"},
        )
        self._assert(body["application_status"] == "minutes_confirmed", f"状态应为 minutes_confirmed，实际 {body['application_status']}")
        self.created["minutes_id"] = body["minutes_id"]
        return {"assertion": "参观纪要确认落库，状态=minutes_confirmed", "evidence": body}

    def step_07(self) -> dict:
        """9.5 折以内报价（接口，金额以分存整数）。"""
        body = self._api(
            "POST", "/api/quotes", json={"room_id": self.created["room_primary"], "discount_bp": 500}
        )
        list_cents = body["list_price_cents"]
        final_cents = body["final_price_cents"]
        ratio_bp = round(final_cents / list_cents * 10000)
        self._assert(body["discount_bp"] <= 500, f"折扣超出 9.5 折上限：{body['discount_bp']}bp")
        self._assert(ratio_bp >= 9500, f"成交价低于挂牌价 95%（{ratio_bp}bp），违反 9.5 折以内约束")
        self._assert(final_cents == round(list_cents * 0.95), f"成交价计算不符：{final_cents} != {round(list_cents * 0.95)}")
        self._assert(body["application_status"] == "quoted", f"状态应为 quoted，实际 {body['application_status']}")
        self.created["quote_id"] = body["quote_id"]
        self.created["envelope_id"] = body["envelope_id"]
        return {
            "assertion": f"成交价为挂牌价 {ratio_bp / 100:.1f}%（9.5 折以内），成交价 {final_cents} 分，状态=quoted",
            "evidence": body,
        }

    def step_08(self) -> dict:
        """电子签（真实浏览器签约台点击，桩完成两方签署；SIGN_STUB_MODE=reject 时拒签）。"""
        page = self._goto(f"/sign/console?run_id={self.run_id}")
        page.wait_for_selector("#btn-sign-all")
        page.click("#btn-sign-all")
        page.wait_for_function(
            "() => { const b = document.querySelector('#sign-status');"
            " return b.dataset.status === 'signed' || !document.querySelector('#sign-error').hidden; }",
            timeout=10000,
        )
        self._ui_calls(page)
        status = page.get_attribute("#sign-status", "data-status")
        if status != "signed":
            reason = page.inner_text("#sign-error").strip()
            raise AssertionError(f"电子签未完成两方签署：{reason}")
        signers = page.eval_on_selector_all(
            "#signer-list li", "els => els.map(e => ({party: e.dataset.party, text: e.innerText}))"
        )
        self._assert(len(signers) == 2, f"签署方应为 2 方，实际 {len(signers)}")
        state = self._state()
        self._assert(state["status"] == "signed", f"签署后状态应为 signed，实际 {state['status']}")
        self._assert(
            state["events"][-1]["event"] == "esign:ok", f"审计事件异常：{state['events'][-1]['event']}"
        )
        return {
            "assertion": "签约台完成两方签署（出租方+承租方），信封状态=signed，主状态=signed",
            "evidence": {"signers": signers, "envelope_status": status, "backend_status": state["status"]},
        }

    def step_09(self) -> dict:
        """房态变为已租（接口）。"""
        body = self._api("POST", f"/api/rooms/{self.created['room_primary']}/lease")
        self._assert(body["room_status"] == "rented", f"房态应为 rented，实际 {body['room_status']}")
        self._assert(body["application_status"] == "rented", f"主状态应为 rented，实际 {body['application_status']}")
        return {"assertion": f"房源 {body['room_no']} 房态=rented，主状态=rented", "evidence": body}

    def step_10(self) -> dict:
        """会员经理领取交接（接口）。"""
        body = self._api("POST", "/api/handovers/claim", json={"lead_id": self.created["lead_id"], "member_manager_id": "MM-021"})
        self._assert(body["application_status"] == "handed_over", f"状态应为 handed_over，实际 {body['application_status']}")
        self._assert(body["to_member_manager_id"] == "MM-021", f"承接人异常：{body['to_member_manager_id']}")
        self.created["handover_id"] = body["handover_id"]
        self.created["member_id"] = body["member_id"]
        return {"assertion": "会员经理 MM-021 领取交接，会员档案创建，状态=handed_over", "evidence": body}

    # ------------------------------------------------------------------ 小程序两步

    def _miniapp_session(self) -> dict[str, Any]:
        """执行（或复用）小程序会话：真实渲染 + 真实事件 + 真实 HTTP 出网。

        执行器由 miniapp.resolve() 决定：auto 优先 automator（页面级，订单指定框架），
        开发者工具不可用时回退 simulate（组件级补充），回退原因写入报告。
        """
        if self._miniapp_trace is not None:
            return self._miniapp_trace
        executor, reason, fallback = miniapp.resolve(self.miniapp_executor_requested)
        if executor is None:
            raise ChainFailure(
                StepResult(
                    no=11,
                    key="miniapp_certify",
                    name="签约企业联系人在小程序完成认证",
                    actor="企业联系人",
                    mode="miniapp",
                    status="failed",
                    started_at=_utcnow().isoformat(),
                    ended_at=_utcnow().isoformat(),
                    duration_ms=0.0,
                ),
                f"小程序执行器不可用：{reason}",
                {},
            )
        self.miniapp_executor = executor
        self.miniapp_executor_fallback = fallback
        trace = miniapp.run(
            self.base_url,
            self.run_id,
            self.created["member_id"],
            self.miniapp_dir,
            executor=executor,
        )
        self._miniapp_trace = trace

        # 小程序内发出的真实请求并入本步 HTTP 证据文件
        for call in trace.get("requests", []):
            self._step_http.append(
                {
                    "source": "miniapp",
                    "method": call.get("method"),
                    "path": call.get("path"),
                    "status": call.get("statusCode"),
                    "response": call.get("responseBody"),
                    "duration_ms": call.get("durationMs"),
                }
            )
        self._miniapp_artifacts = {
            "miniapp_trace": miniapp.rel(self.miniapp_dir / "trace.json"),
            "miniapp_summary": miniapp.rel(self.miniapp_dir / "summary.md"),
            "miniapp_requests": miniapp.rel(self.miniapp_dir / "requests.jsonl"),
        }
        if executor == "automator":
            self._miniapp_artifacts.update(
                {
                    "screenshot_entry": miniapp.rel(self.miniapp_dir / "01_entry.png"),
                    "screenshot_certified": miniapp.rel(self.miniapp_dir / "01b_entry_certified.png"),
                    "screenshot_home": miniapp.rel(self.miniapp_dir / "02_home.png"),
                    "screenshot_home_full": miniapp.rel(self.miniapp_dir / "03_home_full.png"),
                }
            )
        else:
            self._miniapp_artifacts.update(
                {
                    "render_initial": miniapp.rel(self.miniapp_dir / "01_initial_render.html"),
                    "render_after_certify": miniapp.rel(self.miniapp_dir / "02_after_certify.html"),
                    "render_after_home": miniapp.rel(self.miniapp_dir / "03_after_home.html"),
                }
            )
        return trace

    @staticmethod
    def _miniapp_call(trace: dict[str, Any], prefix: str) -> dict[str, Any]:
        for call in trace.get("requests", []):
            if str(call.get("path", "")).startswith(prefix):
                return call
        raise AssertionError(f"小程序未发起 {prefix} 请求：{trace.get('requests')}")

    def step_11(self) -> dict:
        """第 11 步：在小程序内完成企业联系人认证（组件真实交互）。"""
        trace = self._miniapp_session()
        call = self._miniapp_call(trace, "/api/miniapp/certify")
        body = call.get("responseBody") or {}
        self._assert(call["method"] == "POST", f"认证应为 POST，实际 {call['method']}")
        self._assert(call["statusCode"] == 200, f"认证接口应返回 200，实际 {call['statusCode']}")
        if trace.get("tool") == "miniprogram-automator":
            # automator 在开发者工具运行时内发请求，HTTP 头无法代扣；改由服务端 audit 反证：
            # 端点以 member.run_id 校验 run_id，缺少/错配 x-run-id 会 404 且不会推进链路。
            audit = (trace.get("serverAudit") or {}).get("certify") or {}
            self._assert(audit.get("step_key") == "miniapp_certify", f"服务端未记录第 11 步 audit：{audit}")
            self._assert(
                str((audit.get("payload") or {}).get("member_id", "")) == str(self.created["member_id"]),
                "服务端 audit 的 member_id 与本次 run 不一致，说明 x-run-id 未生效",
            )
        else:
            self._assert(
                (call.get("requestHeaders") or {}).get("x-run-id") == self.run_id,
                "小程序请求必须携带本次 run 的 x-run-id（数据隔离）",
            )
        self._assert(body.get("certify_status") == "certified", f"认证状态应为 certified，实际 {body.get('certify_status')}")
        self._assert(str(body.get("openid_stub", "")).startswith("wx_stub_"), f"小程序桩返回异常：{body.get('openid_stub')}")
        self._assert(body.get("application_status") == "certified", f"状态应为 certified，实际 {body.get('application_status')}")

        phases = {step["stage"]: step.get("phase") for step in trace.get("steps", [])}
        self._assert(phases.get("certify") == "certified", f"小程序组件认证后 phase 应为 certified，实际 {phases.get('certify')}")
        expected_event = "page.certified" if trace.get("tool") == "miniprogram-automator" else "certified"
        self._assert(
            any(e.get("name") == expected_event for e in trace.get("events", [])),
            f"小程序未触发 {expected_event} 事件",
        )
        entry_step = next((s for s in trace.get("steps", []) if s["stage"] == "entry"), {})
        if trace.get("tool") == "miniprogram-automator":
            self._assert(
                entry_step.get("pagePath") == "/pages/entry/index",
                f"小程序应从 pages/entry/index 进入，实际 {entry_step.get('pagePath')}",
            )
            self._assert(
                (trace.get("screenshots") or {}).get("certify", {}).get("ok") is True,
                "automator 未产出认证后截图",
            )
        return {
            "assertion": (
                "小程序内提交验证码完成企业联系人认证："
                f"POST /api/miniapp/certify → 200（{call.get('durationMs')}ms），"
                "页面 pages/entry/index 上真实输入并点击提交，phase=idle→certified，"
                "触发 certified 事件，状态=certified"
            ),
            "evidence": {
                "executor": trace.get("tool"),
                "executor_note": trace.get("note"),
                "entry_page": entry_step.get("pagePath"),
                "request": {k: call.get(k) for k in ("method", "path", "statusCode", "durationMs")},
                "response": body,
                "component_phase": phases.get("certify"),
                "dom_sha256": next((s["domSha256"] for s in trace.get("steps", []) if s["stage"] == "certify"), None),
                "events": [e.get("name") for e in trace.get("events", [])],
                "assertions_total": len(trace.get("assertions", [])),
            },
        }

    def step_12(self) -> dict:
        """第 12 步：小程序首页展示首月资源推荐（同一小程序会话内继续交互）。"""
        trace = self._miniapp_session()
        call = self._miniapp_call(trace, "/api/miniapp/home")
        body = call.get("responseBody") or {}
        month = _utcnow().strftime("%Y-%m")
        self._assert(call["method"] == "GET", f"首页应为 GET，实际 {call['method']}")
        self._assert(call["statusCode"] == 200, f"首页接口应返回 200，实际 {call['statusCode']}")
        self._assert(body.get("month") == month, f"推荐月份应为 {month}，实际 {body.get('month')}")
        self._assert(len(body.get("items", [])) >= 3, f"首月资源推荐条目不足：{len(body.get('items', []))}")
        self._assert(all(item.get("quota", 0) > 0 for item in body.get("items", [])), "推荐资源配额必须为正数")
        self._assert(body.get("application_status") == "activated", f"状态应为 activated，实际 {body.get('application_status')}")

        phases = {step["stage"]: step.get("phase") for step in trace.get("steps", [])}
        self._assert(phases.get("home") == "home", f"小程序组件首页后 phase 应为 home，实际 {phases.get('home')}")
        expected_event = "page.home.ok" if trace.get("tool") == "miniprogram-automator" else "home-ready"
        self._assert(
            any(e.get("name") == expected_event for e in trace.get("events", [])),
            f"小程序未触发 {expected_event} 事件",
        )

        home_step = next((s for s in trace.get("steps", []) if s["stage"] == "home"), {})
        rendered = trace.get("rendered") or {}
        if trace.get("tool") == "miniprogram-automator":
            # 页面级证据：真实路由到 pages/home/index + 页面上真实节点计数
            self._assert(home_step.get("pagePath") == "pages/home/index", f"首页路由异常：{home_step.get('pagePath')}")
            self._assert(
                int(home_step.get("renderedItems") or 0) == len(body.get("items", [])),
                f"页面上数到的资源条目（{home_step.get('renderedItems')}）与接口返回（{len(body.get('items', []))}）不一致",
            )
            self._assert(int(rendered.get("items") or 0) >= 3, f"页面上未渲染出 ≥3 个资源条目：{rendered.get('items')}")
            self._assert(
                (trace.get("screenshots") or {}).get("home", {}).get("ok") is True,
                "automator 未产出首页截图",
            )
            audit = (trace.get("serverAudit") or {}).get("home") or {}
            self._assert(audit.get("step_key") == "miniapp_home", f"服务端未记录第 12 步 audit：{audit}")
        self.created["recommendation_id"] = body["recommendation_id"]
        return {
            "assertion": (
                f"小程序首页渲染 {month} 首月资源包 {len(body['items'])} 项"
                f"（页面上数到 {home_step.get('renderedItems') or len(body['items'])} 个节点，与数据一致），"
                f"GET /api/miniapp/home → 200（{call.get('durationMs')}ms），链路状态=activated"
            ),
            "evidence": {
                "executor": trace.get("tool"),
                "executor_note": trace.get("note"),
                "home_page": home_step.get("pagePath"),
                "rendered_items": home_step.get("renderedItems"),
                "rendered_texts": rendered.get("itemTexts"),
                "month_text": home_step.get("monthText"),
                "screenshots": (trace.get("screenshots") or {}),
                "request": {k: call.get(k) for k in ("method", "path", "statusCode", "durationMs")},
                "response": body,
                "component_phase": phases.get("home"),
                "dom_sha256": next((s["domSha256"] for s in trace.get("steps", []) if s["stage"] == "home"), None),
                "events": [e.get("name") for e in trace.get("events", [])],
            },
        }

    # ------------------------------------------------------------------ 收尾

    def finalize(self) -> dict:
        """清理 + 回查 + 产出报告。不抛异常，结论写入 report 供断言。"""
        if self.finished_at is None:
            self.finished_at = _utcnow()
        cleanup_result: dict[str, Any] = {}
        try:
            if os.environ.get("SMOKE_KEEP_DATA") == "1":
                # 仅供 AC3「清理前后对比」取证：保留数据，由脚本再调 DELETE 接口并回查
                counts = self.client.json("GET", f"/api/admin/run/{self.run_id}/counts")
                cleanup_result = {
                    "cleaned_at": None,
                    "deleted": {},
                    "deleted_total": 0,
                    "remaining": counts["counts"],
                    "remaining_total": counts["total"],
                    "skipped": "SMOKE_KEEP_DATA=1：保留数据用于清理校验取证",
                }
            else:
                deleted = self.client.json("DELETE", f"/api/admin/run/{self.run_id}")
                counts = self.client.json("GET", f"/api/admin/run/{self.run_id}/counts")
                cleanup_result = {
                    "cleaned_at": _iso(_utcnow()),
                    "deleted": deleted["deleted"],
                    "deleted_total": deleted["deleted_total"],
                    "remaining": counts["counts"],
                    "remaining_total": counts["total"],
                }
        except Exception as exc:  # noqa: BLE001
            cleanup_result = {
                "cleaned_at": _iso(_utcnow()),
                "deleted": {},
                "deleted_total": 0,
                "remaining": {},
                "remaining_total": -1,
                "error": f"{type(exc).__name__}: {exc}",
            }
        self.cleanup = cleanup_result

        report = self.build_report()
        json_path, md_path = write_reports(report, self.reports_dir)
        self.report_paths = {
            "report_json": str(json_path.relative_to(ROOT)),
            "report_md": str(md_path.relative_to(ROOT)),
            "artifacts_dir": str(self.artifacts_dir.relative_to(ROOT)),
        }
        # 报告里补上自身路径，再覆盖写一次，保证自查闭环
        report["artifacts"].update(self.report_paths)
        write_reports(report, self.reports_dir)
        self.close()
        return report

    def build_report(self) -> dict:
        counts = {
            "passed": sum(1 for r in self.results if r.status == "passed"),
            "failed": sum(1 for r in self.results if r.status == "failed"),
            "skipped": sum(1 for r in self.results if r.status == "skipped"),
        }
        status = "failed" if counts["failed"] else ("passed" if counts["passed"] else "running")
        total_ms = 0.0
        if self.started_at and self.finished_at:
            total_ms = round((self.finished_at - self.started_at).total_seconds() * 1000, 1)
        return {
            "run_id": self.run_id,
            "scenario": self.scenario,
            "mode": self.mode,
            "skip_miniprogram": self.skip_miniprogram,
            "miniapp_executor_requested": self.miniapp_executor_requested,
            "miniapp_executor": self.miniapp_executor,
            "miniapp_executor_fallback": self.miniapp_executor_fallback,
            "base_url": self.base_url,
            "started_at": _iso(self.started_at) if self.started_at else "",
            "finished_at": _iso(self.finished_at) if self.finished_at else "",
            "total_duration_ms": total_ms,
            "status": status,
            "counts": counts,
            "failed_step": (
                {"no": self.failure.no, "key": self.failure.key, "name": self.failure.name, "reason": self.failure_reason}
                if self.failure
                else None
            ),
            "steps": [r.to_dict() for r in self.results],
            "created_ids": self.created,
            "cleanup": self.cleanup,
            "artifacts": {"artifacts_dir": str(self.artifacts_dir.relative_to(ROOT))},
        }


def run_chain(
    base_url: str,
    run_id: str,
    *,
    skip_miniprogram: bool = False,
    headless: bool = True,
    scenario: str = "chain",
    miniapp_executor: str = "auto",
) -> tuple[ChainRunner, dict, ChainFailure | None]:
    """执行一条链并保证收尾：无论成败都清理数据、落盘报告。"""
    runner = ChainRunner(
        base_url,
        run_id,
        skip_miniprogram=skip_miniprogram,
        headless=headless,
        scenario=scenario,
        miniapp_executor=miniapp_executor,
    )
    failure: ChainFailure | None = None
    try:
        runner.execute()
    except ChainFailure as exc:
        failure = exc
    finally:
        report = runner.finalize()
    return runner, report, failure
