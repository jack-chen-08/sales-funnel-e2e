""" Mock 会员空间平台：承载 12 步招商链路的接口 + 3 个真实可点击网页。

网页（供 Playwright 驱动真实点击）：
  GET  /site/apply       官网入会申请表
  GET  /advisor/console  招商顾问工作台（首次联系）
  GET  /frontdesk/checkin 前台访客码核销
  GET  /sign/console     电子签签约台（桩：两方签署）
"""

from __future__ import annotations

import datetime as dt
import secrets
import uuid
from pathlib import Path
from typing import Annotated, Any

from fastapi import Depends, FastAPI, Form, Header, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from . import models, stubs, workflow
from .config import settings
from .db import get_session
from .workflow import STEP_BY_KEY, STEPS, assert_status

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI(title="会员空间平台 · 招商链路冒烟 Mock", version="1.0.0")

SessionDep = Annotated[Session, Depends(get_session)]
RunHeader = Annotated[str | None, Header(alias="X-Run-Id")]

CLEANUP_TABLES = (
    "resource_recommendations",
    "members",
    "handovers",
    "rooms",
    "esign_envelopes",
    "quotes",
    "visit_minutes",
    "visits",
    "contacts",
    "leads",
    "applications",
    "audit_events",
)


# --------------------------------------------------------------------------- 工具


def _now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _run_id(run_id: str | None) -> str:
    if not run_id:
        raise HTTPException(status_code=400, detail={"code": "RUN_ID_REQUIRED", "message": "缺少 X-Run-Id"})
    return run_id


def _application(db: Session, run_id: str) -> models.Application:
    row = db.scalars(select(models.Application).where(models.Application.run_id == run_id)).first()
    if row is None:
        raise HTTPException(status_code=404, detail={"code": "APPLICATION_NOT_FOUND", "run_id": run_id})
    return row


def _audit(db: Session, run_id: str, step_no: int, step_key: str, event: str, payload: dict[str, Any]) -> None:
    db.add(models.AuditEvent(run_id=run_id, step_no=step_no, step_key=step_key, event=event, payload=payload))


def _ensure_run(db: Session, run_id: str, mode: str) -> models.SmokeRun:
    run = db.get(models.SmokeRun, run_id)
    if run is None:
        run = models.SmokeRun(run_id=run_id, mode=mode, status="running")
        db.add(run)
        db.flush()
    return run


def _state_error(exc: workflow.StateError) -> HTTPException:
    return HTTPException(
        status_code=409,
        detail={
            "code": "STATE_CONFLICT",
            "step": exc.step.name,
            "step_no": exc.step.no,
            "expected": exc.expected,
            "actual": exc.actual,
        },
    )


def _advance(db: Session, app_row: models.Application, step: workflow.StepSpec, payload: dict[str, Any]) -> None:
    try:
        app_row.status = workflow.next_status(step, app_row.status)
    except workflow.StateError as exc:  # 状态机拦截
        raise _state_error(exc) from exc
    _audit(db, app_row.run_id, step.no, step.key, f"{step.key}:ok", payload)


# --------------------------------------------------------------------------- 页面


@app.get("/healthz")
def healthz() -> dict:
    return {
        "status": "ok",
        "sign_stub_mode": settings.sign_stub_mode,
        "miniapp_stub_mode": settings.miniapp_stub_mode,
        "steps": len(STEPS),
    }


@app.get("/site/apply", response_class=HTMLResponse)
def page_site_apply(request: Request, run_id: str = Query(...)) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="site_apply.html",
        context={"run_id": run_id, "site_label": "云栖科创园（虚构站点）"},
    )


