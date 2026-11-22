"""Reference stub of the 12-step sales funnel (招商闭环).

This is NOT the customer's platform. It is a faithful, contract-shaped stub that
implements exactly the states the chain-of-steps use case asserts, so the use case
can be executed for real (real HTTP + real browser) before the platform is assembled.
See README "对接点" for the mapping to the real services.
"""
from __future__ import annotations

import os
from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

from .store import (
    STORE, Application, Lead, Visit, Minutes, Quote, Contract, Room, Handover, Member,
    SALESPOOL, new_id, now,
)

app = FastAPI(title="Sales funnel reference stub", version="1.0.0")

MINI_VERIFY_CODE = "246810"


def require(cond: bool, code: str, message: str, status: int = 409) -> None:
    if not cond:
        raise HTTPException(status_code=status, detail={"code": code, "message": message})


def must(table: str, entity_id: str):
    obj = STORE.get(table, entity_id)
    require(obj is not None, "NOT_FOUND", f"{table}/{entity_id} not found", 404)
    return obj


# ---------------------------------------------------------------- models
class ApplicationIn(BaseModel):
    run_id: str
    company: str = Field(min_length=2)
    contact_name: str = Field(min_length=1)
    contact_phone: str = Field(min_length=5)
    intent: str = ""


class ContactIn(BaseModel):
    note: str = ""


class VisitIn(BaseModel):
    scheduled_at: str


class VerifyVisitIn(BaseModel):
    code: str


class MinutesIn(BaseModel):
    summary: str = Field(min_length=2)


class QuoteIn(BaseModel):
    monthly_cents: int = Field(gt=0)
    discount_bps: int = Field(gt=0, le=10000)


class EsignIn(BaseModel):
    quote_id: str
    reject: bool = False


class HandoverIn(BaseModel):
    room_id: str
    manager_id: str


class MiniVerifyIn(BaseModel):
    lead_id: str
    phone: str
    code: str


# ---------------------------------------------------------------- health
@app.get("/healthz")
def healthz():
    return {"ok": True, "service": "sales-funnel-stub"}


# ------------------------------------------------------------- step 1
@app.post("/api/site/applications")
def submit_application(body: ApplicationIn):
    app_obj = Application(
        id=new_id("app"), run_id=body.run_id, created_by="website",
        company=body.company, contact_name=body.contact_name,
        contact_phone=body.contact_phone, intent=body.intent,
    )
    STORE.add("applications", app_obj)

    seq = STORE.next_seq()
    lead = Lead(
        id=new_id("lead"), run_id=body.run_id, created_by="lead-router",
        application_id=app_obj.id, company=body.company,
        assigned_to=SALESPOOL[seq % len(SALESPOOL)], status="assigned",
    )
    STORE.add("leads", lead)
    return {"application_id": app_obj.id, "lead_id": lead.id,
            "assigned_to": lead.assigned_to, "status": lead.status,
            "rule": "round-robin over active sales pool"}


# ------------------------------------------------------------- step 2
@app.get("/api/crm/leads/{lead_id}")
def get_lead(lead_id: str):
    lead = must("leads", lead_id)
    return STORE.dump(lead)


# ------------------------------------------------------------- step 3
@app.post("/api/sales/leads/{lead_id}/contact")
def first_contact(lead_id: str, body: ContactIn):
    lead: Lead = must("leads", lead_id)
    require(lead.status == "assigned", "BAD_STATE", f"lead is {lead.status}, expected assigned")
    lead.status = "contacted"
    lead.first_contact_at = now()
    lead.touch("sales")
    return {"lead_id": lead.id, "status": lead.status, "first_contact_at": lead.first_contact_at}


# ------------------------------------------------------------- step 4
@app.post("/api/sales/leads/{lead_id}/visit")
def schedule_visit(lead_id: str, body: VisitIn):
    lead: Lead = must("leads", lead_id)
    require(lead.status == "contacted", "BAD_STATE", f"lead is {lead.status}, expected contacted")
    visit = Visit(
        id=new_id("visit"), run_id=lead.run_id, created_by="sales",
        lead_id=lead.id, scheduled_at=body.scheduled_at,
        code=str(100000 + STORE.next_seq() % 900000),
    )
    STORE.add("visits", visit)
    lead.status = "visit_scheduled"
    lead.touch("sales")
    return {"visit_id": visit.id, "code": visit.code, "status": visit.status,
            "lead_status": lead.status}


