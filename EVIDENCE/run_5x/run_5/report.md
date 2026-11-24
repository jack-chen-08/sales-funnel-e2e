# 招商全链路冒烟报告 · smk-5x-r5-20261124-144214-d749

- 结论：**通过**
- 模式：full（小程序步骤执行）
- 平台地址：http://127.0.0.1:5600
- 开始：2026-11-24T06:42:14.777+00:00　结束：2026-11-24T06:42:38.832+00:00
- 总耗时：**24.05s**（阈值 600s）
- 通过 / 跳过 / 失败：12 / 0 / 0

| # | 步骤 | 执行方 | 方式 | 状态 | 耗时 | 关键断言 |
|---|------|--------|------|------|------|----------|
| 1 | 官网提交申请 | 官网访客 | ui | 通过 | 0.91s | 官网提交成功，申请单状态=submitted，返回 UUID 单号 |
| 2 | 线索按规则分配 | 销售中台 | api | 通过 | 0.01s | 线索分配命中规则 region=east->ADV-101，状态 assigned |
| 3 | 顾问首次联系 | 招商顾问 | ui | 通过 | 0.81s | 工作台点击后线索状态=contacted，页面回显联系记录 ID |
| 4 | 推进到预约参观 | 招商顾问 | api | 通过 | 0.01s | 预约参观创建成功，生成 6 位访客码，状态=visit_booked |
| 5 | 前台核销访客码 | 前台 | ui | 通过 | 0.80s | 访客码在 A 座前台核销成功，状态=visited |
| 6 | 纪要确认 | 招商顾问 | api | 通过 | 0.01s | 参观纪要确认落库，状态=minutes_confirmed |
| 7 | 9.5 折以内报价 | 招商顾问 | api | 通过 | 0.01s | 成交价为挂牌价 95.0%（9.5 折以内），成交价 1767000 分，状态=quoted |
| 8 | 电子签 | 签约双方 | ui | 通过 | 0.74s | 签约台完成两方签署（出租方+承租方），信封状态=signed，主状态=signed |
| 9 | 房态变为已租 | 运营中台 | api | 通过 | 0.01s | 房源 12F-1801 房态=rented，主状态=rented |
| 10 | 会员经理领取交接 | 会员经理 | api | 通过 | 0.01s | 会员经理 MM-021 领取交接，会员档案创建，状态=handed_over |
| 11 | 签约企业联系人在小程序完成认证 | 企业联系人 | miniapp | 通过 | 19.94s | 小程序内提交验证码完成企业联系人认证：POST /api/miniapp/certify → 200（27ms），页面 pages/entry/index 上真实输入并点击提交，phase=idle→certified，触发 certified 事件，状态=certified |
| 12 | 小程序首页看到首月资源推荐 | 企业联系人 | miniapp | 通过 | 0.00s | 小程序首页渲染 2026-11 首月资源包 3 项（页面上数到 3 个节点，与数据一致），GET /api/miniapp/home → 200（53ms），链路状态=activated |

## 已创建数据 ID

```json
{
  "rooms": "6bb887ad-140e-4934-9fc0-0865ac065ad0,2892f13f-0a87-45f8-b861-675d87804fe4",
  "room_primary": "6bb887ad-140e-4934-9fc0-0865ac065ad0",
  "room_secondary": "2892f13f-0a87-45f8-b861-675d87804fe4",
  "application_id": "7f825fed-cc1c-4260-81dd-ade81ce354eb",
  "lead_id": "11b6487f-386c-4e19-b947-fe6864aa6fd1",
  "advisor_id": "ADV-101",
  "contact_id": "f74e501c-64f2-4fe0-9097-d7a38536e986",
  "visit_id": "3b5753b9-b96b-4891-95bb-7b9e6d704301",
  "visit_code": "976277",
  "minutes_id": "d39ed75f-8aaf-4b72-b8ab-61c15d6f7634",
  "quote_id": "fd231d82-4bf4-44c2-a7cf-c831a38b24cb",
  "envelope_id": "a41e0d15-f2fa-4f23-b600-b49ae2710a32",
  "handover_id": "490a4ec8-485b-4841-9109-b5ab70f11810",
  "member_id": "9a9c2139-8ad6-4eeb-86b9-0f77b571c660",
  "recommendation_id": "29e30a62-3573-4440-b198-c77ac2a38c52"
}
```

## run_id 清理校验

- 清理时间：2026-11-24T06:42:38.873+00:00
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

- artifacts_dir: `reports/artifacts/smk-5x-r5-20261124-144214-d749`
- report_json: `reports/run_smk-5x-r5-20261124-144214-d749.json`
- report_md: `reports/run_smk-5x-r5-20261124-144214-d749.md`