@app.post("/site/apply/submit", response_class=HTMLResponse)
def submit_site_apply(
    request: Request,
    db: SessionDep,
    run_id: Annotated[str, Form()],
    company_name: Annotated[str, Form()],
    applicant_name: Annotated[str, Form()],
    applicant_phone: Annotated[str, Form()],
    region: Annotated[str, Form()],
    seat_demand: Annotated[int, Form()],
) -> HTMLResponse:
    step = STEP_BY_KEY["site_apply"]
    existing = db.scalars(select(models.Application).where(models.Application.run_id == run_id)).first()
    if existing is not None:
        raise HTTPException(status_code=409, detail={"code": "APPLICATION_EXISTS", "run_id": run_id})

    _ensure_run(db, run_id, mode="full")
    row = models.Application(
        run_id=run_id,
        company_name=company_name.strip(),
        applicant_name=applicant_name.strip(),
        applicant_phone=applicant_phone.strip(),
        region=region.strip().lower(),
        seat_demand=int(seat_demand),
        status="none",
    )
    db.add(row)
    db.flush()
    _advance(db, row, step, {"application_id": str(row.id), "company_name": row.company_name})
    db.commit()
    return templates.TemplateResponse(
        request=request,
        name="apply_result.html",
        context={"run_id": run_id, "application_id": str(row.id), "status": row.status, "company": row.company_name},
    )


@app.get("/advisor/console", response_class=HTMLResponse)
def page_advisor_console(request: Request, db: SessionDep, run_id: str = Query(...)) -> HTMLResponse:
    lead = db.scalars(select(models.Lead).where(models.Lead.run_id == run_id)).first()
    if lead is None:
        raise HTTPException(status_code=404, detail={"code": "LEAD_NOT_FOUND"})
    app_row = db.get(models.Application, lead.application_id)
    return templates.TemplateResponse(
        request=request,
        name="advisor_console.html",
        context={
            "run_id": run_id,
            "lead_id": str(lead.id),
            "advisor_id": lead.advisor_id,
            "rule": lead.assign_rule,
            "company": app_row.company_name if app_row else "",
            "status": app_row.status if app_row else "",
            "status_label": "待首次联系" if app_row and app_row.status == "assigned" else "已联系",
        },
    )


@app.get("/frontdesk/checkin", response_class=HTMLResponse)
def page_frontdesk(request: Request, db: SessionDep, run_id: str = Query(...)) -> HTMLResponse:
    visit = db.scalars(select(models.Visit).where(models.Visit.run_id == run_id)).first()
    if visit is None:
        raise HTTPException(status_code=404, detail={"code": "VISIT_NOT_FOUND"})
    return templates.TemplateResponse(
        request=request,
        name="frontdesk_checkin.html",
        context={"run_id": run_id, "visit_id": str(visit.id), "visit_code": visit.visit_code},
    )


@app.get("/sign/console", response_class=HTMLResponse)
def page_sign_console(request: Request, db: SessionDep, run_id: str = Query(...)) -> HTMLResponse:
    envelope = db.scalars(select(models.EsignEnvelope).where(models.EsignEnvelope.run_id == run_id)).first()
    if envelope is None:
        raise HTTPException(status_code=404, detail={"code": "ENVELOPE_NOT_FOUND"})
    return templates.TemplateResponse(
        request=request,
        name="sign_console.html",
        context={
            "run_id": run_id,
            "envelope_id": str(envelope.id),
            "envelope_no": envelope.envelope_no,
            "signers": envelope.signers,
        },
    )


# --------------------------------------------------------------------------- 接口


class AssignIn(BaseModel):
    application_id: uuid.UUID


class ContactIn(BaseModel):
    lead_id: uuid.UUID
    channel: str = "phone"
    note: str = "首次电话联系，确认选址需求与预算区间"


class BookVisitIn(BaseModel):
    lead_id: uuid.UUID
    scheduled_hours_ahead: int = Field(default=24, ge=1, le=240)


class CheckinIn(BaseModel):
    code: str = Field(min_length=6, max_length=6)
    desk: str = "A 座前台"


class MinutesIn(BaseModel):
    visit_id: uuid.UUID
    content: str = "客户确认 12 层南向 186㎡，认可物业与交付标准"


