"""业务表模型。统一约定：id(UUID)、org_id、site_id、created_at/created_by/updated_at/deleted_at。

额外一列 run_id：每次链式冒烟使用独立 run_id，清理接口按 run_id 物理删除。
金额字段一律以「分」存整数。
"""

from __future__ import annotations

import datetime as dt
import uuid

from sqlalchemy import JSON, DateTime, Integer, String, Text, Uuid, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from .config import settings


class Base(DeclarativeBase):
    pass


class CommonMixin:
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    org_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), default=lambda: uuid.UUID(settings.org_id))
    site_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), default=lambda: uuid.UUID(settings.site_id))
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_by: Mapped[str] = mapped_column(String(64), default="smoke-bot")
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class SmokeRun(Base):
    """一次链式冒烟的运行台账（清理后仍保留，便于审计）。"""

    __tablename__ = "smoke_runs"

    run_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    mode: Mapped[str] = mapped_column(String(32), default="full")
    status: Mapped[str] = mapped_column(String(32), default="running")
    started_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_step: Mapped[str | None] = mapped_column(String(64), nullable=True)
    cleaned_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Application(CommonMixin, Base):
    """S4-SITE：官网入会申请。status 承载 12 步主状态机。"""

    __tablename__ = "applications"

    company_name: Mapped[str] = mapped_column(String(128))
    applicant_name: Mapped[str] = mapped_column(String(64))
    applicant_phone: Mapped[str] = mapped_column(String(32))
    region: Mapped[str] = mapped_column(String(32))
    seat_demand: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32), default="submitted", index=True)


class Lead(CommonMixin, Base):
    """S3-SALES：线索与分配结果。"""

    __tablename__ = "leads"

    application_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), index=True)
    advisor_id: Mapped[str] = mapped_column(String(32))
    assign_rule: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), default="assigned")


class Contact(CommonMixin, Base):
    """S3-SALES：顾问首次联系记录。"""

    __tablename__ = "contacts"

    lead_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), index=True)
    channel: Mapped[str] = mapped_column(String(32))
    note: Mapped[str] = mapped_column(Text)
    contacted_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True))


class Visit(CommonMixin, Base):
    """S3-SALES：预约参观 + 访客码核销。"""

    __tablename__ = "visits"

    lead_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), index=True)
    visit_code: Mapped[str] = mapped_column(String(8), index=True)
    scheduled_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True))
    checked_in_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    desk: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="booked")


class VisitMinutes(CommonMixin, Base):
    """S3-SALES：参观纪要确认。"""

    __tablename__ = "visit_minutes"

    visit_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), index=True)
    content: Mapped[str] = mapped_column(Text)
    confirmed_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True))


class Quote(CommonMixin, Base):
    """S3-SALES：报价。金额以分存整数，折扣以基点(bp)表示。"""

    __tablename__ = "quotes"

    lead_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), index=True)
    room_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), index=True)
    list_price_cents: Mapped[int] = mapped_column(Integer)
    discount_bp: Mapped[int] = mapped_column(Integer)
    final_price_cents: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32), default="issued")


class EsignEnvelope(CommonMixin, Base):
    """S2-CRM：电子签信封（桩：两方签署）。"""

    __tablename__ = "esign_envelopes"

    quote_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), index=True)
    envelope_no: Mapped[str] = mapped_column(String(40), unique=True)
    signers: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    reject_reason: Mapped[str | None] = mapped_column(String(200), nullable=True)


class Room(CommonMixin, Base):
    """S2-CRM：房态。status: free / rented。"""

    __tablename__ = "rooms"

    room_no: Mapped[str] = mapped_column(String(32))
    list_price_cents: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32), default="free")


class Handover(CommonMixin, Base):
    """S3-SALES → S3-MINI：会员经理领取交接。"""

    __tablename__ = "handovers"

    lead_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), index=True)
    from_advisor_id: Mapped[str] = mapped_column(String(32))
    to_member_manager_id: Mapped[str] = mapped_column(String(32))
    claimed_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True))


class Member(CommonMixin, Base):
    """S3-MINI：签约企业联系人（会员）身份。"""

    __tablename__ = "members"

    company_name: Mapped[str] = mapped_column(String(128))
    contact_phone: Mapped[str] = mapped_column(String(32))
    certify_status: Mapped[str] = mapped_column(String(32), default="pending")
    certified_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ResourceRecommendation(CommonMixin, Base):
    """S3-MINI：首页首月资源推荐。"""

    __tablename__ = "resource_recommendations"

    member_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), index=True)
    month: Mapped[str] = mapped_column(String(7))
    items: Mapped[list] = mapped_column(JSON, default=list)


class AuditEvent(CommonMixin, Base):
    """每一步的状态变更留痕，失败时用于定位。"""

    __tablename__ = "audit_events"

    step_no: Mapped[int] = mapped_column(Integer)
    step_key: Mapped[str] = mapped_column(String(64))
    event: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
