# 招商全链路冒烟报告 · smk-5x-r1-20261124-142831-aa52

- 结论：**通过**
- 模式：full（小程序步骤执行）
- 平台地址：http://127.0.0.1:5600
- 开始：2026-11-24T06:28:31.391+00:00　结束：2026-11-24T06:28:36.516+00:00
- 总耗时：**5.13s**（阈值 600s）
- 通过 / 跳过 / 失败：12 / 0 / 0

| # | 步骤 | 执行方 | 方式 | 状态 | 耗时 | 关键断言 |
|---|------|--------|------|------|------|----------|
| 1 | 官网提交申请 | 官网访客 | ui | 通过 | 0.86s | 官网提交成功，申请单状态=submitted，返回 UUID 单号 |
| 2 | 线索按规则分配 | 销售中台 | api | 通过 | 0.01s | 线索分配命中规则 region=east->ADV-101，状态 assigned |
| 3 | 顾问首次联系 | 招商顾问 | ui | 通过 | 0.73s | 工作台点击后线索状态=contacted，页面回显联系记录 ID |
| 4 | 推进到预约参观 | 招商顾问 | api | 通过 | 0.01s | 预约参观创建成功，生成 6 位访客码，状态=visit_booked |
| 5 | 前台核销访客码 | 前台 | ui | 通过 | 0.76s | 访客码在 A 座前台核销成功，状态=visited |
| 6 | 纪要确认 | 招商顾问 | api | 通过 | 0.01s | 参观纪要确认落库，状态=minutes_confirmed |
| 7 | 9.5 折以内报价 | 招商顾问 | api | 通过 | 0.01s | 成交价为挂牌价 95.0%（9.5 折以内），成交价 1767000 分，状态=quoted |
| 8 | 电子签 | 签约双方 | ui | 通过 | 0.71s | 签约台完成两方签署（出租方+承租方），信封状态=signed，主状态=signed |
| 9 | 房态变为已租 | 运营中台 | api | 通过 | 0.01s | 房源 12F-1801 房态=rented，主状态=rented |
| 10 | 会员经理领取交接 | 会员经理 | api | 通过 | 0.01s | 会员经理 MM-021 领取交接，会员档案创建，状态=handed_over |
| 11 | 签约企业联系人在小程序完成认证 | 企业联系人 | miniapp | 通过 | 1.45s | 小程序内提交验证码完成企业联系人认证：POST /api/miniapp/certify → 200（31ms），页面 pages/entry/index 上真实输入并点击提交，phase=idle→certified，触发 certified 事件，状态=certified |
| 12 | 小程序首页看到首月资源推荐 | 企业联系人 | miniapp | 通过 | 0.00s | 小程序首页渲染 2026-11 首月资源包 3 项（页面上数到 3 个节点，与数据一致），GET /api/miniapp/home → 200（13ms），链路状态=activated |

## 已创建数据 ID

```json
{
  "rooms": "e0eaf213-34de-4495-befc-68baa89c0210,75c2fdef-ad88-4373-bb46-09b7a1cd7a6a",
  "room_primary": "e0eaf213-34de-4495-befc-68baa89c0210",
  "room_secondary": "75c2fdef-ad88-4373-bb46-09b7a1cd7a6a",
  "application_id": "58a887ef-5c3f-4d86-ac3e-8bb72d66f757",
  "lead_id": "462cc1a3-b643-4af7-b1e7-082520fb45d2",
  "advisor_id": "ADV-101",
  "contact_id": "126977c4-eee0-4389-bfb1-cf99b2713c6a",
  "visit_id": "3df8102a-a2ab-4b6a-a575-b56ead0af97b",
  "visit_code": "320948",
  "minutes_id": "d466c069-a93b-4abe-aa8b-780c14953f66",
  "quote_id": "ffe57276-f627-448a-967d-bd4197ad7d15",
  "envelope_id": "b0acb701-0822-4c8d-ae52-fa51b74cc04f",
  "handover_id": "34471faf-17c1-44f5-988b-31e4c75d360e",
  "member_id": "cbacfe0a-a2ee-4108-a74e-600e71a22938",
  "recommendation_id": "f3ce3208-5dc3-48a6-b6aa-c9c7b07788f4"
}
```

## run_id 清理校验

- 清理时间：2026-11-24T06:28:36.556+00:00
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

- artifacts_dir: `reports/artifacts/smk-5x-r1-20261124-142831-aa52`
- report_json: `reports/run_smk-5x-r1-20261124-142831-aa52.json`
- report_md: `reports/run_smk-5x-r1-20261124-142831-aa52.md`
