# 招商全链路冒烟报告 · smk-auto14-20261124-142939-a30c

- 结论：**通过**
- 模式：full（小程序步骤执行）
- 平台地址：http://127.0.0.1:5600
- 开始：2026-11-24T06:29:39.549+00:00　结束：2026-11-24T06:29:54.934+00:00
- 总耗时：**15.38s**（阈值 600s）
- 通过 / 跳过 / 失败：12 / 0 / 0

| # | 步骤 | 执行方 | 方式 | 状态 | 耗时 | 关键断言 |
|---|------|--------|------|------|------|----------|
| 1 | 官网提交申请 | 官网访客 | ui | 通过 | 1.19s | 官网提交成功，申请单状态=submitted，返回 UUID 单号 |
| 2 | 线索按规则分配 | 销售中台 | api | 通过 | 0.04s | 线索分配命中规则 region=east->ADV-101，状态 assigned |
| 3 | 顾问首次联系 | 招商顾问 | ui | 通过 | 1.05s | 工作台点击后线索状态=contacted，页面回显联系记录 ID |
| 4 | 推进到预约参观 | 招商顾问 | api | 通过 | 0.03s | 预约参观创建成功，生成 6 位访客码，状态=visit_booked |
| 5 | 前台核销访客码 | 前台 | ui | 通过 | 1.09s | 访客码在 A 座前台核销成功，状态=visited |
| 6 | 纪要确认 | 招商顾问 | api | 通过 | 0.02s | 参观纪要确认落库，状态=minutes_confirmed |
| 7 | 9.5 折以内报价 | 招商顾问 | api | 通过 | 0.02s | 成交价为挂牌价 95.0%（9.5 折以内），成交价 1767000 分，状态=quoted |
| 8 | 电子签 | 签约双方 | ui | 通过 | 0.90s | 签约台完成两方签署（出租方+承租方），信封状态=signed，主状态=signed |
| 9 | 房态变为已租 | 运营中台 | api | 通过 | 0.02s | 房源 12F-1801 房态=rented，主状态=rented |
| 10 | 会员经理领取交接 | 会员经理 | api | 通过 | 0.02s | 会员经理 MM-021 领取交接，会员档案创建，状态=handed_over |
| 11 | 签约企业联系人在小程序完成认证 | 企业联系人 | miniapp | 通过 | 10.03s | 小程序内提交验证码完成企业联系人认证：POST /api/miniapp/certify → 200（31ms），页面 pages/entry/index 上真实输入并点击提交，phase=idle→certified，触发 certified 事件，状态=certified |
| 12 | 小程序首页看到首月资源推荐 | 企业联系人 | miniapp | 通过 | 0.00s | 小程序首页渲染 2026-11 首月资源包 3 项（页面上数到 3 个节点，与数据一致），GET /api/miniapp/home → 200（18ms），链路状态=activated |

## 已创建数据 ID

```json
{
  "rooms": "22d4c2aa-2e70-4f14-9c08-cda12d87f17c,035877b8-8079-44f3-ac92-25a08c4a3df6",
  "room_primary": "22d4c2aa-2e70-4f14-9c08-cda12d87f17c",
  "room_secondary": "035877b8-8079-44f3-ac92-25a08c4a3df6",
  "application_id": "70d04ace-8055-434e-ac1e-80f0201cc79b",
  "lead_id": "77050585-dfb2-4b74-89c6-90b5eb55ad11",
  "advisor_id": "ADV-101",
  "contact_id": "85ea265e-0d73-41d2-84a5-de6ae2f7b40a",
  "visit_id": "1afd7e64-a812-43f5-81e7-29e71eb3d3fe",
  "visit_code": "615941",
  "minutes_id": "829af73d-78ff-468a-a3fa-2462ee6cb509",
  "quote_id": "49ad14fd-cd16-4e71-9885-3c8bafc653ad",
  "envelope_id": "41f6b166-2909-4782-ab0a-bc23417fe837",
  "handover_id": "03cfedb6-d93b-4597-aed2-b3a80894c74a",
  "member_id": "5d455fcc-9931-48e2-8e69-790a0a8a9f2e",
  "recommendation_id": "3cc03456-98e1-4325-a4d2-b1ff924b5636"
}
```

## run_id 清理校验

- 清理时间：2026-11-24T06:29:54.980+00:00
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

- artifacts_dir: `reports/artifacts/smk-auto14-20261124-142939-a30c`
- report_json: `reports/run_smk-auto14-20261124-142939-a30c.json`
- report_md: `reports/run_smk-auto14-20261124-142939-a30c.md`
