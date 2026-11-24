# 招商全链路冒烟报告 · smk-5x-r3-20261124-142842-6188

- 结论：**通过**
- 模式：full（小程序步骤执行）
- 平台地址：http://127.0.0.1:5600
- 开始：2026-11-24T06:28:42.164+00:00　结束：2026-11-24T06:28:46.737+00:00
- 总耗时：**4.57s**（阈值 600s）
- 通过 / 跳过 / 失败：12 / 0 / 0

| # | 步骤 | 执行方 | 方式 | 状态 | 耗时 | 关键断言 |
|---|------|--------|------|------|------|----------|
| 1 | 官网提交申请 | 官网访客 | ui | 通过 | 0.86s | 官网提交成功，申请单状态=submitted，返回 UUID 单号 |
| 2 | 线索按规则分配 | 销售中台 | api | 通过 | 0.01s | 线索分配命中规则 region=east->ADV-101，状态 assigned |
| 3 | 顾问首次联系 | 招商顾问 | ui | 通过 | 0.71s | 工作台点击后线索状态=contacted，页面回显联系记录 ID |
| 4 | 推进到预约参观 | 招商顾问 | api | 通过 | 0.01s | 预约参观创建成功，生成 6 位访客码，状态=visit_booked |
| 5 | 前台核销访客码 | 前台 | ui | 通过 | 0.73s | 访客码在 A 座前台核销成功，状态=visited |
| 6 | 纪要确认 | 招商顾问 | api | 通过 | 0.01s | 参观纪要确认落库，状态=minutes_confirmed |
| 7 | 9.5 折以内报价 | 招商顾问 | api | 通过 | 0.01s | 成交价为挂牌价 95.0%（9.5 折以内），成交价 1767000 分，状态=quoted |
| 8 | 电子签 | 签约双方 | ui | 通过 | 0.69s | 签约台完成两方签署（出租方+承租方），信封状态=signed，主状态=signed |
| 9 | 房态变为已租 | 运营中台 | api | 通过 | 0.01s | 房源 12F-1801 房态=rented，主状态=rented |
| 10 | 会员经理领取交接 | 会员经理 | api | 通过 | 0.01s | 会员经理 MM-021 领取交接，会员档案创建，状态=handed_over |
| 11 | 签约企业联系人在小程序完成认证 | 企业联系人 | miniapp | 通过 | 0.95s | 小程序内提交验证码完成企业联系人认证：POST /api/miniapp/certify → 200（28ms），页面 pages/entry/index 上真实输入并点击提交，phase=idle→certified，触发 certified 事件，状态=certified |
| 12 | 小程序首页看到首月资源推荐 | 企业联系人 | miniapp | 通过 | 0.00s | 小程序首页渲染 2026-11 首月资源包 3 项（页面上数到 3 个节点，与数据一致），GET /api/miniapp/home → 200（13ms），链路状态=activated |

## 已创建数据 ID

```json
{
  "rooms": "6374d99d-d076-45c0-b7bb-18525c079ec8,27e7af70-03fc-4ba2-8d35-ae7b6c5e0635",
  "room_primary": "6374d99d-d076-45c0-b7bb-18525c079ec8",
  "room_secondary": "27e7af70-03fc-4ba2-8d35-ae7b6c5e0635",
  "application_id": "51f78128-c743-48b6-8ee3-25e3c63176e6",
  "lead_id": "2733a9cb-db40-4b42-882a-899fc6487da4",
  "advisor_id": "ADV-101",
  "contact_id": "f58f73c1-af4c-48b4-aa96-0586d760e108",
  "visit_id": "b2449521-5d7d-43c2-8ffb-e20bdffbd9ab",
  "visit_code": "749687",
  "minutes_id": "48cd2c44-0f09-47df-9f53-96923fb352fb",
  "quote_id": "b8f5fb9c-7fbb-459b-8a65-cc868573bec0",
  "envelope_id": "aad21fe5-d2b8-4f0f-a19a-cd5652d4af72",
  "handover_id": "c5f62197-2489-4548-a543-0c0e921ceeb8",
  "member_id": "9277f0fc-08a7-478d-89dd-2f47712d3f1b",
  "recommendation_id": "bb1036fe-605e-477e-8574-fa2df27d4467"
}
```

## run_id 清理校验

- 清理时间：2026-11-24T06:28:46.775+00:00
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

- artifacts_dir: `reports/artifacts/smk-5x-r3-20261124-142842-6188`
- report_json: `reports/run_smk-5x-r3-20261124-142842-6188.json`
- report_md: `reports/run_smk-5x-r3-20261124-142842-6188.md`
