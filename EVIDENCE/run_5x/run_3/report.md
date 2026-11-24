# 招商全链路冒烟报告 · smk-5x-r3-20261124-144102-afda

- 结论：**通过**
- 模式：full（小程序步骤执行）
- 平台地址：http://127.0.0.1:5600
- 开始：2026-11-24T06:41:02.393+00:00　结束：2026-11-24T06:41:26.261+00:00
- 总耗时：**23.87s**（阈值 600s）
- 通过 / 跳过 / 失败：12 / 0 / 0

| # | 步骤 | 执行方 | 方式 | 状态 | 耗时 | 关键断言 |
|---|------|--------|------|------|------|----------|
| 1 | 官网提交申请 | 官网访客 | ui | 通过 | 0.93s | 官网提交成功，申请单状态=submitted，返回 UUID 单号 |
| 2 | 线索按规则分配 | 销售中台 | api | 通过 | 0.01s | 线索分配命中规则 region=east->ADV-101，状态 assigned |
| 3 | 顾问首次联系 | 招商顾问 | ui | 通过 | 0.85s | 工作台点击后线索状态=contacted，页面回显联系记录 ID |
| 4 | 推进到预约参观 | 招商顾问 | api | 通过 | 0.02s | 预约参观创建成功，生成 6 位访客码，状态=visit_booked |
| 5 | 前台核销访客码 | 前台 | ui | 通过 | 0.88s | 访客码在 A 座前台核销成功，状态=visited |
| 6 | 纪要确认 | 招商顾问 | api | 通过 | 0.01s | 参观纪要确认落库，状态=minutes_confirmed |
| 7 | 9.5 折以内报价 | 招商顾问 | api | 通过 | 0.01s | 成交价为挂牌价 95.0%（9.5 折以内），成交价 1767000 分，状态=quoted |
| 8 | 电子签 | 签约双方 | ui | 通过 | 0.72s | 签约台完成两方签署（出租方+承租方），信封状态=signed，主状态=signed |
| 9 | 房态变为已租 | 运营中台 | api | 通过 | 0.02s | 房源 12F-1801 房态=rented，主状态=rented |
| 10 | 会员经理领取交接 | 会员经理 | api | 通过 | 0.01s | 会员经理 MM-021 领取交接，会员档案创建，状态=handed_over |
| 11 | 签约企业联系人在小程序完成认证 | 企业联系人 | miniapp | 通过 | 19.64s | 小程序内提交验证码完成企业联系人认证：POST /api/miniapp/certify → 200（22ms），页面 pages/entry/index 上真实输入并点击提交，phase=idle→certified，触发 certified 事件，状态=certified |
| 12 | 小程序首页看到首月资源推荐 | 企业联系人 | miniapp | 通过 | 0.00s | 小程序首页渲染 2026-11 首月资源包 3 项（页面上数到 3 个节点，与数据一致），GET /api/miniapp/home → 200（50ms），链路状态=activated |

## 已创建数据 ID

```json
{
  "rooms": "5a15251f-5211-4dee-bfec-66f4cf1f8cc2,cb2720fd-1536-4f7f-91a4-e806bf37afcb",
  "room_primary": "5a15251f-5211-4dee-bfec-66f4cf1f8cc2",
  "room_secondary": "cb2720fd-1536-4f7f-91a4-e806bf37afcb",
  "application_id": "2538ed38-d209-45b3-8ca6-1dc9b28c3720",
  "lead_id": "c5df9c1e-e05d-4ce4-bc17-3d72d48eaa94",
  "advisor_id": "ADV-101",
  "contact_id": "dd1e67a3-6609-4e7f-be39-d646960c4ebf",
  "visit_id": "ecd6ca49-d24d-4a6f-b7b3-ca582a474e63",
  "visit_code": "971946",
  "minutes_id": "e19d79fa-8b5e-4661-a992-449d32b677bd",
  "quote_id": "042a1800-13b6-4955-a95d-0999162be0b6",
  "envelope_id": "e8f00e14-b7b4-412b-83d9-88b4645feddd",
  "handover_id": "21781502-5237-4677-b875-50cad7c1ce9c",
  "member_id": "9f3eff49-19d7-43c4-9a53-bfd88292ed7f",
  "recommendation_id": "8a28b61b-ae2f-4d5d-b05f-03c4719a63e5"
}
```

## run_id 清理校验

- 清理时间：2026-11-24T06:41:26.300+00:00
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

- artifacts_dir: `reports/artifacts/smk-5x-r3-20261124-144102-afda`
- report_json: `reports/run_smk-5x-r3-20261124-144102-afda.json`
- report_md: `reports/run_smk-5x-r3-20261124-144102-afda.md`
