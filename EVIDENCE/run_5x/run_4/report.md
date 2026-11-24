# 招商全链路冒烟报告 · smk-5x-r4-20261124-142847-54bd

- 结论：**通过**
- 模式：full（小程序步骤执行）
- 平台地址：http://127.0.0.1:5600
- 开始：2026-11-24T06:28:47.242+00:00　结束：2026-11-24T06:28:51.778+00:00
- 总耗时：**4.54s**（阈值 600s）
- 通过 / 跳过 / 失败：12 / 0 / 0

| # | 步骤 | 执行方 | 方式 | 状态 | 耗时 | 关键断言 |
|---|------|--------|------|------|------|----------|
| 1 | 官网提交申请 | 官网访客 | ui | 通过 | 0.83s | 官网提交成功，申请单状态=submitted，返回 UUID 单号 |
| 2 | 线索按规则分配 | 销售中台 | api | 通过 | 0.01s | 线索分配命中规则 region=east->ADV-101，状态 assigned |
| 3 | 顾问首次联系 | 招商顾问 | ui | 通过 | 0.73s | 工作台点击后线索状态=contacted，页面回显联系记录 ID |
| 4 | 推进到预约参观 | 招商顾问 | api | 通过 | 0.01s | 预约参观创建成功，生成 6 位访客码，状态=visit_booked |
| 5 | 前台核销访客码 | 前台 | ui | 通过 | 0.75s | 访客码在 A 座前台核销成功，状态=visited |
| 6 | 纪要确认 | 招商顾问 | api | 通过 | 0.01s | 参观纪要确认落库，状态=minutes_confirmed |
| 7 | 9.5 折以内报价 | 招商顾问 | api | 通过 | 0.01s | 成交价为挂牌价 95.0%（9.5 折以内），成交价 1767000 分，状态=quoted |
| 8 | 电子签 | 签约双方 | ui | 通过 | 0.69s | 签约台完成两方签署（出租方+承租方），信封状态=signed，主状态=signed |
| 9 | 房态变为已租 | 运营中台 | api | 通过 | 0.01s | 房源 12F-1801 房态=rented，主状态=rented |
| 10 | 会员经理领取交接 | 会员经理 | api | 通过 | 0.01s | 会员经理 MM-021 领取交接，会员档案创建，状态=handed_over |
| 11 | 签约企业联系人在小程序完成认证 | 企业联系人 | miniapp | 通过 | 0.93s | 小程序内提交验证码完成企业联系人认证：POST /api/miniapp/certify → 200（22ms），页面 pages/entry/index 上真实输入并点击提交，phase=idle→certified，触发 certified 事件，状态=certified |
| 12 | 小程序首页看到首月资源推荐 | 企业联系人 | miniapp | 通过 | 0.00s | 小程序首页渲染 2026-11 首月资源包 3 项（页面上数到 3 个节点，与数据一致），GET /api/miniapp/home → 200（16ms），链路状态=activated |

## 已创建数据 ID

```json
{
  "rooms": "9a141948-9e73-4431-9b21-f9bb4c8acac5,62143059-4687-48f9-91b9-e4393740721b",
  "room_primary": "9a141948-9e73-4431-9b21-f9bb4c8acac5",
  "room_secondary": "62143059-4687-48f9-91b9-e4393740721b",
  "application_id": "9e6c69dd-b44d-4800-85c0-f1092a315d2e",
  "lead_id": "33dfc72c-bfbd-413b-8b87-ed8d7c514687",
  "advisor_id": "ADV-101",
  "contact_id": "c42b431d-f490-4100-8656-1753369fdc2d",
  "visit_id": "dc7d100a-9056-4d59-a13c-5060894db9c7",
  "visit_code": "540280",
  "minutes_id": "f2348736-980a-44db-ab37-70b50a225e55",
  "quote_id": "ed3dc0f1-c9c3-4391-b05f-243c71082b61",
  "envelope_id": "39bf7f54-e103-4875-bd30-b450c2f19d36",
  "handover_id": "d788ea6e-cbce-44b0-acf6-2977100e367d",
  "member_id": "dd0a291d-8f2e-44f1-b5ee-999ebd7b4661",
  "recommendation_id": "00054e6c-73a6-4a56-be77-b21f9749e55e"
}
```

## run_id 清理校验

- 清理时间：2026-11-24T06:28:51.816+00:00
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

- artifacts_dir: `reports/artifacts/smk-5x-r4-20261124-142847-54bd`
- report_json: `reports/run_smk-5x-r4-20261124-142847-54bd.json`
- report_md: `reports/run_smk-5x-r4-20261124-142847-54bd.md`