# ------------------------------------------------------------- step 5
@app.post("/api/site/visits/verify")
def verify_visit(body: VerifyVisitIn):
    hit = next((v for v in STORE.tables["visits"].values()
                if v.code == body.code and v.deleted_at is None), None)
    require(hit is not None, "INVALID_CODE", "visitor code not found", 404)
    require(hit.status == "scheduled", "BAD_STATE", f"visit is {hit.status}")
    hit.status = "checked_in"
    hit.checked_in_at = now()
    hit.touch("front-desk")
    lead: Lead = must("leads", hit.lead_id)
    lead.status = "visited"
    lead.touch("front-desk")
    return {"visit_id": hit.id, "status": hit.status, "checked_in_at": hit.checked_in_at,
            "lead_status": lead.status}


# ------------------------------------------------------------- step 6
@app.post("/api/sales/leads/{lead_id}/minutes")
def confirm_minutes(lead_id: str, body: MinutesIn):
    lead: Lead = must("leads", lead_id)
    require(lead.status == "visited", "BAD_STATE", f"lead is {lead.status}, expected visited")
    obj = Minutes(id=new_id("min"), run_id=lead.run_id, created_by="sales",
                  lead_id=lead.id, summary=body.summary, confirmed=True)
    STORE.add("minutes", obj)
    lead.status = "minutes_confirmed"
    lead.touch("sales")
    return {"minutes_id": obj.id, "confirmed": True, "lead_status": lead.status}


# ------------------------------------------------------------- step 7
@app.post("/api/sales/leads/{lead_id}/quotes")
def create_quote(lead_id: str, body: QuoteIn):
    lead: Lead = must("leads", lead_id)
    require(lead.status == "minutes_confirmed", "BAD_STATE",
            f"lead is {lead.status}, expected minutes_confirmed")
    # 9.5 折以内 => discount_bps >= 9500 (实付 >= 标准价 * 0.95)
    require(body.discount_bps >= 9500, "BELOW_FLOOR",
            f"discount_bps={body.discount_bps} exceeds 9.5 折 authority", 422)
    quote = Quote(id=new_id("quote"), run_id=lead.run_id, created_by="sales",
                  lead_id=lead.id, monthly_cents=body.monthly_cents,
                  discount_bps=body.discount_bps, status="approved")
    STORE.add("quotes", quote)
    lead.status = "quoted"
    lead.touch("sales")
    net = body.monthly_cents * body.discount_bps // 10000
    return {"quote_id": quote.id, "monthly_cents": body.monthly_cents,
            "discount_bps": body.discount_bps, "net_monthly_cents": net,
            "status": quote.status, "lead_status": lead.status}


# ------------------------------------------------------------- step 8
@app.post("/api/contracts/esign")
def esign(body: EsignIn):
    quote: Quote = must("quotes", body.quote_id)
    require(quote.status == "approved", "BAD_STATE", f"quote is {quote.status}")
    lead: Lead = must("leads", quote.lead_id)
    require(lead.status == "quoted", "BAD_STATE", f"lead is {lead.status}, expected quoted")

    if body.reject or os.getenv("FAIL_STEP") == "esign":
        raise HTTPException(status_code=422, detail={
            "code": "ESIGN_REJECTED",
            "message": "signer rejected the contract (injected)",
            "step": "电子签",
        })

    room = next((r for r in STORE.tables["rooms"].values()
                 if r.status == "vacant" and r.deleted_at is None), None)
    require(room is not None, "NO_VACANCY", "no vacant room available", 409)

    contract = Contract(id=new_id("ctr"), run_id=lead.run_id, created_by="sales",
                        quote_id=quote.id, lead_id=lead.id, room_id=room.id,
                        signed_by_applicant=True, signed_by_org=True, status="signed")
    STORE.add("contracts", contract)

    room.status = "rented"
    room.contract_id = contract.id
    room.lead_id = lead.id
    room.lease_run_id = lead.run_id
    room.touch("sales")
    lead.status = "rented"
    lead.touch("sales")
    return {"contract_id": contract.id, "status": contract.status,
            "signed_by_applicant": True, "signed_by_org": True,
            "room_id": room.id, "room_status": room.status, "lead_status": lead.status}


# ------------------------------------------------------------- step 9
@app.get("/api/site/rooms/{room_id}")
def get_room(room_id: str):
    room: Room = must("rooms", room_id)
    return STORE.dump(room)


# ------------------------------------------------------------ step 10
@app.post("/api/ops/handovers")
def claim_handover(body: HandoverIn):
    room: Room = must("rooms", body.room_id)
    require(room.status == "rented", "BAD_STATE", f"room is {room.status}, expected rented")
    lead: Lead = must("leads", room.lead_id or "")
    require(lead.status == "rented", "BAD_STATE", f"lead is {lead.status}, expected rented")
    obj = Handover(id=new_id("hnd"), run_id=lead.run_id, created_by=body.manager_id,
                   room_id=room.id, lead_id=lead.id, manager_id=body.manager_id)
    STORE.add("handovers", obj)
    lead.status = "handover_claimed"
    lead.touch(body.manager_id)
    return {"handover_id": obj.id, "status": obj.status, "lead_status": lead.status}