class QuoteIn(BaseModel):
    room_id: uuid.UUID
    discount_bp: int = Field(default=500, ge=0, le=500)


class SignIn(BaseModel):
    envelope_id: uuid.UUID


class HandoverIn(BaseModel):
    lead_id: uuid.UUID
    member_manager_id: str = "MM-021"


class CertifyIn(BaseModel):
    member_id: uuid.UUID
    verify_code: str = "123456"


class ProvisionRoomsIn(BaseModel):
    room_count: int = Field(default=2, ge=1, le=5)


@app.post("/api/rooms/provision")
def provision_rooms(payload: ProvisionRoomsIn, db: SessionDep, x_run_id: RunHeader = None) -> dict:
    """运营中台把候选房源放入本次 run 的房态池（房源属于本次冒烟数据，随 run_id 一起清理）。"""
    run_id = _run_id(x_run_id)
    _ensure_run(db, run_id, mode="full")
    existing = db.scalars(select(models.Room).where(models.Room.run_id == run_id)).all()
    if existing:
        return {"run_id": run_id, "rooms": [{"room_id": str(r.id), "room_no": r.room_no} for r in existing]}
    rooms = []
    for idx in range(payload.room_count):
        room = models.Room(
            run_id=run_id,
            room_no=f"12F-{1801 + idx}",
            list_price_cents=1_860_000 + idx * 60_000,
            status="free",
        )
        db.add(room)
        rooms.append(room)
    db.commit()
    return {"run_id": run_id, "rooms": [{"room_id": str(r.id), "room_no": r.room_no} for r in rooms]}


@app.post("/api/leads/assign")
def assign_lead(payload: AssignIn, db: SessionDep, x_run_id: RunHeader = None) -> dict:
    run_id = _run_id(x_run_id)
    step = STEP_BY_KEY["lead_assign"]
    app_row = db.get(models.Application, payload.application_id)
    if app_row is None or app_row.run_id != run_id:
        raise HTTPException(status_code=404, detail={"code": "APPLICATION_NOT_FOUND"})
    if app_row.status != step.entry_status:
        raise _state_error(workflow.StateError(step.entry_status, app_row.status, step))

    if app_row.seat_demand > 50:
        advisor_id, rule = workflow.SENIOR_ADVISOR
    else:
        advisor_id, rule = workflow.ADVISOR_ROUTING.get(app_row.region, workflow.ADVISOR_ROUTING["east"])

    lead = models.Lead(
        run_id=run_id,
        application_id=app_row.id,
        advisor_id=advisor_id,
        assign_rule=rule,
        status="assigned",
    )
    db.add(lead)
    db.flush()
    _advance(db, app_row, step, {"lead_id": str(lead.id), "advisor_id": advisor_id, "rule": rule})
    db.commit()
    return {
        "step": step.name,
        "lead_id": str(lead.id),
        "advisor_id": advisor_id,
        "assign_rule": rule,
        "application_status": app_row.status,
    }


@app.post("/api/contacts/first")
def first_contact(payload: ContactIn, db: SessionDep, x_run_id: RunHeader = None) -> dict:
    run_id = _run_id(x_run_id)
    step = STEP_BY_KEY["first_contact"]
    lead = db.get(models.Lead, payload.lead_id)
    if lead is None or lead.run_id != run_id:
        raise HTTPException(status_code=404, detail={"code": "LEAD_NOT_FOUND"})
    app_row = db.get(models.Application, lead.application_id)
    if app_row is None:
        raise HTTPException(status_code=404, detail={"code": "APPLICATION_NOT_FOUND"})

    contact = models.Contact(
        run_id=run_id,
        lead_id=lead.id,
        channel=payload.channel,
        note=payload.note,
        contacted_at=_now(),
    )
    db.add(contact)
    db.flush()
    _advance(db, app_row, step, {"contact_id": str(contact.id), "channel": payload.channel})
    lead.status = "contacted"
    db.commit()
    return {
        "step": step.name,
        "contact_id": str(contact.id),
        "contacted_at": contact.contacted_at.isoformat(),
        "application_status": app_row.status,
    }


