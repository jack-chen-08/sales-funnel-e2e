# 招商全链路冒烟报告 · smk-5x-r5-20261124-145345-a6e2

- 结论：**通过**
- 模式：full（小程序步骤执行）
- 平台地址：http://127.0.0.1:5600
- 开始：2026-11-24T06:53:45.282+00:00　结束：2026-11-24T06:54:08.927+00:00
- 总耗时：**23.64s**（阈值 600s）
- 通过 / 跳过 / 失败：12 / 0 / 0

| # | 步骤 | 执行方 | 方式 | 状态 | 耗时 | 关键断言 |
|---|------|--------|------|------|------|----------|
| 1 | 官网提交申请 | 官网访客 | ui | 通过 | 0.95s | 官网提交成功，申请单状态=submitted，返回 UUID 单号 |
| 2 | 线索按规则分配 | 销售中台 | api | 通过 | 0.01s | 线索分配命中规则 region=east->ADV-101，状态 assigned |
| 3 | 顾问首次联系 | 招商顾问 | ui | 通过 | 0.86s | 工作台点击后线索状态=contacted，页面回显联系记录 ID |
| 4 | 推进到预约参观 | 招商顾问 | api | 通过 | 0.03s | 预约参观创建成功，生成 6 位访客码，状态=visit_booked |
| 5 | 前台核销访客码 | 前台 | ui | 通过 | 0.92s | 访客码在 A 座前台核销成功，状态=visited |
| 6 | 纪要确认 | 招商顾问 | api | 通过 | 0.01s | 参观纪要确认落库，状态=minutes_confirmed |
| 7 | 9.5 折以内报价 | 招商顾问 | api | 通过 | 0.01s | 成交价为挂牌价 95.0%（9.5 折以内），成交价 1767000 分，状态=quoted |
| 8 | 电子签 | 签约双方 | ui | 通过 | 0.74s | 签约台完成两方签署（出租方+承租方），信封状态=signed，主状态=signed |
| 9 | 房态变为已租 | 运营中台 | api | 通过 | 0.02s | 房源 12F-1801 房态=rented，主状态=rented |
| 10 | 会员经理领取交接 | 会员经理 | api | 通过 | 0.02s | 会员经理 MM-021 领取交接，会员档案创建，状态=handed_over |
| 11 | 签约企业联系人在小程序完成认证 | 企业联系人 | miniapp | 通过 | 19.30s | 小程序内提交验证码完成企业联系人认证：POST /api/miniapp/certify → 200（26ms），页面 pages/entry/index 上真实输入并点击提交，phase=idle→certified，触发 certified 事件，状态=certified |
| 12 | 小程序首页看到首月资源推荐 | 企业联系人 | miniapp | 通过 | 0.00s | 小程序首页渲染 2026-11 首月资源包 3 项（页面上数到 3 个节点，与数据一致），GET /api/miniapp/home → 200（55ms），链路状态=activated |

## 已创建数据 ID

```json
{
  "rooms": "0be28fd5-46b9-4627-b457-66492084854d,174b49d7-006e-45b0-9759-1bfabc3c38d9",
  "room_primary": "0be28fd5-46b9-4627-b457-66492084854d",
  "room_secondary": "174b49d7-006e-45b0-9759-1bfabc3c38d9",
  "application_id": "4e710225-ac76-4b93-9ce8-bca156364250",
  "lead_id": "0d68fbe9-dab3-4022-8b2a-72ffb0ac7b6f",
  "advisor_id": "ADV-101",
  "contact_id": "2d7b0894-621b-45ac-ae68-a455c8b797f4",
  "visit_id": "20d49b1d-1763-4272-96fc-eb7484694533",
  "visit_code": "283534",
  "minutes_id": "11f280da-0265-4fe2-8c5e-20ec65c28f41",
  "quote_id": "d71bb561-f62c-40d4-bd13-485772abdc45",
  "envelope_id": "759af93b-2a4e-4f26-adf7-9c67e833ed21",
  "handover_id": "59009d3f-1d91-46c8-93f2-5db921e71c53",
  "member_id": "24eb0bd6-5588-4929-b5a5-a03aed472534",
  "recommendation_id": "5913350c-af28-4647-9960-b28e0412a10d"
}
```

## run_id 清理校验

- 清理时间：2026-11-24T06:54:08.979+00:00
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

- artifacts_dir: `reports/artifacts/smk-5x-r5-20261124-145345-a6e2`
- report_json: `reports/run_smk-5x-r5-20261124-145345-a6e2.json`
- report_md: `reports/run_smk-5x-r5-20261124-145345-a6e2.md`