# ------------------------------------------------------------ step 11
@app.post("/api/mini/auth/verify")
def mini_verify(body: MiniVerifyIn):
    lead: Lead = must("leads", body.lead_id)
    require(lead.status == "handover_claimed", "BAD_STATE",
            f"lead is {lead.status}, expected handover_claimed")
    require(body.code == MINI_VERIFY_CODE, "INVALID_CODE", "verification code mismatch", 422)
    member = Member(id=new_id("mb"), run_id=lead.run_id, created_by="mini",
                    lead_id=lead.id, phone=body.phone, verified=True)
    STORE.add("members", member)
    lead.status = "member_verified"
    lead.touch("mini")
    return {"member_id": member.id, "verified": True, "lead_status": lead.status}


# ------------------------------------------------------------ step 12
@app.get("/api/mini/home/recommendations")
def mini_home(member_id: str):
    member: Member = must("members", member_id)
    require(member.verified, "BAD_STATE", "member not verified")
    lead: Lead = must("leads", member.lead_id)
    require(lead.status == "member_verified", "BAD_STATE", f"lead is {lead.status}")
    items = [
        {"id": "res-policy", "title": "首月政策速配（3 场）", "kind": "policy"},
        {"id": "res-capital", "title": "产业资本对接日", "kind": "capital"},
        {"id": "res-peer", "title": "同行业私享会", "kind": "peer"},
    ]
    member.first_month_recommendations = items
    return {"member_id": member.id, "first_month": True, "items": items}


# ------------------------------------------------------- run isolation
@app.get("/api/_test/count")
def count_run(run_id: str):
    counts = STORE.count_run(run_id)
    return {"run_id": run_id, "counts": counts, "total": sum(counts.values())}


@app.get("/api/_test/visit-code")
def visit_code(lead_id: str):
    """Test-only helper: the UI step needs the code that the sales step generated."""
    hits = [v for v in STORE.tables["visits"].values()
            if v.lead_id == lead_id and v.deleted_at is None]
    require(bool(hits), "NOT_FOUND", f"no visit for lead {lead_id}", 404)
    return {"lead_id": lead_id, "code": hits[-1].code}


# --- test-only: chain step status feed, so a failed run can be screenshotted ------
CHAIN_STATUS: dict[str, list[dict]] = {}


@app.post("/api/_test/chain-status")
def put_chain_status(payload: dict):
    CHAIN_STATUS[payload["run_id"]] = payload.get("steps", [])
    return {"ok": True, "run_id": payload["run_id"]}


