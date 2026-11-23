# 招商全链路冒烟报告 · smk-5x-r5-20261124-033710-2a82

- 结论：**通过**
- 模式：full（小程序步骤执行）
- 平台地址：http://127.0.0.1:5600
- 开始：2026-11-23T19:37:10.747+00:00　结束：2026-11-23T19:37:15.232+00:00
- 总耗时：**4.49s**（阈值 600s）
- 通过 / 跳过 / 失败：12 / 0 / 0

| # | 步骤 | 执行方 | 方式 | 状态 | 耗时 | 关键断言 |
|---|------|--------|------|------|------|----------|
| 1 | 官网提交申请 | 官网访客 | ui | 通过 | 0.82s | 官网提交成功，申请单状态=submitted，返回 UUID 单号 |
| 2 | 线索按规则分配 | 销售中台 | api | 通过 | 0.01s | 线索分配命中规则 region=east->ADV-101，状态 assigned |
| 3 | 顾问首次联系 | 招商顾问 | ui | 通过 | 0.71s | 工作台点击后线索状态=contacted，页面回显联系记录 ID |
| 4 | 推进到预约参观 | 招商顾问 | api | 通过 | 0.01s | 预约参观创建成功，生成 6 位访客码，状态=visit_booked |
| 5 | 前台核销访客码 | 前台 | ui | 通过 | 0.72s | 访客码在 A 座前台核销成功，状态=visited |
| 6 | 纪要确认 | 招商顾问 | api | 通过 | 0.01s | 参观纪要确认落库，状态=minutes_confirmed |
| 7 | 9.5 折以内报价 | 招商顾问 | api | 通过 | 0.01s | 成交价为挂牌价 95.0%（9.5 折以内），成交价 1767000 分，状态=quoted |
| 8 | 电子签 | 签约双方 | ui | 通过 | 0.73s | 签约台完成两方签署（出租方+承租方），信封状态=signed，主状态=signed |
| 9 | 房态变为已租 | 运营中台 | api | 通过 | 0.01s | 房源 12F-1801 房态=rented，主状态=rented |
| 10 | 会员经理领取交接 | 会员经理 | api | 通过 | 0.01s | 会员经理 MM-021 领取交接，会员档案创建，状态=handed_over |
| 11 | 签约企业联系人在小程序完成认证 | 企业联系人 | miniapp | 通过 | 0.91s | 小程序内提交验证码完成企业联系人认证：POST /api/miniapp/certify → 200（29ms），组件 phase=idle→certified，触发 certified 事件，状态=certified |
| 12 | 小程序首页看到首月资源推荐 | 企业联系人 | miniapp | 通过 | 0.00s | 小程序首页渲染 2026-11 首月资源包 3 项（渲染树条目数与数据一致），GET /api/miniapp/home → 200（13ms），链路状态=activated |

## 已创建数据 ID

```json
{
  "rooms": "6156e28c-c5a3-40c4-aa6a-5c6888a4714c,74ccb655-59fa-4478-a526-5a87fa4bfe55",
  "room_primary": "6156e28c-c5a3-40c4-aa6a-5c6888a4714c",
  "room_secondary": "74ccb655-59fa-4478-a526-5a87fa4bfe55",
  "application_id": "7dc64ce6-5552-4ad5-8c34-4af070af2554",
  "lead_id": "c77f651f-0eb9-44af-96d9-7ce882bb1803",
  "advisor_id": "ADV-101",
  "contact_id": "a975594d-5dd9-46c5-b201-d809636d6318",
  "visit_id": "836143d6-3775-4865-864b-8e208ec2c0a2",
  "visit_code": "621057",
  "minutes_id": "8fed7576-0c02-490a-852a-66bb208b4617",
  "quote_id": "404950d0-accc-4531-809c-d14212be0785",
  "envelope_id": "325178e5-04ff-4aae-827b-a9dc0ff425fa",
  "handover_id": "9a01f4fa-3918-4610-a1f3-8df81353ed2a",
  "member_id": "bad9f6bc-d89b-4ac6-b1d4-a8a89888b22c",
  "recommendation_id": "ffaf16f9-c1e2-479c-b14d-3b02bd1659b5"
}
```

## run_id 清理校验

- 清理时间：2026-11-23T19:37:15.267+00:00
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

- artifacts_dir: `reports/artifacts/smk-5x-r5-20261124-033710-2a82`
- report_json: `reports/run_smk-5x-r5-20261124-033710-2a82.json`
- report_md: `reports/run_smk-5x-r5-20261124-033710-2a82.md`
