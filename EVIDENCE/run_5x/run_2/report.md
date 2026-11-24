# 招商全链路冒烟报告 · smk-5x-r2-20261124-145157-e059

- 结论：**通过**
- 模式：full（小程序步骤执行）
- 平台地址：http://127.0.0.1:5600
- 开始：2026-11-24T06:51:57.650+00:00　结束：2026-11-24T06:52:22.147+00:00
- 总耗时：**24.50s**（阈值 600s）
- 通过 / 跳过 / 失败：12 / 0 / 0

| # | 步骤 | 执行方 | 方式 | 状态 | 耗时 | 关键断言 |
|---|------|--------|------|------|------|----------|
| 1 | 官网提交申请 | 官网访客 | ui | 通过 | 0.92s | 官网提交成功，申请单状态=submitted，返回 UUID 单号 |
| 2 | 线索按规则分配 | 销售中台 | api | 通过 | 0.01s | 线索分配命中规则 region=east->ADV-101，状态 assigned |
| 3 | 顾问首次联系 | 招商顾问 | ui | 通过 | 0.73s | 工作台点击后线索状态=contacted，页面回显联系记录 ID |
| 4 | 推进到预约参观 | 招商顾问 | api | 通过 | 0.02s | 预约参观创建成功，生成 6 位访客码，状态=visit_booked |
| 5 | 前台核销访客码 | 前台 | ui | 通过 | 0.82s | 访客码在 A 座前台核销成功，状态=visited |
| 6 | 纪要确认 | 招商顾问 | api | 通过 | 0.01s | 参观纪要确认落库，状态=minutes_confirmed |
| 7 | 9.5 折以内报价 | 招商顾问 | api | 通过 | 0.01s | 成交价为挂牌价 95.0%（9.5 折以内），成交价 1767000 分，状态=quoted |
| 8 | 电子签 | 签约双方 | ui | 通过 | 0.76s | 签约台完成两方签署（出租方+承租方），信封状态=signed，主状态=signed |
| 9 | 房态变为已租 | 运营中台 | api | 通过 | 0.01s | 房源 12F-1801 房态=rented，主状态=rented |
| 10 | 会员经理领取交接 | 会员经理 | api | 通过 | 0.01s | 会员经理 MM-021 领取交接，会员档案创建，状态=handed_over |
| 11 | 签约企业联系人在小程序完成认证 | 企业联系人 | miniapp | 通过 | 20.49s | 小程序内提交验证码完成企业联系人认证：POST /api/miniapp/certify → 200（28ms），页面 pages/entry/index 上真实输入并点击提交，phase=idle→certified，触发 certified 事件，状态=certified |
| 12 | 小程序首页看到首月资源推荐 | 企业联系人 | miniapp | 通过 | 0.00s | 小程序首页渲染 2026-11 首月资源包 3 项（页面上数到 3 个节点，与数据一致），GET /api/miniapp/home → 200（64ms），链路状态=activated |

## 已创建数据 ID

```json
{
  "rooms": "dc4dbf06-4ae1-4cce-9b3b-ca1f1021ecd3,193db9f9-9688-4531-b66a-7e335523def5",
  "room_primary": "dc4dbf06-4ae1-4cce-9b3b-ca1f1021ecd3",
  "room_secondary": "193db9f9-9688-4531-b66a-7e335523def5",
  "application_id": "f8b86376-0815-4522-a68b-1600ae9e9833",
  "lead_id": "66195d17-d668-464d-81b4-b95ef66f23aa",
  "advisor_id": "ADV-101",
  "contact_id": "a6e55d7a-ea7b-4eb9-b5fe-4a0a2ce92593",
  "visit_id": "6461bcd0-4121-4235-b89a-d25f9bcf7c79",
  "visit_code": "897405",
  "minutes_id": "9e30e437-5aa2-4e3b-a5c1-c188474dff57",
  "quote_id": "24de238b-62df-4eae-92ec-029721b32290",
  "envelope_id": "bcba9104-7a82-415f-9baf-68c2b6299bd0",
  "handover_id": "bea0c56d-28b7-4c92-b5e9-b8307c3f0b47",
  "member_id": "86c00181-5bef-4760-96c4-a6fa6512a322",
  "recommendation_id": "6cc2b57d-b82b-401b-a64a-50012feb0046"
}
```

## run_id 清理校验

- 清理时间：2026-11-24T06:52:22.185+00:00
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

- artifacts_dir: `reports/artifacts/smk-5x-r2-20261124-145157-e059`
- report_json: `reports/run_smk-5x-r2-20261124-145157-e059.json`
- report_md: `reports/run_smk-5x-r2-20261124-145157-e059.md`
