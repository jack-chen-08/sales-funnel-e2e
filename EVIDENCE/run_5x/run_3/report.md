# 招商全链路冒烟报告 · smk-5x-r3-20261124-145234-b7e4

- 结论：**通过**
- 模式：full（小程序步骤执行）
- 平台地址：http://127.0.0.1:5600
- 开始：2026-11-24T06:52:34.576+00:00　结束：2026-11-24T06:52:59.041+00:00
- 总耗时：**24.47s**（阈值 600s）
- 通过 / 跳过 / 失败：12 / 0 / 0

| # | 步骤 | 执行方 | 方式 | 状态 | 耗时 | 关键断言 |
|---|------|--------|------|------|------|----------|
| 1 | 官网提交申请 | 官网访客 | ui | 通过 | 1.00s | 官网提交成功，申请单状态=submitted，返回 UUID 单号 |
| 2 | 线索按规则分配 | 销售中台 | api | 通过 | 0.01s | 线索分配命中规则 region=east->ADV-101，状态 assigned |
| 3 | 顾问首次联系 | 招商顾问 | ui | 通过 | 0.96s | 工作台点击后线索状态=contacted，页面回显联系记录 ID |
| 4 | 推进到预约参观 | 招商顾问 | api | 通过 | 0.05s | 预约参观创建成功，生成 6 位访客码，状态=visit_booked |
| 5 | 前台核销访客码 | 前台 | ui | 通过 | 1.18s | 访客码在 A 座前台核销成功，状态=visited |
| 6 | 纪要确认 | 招商顾问 | api | 通过 | 0.08s | 参观纪要确认落库，状态=minutes_confirmed |
| 7 | 9.5 折以内报价 | 招商顾问 | api | 通过 | 0.06s | 成交价为挂牌价 95.0%（9.5 折以内），成交价 1767000 分，状态=quoted |
| 8 | 电子签 | 签约双方 | ui | 通过 | 0.96s | 签约台完成两方签署（出租方+承租方），信封状态=signed，主状态=signed |
| 9 | 房态变为已租 | 运营中台 | api | 通过 | 0.03s | 房源 12F-1801 房态=rented，主状态=rented |
| 10 | 会员经理领取交接 | 会员经理 | api | 通过 | 0.05s | 会员经理 MM-021 领取交接，会员档案创建，状态=handed_over |
| 11 | 签约企业联系人在小程序完成认证 | 企业联系人 | miniapp | 通过 | 19.00s | 小程序内提交验证码完成企业联系人认证：POST /api/miniapp/certify → 200（26ms），页面 pages/entry/index 上真实输入并点击提交，phase=idle→certified，触发 certified 事件，状态=certified |
| 12 | 小程序首页看到首月资源推荐 | 企业联系人 | miniapp | 通过 | 0.00s | 小程序首页渲染 2026-11 首月资源包 3 项（页面上数到 3 个节点，与数据一致），GET /api/miniapp/home → 200（19ms），链路状态=activated |

## 已创建数据 ID

```json
{
  "rooms": "09aaad7f-eba1-4704-ba93-b307a76b039c,01ed0946-419a-492f-a950-0981a2f35335",
  "room_primary": "09aaad7f-eba1-4704-ba93-b307a76b039c",
  "room_secondary": "01ed0946-419a-492f-a950-0981a2f35335",
  "application_id": "24dae496-6f87-4d24-813f-9a54f91a0c6e",
  "lead_id": "b47a3f35-9a72-4193-b9ea-db701dfd4825",
  "advisor_id": "ADV-101",
  "contact_id": "5edcc618-1158-4285-bfdc-a40c2a540c79",
  "visit_id": "791bd128-4717-4cf2-88b6-432522a7b644",
  "visit_code": "511389",
  "minutes_id": "a12ee31f-09d8-4f9a-b715-cb3e1aa42866",
  "quote_id": "caea22ae-6feb-43e1-8147-dd932ff58b80",
  "envelope_id": "31f873a5-d085-43d9-b511-ac44a6816125",
  "handover_id": "b70ce655-d25c-4c4d-9a79-a8fd19270829",
  "member_id": "5c6b6825-894a-4901-84e8-77f7d918efd2",
  "recommendation_id": "c2c2ca58-75e8-4eb5-8ba9-82513d96319e"
}
```

## run_id 清理校验

- 清理时间：2026-11-24T06:52:59.077+00:00
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

- artifacts_dir: `reports/artifacts/smk-5x-r3-20261124-145234-b7e4`
- report_json: `reports/run_smk-5x-r3-20261124-145234-b7e4.json`
- report_md: `reports/run_smk-5x-r3-20261124-145234-b7e4.md`
