"""12 步主状态机：唯一的状态流转定义，所有接口都要经过 assert_status。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StepSpec:
    no: int
    key: str
    name: str
    actor: str
    entry_status: str
    exit_status: str
    ui: bool


STEPS: tuple[StepSpec, ...] = (
    StepSpec(1, "site_apply", "官网提交申请", "官网访客", "none", "submitted", True),
    StepSpec(2, "lead_assign", "线索按规则分配", "销售中台", "submitted", "assigned", False),
    StepSpec(3, "first_contact", "顾问首次联系", "招商顾问", "assigned", "contacted", True),
    StepSpec(4, "book_visit", "推进到预约参观", "招商顾问", "contacted", "visit_booked", False),
    StepSpec(5, "visitor_checkin", "前台核销访客码", "前台", "visit_booked", "visited", True),
    StepSpec(6, "minutes_confirm", "纪要确认", "招商顾问", "visited", "minutes_confirmed", False),
    StepSpec(7, "quote", "9.5 折以内报价", "招商顾问", "minutes_confirmed", "quoted", False),
    StepSpec(8, "esign", "电子签", "签约双方", "quoted", "signed", True),
    StepSpec(9, "room_rented", "房态变为已租", "运营中台", "signed", "rented", False),
    StepSpec(10, "handover_claim", "会员经理领取交接", "会员经理", "rented", "handed_over", False),
    StepSpec(11, "miniapp_certify", "签约企业联系人在小程序完成认证", "企业联系人", "handed_over", "certified", False),
    StepSpec(12, "miniapp_home", "小程序首页看到首月资源推荐", "企业联系人", "certified", "activated", False),
)

STATUS_ORDER: tuple[str, ...] = ("none",) + tuple(s.exit_status for s in STEPS)

STEP_BY_KEY = {s.key: s for s in STEPS}
STEP_BY_NO = {s.no: s for s in STEPS}
UI_STEP_NOS = tuple(s.no for s in STEPS if s.ui)
MINIPROGRAM_STEP_NOS = (11, 12)

# 分配规则（虚构）：按区域路由到顾问组，坐席需求 > 50 时升级到资深顾问
ADVISOR_ROUTING: dict[str, tuple[str, str]] = {
    "east": ("ADV-101", "region=east->ADV-101"),
    "south": ("ADV-207", "region=south->ADV-207"),
    "north": ("ADV-305", "region=north->ADV-305"),
    "west": ("ADV-402", "region=west->ADV-402"),
}
SENIOR_ADVISOR = ("ADV-900", "seat_demand>50->ADV-900")


class StateError(Exception):
    def __init__(self, expected: str, actual: str, step: StepSpec) -> None:
        self.expected = expected
        self.actual = actual
        self.step = step
        super().__init__(f"步骤「{step.name}」要求状态 {expected}，实际 {actual}")


def assert_status(step: StepSpec, current: str) -> None:
    if current != step.entry_status:
        raise StateError(step.entry_status, current, step)


def next_status(step: StepSpec, current: str) -> str:
    assert_status(step, current)
    return step.exit_status
