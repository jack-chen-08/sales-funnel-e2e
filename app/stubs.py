"""外部依赖桩。每个桩都在注释里写明对接点，方便后续替换为真实系统。

对接点：
- S4-SITE  官网与入会申请  → 本仓库 app.main 的 /site/apply* 原生实现（mock 平台自带的官网页面）
- S3-SALES 业务员工作台 v1 → /advisor/console 页面 + /api/leads、/api/contacts、/api/visits、/api/quotes
- S3-MINI  会员小程序 v1   → /api/miniapp/*（接口桩；默认由官方 miniprogram-simulate 驱动组件真实调用，可被 --skip-miniprogram 跳过）
- S2-CRM   CRM 核心对象    → EsignStub（电子签）+ rooms 房态表
"""

from __future__ import annotations

import datetime as dt
import hashlib
import random
import uuid

from .config import settings

ESIGN_REJECT_REASON = "签约方在签署页点击拒签（电子签桩模拟）"

MONTH_RESOURCES = (
    {"code": "RES-MEETING-4", "name": "共享会议室 4 小时", "quota": 4, "unit": "小时"},
    {"code": "RES-PRINT-500", "name": "黑白打印 500 页", "quota": 500, "unit": "页"},
    {"code": "RES-LOUNGE-8", "name": "洽谈区使用 8 次", "quota": 8, "unit": "次"},
    {"code": "RES-PARK-2", "name": "固定车位 2 个", "quota": 2, "unit": "个"},
)


def new_envelope_no(run_id: str) -> str:
    digest = hashlib.sha1(f"{run_id}:{uuid.uuid4()}".encode()).hexdigest()[:10].upper()
    return f"ESN-{digest}"


def pending_signers(company_name: str, applicant_name: str) -> list[dict]:
    """两方签署：出租方（园区运营主体）与承租方（签约企业）。"""
    return [
        {"party": "landlord", "name": "园区运营主体（虚构）", "signed_at": None, "result": "pending"},
        {"party": "tenant", "name": f"{company_name} / {applicant_name}", "signed_at": None, "result": "pending"},
    ]


def sign_envelope(envelope) -> dict:
    """执行两方签署。SIGN_STUB_MODE=reject 时第二方拒签。"""
    now = dt.datetime.now(dt.timezone.utc)
    signers = [dict(s) for s in (envelope.signers or [])]
    if not signers:
        signers = pending_signers("承租企业（虚构）", "联系人（虚构）")

    first = signers[0]
    first["signed_at"] = now.isoformat()
    first["result"] = "signed"

    if settings.esign_will_reject:
        second = signers[1]
        second["result"] = "rejected"
        second["signed_at"] = None
        return {
            "status": "rejected",
            "signers": signers,
            "reject_reason": ESIGN_REJECT_REASON,
            "stub_mode": settings.sign_stub_mode,
        }

    for signer in signers[1:]:
        signer["signed_at"] = now.isoformat()
        signer["result"] = "signed"
    return {"status": "signed", "signers": signers, "reject_reason": None, "stub_mode": settings.sign_stub_mode}


def miniapp_certify(company_name: str, phone: str) -> dict:
    """S3-MINI 桩：企业联系人认证。真实环境走微信 code2session，这里返回确定性桩数据。"""
    if settings.miniapp_stub_mode.lower() == "error":
        raise RuntimeError("小微企业认证桩不可用（MINIAPP_STUB_MODE=error）")
    digest = hashlib.sha1(f"{company_name}:{phone}".encode()).hexdigest()[:12]
    return {
        "openid_stub": f"wx_stub_{digest}",
        "certify_status": "certified",
        "channel": "miniprogram-stub",
        "certified_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    }


def first_month_resources(seed: str) -> dict:
    """S3-MINI 桩：首页首月资源推荐。"""
    rng = random.Random(seed)
    picked = rng.sample(MONTH_RESOURCES, k=3)
    month = dt.date.today().strftime("%Y-%m")
    return {
        "month": month,
        "headline": f"{month} 首月资源包",
        "items": [dict(item, source="miniprogram-stub") for item in picked],
    }
