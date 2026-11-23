# 招商全链路冒烟报告 · smk-5x-r4-20261124-033705-7779

- 结论：**通过**
- 模式：full（小程序步骤执行）
- 平台地址：http://127.0.0.1:5600
- 开始：2026-11-23T19:37:05.791+00:00　结束：2026-11-23T19:37:10.280+00:00
- 总耗时：**4.49s**（阈值 600s）
- 通过 / 跳过 / 失败：12 / 0 / 0

| # | 步骤 | 执行方 | 方式 | 状态 | 耗时 | 关键断言 |
|---|------|--------|------|------|------|----------|
| 1 | 官网提交申请 | 官网访客 | ui | 通过 | 0.84s | 官网提交成功，申请单状态=submitted，返回 UUID 单号 |
| 2 | 线索按规则分配 | 销售中台 | api | 通过 | 0.01s | 线索分配命中规则 region=east->ADV-101，状态 assigned |
| 3 | 顾问首次联系 | 招商顾问 | ui | 通过 | 0.71s | 工作台点击后线索状态=contacted，页面回显联系记录 ID |
| 4 | 推进到预约参观 | 招商顾问 | api | 通过 | 0.01s | 预约参观创建成功，生成 6 位访客码，状态=visit_booked |
| 5 | 前台核销访客码 | 前台 | ui | 通过 | 0.73s | 访客码在 A 座前台核销成功，状态=visited |
| 6 | 纪要确认 | 招商顾问 | api | 通过 | 0.01s | 参观纪要确认落库，状态=minutes_confirmed |
| 7 | 9.5 折以内报价 | 招商顾问 | api | 通过 | 0.01s | 成交价为挂牌价 95.0%（9.5 折以内），成交价 1767000 分，状态=quoted |
| 8 | 电子签 | 签约双方 | ui | 通过 | 0.69s | 签约台完成两方签署（出租方+承租方），信封状态=signed，主状态=signed |
| 9 | 房态变为已租 | 运营中台 | api | 通过 | 0.01s | 房源 12F-1801 房态=rented，主状态=rented |
| 10 | 会员经理领取交接 | 会员经理 | api | 通过 | 0.01s | 会员经理 MM-021 领取交接，会员档案创建，状态=handed_over |
| 11 | 签约企业联系人在小程序完成认证 | 企业联系人 | miniapp | 通过 | 0.92s | 小程序内提交验证码完成企业联系人认证：POST /api/miniapp/certify → 200（23ms），组件 phase=idle→certified，触发 certified 事件，状态=certified |
| 12 | 小程序首页看到首月资源推荐 | 企业联系人 | miniapp | 通过 | 0.00s | 小程序首页渲染 2026-11 首月资源包 3 项（渲染树条目数与数据一致），GET /api/miniapp/home → 200（13ms），链路状态=activated |

## 已创建数据 ID

```json
{
  "rooms": "f86aa798-6210-4b7f-abc9-0495298d077d,36ac1855-f708-4163-8ef7-1bfd16f9d38c",
  "room_primary": "f86aa798-6210-4b7f-abc9-0495298d077d",
  "room_secondary": "36ac1855-f708-4163-8ef7-1bfd16f9d38c",
  "application_id": "43f5321e-b4b4-4be5-bb1d-8a894353ec90",
  "lead_id": "cf59f6d5-6224-4f62-bc4c-1da165e0adcf",
  "advisor_id": "ADV-101",
  "contact_id": "24d16813-3029-4173-aecc-b56f47ac4a0f",
  "visit_id": "3c764f4d-08c4-43ef-89ec-bff10f45476b",
  "visit_code": "808519",
  "minutes_id": "33f27ddf-424a-4464-8955-64ae6f441ff6",
  "quote_id": "0439da5a-6d74-40b4-bccf-0b034836bf53",
  "envelope_id": "90a936e4-9cae-4b2a-b7de-ba53c1152bcd",
  "handover_id": "918d7734-3a03-4135-bed7-2fe165f11db0",
  "member_id": "2be69e2f-58b9-4395-b3a5-2a01673e77d4",
  "recommendation_id": "f611844b-f6b0-4855-8f53-842ab93a4e48"
}
```

## run_id 清理校验

- 清理时间：2026-11-23T19:37:10.316+00:00
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

- artifacts_dir: `reports/artifacts/smk-5x-r4-20261124-033705-7779`
- report_json: `reports/run_smk-5x-r4-20261124-033705-7779.json`
- report_md: `reports/run_smk-5x-r4-20261124-033705-7779.md`