@app.post("/api/visits/book")
def book_visit(payload: BookVisitIn, db: SessionDep, x_run_id: RunHeader = None) -> dict:
    run_id = _run_id(x_run_id)
    step = STEP_BY_KEY["book_visit"]
    lead = db.get(models.Lead, payload.lead_id)
    if lead is None or lead.run_id != run_id:
        raise HTTPException(status_code=404, detail={"code": "LEAD_NOT_FOUND"})
    app_row = db.get(models.Application, lead.application_id)
    if app_row is None:
        raise HTTPException(status_code=404, detail={"code": "APPLICATION_NOT_FOUND"})

    code = f"{secrets.randbelow(900000) + 100000}"
    visit = models.Visit(
        run_id=run_id,
        lead_id=lead.id,
        visit_code=code,
        scheduled_at=_now() + dt.timedelta(hours=payload.scheduled_hours_ahead),
        status="booked",
    )
    db.add(visit)
    db.flush()
    _advance(db, app_row, step, {"visit_id": str(visit.id), "visit_code": code})
    lead.status = "visit_booked"
    db.commit()
    return {
        "step": step.name,
        "visit_id": str(visit.id),
        "visit_code": code,
        "scheduled_at": visit.scheduled_at.isoformat(),
        "application_status": app_row.status,
    }


@app.post("/api/visits/checkin")
def checkin(payload: CheckinIn, db: SessionDep, x_run_id: RunHeader = None) -> dict:
    run_id = _run_id(x_run_id)
    step = STEP_BY_KEY["visitor_checkin"]
    visit = db.scalars(
        select(models.Visit).where(models.Visit.run_id == run_id, models.Visit.visit_code == payload.code)
    ).first()
    if visit is None:
        raise HTTPException(status_code=404, detail={"code": "VISIT_CODE_INVALID", "code_input": payload.code})
    if visit.status != "booked":
        raise HTTPException(status_code=409, detail={"code": "VISIT_ALREADY_CHECKED_IN", "status": visit.status})
    app_row = _application(db, run_id)

    visit.checked_in_at = _now()
    visit.desk = payload.desk
    visit.status = "checked_in"
    _advance(db, app_row, step, {"visit_id": str(visit.id), "desk": payload.desk})
    db.commit()
    return {
        "step": step.name,
        "visit_id": str(visit.id),
        "status": visit.status,
        "checked_in_at": visit.checked_in_at.isoformat(),
        "desk": visit.desk,
        "application_status": app_row.status,
    }


@app.post("/api/minutes/confirm")
def confirm_minutes(payload: MinutesIn, db: SessionDep, x_run_id: RunHeader = None) -> dict:
    run_id = _run_id(x_run_id)
    step = STEP_BY_KEY["minutes_confirm"]
    visit = db.get(models.Visit, payload.visit_id)
    if visit is None or visit.run_id != run_id:
        raise HTTPException(status_code=404, detail={"code": "VISIT_NOT_FOUND"})
    if visit.status != "checked_in":
        raise HTTPException(status_code=409, detail={"code": "VISIT_NOT_CHECKED_IN", "status": visit.status})
    app_row = _application(db, run_id)

    minutes = models.VisitMinutes(run_id=run_id, visit_id=visit.id, content=payload.content, confirmed_at=_now())
    db.add(minutes)
    db.flush()
    _advance(db, app_row, step, {"minutes_id": str(minutes.id), "visit_id": str(visit.id)})
    db.commit()
    return {
        "step": step.name,
        "minutes_id": str(minutes.id),
        "confirmed_at": minutes.confirmed_at.isoformat(),
        "application_status": app_row.status,
    }


