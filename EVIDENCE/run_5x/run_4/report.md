# 招商全链路冒烟报告 · smk-5x-r4-20261124-145310-6cdc

- 结论：**通过**
- 模式：full（小程序步骤执行）
- 平台地址：http://127.0.0.1:5600
- 开始：2026-11-24T06:53:10.307+00:00　结束：2026-11-24T06:53:34.069+00:00
- 总耗时：**23.76s**（阈值 600s）
- 通过 / 跳过 / 失败：12 / 0 / 0

| # | 步骤 | 执行方 | 方式 | 状态 | 耗时 | 关键断言 |
|---|------|--------|------|------|------|----------|
| 1 | 官网提交申请 | 官网访客 | ui | 通过 | 0.93s | 官网提交成功，申请单状态=submitted，返回 UUID 单号 |
| 2 | 线索按规则分配 | 销售中台 | api | 通过 | 0.01s | 线索分配命中规则 region=east->ADV-101，状态 assigned |
| 3 | 顾问首次联系 | 招商顾问 | ui | 通过 | 0.77s | 工作台点击后线索状态=contacted，页面回显联系记录 ID |
| 4 | 推进到预约参观 | 招商顾问 | api | 通过 | 0.02s | 预约参观创建成功，生成 6 位访客码，状态=visit_booked |
| 5 | 前台核销访客码 | 前台 | ui | 通过 | 0.82s | 访客码在 A 座前台核销成功，状态=visited |
| 6 | 纪要确认 | 招商顾问 | api | 通过 | 0.01s | 参观纪要确认落库，状态=minutes_confirmed |
| 7 | 9.5 折以内报价 | 招商顾问 | api | 通过 | 0.01s | 成交价为挂牌价 95.0%（9.5 折以内），成交价 1767000 分，状态=quoted |
| 8 | 电子签 | 签约双方 | ui | 通过 | 0.74s | 签约台完成两方签署（出租方+承租方），信封状态=signed，主状态=signed |
| 9 | 房态变为已租 | 运营中台 | api | 通过 | 0.01s | 房源 12F-1801 房态=rented，主状态=rented |
| 10 | 会员经理领取交接 | 会员经理 | api | 通过 | 0.01s | 会员经理 MM-021 领取交接，会员档案创建，状态=handed_over |
| 11 | 签约企业联系人在小程序完成认证 | 企业联系人 | miniapp | 通过 | 19.78s | 小程序内提交验证码完成企业联系人认证：POST /api/miniapp/certify → 200（34ms），页面 pages/entry/index 上真实输入并点击提交，phase=idle→certified，触发 certified 事件，状态=certified |
| 12 | 小程序首页看到首月资源推荐 | 企业联系人 | miniapp | 通过 | 0.00s | 小程序首页渲染 2026-11 首月资源包 3 项（页面上数到 3 个节点，与数据一致），GET /api/miniapp/home → 200（60ms），链路状态=activated |

## 已创建数据 ID

```json
{
  "rooms": "428ee7c8-2022-4221-86be-b07b6676a375,85007f47-b915-42e8-a468-3f142bccd018",
  "room_primary": "428ee7c8-2022-4221-86be-b07b6676a375",
  "room_secondary": "85007f47-b915-42e8-a468-3f142bccd018",
  "application_id": "b2cc145b-ebaa-40bd-9efe-b5b6e5ee9895",
  "lead_id": "fe200dba-9704-4eb5-9222-2682c89126cb",
  "advisor_id": "ADV-101",
  "contact_id": "4fe0cfac-abdf-4bef-b698-ab8f6d1fd84d",
  "visit_id": "34014446-89ce-4320-aeea-3cc1c45e8be4",
  "visit_code": "219383",
  "minutes_id": "3b6f9aec-4aee-4260-8ce3-190f742d5920",
  "quote_id": "a6c5ea96-e8fa-4843-878b-9ebec0fe6ab9",
  "envelope_id": "6115a36d-5b13-46e0-84d6-55cc66356ebd",
  "handover_id": "dc4df3ff-32bf-4bec-a4d6-2e42d7f67407",
  "member_id": "05fc4cd7-ad43-48d0-9954-132babd6afbc",
  "recommendation_id": "4d3b7a22-8318-4038-a69e-005247dfb200"
}
```

## run_id 清理校验

- 清理时间：2026-11-24T06:53:34.108+00:00
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

- artifacts_dir: `reports/artifacts/smk-5x-r4-20261124-145310-6cdc`
- report_json: `reports/run_smk-5x-r4-20261124-145310-6cdc.json`
- report_md: `reports/run_smk-5x-r4-20261124-145310-6cdc.md`
