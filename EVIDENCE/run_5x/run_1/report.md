# 招商全链路冒烟报告 · smk-5x-r1-20261124-145119-2595

- 结论：**通过**
- 模式：full（小程序步骤执行）
- 平台地址：http://127.0.0.1:5600
- 开始：2026-11-24T06:51:19.818+00:00　结束：2026-11-24T06:51:46.302+00:00
- 总耗时：**26.48s**（阈值 600s）
- 通过 / 跳过 / 失败：12 / 0 / 0

| # | 步骤 | 执行方 | 方式 | 状态 | 耗时 | 关键断言 |
|---|------|--------|------|------|------|----------|
| 1 | 官网提交申请 | 官网访客 | ui | 通过 | 1.16s | 官网提交成功，申请单状态=submitted，返回 UUID 单号 |
| 2 | 线索按规则分配 | 销售中台 | api | 通过 | 0.02s | 线索分配命中规则 region=east->ADV-101，状态 assigned |
| 3 | 顾问首次联系 | 招商顾问 | ui | 通过 | 0.96s | 工作台点击后线索状态=contacted，页面回显联系记录 ID |
| 4 | 推进到预约参观 | 招商顾问 | api | 通过 | 0.06s | 预约参观创建成功，生成 6 位访客码，状态=visit_booked |
| 5 | 前台核销访客码 | 前台 | ui | 通过 | 1.32s | 访客码在 A 座前台核销成功，状态=visited |
| 6 | 纪要确认 | 招商顾问 | api | 通过 | 0.03s | 参观纪要确认落库，状态=minutes_confirmed |
| 7 | 9.5 折以内报价 | 招商顾问 | api | 通过 | 0.04s | 成交价为挂牌价 95.0%（9.5 折以内），成交价 1767000 分，状态=quoted |
| 8 | 电子签 | 签约双方 | ui | 通过 | 1.00s | 签约台完成两方签署（出租方+承租方），信封状态=signed，主状态=signed |
| 9 | 房态变为已租 | 运营中台 | api | 通过 | 0.02s | 房源 12F-1801 房态=rented，主状态=rented |
| 10 | 会员经理领取交接 | 会员经理 | api | 通过 | 0.02s | 会员经理 MM-021 领取交接，会员档案创建，状态=handed_over |
| 11 | 签约企业联系人在小程序完成认证 | 企业联系人 | miniapp | 通过 | 20.68s | 小程序内提交验证码完成企业联系人认证：POST /api/miniapp/certify → 200（23ms），页面 pages/entry/index 上真实输入并点击提交，phase=idle→certified，触发 certified 事件，状态=certified |
| 12 | 小程序首页看到首月资源推荐 | 企业联系人 | miniapp | 通过 | 0.00s | 小程序首页渲染 2026-11 首月资源包 3 项（页面上数到 3 个节点，与数据一致），GET /api/miniapp/home → 200（59ms），链路状态=activated |

## 已创建数据 ID

```json
{
  "rooms": "0d8e602f-8ef1-46c3-9a1a-47ad4f750ac2,e486f45f-46e6-463d-89bd-0e1b09e718ac",
  "room_primary": "0d8e602f-8ef1-46c3-9a1a-47ad4f750ac2",
  "room_secondary": "e486f45f-46e6-463d-89bd-0e1b09e718ac",
  "application_id": "c2aaa300-c32d-41a3-9650-e03c99bd9d60",
  "lead_id": "7c979c29-2b78-4cf7-b8de-1e6a47a4fc32",
  "advisor_id": "ADV-101",
  "contact_id": "8e2c1039-6539-48e9-9776-7ec976d7eee7",
  "visit_id": "9b392d30-5661-49bc-9d93-3c716d75fbe0",
  "visit_code": "567416",
  "minutes_id": "4496492b-c33b-40ee-815e-d949228481c8",
  "quote_id": "58d7858a-08b4-4113-ada5-768dd0a9bb82",
  "envelope_id": "cab95bf5-f1a9-4954-943a-0941210702d0",
  "handover_id": "15cc6218-a039-4735-93ab-f15d8093e0f7",
  "member_id": "0d3ae68b-f23d-434b-bb00-09a4bfc50fd8",
  "recommendation_id": "1308ca83-a6a7-41b1-86bd-d184db591176"
}
```

## run_id 清理校验

- 清理时间：2026-11-24T06:51:46.343+00:00
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

- artifacts_dir: `reports/artifacts/smk-5x-r1-20261124-145119-2595`
- report_json: `reports/run_smk-5x-r1-20261124-145119-2595.json`
- report_md: `reports/run_smk-5x-r1-20261124-145119-2595.md`
