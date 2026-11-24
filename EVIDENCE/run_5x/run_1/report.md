# 招商全链路冒烟报告 · smk-5x-r1-20261124-143951-eeb4

- 结论：**通过**
- 模式：full（小程序步骤执行）
- 平台地址：http://127.0.0.1:5600
- 开始：2026-11-24T06:39:51.474+00:00　结束：2026-11-24T06:40:15.764+00:00
- 总耗时：**24.29s**（阈值 600s）
- 通过 / 跳过 / 失败：12 / 0 / 0

| # | 步骤 | 执行方 | 方式 | 状态 | 耗时 | 关键断言 |
|---|------|--------|------|------|------|----------|
| 1 | 官网提交申请 | 官网访客 | ui | 通过 | 0.95s | 官网提交成功，申请单状态=submitted，返回 UUID 单号 |
| 2 | 线索按规则分配 | 销售中台 | api | 通过 | 0.01s | 线索分配命中规则 region=east->ADV-101，状态 assigned |
| 3 | 顾问首次联系 | 招商顾问 | ui | 通过 | 0.81s | 工作台点击后线索状态=contacted，页面回显联系记录 ID |
| 4 | 推进到预约参观 | 招商顾问 | api | 通过 | 0.02s | 预约参观创建成功，生成 6 位访客码，状态=visit_booked |
| 5 | 前台核销访客码 | 前台 | ui | 通过 | 0.87s | 访客码在 A 座前台核销成功，状态=visited |
| 6 | 纪要确认 | 招商顾问 | api | 通过 | 0.02s | 参观纪要确认落库，状态=minutes_confirmed |
| 7 | 9.5 折以内报价 | 招商顾问 | api | 通过 | 0.02s | 成交价为挂牌价 95.0%（9.5 折以内），成交价 1767000 分，状态=quoted |
| 8 | 电子签 | 签约双方 | ui | 通过 | 0.83s | 签约台完成两方签署（出租方+承租方），信封状态=signed，主状态=signed |
| 9 | 房态变为已租 | 运营中台 | api | 通过 | 0.02s | 房源 12F-1801 房态=rented，主状态=rented |
| 10 | 会员经理领取交接 | 会员经理 | api | 通过 | 0.01s | 会员经理 MM-021 领取交接，会员档案创建，状态=handed_over |
| 11 | 签约企业联系人在小程序完成认证 | 企业联系人 | miniapp | 通过 | 20.00s | 小程序内提交验证码完成企业联系人认证：POST /api/miniapp/certify → 200（28ms），页面 pages/entry/index 上真实输入并点击提交，phase=idle→certified，触发 certified 事件，状态=certified |
| 12 | 小程序首页看到首月资源推荐 | 企业联系人 | miniapp | 通过 | 0.00s | 小程序首页渲染 2026-11 首月资源包 3 项（页面上数到 3 个节点，与数据一致），GET /api/miniapp/home → 200（56ms），链路状态=activated |

## 已创建数据 ID

```json
{
  "rooms": "29bd5472-aa68-46ce-95a5-6775034f8d36,11bafb3d-f821-4d6f-b0d6-f4755375fec2",
  "room_primary": "29bd5472-aa68-46ce-95a5-6775034f8d36",
  "room_secondary": "11bafb3d-f821-4d6f-b0d6-f4755375fec2",
  "application_id": "f6e73eea-ef87-4c06-8963-69073d042ba1",
  "lead_id": "f6ab9ef2-842e-4e7e-a1d6-7b84d02afa94",
  "advisor_id": "ADV-101",
  "contact_id": "ac5995dd-9d51-443f-aed1-60e35a544628",
  "visit_id": "d3744542-204f-4c59-b4ba-addd9ae4bf6b",
  "visit_code": "567278",
  "minutes_id": "902dc55a-bdd3-4a65-88ce-2fe968ec3897",
  "quote_id": "ee729bd2-bc39-487a-942b-a984abed8cb7",
  "envelope_id": "1f825c85-2576-48ef-a514-270aea71db69",
  "handover_id": "39348d37-3c8f-476e-9c43-ca554fbef580",
  "member_id": "bccb3a82-66d0-4eea-bd39-c4634a8ce7e8",
  "recommendation_id": "02e6f33f-f2a1-492a-a53f-cf97949e7bf5"
}
```

## run_id 清理校验

- 清理时间：2026-11-24T06:40:15.816+00:00
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

- artifacts_dir: `reports/artifacts/smk-5x-r1-20261124-143951-eeb4`
- report_json: `reports/run_smk-5x-r1-20261124-143951-eeb4.json`
- report_md: `reports/run_smk-5x-r1-20261124-143951-eeb4.md`