@app.get("/_diag/chain", response_class=HTMLResponse)
def diag_chain(run_id: str):
    steps = CHAIN_STATUS.get(run_id, [])
    rows = "".join(
        f'<tr class="{s["status"]}"><td>{s["index"]}</td><td>{s["name"]}</td>'
        f'<td class="st">{s["status"]}</td><td>{s["duration_ms"]:.0f} ms</td></tr>'
        for s in steps) or '<tr><td colspan="4">no step recorded</td></tr>'
    failed = next((s for s in steps if s["status"] == "failed"), None)
    banner = (f'<h2 id="failed-step" style="color:#b91c1c">失败步骤：第 {failed["index"]} 步「{failed["name"]}」</h2>'
              if failed else '<h2 id="failed-step" style="color:#15803d">全部步骤通过</h2>')
    return HTMLResponse(f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<title>链式步骤状态 {run_id}</title><style>
body{{font:14px/1.6 -apple-system,"Segoe UI",sans-serif;margin:24px;color:#1f2937}}
h1{{font-size:18px}} .meta{{color:#6b7280;margin-bottom:12px}}
table{{border-collapse:collapse;width:820px}} th,td{{padding:7px 10px;border-bottom:1px solid #e5e7eb;text-align:left}}
th{{background:#f3f4f6;font-weight:600}} tr.passed .st{{color:#15803d;font-weight:600}}
tr.failed .st{{color:#b91c1c;font-weight:600}} tr.failed{{background:#fef2f2}}
tr.skipped .st{{color:#9ca3af;font-weight:600}} h2{{font-size:16px;color:#b91c1c}}
</style></head><body>
<h1>链式用例步骤状态</h1>
<div class="meta">run_id: <code>{run_id}</code></div>
{banner}
<table><thead><tr><th>#</th><th>步骤</th><th>结果</th><th>耗时</th></tr></thead>
<tbody>{rows}</tbody></table>
</body></html>""")


@app.post("/api/_test/purge")
def purge_run(run_id: str):
    removed = STORE.purge_run(run_id)
    counts = STORE.count_run(run_id)
    return {"run_id": run_id, "removed": removed, "remaining": counts,
            "total_remaining": sum(counts.values())}


# ------------------------------------------------------------------ UI
# Real HTML endpoints so the Playwright steps drive a browser, not mocked DOM.
APPLY_PAGE = """<!doctype html><html lang="zh"><head><meta charset="utf-8">
<title>会员空间 · 入会申请</title></head><body>
<h1>入会申请</h1>
<form method="post" action="/apply">
  <label>公司名称 <input name="company" id="company" required></label><br>
  <label>联系人 <input name="contact_name" id="contact_name" required></label><br>
  <label>手机号 <input name="contact_phone" id="contact_phone" required></label><br>
  <label>入驻意向 <input name="intent" id="intent"></label><br>
  <input type="hidden" name="run_id" id="run_id">
  <button type="submit" id="submit-apply">提交申请</button>
</form>
<div id="result"></div>
<script>document.getElementById('run_id').value =
  new URLSearchParams(location.search).get('run_id') || '';</script>
</body></html>"""


@app.get("/apply", response_class=HTMLResponse)
def apply_page():
    return APPLY_PAGE


@app.post("/apply", response_class=HTMLResponse)
def apply_submit(company: str = Form(...), contact_name: str = Form(...),
                 contact_phone: str = Form(...), intent: str = Form(""),
                 run_id: str = Form("")):
    body = ApplicationIn(run_id=run_id or "ui-default", company=company,
                         contact_name=contact_name, contact_phone=contact_phone,
                         intent=intent)
    res = submit_application(body)
    return HTMLResponse(
        f"<html><body><h1 id='ok'>申请已提交</h1>"
        f"<p id='application-id'>{res['application_id']}</p>"
        f"<p id='lead-id'>{res['lead_id']}</p>"
        f"<p id='assigned-to'>{res['assigned_to']}</p></body></html>")


VERIFY_PAGE = """<!doctype html><html lang="zh"><head><meta charset="utf-8">
<title>前台 · 访客码核销</title></head><body>
<h1>访客码核销</h1>
<form method="post" action="/desk/verify">
  <label>访客码 <input name="code" id="code" required></label>
  <button type="submit" id="submit-verify">核销</button>
</form></body></html>"""


@app.get("/desk/verify", response_class=HTMLResponse)
def verify_page():
    return VERIFY_PAGE


@app.post("/desk/verify", response_class=HTMLResponse)
def verify_submit(code: str = Form(...)):
    try:
        res = verify_visit(VerifyVisitIn(code=code))
    except HTTPException as exc:
        return HTMLResponse(
            f"<html><body><h1 id='fail'>核销失败</h1>"
            f"<p id='err'>{exc.detail}</p></body></html>", status_code=exc.status_code)
    return HTMLResponse(
        f"<html><body><h1 id='ok'>核销成功</h1>"
        f"<p id='visit-id'>{res['visit_id']}</p>"
        f"<p id='checked-in-at'>{res['checked_in_at']}</p></body></html>")


MINI_PAGE = """<!doctype html><html lang="zh"><head><meta charset="utf-8">
<title>会员小程序 · 认证</title></head><body>
<h1>会员认证</h1>
<form method="post" action="/mini/login">
  <label>手机号 <input name="phone" id="phone" required></label>
  <label>验证码 <input name="code" id="code" required></label>
  <input type="hidden" name="lead_id" id="lead_id">
  <button type="submit" id="submit-mini">认证</button>
</form>
<script>document.getElementById('lead_id').value =
  new URLSearchParams(location.search).get('lead_id') || '';</script>
</body></html>"""


@app.get("/mini/login", response_class=HTMLResponse)
def mini_page():
    return MINI_PAGE


@app.post("/mini/login", response_class=HTMLResponse)
def mini_login(phone: str = Form(...), code: str = Form(...), lead_id: str = Form("")):
    try:
        res = mini_verify(MiniVerifyIn(lead_id=lead_id, phone=phone, code=code))
    except HTTPException as exc:
        return HTMLResponse(f"<html><body><h1 id='fail'>认证失败</h1>"
                            f"<p id='err'>{exc.detail}</p></body></html>",
                            status_code=exc.status_code)
    return HTMLResponse(f"<html><body><h1 id='ok'>认证成功</h1>"
                        f"<p id='member-id'>{res['member_id']}</p></body></html>")


@app.exception_handler(HTTPException)
def http_exc_handler(_request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code,
                        content={"error": exc.detail if isinstance(exc.detail, dict)
                                 else {"code": "ERROR", "message": str(exc.detail)}})
