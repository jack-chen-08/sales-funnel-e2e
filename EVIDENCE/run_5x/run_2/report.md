# 招商全链路冒烟报告 · smk-5x-r2-20261124-144026-f594

- 结论：**通过**
- 模式：full（小程序步骤执行）
- 平台地址：http://127.0.0.1:5600
- 开始：2026-11-24T06:40:27.034+00:00　结束：2026-11-24T06:40:50.849+00:00
- 总耗时：**23.81s**（阈值 600s）
- 通过 / 跳过 / 失败：12 / 0 / 0

| # | 步骤 | 执行方 | 方式 | 状态 | 耗时 | 关键断言 |
|---|------|--------|------|------|------|----------|
| 1 | 官网提交申请 | 官网访客 | ui | 通过 | 0.91s | 官网提交成功，申请单状态=submitted，返回 UUID 单号 |
| 2 | 线索按规则分配 | 销售中台 | api | 通过 | 0.01s | 线索分配命中规则 region=east->ADV-101，状态 assigned |
| 3 | 顾问首次联系 | 招商顾问 | ui | 通过 | 0.77s | 工作台点击后线索状态=contacted，页面回显联系记录 ID |
| 4 | 推进到预约参观 | 招商顾问 | api | 通过 | 0.02s | 预约参观创建成功，生成 6 位访客码，状态=visit_booked |
| 5 | 前台核销访客码 | 前台 | ui | 通过 | 0.85s | 访客码在 A 座前台核销成功，状态=visited |
| 6 | 纪要确认 | 招商顾问 | api | 通过 | 0.02s | 参观纪要确认落库，状态=minutes_confirmed |
| 7 | 9.5 折以内报价 | 招商顾问 | api | 通过 | 0.01s | 成交价为挂牌价 95.0%（9.5 折以内），成交价 1767000 分，状态=quoted |
| 8 | 电子签 | 签约双方 | ui | 通过 | 0.79s | 签约台完成两方签署（出租方+承租方），信封状态=signed，主状态=signed |
| 9 | 房态变为已租 | 运营中台 | api | 通过 | 0.02s | 房源 12F-1801 房态=rented，主状态=rented |
| 10 | 会员经理领取交接 | 会员经理 | api | 通过 | 0.01s | 会员经理 MM-021 领取交接，会员档案创建，状态=handed_over |
| 11 | 签约企业联系人在小程序完成认证 | 企业联系人 | miniapp | 通过 | 19.67s | 小程序内提交验证码完成企业联系人认证：POST /api/miniapp/certify → 200（26ms），页面 pages/entry/index 上真实输入并点击提交，phase=idle→certified，触发 certified 事件，状态=certified |
| 12 | 小程序首页看到首月资源推荐 | 企业联系人 | miniapp | 通过 | 0.00s | 小程序首页渲染 2026-11 首月资源包 3 项（页面上数到 3 个节点，与数据一致），GET /api/miniapp/home → 200（63ms），链路状态=activated |

## 已创建数据 ID

```json
{
  "rooms": "72e84b9a-13af-4ec9-be77-5787e5aa16de,f2d00172-03c9-452e-9101-69870af55ecd",
  "room_primary": "72e84b9a-13af-4ec9-be77-5787e5aa16de",
  "room_secondary": "f2d00172-03c9-452e-9101-69870af55ecd",
  "application_id": "8d9b6303-767b-475f-b01c-93a268a4a28d",
  "lead_id": "f6f4e057-3c76-4801-a688-8157b9a21226",
  "advisor_id": "ADV-101",
  "contact_id": "0123b011-d38b-4e3b-8d86-0113644eec50",
  "visit_id": "45ee57c5-5f1a-4a2e-b8ec-ebac14005538",
  "visit_code": "180355",
  "minutes_id": "1b700723-b79d-4bff-be66-75cefb2d6743",
  "quote_id": "f08a871b-d04b-4e9b-9ec9-55322f1693eb",
  "envelope_id": "1ed1a38f-dda3-4e2e-9f5d-bb22ca84ddc9",
  "handover_id": "09db1a89-dac8-424b-92a5-bb0d3df6d3b0",
  "member_id": "ef69129a-f0f1-4fd2-bcc9-e02a4ca778f4",
  "recommendation_id": "20183d77-9f11-4558-8b2c-c5f2bf8fd3d4"
}
```

## run_id 清理校验

- 清理时间：2026-11-24T06:40:50.886+00:00
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

- artifacts_dir: `reports/artifacts/smk-5x-r2-20261124-144026-f594`
- report_json: `reports/run_smk-5x-r2-20261124-144026-f594.json`
- report_md: `reports/run_smk-5x-r2-20261124-144026-f594.md`
