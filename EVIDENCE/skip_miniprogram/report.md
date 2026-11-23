# 招商全链路冒烟报告 · smk-skipmode-20261124-035335-043d

- 结论：**通过**
- 模式：skip-miniprogram（小程序步骤跳过）
- 平台地址：http://127.0.0.1:5600
- 开始：2026-11-23T19:53:35.588+00:00　结束：2026-11-23T19:53:39.259+00:00
- 总耗时：**3.67s**（阈值 600s）
- 通过 / 跳过 / 失败：10 / 2 / 0

| # | 步骤 | 执行方 | 方式 | 状态 | 耗时 | 关键断言 |
|---|------|--------|------|------|------|----------|
| 1 | 官网提交申请 | 官网访客 | ui | 通过 | 0.84s | 官网提交成功，申请单状态=submitted，返回 UUID 单号 |
| 2 | 线索按规则分配 | 销售中台 | api | 通过 | 0.01s | 线索分配命中规则 region=east->ADV-101，状态 assigned |
| 3 | 顾问首次联系 | 招商顾问 | ui | 通过 | 0.72s | 工作台点击后线索状态=contacted，页面回显联系记录 ID |
| 4 | 推进到预约参观 | 招商顾问 | api | 通过 | 0.01s | 预约参观创建成功，生成 6 位访客码，状态=visit_booked |
| 5 | 前台核销访客码 | 前台 | ui | 通过 | 0.74s | 访客码在 A 座前台核销成功，状态=visited |
| 6 | 纪要确认 | 招商顾问 | api | 通过 | 0.01s | 参观纪要确认落库，状态=minutes_confirmed |
| 7 | 9.5 折以内报价 | 招商顾问 | api | 通过 | 0.01s | 成交价为挂牌价 95.0%（9.5 折以内），成交价 1767000 分，状态=quoted |
| 8 | 电子签 | 签约双方 | ui | 通过 | 0.69s | 签约台完成两方签署（出租方+承租方），信封状态=signed，主状态=signed |
| 9 | 房态变为已租 | 运营中台 | api | 通过 | 0.01s | 房源 12F-1801 房态=rented，主状态=rented |
| 10 | 会员经理领取交接 | 会员经理 | api | 通过 | 0.01s | 会员经理 MM-021 领取交接，会员档案创建，状态=handed_over |
| 11 | 签约企业联系人在小程序完成认证 | 企业联系人 | skipped | 跳过 | 0.00s | 小程序步骤按 --skip-miniprogram 标记跳过（本轮显式要求跳过；默认执行方式为官方模拟器组件级真跑） |
| 12 | 小程序首页看到首月资源推荐 | 企业联系人 | skipped | 跳过 | 0.00s | 小程序步骤按 --skip-miniprogram 标记跳过（本轮显式要求跳过；默认执行方式为官方模拟器组件级真跑） |

## 已创建数据 ID

```json
{
  "rooms": "627f94b8-f6ad-477e-92fc-5214dcd29955,ca5c3d98-5c36-41ec-9261-34e3589bc11f",
  "room_primary": "627f94b8-f6ad-477e-92fc-5214dcd29955",
  "room_secondary": "ca5c3d98-5c36-41ec-9261-34e3589bc11f",
  "application_id": "0abb9691-853c-4d10-bfd9-892fe2d250e8",
  "lead_id": "58cc5c36-3e65-40eb-8de3-f8ac85ab1542",
  "advisor_id": "ADV-101",
  "contact_id": "412ce6e8-1c0f-445e-8464-4cbf55db70f8",
  "visit_id": "cb99a88a-7ef5-4418-8005-2032c4e31a5a",
  "visit_code": "429051",
  "minutes_id": "cf72dae5-6188-4489-8e08-4ff8019dd8f8",
  "quote_id": "36b2efa9-d620-4d42-b1de-3201085152ff",
  "envelope_id": "724966f4-1bad-464f-9402-f56049927fd4",
  "handover_id": "b93bae25-48ff-418b-978e-ba49fa7895eb",
  "member_id": "958fee6f-54f4-45bb-a01f-071e901af901"
}
```

## run_id 清理校验

- 清理时间：2026-11-23T19:53:39.295+00:00
- 删除行数合计：21
- 剩余行数合计：**0**

| 表 | 删除 | 剩余 |
|----|------|------|
| resource_recommendations | 0 | 0 |
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
| audit_events | 10 | 0 |

## 证据文件

- artifacts_dir: `reports/artifacts/smk-skipmode-20261124-035335-043d`
- report_json: `reports/run_smk-skipmode-20261124-035335-043d.json`
- report_md: `reports/run_smk-skipmode-20261124-035335-043d.md`
