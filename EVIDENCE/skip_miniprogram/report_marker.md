# 招商全链路冒烟报告 · smk-skipmode-20261124-035339-6455

- 结论：**通过**
- 模式：skip-miniprogram（小程序步骤跳过）
- 平台地址：http://127.0.0.1:5600
- 开始：2026-11-23T19:53:39.343+00:00　结束：2026-11-23T19:53:42.974+00:00
- 总耗时：**3.63s**（阈值 600s）
- 通过 / 跳过 / 失败：10 / 2 / 0

| # | 步骤 | 执行方 | 方式 | 状态 | 耗时 | 关键断言 |
|---|------|--------|------|------|------|----------|
| 1 | 官网提交申请 | 官网访客 | ui | 通过 | 0.84s | 官网提交成功，申请单状态=submitted，返回 UUID 单号 |
| 2 | 线索按规则分配 | 销售中台 | api | 通过 | 0.01s | 线索分配命中规则 region=east->ADV-101，状态 assigned |
| 3 | 顾问首次联系 | 招商顾问 | ui | 通过 | 0.73s | 工作台点击后线索状态=contacted，页面回显联系记录 ID |
| 4 | 推进到预约参观 | 招商顾问 | api | 通过 | 0.01s | 预约参观创建成功，生成 6 位访客码，状态=visit_booked |
| 5 | 前台核销访客码 | 前台 | ui | 通过 | 0.73s | 访客码在 A 座前台核销成功，状态=visited |
| 6 | 纪要确认 | 招商顾问 | api | 通过 | 0.01s | 参观纪要确认落库，状态=minutes_confirmed |
| 7 | 9.5 折以内报价 | 招商顾问 | api | 通过 | 0.02s | 成交价为挂牌价 95.0%（9.5 折以内），成交价 1767000 分，状态=quoted |
| 8 | 电子签 | 签约双方 | ui | 通过 | 0.72s | 签约台完成两方签署（出租方+承租方），信封状态=signed，主状态=signed |
| 9 | 房态变为已租 | 运营中台 | api | 通过 | 0.01s | 房源 12F-1801 房态=rented，主状态=rented |
| 10 | 会员经理领取交接 | 会员经理 | api | 通过 | 0.01s | 会员经理 MM-021 领取交接，会员档案创建，状态=handed_over |
| 11 | 签约企业联系人在小程序完成认证 | 企业联系人 | skipped | 跳过 | 0.00s | 小程序步骤按 --skip-miniprogram 标记跳过（本轮显式要求跳过；默认执行方式为官方模拟器组件级真跑） |
| 12 | 小程序首页看到首月资源推荐 | 企业联系人 | skipped | 跳过 | 0.00s | 小程序步骤按 --skip-miniprogram 标记跳过（本轮显式要求跳过；默认执行方式为官方模拟器组件级真跑） |

## 已创建数据 ID

```json
{
  "rooms": "967729cb-8d90-4aff-bd10-ac8716a5680d,278acfe9-e6be-4998-8eaf-99ddd6be399e",
  "room_primary": "967729cb-8d90-4aff-bd10-ac8716a5680d",
  "room_secondary": "278acfe9-e6be-4998-8eaf-99ddd6be399e",
  "application_id": "17c3eabe-99c7-4789-bccb-cfcc5afe9041",
  "lead_id": "4961037a-8da3-4f2e-99a1-5fd1a5a846fb",
  "advisor_id": "ADV-101",
  "contact_id": "ad1e7628-b825-4fb1-930b-32a4cb1c72b3",
  "visit_id": "2aa2543b-6ed7-473d-88c3-1471a340c502",
  "visit_code": "605928",
  "minutes_id": "49cd50c8-c53e-4a21-995e-dd07d4ca4ee5",
  "quote_id": "87a9f668-fd9b-4d88-9e0e-d43eb6f042c8",
  "envelope_id": "d4c5c5d9-2c0f-4d2f-af36-2edac77f8f0b",
  "handover_id": "0561ca3e-7f35-4adf-8963-81100c100143",
  "member_id": "925b91e7-0d4d-4345-b637-67668ef1200d"
}
```

## run_id 清理校验

- 清理时间：2026-11-23T19:53:43.010+00:00
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

- artifacts_dir: `reports/artifacts/smk-skipmode-20261124-035339-6455`
- report_json: `reports/run_smk-skipmode-20261124-035339-6455.json`
- report_md: `reports/run_smk-skipmode-20261124-035339-6455.md`
