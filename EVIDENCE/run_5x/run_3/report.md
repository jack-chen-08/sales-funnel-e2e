# 招商全链路冒烟报告 · smk-5x-r3-20261124-033700-1ab8

- 结论：**通过**
- 模式：full（小程序步骤执行）
- 平台地址：http://127.0.0.1:5600
- 开始：2026-11-23T19:37:00.856+00:00　结束：2026-11-23T19:37:05.312+00:00
- 总耗时：**4.46s**（阈值 600s）
- 通过 / 跳过 / 失败：12 / 0 / 0

| # | 步骤 | 执行方 | 方式 | 状态 | 耗时 | 关键断言 |
|---|------|--------|------|------|------|----------|
| 1 | 官网提交申请 | 官网访客 | ui | 通过 | 0.83s | 官网提交成功，申请单状态=submitted，返回 UUID 单号 |
| 2 | 线索按规则分配 | 销售中台 | api | 通过 | 0.01s | 线索分配命中规则 region=east->ADV-101，状态 assigned |
| 3 | 顾问首次联系 | 招商顾问 | ui | 通过 | 0.71s | 工作台点击后线索状态=contacted，页面回显联系记录 ID |
| 4 | 推进到预约参观 | 招商顾问 | api | 通过 | 0.01s | 预约参观创建成功，生成 6 位访客码，状态=visit_booked |
| 5 | 前台核销访客码 | 前台 | ui | 通过 | 0.75s | 访客码在 A 座前台核销成功，状态=visited |
| 6 | 纪要确认 | 招商顾问 | api | 通过 | 0.01s | 参观纪要确认落库，状态=minutes_confirmed |
| 7 | 9.5 折以内报价 | 招商顾问 | api | 通过 | 0.01s | 成交价为挂牌价 95.0%（9.5 折以内），成交价 1767000 分，状态=quoted |
| 8 | 电子签 | 签约双方 | ui | 通过 | 0.69s | 签约台完成两方签署（出租方+承租方），信封状态=signed，主状态=signed |
| 9 | 房态变为已租 | 运营中台 | api | 通过 | 0.01s | 房源 12F-1801 房态=rented，主状态=rented |
| 10 | 会员经理领取交接 | 会员经理 | api | 通过 | 0.01s | 会员经理 MM-021 领取交接，会员档案创建，状态=handed_over |
| 11 | 签约企业联系人在小程序完成认证 | 企业联系人 | miniapp | 通过 | 0.90s | 小程序内提交验证码完成企业联系人认证：POST /api/miniapp/certify → 200（19ms），组件 phase=idle→certified，触发 certified 事件，状态=certified |
| 12 | 小程序首页看到首月资源推荐 | 企业联系人 | miniapp | 通过 | 0.00s | 小程序首页渲染 2026-11 首月资源包 3 项（渲染树条目数与数据一致），GET /api/miniapp/home → 200（12ms），链路状态=activated |

## 已创建数据 ID

```json
{
  "rooms": "2340e534-27ff-4d46-84e8-b2c1fa04dcf4,b8ec0284-cdd4-4511-b8ae-89dfb1cb96a7",
  "room_primary": "2340e534-27ff-4d46-84e8-b2c1fa04dcf4",
  "room_secondary": "b8ec0284-cdd4-4511-b8ae-89dfb1cb96a7",
  "application_id": "8ec5b029-c855-4a31-bfac-6a430b98c495",
  "lead_id": "678f2b08-3463-4ab9-8697-780342c3f633",
  "advisor_id": "ADV-101",
  "contact_id": "ee92e8e2-fd68-4458-b020-06a025a0f8ef",
  "visit_id": "1eaed49c-c70c-4a15-92d2-c2cf783a406f",
  "visit_code": "929025",
  "minutes_id": "18d33f14-691a-4100-8ae3-03aea24cc49c",
  "quote_id": "12836148-509b-4a38-b89a-d78e073be7f2",
  "envelope_id": "7a784d94-a8af-4c8e-8377-94241c4f3818",
  "handover_id": "cc6d8b72-e596-46fa-9cb0-7e346ae171b0",
  "member_id": "a4816916-a86b-466b-96d3-a94c3bd8baab",
  "recommendation_id": "d32d7b71-0bc6-4dea-ae47-52e4167b1ed3"
}
```

## run_id 清理校验

- 清理时间：2026-11-23T19:37:05.348+00:00
- 删除行数合计：24
- 剩余行数合计：**0**

| 表 | 删除 | 剩余 |
|----|------|------|
| resource_recommendations | 1 | 0 |
| members | 1 | 0 |
| handovers | 1 | 0 |
| rooms | 2 | 0 |
| esign_envelopes | 1 | 0 |
| quotes | 1 | 0 |
| visit_minutes | 1 | 0 |
| visits | 1 | 0 |
| contacts | 1 | 0 |
| leads | 1 | 0 |
| applications | 1 | 0 |
| audit_events | 12 | 0 |

## 证据文件

- artifacts_dir: `reports/artifacts/smk-5x-r3-20261124-033700-1ab8`
- report_json: `reports/run_smk-5x-r3-20261124-033700-1ab8.json`
- report_md: `reports/run_smk-5x-r3-20261124-033700-1ab8.md`
