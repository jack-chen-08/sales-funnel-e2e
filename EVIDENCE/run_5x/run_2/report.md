# 招商全链路冒烟报告 · smk-5x-r2-20261124-033655-33ba

- 结论：**通过**
- 模式：full（小程序步骤执行）
- 平台地址：http://127.0.0.1:5600
- 开始：2026-11-23T19:36:55.855+00:00　结束：2026-11-23T19:37:00.363+00:00
- 总耗时：**4.51s**（阈值 600s）
- 通过 / 跳过 / 失败：12 / 0 / 0

| # | 步骤 | 执行方 | 方式 | 状态 | 耗时 | 关键断言 |
|---|------|--------|------|------|------|----------|
| 1 | 官网提交申请 | 官网访客 | ui | 通过 | 0.82s | 官网提交成功，申请单状态=submitted，返回 UUID 单号 |
| 2 | 线索按规则分配 | 销售中台 | api | 通过 | 0.01s | 线索分配命中规则 region=east->ADV-101，状态 assigned |
| 3 | 顾问首次联系 | 招商顾问 | ui | 通过 | 0.71s | 工作台点击后线索状态=contacted，页面回显联系记录 ID |
| 4 | 推进到预约参观 | 招商顾问 | api | 通过 | 0.01s | 预约参观创建成功，生成 6 位访客码，状态=visit_booked |
| 5 | 前台核销访客码 | 前台 | ui | 通过 | 0.74s | 访客码在 A 座前台核销成功，状态=visited |
| 6 | 纪要确认 | 招商顾问 | api | 通过 | 0.01s | 参观纪要确认落库，状态=minutes_confirmed |
| 7 | 9.5 折以内报价 | 招商顾问 | api | 通过 | 0.01s | 成交价为挂牌价 95.0%（9.5 折以内），成交价 1767000 分，状态=quoted |
| 8 | 电子签 | 签约双方 | ui | 通过 | 0.71s | 签约台完成两方签署（出租方+承租方），信封状态=signed，主状态=signed |
| 9 | 房态变为已租 | 运营中台 | api | 通过 | 0.01s | 房源 12F-1801 房态=rented，主状态=rented |
| 10 | 会员经理领取交接 | 会员经理 | api | 通过 | 0.01s | 会员经理 MM-021 领取交接，会员档案创建，状态=handed_over |
| 11 | 签约企业联系人在小程序完成认证 | 企业联系人 | miniapp | 通过 | 0.92s | 小程序内提交验证码完成企业联系人认证：POST /api/miniapp/certify → 200（20ms），组件 phase=idle→certified，触发 certified 事件，状态=certified |
| 12 | 小程序首页看到首月资源推荐 | 企业联系人 | miniapp | 通过 | 0.00s | 小程序首页渲染 2026-11 首月资源包 3 项（渲染树条目数与数据一致），GET /api/miniapp/home → 200（12ms），链路状态=activated |

## 已创建数据 ID

```json
{
  "rooms": "e2fb74f9-7bfa-4933-b7e4-c8c6569b0141,572a94f3-66f6-4e8d-acdd-1214edbc0777",
  "room_primary": "e2fb74f9-7bfa-4933-b7e4-c8c6569b0141",
  "room_secondary": "572a94f3-66f6-4e8d-acdd-1214edbc0777",
  "application_id": "bb76fc40-96ba-40b7-80be-beea786cadea",
  "lead_id": "d474bf99-0fa0-452c-9c80-a923942229b4",
  "advisor_id": "ADV-101",
  "contact_id": "50b760e8-a378-4a93-a3ab-b9812122130f",
  "visit_id": "c56c8dd4-2493-47b7-8e62-f186ef305849",
  "visit_code": "591142",
  "minutes_id": "8142c546-4b59-4403-8fad-d281a22dc862",
  "quote_id": "1798683c-37fa-474e-8394-a8d638417cbf",
  "envelope_id": "3e662ec8-da36-4082-8e0d-31c844f9d3ce",
  "handover_id": "4ccfef50-e8dd-4b2e-a4f1-178aaac83c98",
  "member_id": "9ed42eb8-d65f-4907-9841-1934007542bd",
  "recommendation_id": "cff4ca4f-839b-4f03-908f-594c03f49b46"
}
```

## run_id 清理校验

- 清理时间：2026-11-23T19:37:00.399+00:00
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

- artifacts_dir: `reports/artifacts/smk-5x-r2-20261124-033655-33ba`
- report_json: `reports/run_smk-5x-r2-20261124-033655-33ba.json`
- report_md: `reports/run_smk-5x-r2-20261124-033655-33ba.md`
