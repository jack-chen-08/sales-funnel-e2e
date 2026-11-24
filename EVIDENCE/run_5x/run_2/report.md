# 招商全链路冒烟报告 · smk-5x-r2-20261124-142837-e421

- 结论：**通过**
- 模式：full（小程序步骤执行）
- 平台地址：http://127.0.0.1:5600
- 开始：2026-11-24T06:28:37.032+00:00　结束：2026-11-24T06:28:41.605+00:00
- 总耗时：**4.57s**（阈值 600s）
- 通过 / 跳过 / 失败：12 / 0 / 0

| # | 步骤 | 执行方 | 方式 | 状态 | 耗时 | 关键断言 |
|---|------|--------|------|------|------|----------|
| 1 | 官网提交申请 | 官网访客 | ui | 通过 | 0.85s | 官网提交成功，申请单状态=submitted，返回 UUID 单号 |
| 2 | 线索按规则分配 | 销售中台 | api | 通过 | 0.01s | 线索分配命中规则 region=east->ADV-101，状态 assigned |
| 3 | 顾问首次联系 | 招商顾问 | ui | 通过 | 0.69s | 工作台点击后线索状态=contacted，页面回显联系记录 ID |
| 4 | 推进到预约参观 | 招商顾问 | api | 通过 | 0.01s | 预约参观创建成功，生成 6 位访客码，状态=visit_booked |
| 5 | 前台核销访客码 | 前台 | ui | 通过 | 0.74s | 访客码在 A 座前台核销成功，状态=visited |
| 6 | 纪要确认 | 招商顾问 | api | 通过 | 0.01s | 参观纪要确认落库，状态=minutes_confirmed |
| 7 | 9.5 折以内报价 | 招商顾问 | api | 通过 | 0.01s | 成交价为挂牌价 95.0%（9.5 折以内），成交价 1767000 分，状态=quoted |
| 8 | 电子签 | 签约双方 | ui | 通过 | 0.72s | 签约台完成两方签署（出租方+承租方），信封状态=signed，主状态=signed |
| 9 | 房态变为已租 | 运营中台 | api | 通过 | 0.01s | 房源 12F-1801 房态=rented，主状态=rented |
| 10 | 会员经理领取交接 | 会员经理 | api | 通过 | 0.01s | 会员经理 MM-021 领取交接，会员档案创建，状态=handed_over |
| 11 | 签约企业联系人在小程序完成认证 | 企业联系人 | miniapp | 通过 | 0.95s | 小程序内提交验证码完成企业联系人认证：POST /api/miniapp/certify → 200（18ms），页面 pages/entry/index 上真实输入并点击提交，phase=idle→certified，触发 certified 事件，状态=certified |
| 12 | 小程序首页看到首月资源推荐 | 企业联系人 | miniapp | 通过 | 0.00s | 小程序首页渲染 2026-11 首月资源包 3 项（页面上数到 3 个节点，与数据一致），GET /api/miniapp/home → 200（12ms），链路状态=activated |

## 已创建数据 ID

```json
{
  "rooms": "4801f024-9451-45b9-9b77-8e1aba086ea8,701e145f-b88b-46cd-a32c-a38a3d166fd0",
  "room_primary": "4801f024-9451-45b9-9b77-8e1aba086ea8",
  "room_secondary": "701e145f-b88b-46cd-a32c-a38a3d166fd0",
  "application_id": "b173c826-d4f6-467f-9c7d-11c0f162ae3f",
  "lead_id": "ea954444-f4c9-4ed0-8379-2527b264878c",
  "advisor_id": "ADV-101",
  "contact_id": "02137867-4b98-4694-b3ce-e67875ace073",
  "visit_id": "ef9d994d-ff5d-4dca-b850-07e8e0ff2cea",
  "visit_code": "876510",
  "minutes_id": "7b93d3bc-3213-4c9a-99c5-7987ab22ae0e",
  "quote_id": "b15d1789-1c6b-4104-b332-fb19e6ee5d72",
  "envelope_id": "d13fb6f1-55e6-4d0d-bfad-0ca982ddc874",
  "handover_id": "2a96b59f-49c5-48ad-af24-e1d41829aa1a",
  "member_id": "d70f2e1e-f71b-442f-8819-d6ee1362db31",
  "recommendation_id": "9b0ba13d-6c6e-49d0-8d38-2d95cfac70ae"
}
```

## run_id 清理校验

- 清理时间：2026-11-24T06:28:41.645+00:00
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

- artifacts_dir: `reports/artifacts/smk-5x-r2-20261124-142837-e421`
- report_json: `reports/run_smk-5x-r2-20261124-142837-e421.json`
- report_md: `reports/run_smk-5x-r2-20261124-142837-e421.md`