@app.post("/api/quotes")
def create_quote(payload: QuoteIn, db: SessionDep, x_run_id: RunHeader = None) -> dict:
    run_id = _run_id(x_run_id)
    step = STEP_BY_KEY["quote"]
    lead = db.scalars(select(models.Lead).where(models.Lead.run_id == run_id)).first()
    if lead is None:
        raise HTTPException(status_code=404, detail={"code": "LEAD_NOT_FOUND"})
    room = db.get(models.Room, payload.room_id)
    if room is None or room.run_id != run_id:
        raise HTTPException(status_code=404, detail={"code": "ROOM_NOT_FOUND"})
    if room.status != "free":
        raise HTTPException(status_code=409, detail={"code": "ROOM_NOT_FREE", "status": room.status})
    app_row = _application(db, run_id)

    # 9.5 折以内：折扣基点不超过 500（即成交价 >= 挂牌价 95%），金额全部用分
    if payload.discount_bp > 500:
        raise HTTPException(
            status_code=422,
            detail={"code": "DISCOUNT_EXCEEDS_POLICY", "discount_bp": payload.discount_bp, "max_bp": 500},
        )
    final_cents = round(room.list_price_cents * (10000 - payload.discount_bp) / 10000)
    quote = models.Quote(
        run_id=run_id,
        lead_id=lead.id,
        room_id=room.id,
        list_price_cents=room.list_price_cents,
        discount_bp=payload.discount_bp,
        final_price_cents=final_cents,
        status="issued",
    )
    db.add(quote)
    db.flush()

    envelope = models.EsignEnvelope(
        run_id=run_id,
        quote_id=quote.id,
        envelope_no=stubs.new_envelope_no(run_id),
        signers=stubs.pending_signers(app_row.company_name, app_row.applicant_name),
        status="pending",
    )
    db.add(envelope)
    db.flush()
    _advance(
        db,
        app_row,
        step,
        {
            "quote_id": str(quote.id),
            "final_price_cents": final_cents,
            "discount_bp": payload.discount_bp,
            "envelope_id": str(envelope.id),
        },
    )
    db.commit()
    return {
        "step": step.name,
        "quote_id": str(quote.id),
        "envelope_id": str(envelope.id),
        "room_id": str(room.id),
        "list_price_cents": room.list_price_cents,
        "discount_bp": payload.discount_bp,
        "final_price_cents": final_cents,
        "application_status": app_row.status,
    }


@app.post("/api/esign/sign")
def esign_sign(payload: SignIn, db: SessionDep, x_run_id: RunHeader = None) -> JSONResponse:
    run_id = _run_id(x_run_id)
    step = STEP_BY_KEY["esign"]
    envelope = db.get(models.EsignEnvelope, payload.envelope_id)
    if envelope is None or envelope.run_id != run_id:
        raise HTTPException(status_code=404, detail={"code": "ENVELOPE_NOT_FOUND"})
    if envelope.status != "pending":
        raise HTTPException(status_code=409, detail={"code": "ENVELOPE_NOT_PENDING", "status": envelope.status})
    app_row = _application(db, run_id)

    result = stubs.sign_envelope(envelope)
    envelope.signers = result["signers"]
    envelope.status = result["status"]
    envelope.reject_reason = result["reject_reason"]

    if result["status"] != "signed":
        envelope.reject_reason = result["reject_reason"]
        _audit(
            db,
            run_id,
            step.no,
            step.key,
            "esign:rejected",
            {"envelope_id": str(envelope.id), "reason": result["reject_reason"]},
        )
        db.commit()
        return JSONResponse(
            status_code=422,
            content={
                "code": "ESIGN_REJECTED",
                "step": step.name,
                "step_no": step.no,
                "envelope_id": str(envelope.id),
                "envelope_status": envelope.status,
                "reject_reason": result["reject_reason"],
                "application_status": app_row.status,
            },
        )

    _advance(db, app_row, step, {"envelope_id": str(envelope.id), "envelope_no": envelope.envelope_no})
    db.commit()
    return JSONResponse(
        status_code=200,
        content={
            "step": step.name,
            "envelope_id": str(envelope.id),
            "envelope_no": envelope.envelope_no,
            "envelope_status": envelope.status,
            "signers": envelope.signers,
            "application_status": app_row.status,
        },
    )


@app.post("/api/rooms/{room_id}/lease")
def lease_room(room_id: uuid.UUID, db: SessionDep, x_run_id: RunHeader = None) -> dict:
    run_id = _run_id(x_run_id)
    step = STEP_BY_KEY["room_rented"]
    room = db.get(models.Room, room_id)
    if room is None or room.run_id != run_id:
        raise HTTPException(status_code=404, detail={"code": "ROOM_NOT_FOUND"})
    app_row = _application(db, run_id)
    envelope = db.scalars(select(models.EsignEnvelope).where(models.EsignEnvelope.run_id == run_id)).first()
    if envelope is None or envelope.status != "signed":
        raise HTTPException(status_code=409, detail={"code": "NOT_SIGNED", "envelope_status": getattr(envelope, "status", None)})

    room.status = "rented"
    _advance(db, app_row, step, {"room_id": str(room.id), "room_no": room.room_no})
    db.commit()
    return {
        "step": step.name,
        "room_id": str(room.id),
        "room_no": room.room_no,
        "room_status": room.status,
        "application_status": app_row.status,
    }


@app.post("/api/handovers/claim")
def claim_handover(payload: HandoverIn, db: SessionDep, x_run_id: RunHeader = None) -> dict:
    run_id = _run_id(x_run_id)
    step = STEP_BY_KEY["handover_claim"]
    lead = db.get(models.Lead, payload.lead_id)
    if lead is None or lead.run_id != run_id:
        raise HTTPException(status_code=404, detail={"code": "LEAD_NOT_FOUND"})
    app_row = _application(db, run_id)

    handover = models.Handover(
        run_id=run_id,
        lead_id=lead.id,
        from_advisor_id=lead.advisor_id,
        to_member_manager_id=payload.member_manager_id,
        claimed_at=_now(),
    )
    db.add(handover)
    member = models.Member(
        run_id=run_id,
        company_name=app_row.company_name,
        contact_phone=app_row.applicant_phone,
        certify_status="pending",
    )
    db.add(member)
    db.flush()
    _advance(db, app_row, step, {"handover_id": str(handover.id), "member_id": str(member.id)})
    db.commit()
    return {
        "step": step.name,
        "handover_id": str(handover.id),
        "member_id": str(member.id),
        "from_advisor_id": handover.from_advisor_id,
        "to_member_manager_id": handover.to_member_manager_id,
        "application_status": app_row.status,
    }


@app.post("/api/miniapp/certify")
def miniapp_certify(payload: CertifyIn, db: SessionDep, x_run_id: RunHeader = None) -> dict:
    """S3-MINI 桩：企业联系人小程序认证（由 Node 端官方模拟器驱动的组件真实调用；跳过后可按接口桩执行）。"""
    run_id = _run_id(x_run_id)
    step = STEP_BY_KEY["miniapp_certify"]
    member = db.get(models.Member, payload.member_id)
    if member is None or member.run_id != run_id:
        raise HTTPException(status_code=404, detail={"code": "MEMBER_NOT_FOUND"})
    if payload.verify_code != "123456":
        raise HTTPException(status_code=422, detail={"code": "SMS_CODE_INVALID"})
    app_row = _application(db, run_id)

    result = stubs.miniapp_certify(member.company_name, member.contact_phone)
    member.certify_status = result["certify_status"]
    member.certified_at = _now()
    _advance(db, app_row, step, {"member_id": str(member.id), "openid_stub": result["openid_stub"]})
    db.commit()
    return {
        "step": step.name,
        "member_id": str(member.id),
        "certify_status": member.certify_status,
        "openid_stub": result["openid_stub"],
        "channel": result["channel"],
        "application_status": app_row.status,
    }


@app.get("/api/miniapp/home")
def miniapp_home(member_id: uuid.UUID, db: SessionDep, x_run_id: RunHeader = None) -> dict:
    """S3-MINI 桩：小程序首页首月资源推荐。"""
    run_id = _run_id(x_run_id)
    step = STEP_BY_KEY["miniapp_home"]
    member = db.get(models.Member, member_id)
    if member is None or member.run_id != run_id:
        raise HTTPException(status_code=404, detail={"code": "MEMBER_NOT_FOUND"})
    if member.certify_status != "certified":
        raise HTTPException(status_code=409, detail={"code": "MEMBER_NOT_CERTIFIED", "status": member.certify_status})
    app_row = _application(db, run_id)

    resource = stubs.first_month_resources(seed=str(member.id))
    rec = models.ResourceRecommendation(
        run_id=run_id, member_id=member.id, month=resource["month"], items=resource["items"]
    )
    db.add(rec)
    db.flush()
    _advance(db, app_row, step, {"recommendation_id": str(rec.id), "month": resource["month"]})
    db.commit()
    return {
        "step": step.name,
        "recommendation_id": str(rec.id),
        "member_id": str(member.id),
        "month": resource["month"],
        "headline": resource["headline"],
        "items": resource["items"],
        "application_status": app_row.status,
    }


# --------------------------------------------------------------------------- 运维/清理


@app.get("/api/admin/run/{run_id}/state")
def run_state(run_id: str, db: SessionDep) -> dict:
    app_row = db.scalars(select(models.Application).where(models.Application.run_id == run_id)).first()
    if app_row is None:
        return {"run_id": run_id, "application": None, "events": []}
    events = db.scalars(
        select(models.AuditEvent).where(models.AuditEvent.run_id == run_id).order_by(models.AuditEvent.step_no)
    ).all()
    return {
        "run_id": run_id,
        "application_id": str(app_row.id),
        "status": app_row.status,
        "company_name": app_row.company_name,
        "events": [
            {"step_no": e.step_no, "step_key": e.step_key, "event": e.event, "payload": e.payload}
            for e in events
        ],
    }


@app.get("/api/admin/run/{run_id}/counts")
def run_counts(run_id: str, db: SessionDep) -> dict:
    counts = {
        table: db.execute(
            select(func.count()).select_from(models.Base.metadata.tables[table]).where(
                models.Base.metadata.tables[table].c.run_id == run_id
            )
        ).scalar_one()
        for table in CLEANUP_TABLES
    }
    return {"run_id": run_id, "counts": counts, "total": sum(counts.values())}


@app.delete("/api/admin/run/{run_id}")
def cleanup_run(run_id: str, db: SessionDep) -> dict:
    deleted: dict[str, int] = {}
    for table in CLEANUP_TABLES:
        tbl = models.Base.metadata.tables[table]
        result = db.execute(tbl.delete().where(tbl.c.run_id == run_id))
        deleted[table] = int(result.rowcount or 0)
    run = db.get(models.SmokeRun, run_id)
    if run is not None:
        run.cleaned_at = _now()
        if run.status == "running":
            run.status = "cleaned"
    db.commit()
    remaining = {
        table: db.execute(
            select(func.count()).select_from(models.Base.metadata.tables[table]).where(
                models.Base.metadata.tables[table].c.run_id == run_id
            )
        ).scalar_one()
        for table in CLEANUP_TABLES
    }
    return {
        "run_id": run_id,
        "deleted": deleted,
        "deleted_total": sum(deleted.values()),
        "remaining": remaining,
        "remaining_total": sum(remaining.values()),
    }


@app.exception_handler(workflow.StateError)
def _state_error_handler(_: Request, exc: workflow.StateError) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content={
            "code": "STATE_CONFLICT",
            "step": exc.step.name,
            "expected": exc.expected,
            "actual": exc.actual,
        },
    )
